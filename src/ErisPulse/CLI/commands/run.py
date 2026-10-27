"""
Run 命令实现

直接运行主程序，支持热重载模式

{!--< tips >!--}
1. `epsdk run` 以「监督进程 + 框架子进程」结构运行：子进程崩溃自动退避重试、
   硬重启（退出码 42）自动重拉，监督进程自身只有 Ctrl+C 能停止
2. `epsdk run --reload` 同样走监督结构：worker 子进程内做文件监控与组件级
   热重载（保存 .py 即触发热重载，不再整框架重启）；硬重启由监督进程重拉
   全新 worker（框架新代码生效）
3. `epsdk run main.py --reload` 以脚本子进程 + 重载信号方式运行（脚本退出码
   42 同样立即重拉）
{!--< /tips >!--}
"""

import asyncio
import os
import runpy
import subprocess
import sys
import threading
import time
from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from pathlib import Path

from rich.panel import Panel

from ...runtime.file_watcher import (
    FileChangeEvent,
    FileSystemEventHandler,
    PollingObserver,
)
from ..base import Command
from ..console import console
from ..constants import (
    CLI_CHILD_TERMINATE_WAIT_SECS,
    ENV_RELOAD_WORKER,
    ENV_SUPERVISED,
    HARD_RESTART_EXIT_CODE,
    RUN_CRASH_BACKOFF_MAX_SECS,
    RUN_CRASH_BACKOFF_PER_CRASH_SECS,
    RUN_PERSISTENT_CRASH_HINT_THRESHOLD,
    RUN_RESTART_PAUSE_SECS,
)
from ..i18n import i18n
from ..utils import runtime_state
from ..utils.package_manager import (
    PythonSource,
    resolve_target_python,
    warn_if_uv_isolated,
    warn_if_uv_tool_env_without_project,
)

# reload worker 子进程的引导代码：经 `python -c` 拉起，argv 尾部携带可选脚本路径
_RELOAD_WORKER_BOOTSTRAP = (
    "import sys; "
    "from ErisPulse.CLI.commands.run import run_reload_worker; "
    "sys.exit(run_reload_worker(sys.argv[1] if len(sys.argv) > 1 else None))"
)

# SDK 直跑引导（非 reload 模式的框架子进程入口，与既有行为一致）
_SDK_BOOTSTRAP = (
    "import asyncio; from ErisPulse import sdk; "
    "asyncio.run(sdk.run(keep_running=True))"
)


class ReloadHandler(FileSystemEventHandler):
    """
    文件系统事件处理器

    监控 .py 文件变更并触发 sdk.restart() 组件级热重载

    {!--< tips >!--}
    1. 文件监控运行在独立线程，通过 run_coroutine_threadsafe 安全调度到事件循环
    2. 合并去抖：首个事件立即触发，窗口（FILE_RELOAD_DEBOUNCE_SECS）内的后续
       变更合并且窗口静默后统一补发一次（不丢弃）
    3. 新建 .py 文件（on_created）同样触发热重载；删除不触发（插件目录的删除
       清理由插件热重载 watcher 负责）
    {!--< /tips >!--}
    """

    def __init__(self, loop: asyncio.AbstractEventLoop):
        """
        初始化热重载处理器

        :param loop: [asyncio.AbstractEventLoop] 用于调度重载协程的事件循环
        """
        super().__init__()
        from ...Core.constants import FILE_RELOAD_DEBOUNCE_SECS

        self._loop = loop
        self._debounce = FILE_RELOAD_DEBOUNCE_SECS
        self._lock = threading.Lock()
        self._pending: set[str] = set()
        self._timer: threading.Timer | None = None

    def on_modified(self, event: FileChangeEvent) -> None:
        """
        文件修改事件回调，对 .py 文件触发热重载

        :param event: [FileChangeEvent] 文件系统事件
        """
        self._on_event(event.src_path)

    def on_created(self, event: FileChangeEvent) -> None:
        """
        文件创建事件回调（新建 .py 文件同样触发热重载）

        :param event: [FileChangeEvent] 文件系统事件
        """
        self._on_event(event.src_path)

    def _on_event(self, src_path: str) -> None:
        """{!--< internal-use >!--} 合并去抖入口"""
        if not src_path.endswith(".py"):
            return
        with self._lock:
            if self._timer is not None:
                # 去抖窗口内：合并入队，窗口静默后由定时器统一补发
                self._pending.add(src_path)
                return
            # 窗口外：立即触发（保持「保存即重载」的即时性），并武装补发定时器。
            # 定时器先存字段再在锁外 start：并发 close() 可能把字段置 None，
            # 锁外必须用局部引用，否则 watcher 线程内 AttributeError
            paths = {src_path}
            timer = threading.Timer(self._debounce, self._flush_pending)
            timer.daemon = True
            self._timer = timer
        timer.start()
        self._dispatch(paths)

    def _flush_pending(self) -> None:
        """去抖窗口到期：补发窗口内合并的变更（可为空）"""
        with self._lock:
            self._timer = None
            if not self._pending:
                return
            paths = set(self._pending)
            self._pending.clear()
        self._dispatch(paths)

    def close(self) -> None:
        """停止补发定时器（监控停止时调用）"""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._pending.clear()

    def _dispatch(self, paths: set[str]) -> None:
        """
        {!--< internal-use >!--}
        先提示变更文件（在调度重载之前——用户应先看到触发原因），再调度热重载
        """
        for path in sorted(paths):
            console.print(i18n.t("cli.run.file_changed", file=Path(path).name))

        async def _do_reload():
            """执行 SDK 组件级热重载"""
            try:
                from ... import sdk

                await sdk.restart()
            except Exception as e:
                console.print(
                    f"[error]{i18n.t('cli.run.hot_reload_failed', error=e)}[/]"
                )

        try:
            asyncio.run_coroutine_threadsafe(_do_reload(), self._loop)
        except RuntimeError:
            pass


class _DevWatchdog:
    """
    {!--< internal-use >!--}
    dev 模式文件监控（reload worker 内运行）

    忽略 .venv/.git 等目录；插件目录默认移交插件热重载 watcher 处理
    （全量 restart 本就覆盖插件代码，避免双重触发）。
    """

    def __init__(self) -> None:
        self._observer: PollingObserver | None = None
        self._handler: ReloadHandler | None = None

    @staticmethod
    def _resolve_excludes() -> "tuple[list[str] | None, list[str]]":
        """
        解析 dev 监控的忽略目录与插件目录移交清单

        :return: (PollingObserver ignore_dirs——None = 内置默认清单, 需移交
            插件 watcher 并从自身监控排除的插件目录名列表)
        """
        from ...runtime.frame_config import get_framework_config

        try:
            framework = get_framework_config()
        except Exception:
            framework = {}
        raw = framework.get("watch_ignore_dirs")
        ignore: list[str] | None = None
        if isinstance(raw, (list, tuple)):
            ignore = [str(d) for d in raw]
        plugin_dirs: list[str] = []
        if framework.get("watch_include_plugin_dirs", True):
            raw_dirs = framework.get("plugins_dir", "plugins")
            if isinstance(raw_dirs, str):
                plugin_dirs = [raw_dirs]
            elif isinstance(raw_dirs, (list, tuple)):
                plugin_dirs = [str(d) for d in raw_dirs]
        return ignore, plugin_dirs

    def start(self, watch_dir: str, loop: asyncio.AbstractEventLoop) -> None:
        """
        启动 dev 文件监控并打印模式面板

        :param watch_dir: 监控目录
        :param loop: 用于调度重载的事件循环
        """
        from ...Core.constants import FILE_WATCHER_IGNORED_DIRS

        if not Path(watch_dir).exists():
            return

        ignore, plugin_dirs = self._resolve_excludes()
        merged_ignore = set(FILE_WATCHER_IGNORED_DIRS) if ignore is None else set(ignore)
        merged_ignore.update(plugin_dirs)

        self._observer = PollingObserver(ignore_dirs=sorted(merged_ignore))
        self._handler = ReloadHandler(loop=loop)
        self._observer.schedule(self._handler, watch_dir, recursive=True)
        self._observer.start()

        console.print(
            Panel(
                i18n.t(
                    "cli.run.reload_mode_panel",
                    watch_dir=watch_dir,
                    ignored=", ".join(sorted(merged_ignore)),
                ),
                title=i18n.t("cli.run.reload_title"),
                border_style="info",
            )
        )

    def stop(self) -> None:
        """停止 dev 文件监控（幂等）"""
        if self._handler is not None:
            self._handler.close()
            self._handler = None
        if self._observer is not None:
            from ...Core.constants import FILE_WATCH_POLL_INTERVAL_SECS
            from ...Core.logger import logger

            try:
                self._observer.stop()
                # 有限等待：轮询线程为守护线程，超时后自行退出
                self._observer.join(timeout=FILE_WATCH_POLL_INTERVAL_SECS * 2)
            except Exception as e:
                logger.debug(f"dev watcher stop failed: {e!r}")
            self._observer = None


def run_reload_worker(script: str | None) -> int:
    """
    reload worker 进程入口（由监督进程经 ``-c`` 引导拉起，跨进程公共入口）

    SDK 模式（script=None）：dev 文件监控 + 自动启用插件热重载 + ``sdk.run``；
    保存 .py 触发组件级热重载。硬重启（``hard_restart``）以退出码 42 退出，
    由监督进程重拉全新 worker（框架新代码生效）。

    不写运行状态文件（runtime.json 归监督进程维护）；argv 由监督进程透传。

    :param script: 保留参数位（脚本模式的 --reload 不走 worker，见
        ``RunCommand._run_script``）
    :return: 进程退出码
    """
    watchdog = _DevWatchdog()
    try:

        async def _run():
            """dev 监控 + 框架主循环"""
            from ... import sdk

            loop = asyncio.get_running_loop()
            watchdog.start(".", loop)
            # 插件目录已从全量监控排除：显式接管插件目录的精确监控
            # （单模块热重载，而非每次保存都全量 restart）
            try:
                sdk.enable_plugin_hot_reload()
            except Exception:
                pass
            await sdk.run(keep_running=True)

        asyncio.run(_run())
    except KeyboardInterrupt:
        pass
    finally:
        watchdog.stop()
    return 0


__all__ = ["RunCommand", "run_reload_worker"]


class RunCommand(Command):
    """
    Run 命令

    运行主程序，支持热重载模式
    """

    name = "run"
    description = i18n.t("cli.run.description")
    aliases = ["r"]
    category = "project"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "script", nargs="?", default=None, help=i18n.t("cli.run.script_help")
        )
        parser.add_argument(
            "--reload",
            action="store_true",
            default=False,
            help=i18n.t("cli.run.reload_help"),
        )
        parser.add_argument(
            "--strict",
            action=BooleanOptionalAction,
            default=None,
            help=i18n.t("cli.run.strict_help"),
        )

    def execute(self, args: Namespace) -> None:
        script = args.script
        reload_mode = args.reload

        # uv 隔离环境检测：无项目的 `uv run` 语义下安装的包不会持久化
        warn_if_uv_isolated()
        # uv tool 环境且无项目环境：组件应装进项目 .venv 而非工具环境
        warn_if_uv_tool_env_without_project()
        # 目标解释器解析：项目 .venv 优先（bot 依赖应装在项目环境而非全局）
        self.python_exe, self.python_source = resolve_target_python()
        if self.python_source != PythonSource.CURRENT:
            console.print(
                f"[info]  {i18n.t('cli.run.venv_using', python=self.python_exe)}[/]"
            )

        # 严格模式三态：--strict/--no-strict 临时覆盖（不落盘），缺省跟随
        # ErisPulse.framework.strict_mode 配置
        preflight_strict, strict_env = self._resolve_strict(
            getattr(args, "strict", None)
        )
        if strict_env is not None:
            # 经 ERISPULSE_FRAMEWORK_STRICT_MODE → ErisPulse.framework.strict_mode
            # 的环境变量覆盖通道临时改写本次运行的框架严格级别；子进程由
            # Popen 继承环境自动生效，runpy 同进程 / reload worker 同样读取
            os.environ["ERISPULSE_FRAMEWORK_STRICT_MODE"] = str(strict_env)

        # 启动前自检：配置可解析性 / 组件必填项（严格模式失败即退出）
        self._preflight(strict=preflight_strict)

        if script:
            if not Path(script).exists():
                # 列出当前目录的 .py 文件作为上下文参考
                py_files = sorted(Path().glob("*.py"))
                file_list = ", ".join(f.name for f in py_files[:5]) if py_files else None
                hint_text = i18n.t("cli.run.use_init")
                if file_list:
                    hint_text += "  " + i18n.t("cli.run.available_scripts", files=file_list)
                console.print(
                    f"[error]{i18n.t('cli.run.script_not_found', script=script)}[/]"
                )
                console.print(f"[info]{hint_text}[/]")
                return
            if Path(script).is_dir():
                console.print(
                    f"[error]{i18n.t('cli.run.is_directory', script=script)}[/]"
                )
                console.print(
                    "[info]{}[/]".format(i18n.t("cli.run.specify_file", script=script))
                )
                return
            self._run_script(script, reload_mode)
        else:
            self._run_internal(reload_mode)

    _RESTART_EXIT_CODE = HARD_RESTART_EXIT_CODE

    def _read_strict_mode(self) -> int:
        """
        读取框架严格模式配置级别（``ErisPulse.framework.strict_mode``）

        走 frame_config 的内存合并默认值通道（不要求配置文件存在该键），
        环境变量 ``ERISPULSE_FRAMEWORK_STRICT_MODE`` 的覆盖同样生效。

        :return: [int] 0=宽松 / 1=跳过 / 2=致命；读取失败按宽松(0)处理
        """
        try:
            from ...runtime.frame_config import get_config

            value = get_config("framework").get("strict_mode", 0)
            return int(value) if isinstance(value, (int, float)) else 0
        except Exception:
            return 0

    def _resolve_strict(self, strict_arg: bool | None) -> tuple[bool, int | None]:
        """
        解析严格模式三态：显式参数临时覆盖，缺省跟随框架配置

        :param strict_arg: [bool | None] ``--strict`` / ``--no-strict`` 的解析值，
            None 表示未传参
        :return: ([tuple]) ``(预检是否严格, 框架级别注入值)``——注入值非 None 时
            写入 ``ERISPULSE_FRAMEWORK_STRICT_MODE`` 临时覆盖本次运行的框架
            严格级别（不落盘，子进程经环境继承）；None 表示框架级别不动
        """
        configured = self._read_strict_mode()
        if strict_arg is None:
            # 未传参：预检严格性跟随配置；框架级别不动
            return configured >= 1, None
        if strict_arg:
            # 临时开启：预检失败即退出；框架级别提升为至少"跳过"级
            # （配置已为 2 时保持 2，只升不降）
            return True, max(configured, 1)
        # 临时关闭：预检仅警告；框架级别压到宽松
        return False, 0

    def _preflight(self, strict: bool):
        """
        启动前快速自检：配置文件可解析性与已装组件必填项完整性

        严格性来源：``--strict`` / ``--no-strict`` 显式指定，缺省跟随
        ``ErisPulse.framework.strict_mode``（>=1 视为严格）。检查失败默认仅
        警告并继续启动——框架对缺失配置按"正常首次启动"容忍，警告不应
        挡住运行；``strict=True`` 时打印失败项并以退出码 1 终止。自检自身
        出现任何异常（依赖缺失、组件发现失败等）一律跳过，绝不阻塞启动。
        不含任何网络探测。

        :param strict: [bool] 检查失败时是否强制退出
        """
        failures: list[str] = []
        infos: list[str] = []
        try:
            config_path = Path("config") / "config.toml"
            if not config_path.exists():
                infos.append(
                    i18n.t("cli.run.preflight_config_missing", path=config_path)
                )
            else:
                import tomlclass
                from tomlclass import TOMLParseError

                try:
                    tomlclass.load_path(str(config_path))
                except TOMLParseError as e:
                    failures.append(
                        i18n.t(
                            "cli.run.preflight_config_broken",
                            path=config_path,
                            error=(
                                f"line {e.line if e.line is not None else '?'}, "
                                f"col {e.col if e.col is not None else '?'}: {e.message}"
                            ),
                        )
                    )

            from ..utils.config_wizard import (
                STATUS_INCOMPLETE,
                get_target_status,
                load_config_targets,
            )

            incomplete = []
            for target in load_config_targets():
                status, _errors = get_target_status(target)
                # 与 doctor 同口径：仅"已启用但必填项缺失"判失败，
                # 完全未配置属尚未开始配置，不算故障
                if status == STATUS_INCOMPLETE:
                    incomplete.append(target.name)
            if incomplete:
                failures.append(
                    i18n.t("cli.run.preflight_incomplete", names=", ".join(incomplete))
                )
        except Exception:
            console.print(f"[dim]  {i18n.t('cli.run.preflight_skipped')}[/]")
            return

        for info in infos:
            console.print(f"[info]  {info}[/]")
        if not failures:
            return

        for failure in failures:
            console.print(f"[warning]  {failure}[/]")
        if strict:
            console.print(f"[error]{i18n.t('cli.run.preflight_strict_exit')}[/]")
            sys.exit(1)
        console.print(f"[info]{i18n.t('cli.run.preflight_warn_continue')}[/]")

    def _print_hard_restart_reason(self) -> None:
        """
        {!--< internal-use >!--}
        展示并消费硬重启观测标记（worker 退出前写入 runtime.json）
        """
        data = runtime_state.read()
        if not data:
            return
        reason = data.get("hard_restart_reason")
        if reason is None:
            return
        console.print(
            f"[info]{i18n.t('cli.run.hard_restart_reason', reason=reason or '-')}[/]"
        )
        runtime_state.clear_mark()

    def _supervise(self, cmd: list[str], *, reload_worker: bool = False) -> None:
        """
        {!--< internal-use >!--}
        监督循环：拉起并看护框架子进程

        - 退出码 42（硬重启）：展示原因后重拉全新子进程
        - 退出码 0：正常退出，停止监督
        - 其它退出码：按递增退避自动重试；连续同码崩溃达到阈值输出排查指引

        :param cmd: 子进程命令行
        :param reload_worker: 子进程是否为 reload worker（注入 ENV_RELOAD_WORKER）
        """
        crash_count = 0
        # 连续同退出码崩溃计数：达到阈值输出一次排查指引（确定性故障
        # 退避重试无意义，与其反复失败不如引导留现场）
        consecutive_same_code = 0
        last_crash_code: int | None = None
        crash_hint_shown = False
        process = None
        try:
            while True:
                # 注入监督者标记：子进程据此判断"有父进程会在退出码 42 时重新拉起我"，
                # 从而 hard_restart() 走退出码契约而非 self-respawn。
                child_env = dict(os.environ)
                child_env[ENV_SUPERVISED] = "cli"
                child_env.setdefault("PYTHONIOENCODING", "utf-8")
                if reload_worker:
                    child_env[ENV_RELOAD_WORKER] = "1"
                process = subprocess.Popen(cmd, env=child_env)
                # 每次拉起新子进程都更新状态文件（stop 先断子进程再停监督者）
                runtime_state.update_child(process.pid)
                process.wait()

                if process.returncode == self._RESTART_EXIT_CODE:
                    self._print_hard_restart_reason()
                    console.print(f"[info]{i18n.t('cli.run.restart_request')}[/]")
                    crash_count = 0
                    time.sleep(RUN_RESTART_PAUSE_SECS)
                    continue

                if process.returncode == 0:
                    # 子进程正常退出：finish，不再拉起
                    console.print(f"[info]{i18n.t('cli.run.process_exited')}[/]")
                    break

                # 非硬重启/非正常退出码：模块/适配器内部错误导致子进程异常终止
                # 不退出主进程，等待后自动重试
                crash_count += 1
                if process.returncode == last_crash_code:
                    consecutive_same_code += 1
                else:
                    consecutive_same_code = 1
                    last_crash_code = process.returncode
                if (
                    not crash_hint_shown
                    and RUN_PERSISTENT_CRASH_HINT_THRESHOLD > 0
                    and consecutive_same_code >= RUN_PERSISTENT_CRASH_HINT_THRESHOLD
                ):
                    crash_hint_shown = True
                    console.print(
                        f"[hint]{i18n.t('cli.run.persistent_crash_hint', count=consecutive_same_code, code=process.returncode)}[/]"
                    )
                backoff = min(RUN_CRASH_BACKOFF_MAX_SECS, RUN_CRASH_BACKOFF_PER_CRASH_SECS * crash_count)
                console.print(
                    f"[warning]{i18n.t('cli.run.process_crashed', code=process.returncode)}[/]"
                )
                console.print(
                    f"[info]{i18n.t('cli.run.subprocess_crashed_retry', seconds=backoff)}[/]"
                )
                time.sleep(backoff)
                # 继续循环，重新启动子进程
        except KeyboardInterrupt:
            pass
        finally:
            # 运行器退出（Ctrl+C 等）前必须终止子进程，否则孤儿进程会继续持有
            # 端口等资源，导致下次启动时端口被占用（如监听 8000 的残留进程）。
            if process is not None and process.poll() is None:
                console.print(f"[info]{i18n.t('cli.run.terminating_child')}[/]")
                process.terminate()
                try:
                    process.wait(timeout=CLI_CHILD_TERMINATE_WAIT_SECS)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            runtime_state.clear()

    def _run_internal(self, reload_mode: bool):
        """
        直接运行 SDK（不指定脚本时）

        以「监督进程 + 框架子进程」结构运行：子进程崩溃自动重试，硬重启
        （退出码 42）重拉全新进程。reload 模式的子进程为 reload worker
        （dev 文件监控 + 组件级热重载），两种模式共享同一套监督语义。

        {!--< tips >!--}
        重要设计原则：
        1. 只有硬重启（退出码 42）或 KeyboardInterrupt 才能停止主进程
        2. 模块/适配器的任何错误都**不会**导致主进程退出
        3. 子进程异常退出时自动重试，使用递增退避策略避免刷屏
        {!--< /tips >!--}
        """
        python_exe = getattr(self, "python_exe", sys.executable)
        if reload_mode:
            runtime_state.write(os.getpid(), argv=sys.argv)
            self._supervise(
                [python_exe, "-c", _RELOAD_WORKER_BOOTSTRAP],
                reload_worker=True,
            )
            return

        runtime_state.write(os.getpid(), argv=sys.argv)
        self._supervise([python_exe, "-c", _SDK_BOOTSTRAP])

    def _run_script(self, script_path: str, reload_mode: bool):
        """
        运行指定的脚本文件，可选启用热重载

        :param script_path: [str] 脚本文件路径
        :param reload_mode: [bool] 是否启用热重载模式
        """
        script_path_abs = str(Path(script_path).resolve())

        if reload_mode:
            runtime_state.write(os.getpid(), argv=sys.argv)
            try:
                self._run_script_with_reload(script_path_abs)
            finally:
                runtime_state.clear()
        else:
            runtime_state.write(os.getpid(), argv=sys.argv)
            try:
                script_dir = str(Path(script_path_abs).parent)
                if script_dir not in sys.path:
                    sys.path.insert(0, script_dir)
                try:
                    runpy.run_path(script_path_abs, run_name="__main__")
                except SystemExit:
                    pass
                except KeyboardInterrupt:
                    pass
            finally:
                runtime_state.clear()

    def _run_script_with_reload(self, script_path_abs: str):
        """
        以子进程方式运行脚本并监控文件变更以自动重启

        进程的所有终止与重启均在主线程完成；文件监控线程仅负责发出重载信号，
        避免双线程同时操作子进程导致的竞态。脚本进程因错误（如语法错误、异常）
        退出时不会终止重载循环，而是等待下一次文件变更后再尝试重启；硬重启
        （退出码 42）例外——立即重拉全新脚本进程。

        :param script_path_abs: [str] 脚本的绝对路径
        """
        from ...Core.constants import FILE_RELOAD_DEBOUNCE_SECS

        watch_dir = str(Path(script_path_abs).parent)
        python_exe = getattr(self, "python_exe", sys.executable)

        reload_state = {
            "process": None,
            "last_reload": 0.0,
            "changed_file": None,
            "reload_event": threading.Event(),
        }

        def _spawn():
            """启动脚本子进程并记录到 reload_state（注入监督者标记）"""
            child_env = dict(os.environ)
            child_env[ENV_SUPERVISED] = "cli"
            child_env.setdefault("PYTHONIOENCODING", "utf-8")
            reload_state["process"] = subprocess.Popen(
                [python_exe, script_path_abs], env=child_env
            )
            runtime_state.update_child(reload_state["process"].pid)

        class _ScriptReloadHandler(FileSystemEventHandler):
            """
            脚本重载信号处理器，监控 .py 文件变更并发出重载信号

            仅设置重载事件，不直接操作子进程（终止/重启由主线程统一处理）。
            """

            def on_modified(self, event: FileChangeEvent) -> None:
                """
                文件修改事件回调，设置重载信号供主线程处理

                :param event: [FileChangeEvent] 文件系统事件
                """
                self._on_event(event)

            def on_created(self, event: FileChangeEvent) -> None:
                """
                文件创建事件回调（新建 .py 文件同样触发重启）

                :param event: [FileChangeEvent] 文件系统事件
                """
                self._on_event(event)

            def _on_event(self, event: FileChangeEvent) -> None:
                now = time.time()
                if now - reload_state["last_reload"] < FILE_RELOAD_DEBOUNCE_SECS:
                    return
                if not event.src_path.endswith(".py"):
                    return
                reload_state["last_reload"] = now
                reload_state["changed_file"] = Path(event.src_path).name
                reload_state["reload_event"].set()

        observer = PollingObserver()
        observer.schedule(_ScriptReloadHandler(), watch_dir, recursive=True)
        observer.start()

        console.print(
            Panel(
                i18n.t("cli.run.reload_mode_panel", watch_dir=watch_dir, ignored="-"),
                title=i18n.t("cli.run.reload_title"),
                border_style="info",
            )
        )

        try:
            _spawn()
            while True:
                proc = reload_state["process"]
                # 等待进程退出或重载信号（带超时轮询，保证 Ctrl+C 可响应）
                while proc.poll() is None and not reload_state["reload_event"].is_set():
                    reload_state["reload_event"].wait(timeout=0.2)

                if proc.poll() is None:
                    # 进程仍在运行，由文件变更触发重载：先终止再重启
                    console.print(
                        f"[info]{i18n.t('cli.run.file_changed_restart', file=reload_state['changed_file'])}[/]"
                    )
                    reload_state["reload_event"].clear()
                    proc.terminate()
                    try:
                        proc.wait(timeout=CLI_CHILD_TERMINATE_WAIT_SECS)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                    _spawn()
                    continue

                if proc.returncode == self._RESTART_EXIT_CODE:
                    # 硬重启请求：立即重拉全新脚本进程
                    self._print_hard_restart_reason()
                    console.print(f"[info]{i18n.t('cli.run.restart_request')}[/]")
                    time.sleep(RUN_RESTART_PAUSE_SECS)
                    _spawn()
                    continue

                # 进程已退出。若无排队的重载请求，提示等待文件变更
                if not reload_state["reload_event"].is_set():
                    if proc.returncode == 0:
                        console.print(f"[info]{i18n.t('cli.run.process_exited')}[/]")
                    else:
                        console.print(
                            f"[warning]{i18n.t('cli.run.process_crashed', code=proc.returncode)}[/]"
                        )
                    while not reload_state["reload_event"].wait(timeout=0.3):
                        pass

                # 收到重载请求，重启进程
                reload_state["reload_event"].clear()
                console.print(
                    f"[info]{i18n.t('cli.run.file_changed_restart', file=reload_state['changed_file'])}[/]"
                )
                _spawn()
        except KeyboardInterrupt:
            pass
        finally:
            proc = reload_state["process"]
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=CLI_CHILD_TERMINATE_WAIT_SECS)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            observer.stop()
            observer.join()

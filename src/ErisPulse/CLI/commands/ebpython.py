from ..base import Command
from ..console import console
from argparse import ArgumentParser
import pathlib
import urllib.request
import platform
import json
from rich.json import JSON
import subprocess


class BuildCommand(Command):
    name = "ebpython"
    description = "多架构跨平台打包器"

    def __init__(self) -> None:
        self.rootdir = pathlib.Path(".ebpython")
        self.rootdir.mkdir(parents=True, exist_ok=True)

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--install",
            "-i",
            type=str,
            nargs="?",
            const="",
            default=None,
            help="安装 ebpython 到项目，格式 version/arch",
        )

        parser.add_argument(
            "--generate",
            "-g",
            action="store_true",
            help="交互式生成 ebpython 配置",
        )

        parser.add_argument(
            "--config",
            "-c",
            type=str,
            default=None,
            help="使用指定配置调用 ebpython 打包",
        )

    def execute(self, args):
        if isinstance(args.install, str):
            self._do_ebpython_install(args.install)

        if args.generate:
            self._do_ebpython_config_generate()

        if isinstance(args.config, str):
            self._do_ebpython_build(args.config)

    def _do_ebpython_install(self, target: str):
        os_type = platform.system().lower()

        try:
            version, arch = target.split("/", 1)

        except ValueError:
            version = console.input("[bold green]ebpython 的版本? [dim white]latest[/] [/]") or "latest"
            arch = console.input("[bold green]ebpython 的架构? [dim white]amd64[/] [/]") or "amd64"

        baseurl = "https://github.com/runoneall/ebpython/releases"
        suffix = ".exe" if os_type == "windows" else ""
        release = f"download/{version}" if version != "latest" else "latest/download"
        url = f"{baseurl}/{release}/ebpython-{os_type}-{arch}{suffix}"

        ext = ".exe" if os_type == "windows" else ""
        binfile = self.rootdir / f"ebpython{ext}"

        if binfile.is_file():
            binfile.unlink(missing_ok=True)

        self._download_url_to_file(url, binfile)

    def _download_url_to_file(self, url: str, file: pathlib.Path):
        console.print(f"[white]开始下载 {url}...[/]")

        try:
            with urllib.request.urlopen(url) as resp:
                console.print(f"[white]保存到 {file}[/]")
                with file.open("wb") as out:
                    while True:
                        buffer = resp.read(16384)
                        if not buffer:
                            break
                        out.write(buffer)
            console.print("[bold green]下载成功[/]")

        except Exception as e:
            console.print(f"[bold red]下载失败: {e}[/]")

    def _do_ebpython_config_generate(self):
        config = {}
        console.print("\n[bold yellow]1: 基本路径定义[/]")

        console.print("\n[bold yellow]1-1: source 指向 python 程序目录，打包时这个目录会被完整保留[/]")
        config["source"] = console.input("[bold green]source 的值是? [dim white]src[/] [/]") or "src"

        console.print("\n[bold yellow]1-2: output 指向打包产物输出目录[/]")
        config["output"] = console.input("[bold green]output 的值是? [dim white]dist[/] [/]") or "dist"

        console.print("\n[bold yellow]2: 定义需要的 python 版本以及信息, 配置参考: astral-sh/python-build-standalone[/]")
        config["python"] = {}

        console.print("\n[bold yellow]2-1: release 是构建的版本[/]")
        config["python"]["release"] = console.input("[bold green]release 的值是? [dim white]20260510[/] [/]") or "20260510"

        console.print("\n[bold yellow]2-2: version 是 python 解释器版本[/]")
        config["python"]["version"] = console.input("[bold green]version 的值是? [dim white]3.12.13[/] [/]") or "3.12.13"

        def ask_python(step: str):
            cfg = {}

            console.print(f"\n[bold yellow]{step}-1: arch 是 python 解释器运行架构[/]")
            cfg["arch"] = console.input("[bold green]arch 的值是? [dim white]x86_64[/] [/]") or "x86_64"

            console.print(f"\n[bold yellow]{step}-2: os 是 python 解释器运行系统[/]")
            cfg["os"] = console.input("[bold green]os 的值是? [dim white]pc-windows-msvc[/] [/]") or "pc-windows-msvc"

            console.print(f"\n[bold yellow]{step}-3: flag 是 python 解释器构建时的标志[/]")
            cfg["flag"] = console.input("[bold green]flag 的值是? [dim white]install_only_stripped[/] [/]") or "install_only_stripped"

            console.print(f"\n[bold yellow]{step}-4: ext 是 python 解释器的压缩格式[/]")
            cfg["ext"] = console.input("[bold green]ext 的值是? [dim white]tar.gz[/] [/]") or "tar.gz"

            return cfg

        console.print("\n[bold yellow]2-3: 定义打包时的 python 版本以及信息[/]")
        config["python"]["local"] = ask_python("2-3")

        console.print("\n[bold yellow]2-4: 定义目标平台的 python 版本以及信息[/]")
        config["python"]["target"] = ask_python("2-4")

        console.print("\n[bold yellow]3: 定义需要的 python 扩展包[/]")
        config["pip"] = {}

        console.print("\n[bold yellow]3-1: platform 是 python 扩展包运行的目标平台[/]")
        config["pip"]["platform"] = console.input("[bold green]platform 的值是? [dim white]win_amd64[/] [/]") or "win_amd64"

        console.print("\n[bold yellow]3-2: download 是用到的 python 扩展包列表[/]")
        download = console.input('[bold green]download 的值是? [dim white]以 "," 分隔[/] [/]') or ""
        config["pip"]["download"] = download.split(",") if download != "" else []

        console.print("\n[bold yellow]4: 定义 python 启动器配置 (需要 Go 版本 >= 1.22)[/]")
        config["launcher"] = {}

        console.print("\n[bold yellow]4-1: goos 是启动器编译的目标平台[/]")
        config["launcher"]["goos"] = console.input("[bold green]goos 的值是? [dim white]windows[/] [/]") or "windows"

        console.print("\n[bold yellow]4-2: goarch 是启动器编译的目标架构[/]")
        config["launcher"]["goarch"] = console.input("[bold green]goarch 的值是? [dim white]amd64[/] [/]") or "amd64"

        console.print("\n[bold yellow]4-3: main 是 python 项目入口点文件[/]")
        config["launcher"]["main"] = console.input("[bold green]main 的值是? [dim white]app.py[/] [/]") or "app.py"

        console.print("\n[bold yellow]4-4: name 是应用程序名称[/]")
        config["launcher"]["name"] = console.input("[bold green]name 的值是? [dim white]我的应用程序[/] [/]") or "我的应用程序"

        console.print("\n[bold yellow]自动生成了如下的配置[/]")
        config = json.dumps(config, indent=4, ensure_ascii=False)
        console.print(JSON(config, indent=4, ensure_ascii=False))

        saveas = (console.input("[bold green]保存此配置为? [dim white]default[/] [/]") or "default") + ".json"
        savefile = self.rootdir / saveas

        with savefile.open("w", encoding="utf-8") as f:
            f.write(config)

    def _do_ebpython_build(self, config: str):
        configfile = self.rootdir / f"{config}.json"
        if not configfile.exists():
            console.print(f"[bold red]配置 {config} 不存在[/]")
            return

        console.print(f"[bold yellow]使用 {config} 配置打包[/]")

        os_type = platform.system().lower()
        ext = ".exe" if os_type == "windows" else ""
        binfile = self.rootdir / f"ebpython{ext}"

        cmd = [binfile, configfile]
        subprocess.run(cmd)

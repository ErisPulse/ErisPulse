"""
ErisPulse SDK 命令行工具

提供ErisPulse生态系统的包管理、模块控制和开发工具功能。
"""

import sys

from .CLI import CLI


def main():
    """
    CLI入口点

    {!--< tips >!--}
    1. 创建CLI实例并运行
    2. 处理全局异常：初始化/执行阶段的任何异常都输出可诊断信息，
       保证"epsdk 无响应且无输出"不再出现（此前裸异常会被 exe shim 吞掉）
    {!--< /tips >!--}
    """
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n(interrupted)", file=sys.stderr)
        sys.exit(130)
    except SystemExit:
        raise
    except BaseException as e:
        # exe shim（console_scripts）只回显退出码不回显 traceback；
        # 顶层兜底打印纯文本诊断，确保失败必有输出
        print(f"epsdk internal error: {type(e).__name__}: {e}", file=sys.stderr)
        try:
            import traceback as _tb

            _tb.print_exc(file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()

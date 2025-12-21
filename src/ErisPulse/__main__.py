"""
ErisPulse SDK 命令行工具

提供ErisPulse生态系统的包管理、模块控制和开发工具功能。

{!--< tips >!--}
1. 需要Python 3.8+环境
2. Windows平台需要colorama支持ANSI颜色
{!--< /tips >!--}
"""
from .utils import CLI

def main():
    """
    CLI入口点
    
    {!--< tips >!--}
    1. 创建CLI实例并运行
    2. 处理全局异常
    {!--< /tips >!--}
    """
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()
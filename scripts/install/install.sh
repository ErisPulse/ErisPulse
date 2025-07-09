#!/bin/bash
# ErisPulse 安装脚本

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_python_version() {
    if command_exists python3; then
        python_version=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
        if [ "$(printf '%s\n' "3.9" "$python_version" | sort -V | head -n1)" = "3.9" ]; then
            return 0
        fi
    fi
    return 1
}

install_uv() {
    echo -e "${YELLOW}正在安装 uv...${NC}"
    
    if command_exists uv; then
        echo -e "${GREEN}uv 已安装${NC}"
        return
    fi
    
    if command_exists curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    elif command_exists wget; then
        wget -qO- https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    else
        echo -e "${RED}需要 curl 或 wget 来安装 uv${NC}"
        exit 1
    fi
    
    if ! command_exists uv; then
        echo -e "${RED}uv 安装失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}uv 安装成功${NC}"
}

install_python_with_uv() {
    echo -e "${YELLOW}正在使用 uv 安装 Python 3.12...${NC}"
    
    if ! command_exists uv; then
        echo -e "${RED}错误: uv 未安装${NC}"
        exit 1
    fi
    
    uv python install 3.12
    if [ $? -ne 0 ]; then
        echo -e "${RED}Python 3.12 安装失败${NC}"
        exit 1
    fi
    
    python_path=$(uv python find 3.12)
    if [ -z "$python_path" ]; then
        echo -e "${RED}无法找到安装的Python 3.12${NC}"
        exit 1
    fi
    
    python_dir=$(dirname "$python_path")
    export PATH="$python_dir:$PATH"
    
    echo -e "${GREEN}Python 3.12 安装成功${NC}"
}

create_virtualenv() {
    echo -e "${YELLOW}正在创建虚拟环境...${NC}"
    
    if ! command_exists uv; then
        echo -e "${RED}错误: uv 未安装${NC}"
        exit 1
    fi
    
    uv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}虚拟环境创建失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}虚拟环境创建成功${NC}"
}

install_erispulse() {
    echo -e "${YELLOW}正在安装 ErisPulse...${NC}"
    
    if ! command_exists uv; then
        echo -e "${RED}错误: uv 未安装${NC}"
        exit 1
    fi
    
    uv pip install ErisPulse --upgrade
    if [ $? -ne 0 ]; then
        echo -e "${RED}ErisPulse 安装失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}ErisPulse 安装成功${NC}"
}

create_startup_scripts() {
    cat > start.sh << 'EOF'
#!/bin/bash
# ErisPulse 快速启动脚本

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境不存在，请先运行安装脚本"
    exit 1
fi

# 检测操作系统类型
if [ "$(uname)" = "Linux" ]; then
    source "$(dirname "$0")/.venv/bin/activate"
else
    source .venv/bin/activate
fi

echo "启动 ErisPulse 机器人..."
epsdk run main.py "$@"
EOF

    # 创建激活脚本
    cat > activate.sh << 'EOF'
#!/bin/bash
# 激活虚拟环境脚本

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境不存在，请先运行安装脚本"
    exit 1
fi

echo "激活虚拟环境..."
# 检测操作系统类型
if [ "$(uname)" = "Linux" ]; then
    source "$(dirname "$0")/.venv/bin/activate"
else
    source .venv/bin/activate
fi

echo "虚拟环境已激活，输入 exit 退出"
exec "$SHELL"
EOF

    chmod +x start.sh activate.sh
    
    echo -e "${GREEN}快捷脚本创建成功${NC}"
}

main() {
    echo -e "${BLUE}=== ErisPulse 安装程序 ===${NC}"
    
    if check_python_version; then
        echo -e "${GREEN}检测到符合要求的 Python 版本${NC}"
        read -p "是否使用当前 Python 版本？[Y/n] " use_current_python
        if [[ "$use_current_python" =~ ^[nN]$ ]]; then
            install_python=true
        else
            install_python=false
        fi
    else
        echo -e "${YELLOW}未检测到符合要求的 Python 版本 (需要 3.9+)${NC}"
        install_python=true
    fi
    
    if ! command_exists uv; then
        echo -e "${YELLOW}未检测到 uv 安装${NC}"
        read -p "是否安装 uv？[Y/n] " install_uv_choice
        if [[ "$install_uv_choice" =~ ^[nN]$ ]]; then
            echo -e "${RED}需要 uv 才能继续安装${NC}"
            exit 1
        fi
        install_uv
    else
        echo -e "${GREEN}检测到 uv 已安装${NC}"
    fi
    
    if [ "$install_python" = true ]; then
        read -p "是否使用 uv 安装 Python 3.12？[Y/n] " install_python_choice
        if [[ "$install_python_choice" =~ ^[nN]$ ]]; then
            echo -e "${RED}需要 Python 3.12 才能继续安装${NC}"
            exit 1
        fi
        install_python_with_uv
    fi
    
    read -p "是否创建虚拟环境？[Y/n] " create_venv_choice
    if ! [[ "$create_venv_choice" =~ ^[nN]$ ]]; then
        create_virtualenv
    fi
    
    install_erispulse
    
    create_startup_scripts
    
    echo -e "\n${GREEN}=== 安装完成 ===${NC}"
    echo -e "常用命令:"
    echo -e "1. 查看帮助: ${BLUE}epsdk -h${NC}"
    echo -e "2. 初始化项目: ${BLUE}epsdk init${NC}"
    echo -e "3. 更新资源: ${BLUE}epsdk update${NC}"
    echo -e "4. 安装模块: ${BLUE}epsdk install 模块名${NC}"
    echo -e "5. 运行示例: ${BLUE}epsdk run main.py${NC}"
    echo -e "\n${GREEN}=== 快速启动指南 ===${NC}"
    echo -e "1. 进入项目目录: ${BLUE}cd $(pwd)${NC}"
    echo -e "2. 启动机器人: ${BLUE}./start.sh${NC}"
    echo -e "3. 进入开发环境: ${BLUE}./activate.sh${NC}"
    echo -e "\n${YELLOW}提示:${NC}"
    echo -e "- 每次打开新终端时，需要先进入项目目录"
    echo -e "- 虚拟环境就像'独立的工作空间'，所有安装的包都在里面"
    echo -e "- 如果移动项目文件夹，需要重新运行安装脚本"
    echo -e "- 更新框架使用: ${BLUE}uv pip install ErisPulse --upgrade${NC}"
    
    if [ -d ".venv" ]; then
        echo -e "\n${YELLOW}正在激活虚拟环境...${NC}"
        if [ "$(uname)" = "Linux" ]; then
            source "$(pwd)/.venv/bin/activate"
        else
            source .venv/bin/activate
        fi
        echo -e "${GREEN}虚拟环境已激活${NC}"
        echo -e "${YELLOW}当前Python路径: ${BLUE}$(which python)${NC}"
        echo -e "下次激活环境请使用 ${BLUE}./activate.sh${NC}"
    fi
}

if [ "$(id -u)" -eq 0 ]; then
    echo -e "${YELLOW}警告: 不建议使用root用户运行此脚本${NC}"
    read -p "是否继续？[y/N] " continue_as_root
    if [[ ! "$continue_as_root" =~ ^[yY]$ ]]; then
        exit 1
    fi
fi

main

#!/bin/bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 全局变量
USE_UV=false
TARGET_VERSION=""
INSTALL_DIR=""
PYTHON_CMD=""
VENV_DIR=".venv"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}${BOLD}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}${BOLD}[成功]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}${BOLD}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}${BOLD}[错误]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}$1${NC}"
    echo -e "${CYAN}${BOLD}$(printf '=%.0s' {1..50})${NC}"
    echo ""
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 从PyPI获取版本列表（不输出到stdout，只返回版本数据）
get_pypi_versions() {
    local temp_file="/tmp/erispulse_versions_$$"
    
    # 在调用前显示信息
    
    # 尝试下载版本信息
    if command_exists curl; then
        curl -s --max-time 10 "https://pypi.org/pypi/ErisPulse/json" -o "$temp_file" 2>/dev/null || true
    elif command_exists wget; then
        wget -q --timeout=10 "https://pypi.org/pypi/ErisPulse/json" -O "$temp_file" 2>/dev/null || true
    fi
    
    if [ ! -s "$temp_file" ]; then
        rm -f "$temp_file"
        echo ""
        return 1
    fi
    
    # 使用 Python 解析 JSON
    if command_exists python3; then
        python3 -c "
import json
import sys
try:
    with open('$temp_file', 'r') as f:
        data = json.load(f)
    
    releases = data.get('releases', {})
    
    # 收集所有版本
    versions = []
    for version, files in releases.items():
        if not files:
            continue
        upload_time = files[0].get('upload_time_iso_8601', '')
        date_str = upload_time.split('T')[0] if upload_time else '未知'
        is_pre = any(x in version.lower() for x in ['a', 'b', 'rc', 'dev', 'alpha', 'beta'])
        versions.append((version, is_pre, date_str))
    
    # 按版本号排序
    def sort_key(v):
        parts = v[0].split('.')
        major = int(parts[0]) if parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].replace('.', '').isdigit() else 0
        patch_str = parts[2].split('-')[0] if len(parts) > 2 else '0'
        patch_num = int(patch_str) if patch_str.isdigit() else 0
        pre = 0 if not v[1] else 1
        return (major, minor, patch_num, pre, v[0])
    
    versions.sort(key=sort_key, reverse=True)
    
    # 输出版本列表（每行一个：版本号|是否预发布|日期）
    for v, is_pre, date in versions:
        print(f'{v}|{is_pre}|{date}')
except Exception as e:
    sys.stderr.write(str(e) + '\n')
    sys.exit(1)
"
        local ret=$?
        rm -f "$temp_file"
        
        if [ $ret -eq 0 ]; then
            return 0
        else
            return 1
        fi
    else
        rm -f "$temp_file"
        return 1
    fi
}

# 显示版本选择菜单
show_version_menu() {
    print_info "正在从 PyPI 获取版本信息..."
    
    local versions_output
    versions_output=$(get_pypi_versions)
    local has_versions=$?
    
    echo ""
    
    if [ $has_versions -eq 0 ] && [ -n "$versions_output" ]; then
        # 解析版本列表
        local stable_count=0
        local pre_count=0
        local latest_stable=""
        local latest_pre=""
        
        # 解析第一行获取最新稳定版和预发布版
        local first_line=$(echo "$versions_output" | head -1)
        local first_ver=$(echo "$first_line" | cut -d'|' -f1)
        local first_is_pre=$(echo "$first_line" | cut -d'|' -f2)
        
        if [ "$first_is_pre" = "True" ]; then
            latest_pre="$first_ver"
        else
            latest_stable="$first_ver"
        fi
        
        # 查找第一个稳定版
        while IFS='|' read -r ver is_pre date; do
            if [ "$is_pre" = "False" ] && [ -z "$latest_stable" ]; then
                latest_stable="$ver"
                break
            fi
        done <<< "$versions_output"
        
        echo -e "${CYAN}可用版本:${NC}"
        echo ""
        
        # 选项1：最新稳定版
        if [ -n "$latest_stable" ]; then
            echo -e "  ${BOLD}1${NC}. ${GREEN}最新稳定版 ($latest_stable)${NC}"
        fi
        
        # 选项2：最新预发布版
        if [ -n "$latest_pre" ]; then
            echo -e "  ${BOLD}2${NC}. ${YELLOW}最新预发布版 ($latest_pre)${NC}"
        fi
        
        # 选项3：查看所有版本
        echo -e "  ${BOLD}3${NC}. 查看所有版本"
        
        # 选项4：手动指定版本
        echo -e "  ${BOLD}4${NC}. 手动指定版本号"
        
        echo ""
        
        # 询问用户选择
        while true; do
            read -p "请选择 [1-4] (默认: 1): " choice
            choice=${choice:-1}
            
            case "$choice" in
                1)
                    if [ -n "$latest_stable" ]; then
                        TARGET_VERSION="$latest_stable"
                        return 0
                    else
                        print_warning "没有找到稳定版本"
                    fi
                    ;;
                2)
                    if [ -n "$latest_pre" ]; then
                        TARGET_VERSION="$latest_pre"
                        return 0
                    else
                        print_warning "没有找到预发布版本"
                    fi
                    ;;
                3)
                    show_all_versions "$versions_output"
                    return 0
                    ;;
                4)
                    read -p "请输入版本号: " manual_ver
                    if [ -n "$manual_ver" ]; then
                        TARGET_VERSION="$manual_ver"
                        return 0
                    else
                        print_warning "版本号不能为空"
                    fi
                    ;;
                *)
                    print_warning "请输入 1-4 之间的数字"
                    ;;
            esac
        done
    else
        print_warning "无法获取版本信息，将安装最新版本"
        TARGET_VERSION=""
        return 0
    fi
}

# 显示所有版本列表
show_all_versions() {
    local versions_output="$1"
    local index=1
    local version_list=()
    
    echo ""
    echo -e "${CYAN}${BOLD}=== 可用版本列表 ===${NC}"
    echo ""
    
    while IFS='|' read -r ver is_pre date; do
        version_list+=("$ver")
        
        # 格式化版本显示
        local version_text
        local pre_marker=""
        
        if [ "$is_pre" = "True" ]; then
            version_text="${YELLOW}${ver}${NC}"
            pre_marker=" ${YELLOW}[预发布]${NC}"
        else
            version_text="${GREEN}${ver}${NC}"
        fi
        
        echo -e "  ${BOLD}$index${NC}. ${version_text}${pre_marker}  ${CYAN}(${date})${NC}"
        
        index=$((index + 1))
        
        if [ $index -gt 15 ]; then
            break
        fi
    done <<< "$versions_output"
    
    echo ""
    
    # 选择版本
    while true; do
        read -p "请输入版本序号 [1-$index] 或版本号: " input
        
        # 检查是否是数字
        if [[ "$input" =~ ^[0-9]+$ ]]; then
            local idx=$((input - 1))
            if [ $idx -ge 0 ] && [ $idx -lt ${#version_list[@]} ]; then
                TARGET_VERSION="${version_list[$idx]}"
                return 0
            else
                print_warning "请输入有效的序号"
            fi
        else
            # 检查版本号是否存在
            for ver in "${version_list[@]}"; do
                if [ "$ver" = "$input" ]; then
                    TARGET_VERSION="$input"
                    return 0
                fi
            done
            print_warning "请输入有效的序号或版本号"
        fi
    done
}

# 检查Python版本
check_python() {
    local py_cmd=""
    
    if command_exists python3; then
        py_cmd="python3"
    elif command_exists python; then
        py_cmd="python"
    else
        print_error "未找到 Python，请先安装 Python 3.10 或更高版本"
        print_info "下载地址: https://www.python.org/downloads/"
        return 1
    fi
    
    # 检查版本
    local py_version=$($py_cmd -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>/dev/null || echo "0.0")
    
    # 简单的版本比较
    if [ "$py_version" = "0.0" ]; then
        print_error "无法检测 Python 版本"
        return 1
    fi
    
    print_success "检测到 Python $py_version"
    
    # 检查是否满足要求（>= 3.10）
    local major=$(echo $py_version | cut -d'.' -f1)
    local minor=$(echo $py_version | cut -d'.' -f2)
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 10 ]); then
        print_warning "Python 版本过低，建议使用 3.10 或更高版本"
        read -p "是否继续？ [y/N]: " continue_choice
        if [[ ! "$continue_choice" =~ ^[yY]$ ]]; then
            return 1
        fi
    fi
    
    PYTHON_CMD="$py_cmd"
    return 0
}

# 安装 uv
install_uv() {
    print_info "正在安装 uv..."
    
    if command_exists uv; then
        print_success "uv 已安装"
        return 0
    fi
    
    local install_script="/tmp/uv_install_$$"
    
    if command_exists curl; then
        curl -LsSf https://astral.sh/uv/install.sh -o "$install_script"
    elif command_exists wget; then
        wget -qO- https://astral.sh/uv/install.sh -O "$install_script"
    else
        print_error "需要 curl 或 wget 来安装 uv"
        return 1
    fi
    
    if [ -f "$install_script" ]; then
        sh "$install_script"
        rm -f "$install_script"
        
        # 更新 PATH
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if command_exists uv; then
            print_success "uv 安装成功"
            return 0
        else
            print_warning "uv 安装可能未完成，请尝试重启终端或手动添加到 PATH"
            return 1
        fi
    else
        print_error "下载 uv 安装脚本失败"
        return 1
    fi
}

# 创建虚拟环境
create_venv() {
    print_info "正在创建虚拟环境..."
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "虚拟环境已存在"
        read -p "是否删除并重新创建？ [y/N]: " recreate
        if [[ "$recreate" =~ ^[yY]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            print_info "使用现有虚拟环境"
            return 0
        fi
    fi
    
    local venv_cmd="$PYTHON_CMD -m venv"
    
    if [ "$USE_UV" = true ] && command_exists uv; then
        venv_cmd="uv venv"
    fi
    
    if $venv_cmd "$VENV_DIR"; then
        print_success "虚拟环境创建成功"
        return 0
    else
        print_error "虚拟环境创建失败"
        return 1
    fi
}

# 激活虚拟环境
activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        print_success "虚拟环境已激活"
    else
        print_error "虚拟环境激活脚本不存在"
        return 1
    fi
}

# 安装 ErisPulse
install_erispulse() {
    local version="$1"
    
    print_info "正在安装 ErisPulse..."
    
    local pkg_spec="ErisPulse"
    if [ -n "$version" ]; then
        pkg_spec="ErisPulse==$version"
        print_info "安装版本: $version"
    else
        print_info "安装最新版本"
    fi
    
    local install_cmd
    
    if [ "$USE_UV" = true ] && command_exists uv; then
        install_cmd="uv pip install $pkg_spec"
    else
        install_cmd="pip install $pkg_spec"
    fi
    
    if eval "$install_cmd"; then
        print_success "ErisPulse 安装成功"
        return 0
    else
        print_error "ErisPulse 安装失败"
        return 1
    fi
}

# 显示完成信息
show_completion() {
    echo ""
    print_header "安装完成"
    
    echo -e "${BOLD}如何激活虚拟环境:${NC}"
    echo ""
    echo -e "  在当前终端运行: ${GREEN}source .venv/bin/activate${NC}"
    echo ""
    
    echo -e "${BOLD}快速开始:${NC}"
    echo ""
    echo -e "  1. 激活虚拟环境: ${GREEN}source .venv/bin/activate${NC}"
    echo -e "  2. 查看帮助: ${GREEN}epsdk -h${NC}"
    echo -e "  3. 初始化项目: ${GREEN}epsdk init${NC}"
    echo -e "  4. 查看可用包: ${GREEN}epsdk list-remote${NC}"
    echo -e "  5. 安装模块: ${GREEN}epsdk install <模块名>${NC}"
    echo ""
    
    echo -e "${BOLD}提示:${NC}"
    echo -e "  - 每次打开新终端时，需要先进入项目目录并运行激活命令"
    echo -e "  - 虚拟环境就像'独立的工作空间'，所有安装的包都在里面"
    echo -e "  - 输入 ${GREEN}deactivate${NC} 可以退出虚拟环境"
    echo -e "  - 更新框架使用: ${GREEN}epsdk self-update${NC}"
    echo ""
    
    # 激活虚拟环境
    if [ -f "$VENV_DIR/bin/activate" ]; then
        print_info "正在激活虚拟环境..."
        source "$VENV_DIR/bin/activate"
        print_success "虚拟环境已激活"
        echo -e "${YELLOW}当前Python路径: ${BLUE}$(which python)${NC}"
    fi
}

# 主流程
main() {
    print_header "ErisPulse 安装程序"
    
    # 检查 Python
    if ! check_python; then
        exit 1
    fi
    
    # 询问是否使用 uv
    if ! command_exists uv; then
        echo ""
        echo -e "${CYAN}uv 是一个快速的 Python 工具链，可以加速安装过程（推荐使用）${NC}"
        read -p "是否安装 uv？ [y/N]: " install_uv_choice
        if [[ "$install_uv_choice" =~ ^[yY]$ ]]; then
            if install_uv; then
                USE_UV=true
            else
                print_warning "uv 安装失败，将使用标准 pip"
            fi
        else
            print_info "将使用标准 pip 进行安装"
        fi
    else
        print_success "检测到 uv 已安装"
        USE_UV=true
    fi
    
    # 选择版本
    show_version_menu
    
    echo ""
    if [ -n "$TARGET_VERSION" ]; then
        echo -e "${CYAN}将安装 ErisPulse ${BOLD}${TARGET_VERSION}${NC}"
    else
        echo -e "${CYAN}将安装 ErisPulse ${BOLD}最新版本${NC}"
    fi
    
    read -p "确认安装？ [Y/n]: " confirm
    if [[ "$confirm" =~ ^[nN]$ ]]; then
        print_info "操作已取消"
        exit 0
    fi
    
    # 创建虚拟环境
    if ! create_venv; then
        exit 1
    fi
    
    # 激活虚拟环境
    if ! activate_venv; then
        exit 1
    fi
    
    # 安装 ErisPulse
    if ! install_erispulse "$TARGET_VERSION"; then
        exit 1
    fi
    
    # 显示完成信息
    show_completion
}

# 检查是否以 root 用户运行
if [ "$(id -u)" -eq 0 ]; then
    print_warning "不建议使用 root 用户运行此脚本"
    read -p "是否继续？ [y/N]: " continue_as_root
    if [[ ! "$continue_as_root" =~ ^[yY]$ ]]; then
        exit 1
    fi
fi

# 运行主流程
main

<#
.SYNOPSIS
ErisPulse 安装脚本 - PowerShell

.DESCRIPTION
此脚本将自动检测并安装 ErisPulse 所需的环境：
- 安装 uv (Python 环境管理工具)
- 安装 Python 3.12 (通过 uv)
- 创建虚拟环境
- 安装 ErisPulse 框架
#>

[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ESC = [char]27
if ($Host.UI.SupportsVirtualTerminal) {
    $RED = "$ESC[31m"
    $GREEN = "$ESC[32m"
    $YELLOW = "$ESC[33m"
    $BLUE = "$ESC[34m"
    $NC = "$ESC[0m"
} else {
    $RED = $GREEN = $YELLOW = $BLUE = $NC = ""
}

# 函数：检测Python版本是否符合要求
function Test-PythonVersion {
    try {
        $pythonVersion = (python --version 2>&1 | Out-String).Trim()
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [version]$Matches[1]
            if ($version -ge [version]"3.9") {
                return $true
            }
        }
        return $false
    } catch {
        return $false
    }
}

# 函数：安装uv
function Install-UV {
    Write-Host "${YELLOW}正在安装 uv...${NC}"
    
    # 检查是否已安装
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-Host "${GREEN}uv 已安装${NC}"
        return
    }
    
    # 安装uv
    try {
        Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" | Invoke-Expression
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            # 如果不在PATH中，尝试添加到PATH
            $uvPath = Join-Path $HOME ".cargo\bin"
            if (Test-Path $uvPath) {
                $env:PATH = "$uvPath;$env:PATH"
            }
        }
        
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            Write-Host "${GREEN}uv 安装成功${NC}"
        } else {
            throw "uv 安装后仍不可用"
        }
    } catch {
        Write-Host "${RED}uv 安装失败: $_${NC}"
        exit 1
    }
}

# 函数：使用uv安装Python 3.12
function Install-PythonWithUV {
    Write-Host "${YELLOW}正在使用 uv 安装 Python 3.12...${NC}"
    
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "${RED}错误: uv 未安装${NC}"
        exit 1
    }
    
    try {
        uv python install 3.12
        if ($LASTEXITCODE -ne 0) {
            throw "uv python install 命令执行失败"
        }
        
        # 检查Python是否安装成功
        $pythonPath = uv python find 3.12
        if (-not $pythonPath) {
            throw "无法找到安装的Python 3.12"
        }
        
        # 添加到PATH
        $pythonDir = Split-Path $pythonPath
        $env:PATH = "$pythonDir;$env:PATH"
        
        Write-Host "${GREEN}Python 3.12 安装成功${NC}"
    } catch {
        Write-Host "${RED}Python 3.12 安装失败: $_${NC}"
        exit 1
    }
}

# 函数：创建虚拟环境
function New-VirtualEnvironment {
    Write-Host "${YELLOW}正在创建虚拟环境...${NC}"
    
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "${RED}错误: uv 未安装${NC}"
        exit 1
    }
    
    try {
        uv venv
        if ($LASTEXITCODE -ne 0) {
            throw "uv venv 命令执行失败"
        }
        
        # 激活虚拟环境
        $activatePath = Join-Path (Get-Location) ".venv\Scripts\Activate.ps1"
        if (Test-Path $activatePath) {
            . $activatePath
            Write-Host "${GREEN}虚拟环境创建并激活成功${NC}"
        } else {
            throw "无法找到虚拟环境激活脚本"
        }
    } catch {
        Write-Host "${RED}虚拟环境创建失败: $_${NC}"
        exit 1
    }
}

# 函数：安装ErisPulse
function Install-ErisPulse {
    Write-Host "${YELLOW}正在安装 ErisPulse...${NC}"
    
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "${RED}错误: uv 未安装${NC}"
        exit 1
    }
    
    try {
        uv pip install ErisPulse --upgrade
        if ($LASTEXITCODE -ne 0) {
            throw "uv pip install 命令执行失败"
        }
        
        Write-Host "${GREEN}ErisPulse 安装成功${NC}"
    } catch {
        Write-Host "${RED}ErisPulse 安装失败: $_${NC}"
        exit 1
    }
}

# 主安装流程
function Main {
    Write-Host "${BLUE}=== ErisPulse 安装程序 ===${NC}"
    
    # 检查Python版本
    $hasValidPython = Test-PythonVersion
    if ($hasValidPython) {
        Write-Host "${GREEN}检测到符合要求的 Python 版本${NC}"
        $useCurrentPython = Read-Host "是否继续使用当前 Python 版本？[Y/n]"
        if ($useCurrentPython -match "^[nN]$") {
            $installPython = $true
        } else {
            $installPython = $false
        }
    } else {
        Write-Host "${YELLOW}未检测到符合要求的 Python 版本 (需要 3.9+)${NC}"
        $installPython = $true
    }
    
    # 安装uv
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "${YELLOW}未检测到 uv 安装${NC}"
        $installUV = Read-Host "是否安装 uv？[Y/n]"
        if ($installUV -match "^[nN]$") {
            Write-Host "${RED}需要 uv 才能继续安装${NC}"
            exit 1
        }
        Install-UV
    } else {
        Write-Host "${GREEN}检测到 uv 已安装${NC}"
    }
    
    # 安装Python 3.12
    if ($installPython) {
        $installPythonChoice = Read-Host "是否使用 uv 安装 Python 3.12？[Y/n]"
        if ($installPythonChoice -match "^[nN]$") {
            Write-Host "${RED}需要 Python 3.12 才能继续安装${NC}"
            exit 1
        }
        Install-PythonWithUV
    }
    
    # 创建虚拟环境
    $createVenvChoice = Read-Host "是否创建虚拟环境？[Y/n]"
    if (-not ($createVenvChoice -match "^[nN]$")) {
        New-VirtualEnvironment
    }
    
    Install-ErisPulse
    
    Write-Host ""
    Write-Host "${GREEN}=== 安装完成 ===${NC}"
    Write-Host "现在您可以:"
    Write-Host "1. 查看帮助: ${BLUE}epsdk -h${NC}"
    Write-Host "2. 初始化新项目: ${BLUE}epsdk init${NC}"
    Write-Host "3. 更新源: ${BLUE}epsdk update${NC}"
    Write-Host "4. 安装模块: ${BLUE}epsdk install 模块名${NC}"
    Write-Host "5. 运行示例程序: ${BLUE}epsdk run main.py${NC}"
    Write-Host ""
    Write-Host "${GREEN}=== 启动指南 ===${NC}"
    Write-Host "1. 进入项目目录: ${BLUE}cd $(Get-Location)${NC}"
    Write-Host "2. 激活虚拟环境: ${BLUE}.\.venv\Scripts\Activate.ps1${NC}"
    Write-Host "3. 运行程序: ${BLUE}epsdk run main.py${NC}"
    Write-Host ""
    Write-Host "${YELLOW}注意:${NC}"
    Write-Host "- 请确保在 PowerShell 中运行这些命令"
    Write-Host "- 如果遇到权限问题，请先执行: ${BLUE}Set-ExecutionPolicy RemoteSigned -Scope CurrentUser${NC}"
    Write-Host "- 每次打开新终端时，需要重新激活虚拟环境"
}

$executionPolicy = Get-ExecutionPolicy
if ($executionPolicy -eq "Restricted") {
    Write-Host "${YELLOW}当前执行策略为 Restricted，建议设置为 RemoteSigned${NC}"
    $changePolicy = Read-Host "是否要更改执行策略？[Y/n]"
    if ($changePolicy -notmatch "^[nN]$") {
        Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    }
}

Main
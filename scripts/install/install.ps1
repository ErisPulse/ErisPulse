# ErisPulse 安装脚本

# 错误处理
$ErrorActionPreference = "Stop"

# 全局变量
$script:UseUv = $false
$script:TargetVersion = ""
$script:InstallDir = ""
$script:PythonCmd = ""
$script:VenvDir = ".venv"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[信息] $Message" "Blue"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[成功] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[警告] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[错误] $Message" "Red"
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-ColorOutput $Message "Cyan"
    Write-ColorOutput ("=" * 50) "Cyan"
    Write-Host ""
}

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# 从PyPI获取版本列表（不输出到stdout，只返回版本数据）
function Get-PyPiVersions {
    $tempFile = Join-Path $env:TEMP "erispulse_versions_$([Guid]::NewGuid())"
    
    # 尝试下载版本信息
    try {
        if (Test-Command "curl") {
            $null = curl.exe -s --max-time 10 "https://pypi.org/pypi/ErisPulse/json" -o $tempFile 2>$null
        } elseif (Test-Command "wget") {
            $null = wget.exe -q --timeout=10 "https://pypi.org/pypi/ErisPulse/json" -O $tempFile 2>$null
        } else {
            # 使用 PowerShell 的 Invoke-WebRequest
            Invoke-WebRequest -Uri "https://pypi.org/pypi/ErisPulse/json" -OutFile $tempFile -TimeoutSec 10
        }
    } catch {
        Write-Warning "无法获取版本信息，将使用最新版本"
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return @()
    }
    
    if (-not (Test-Path $tempFile) -or ((Get-Item $tempFile).Length -eq 0)) {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return @()
    }
    
    # 使用 PowerShell 解析 JSON
    try {
        $jsonContent = Get-Content $tempFile -Raw -Encoding UTF8
        $data = $jsonContent | ConvertFrom-Json
        
        $versions = @()
        foreach ($version in $data.releases.PSObject.Properties.Name) {
            $files = $data.releases.$version
            if ($files -and $files.Count -gt 0) {
                $uploadTime = $files[0].upload_time_iso_8601
                $dateStr = if ($uploadTime) { $uploadTime.Split('T')[0] } else { "未知" }
                
                # 判断是否为预发布版本
                $isPre = @('a', 'b', 'rc', 'dev', 'alpha', 'beta') | Where-Object { $version.ToLower().Contains($_) }
                
                $versions += [PSCustomObject]@{
                    Version = $version
                    IsPre = $isPre.Count -gt 0
                    Date = $dateStr
                }
            }
        }
        
        # 按版本号排序
        $sortedVersions = $versions | Sort-Object {
            $parts = $_.Version.Split('.')
            $major = if ($parts[0] -match '^\d+$') { [int]$parts[0] } else { 0 }
            $minor = if ($parts.Count -gt 1 -and $parts[1] -match '^\d+$') { [int]$parts[1] } else { 0 }
            $patchStr = if ($parts.Count -gt 2) { $parts[2].Split('-')[0] } else { "0" }
            $patchNum = if ($patchStr -match '^\d+$') { [int]$patchStr } else { 0 }
            $pre = if ($_.IsPre) { 1 } else { 0 }
            "$major,$minor,$patchNum,$pre,$($_.Version)"
        } -Descending
        
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return $sortedVersions
        
    } catch {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return @()
    }
}

# 显示版本选择菜单
function Show-VersionMenu {
    Write-Info "正在从 PyPI 获取版本信息..."
    
    $versions = Get-PyPiVersions
    
    Write-Host ""
    
    if ($versions.Count -gt 0) {
        $latestStable = $null
        $latestPre = $null
        
        # 查找最新稳定版和预发布版
        foreach ($ver in $versions) {
            if (-not $ver.IsPre -and -not $latestStable) {
                $latestStable = $ver.Version
            }
            if ($ver.IsPre -and -not $latestPre) {
                $latestPre = $ver.Version
            }
            if ($latestStable -and $latestPre) { break }
        }
        
        Write-Host "可用版本:" -ForegroundColor Cyan
        Write-Host ""
        
        # 选项1：最新稳定版
        if ($latestStable) {
            Write-Host "  1. 最新稳定版 ($latestStable)" -ForegroundColor Green
        }
        
        # 选项2：最新预发布版
        if ($latestPre) {
            Write-Host "  2. 最新预发布版 ($latestPre)" -ForegroundColor Yellow
        }
        
        # 选项3：查看所有版本
        Write-Host "  3. 查看所有版本"
        
        # 选项4：手动指定版本
        Write-Host "  4. 手动指定版本号"
        
        Write-Host ""
        
        # 询问用户选择
        while ($true) {
            $choice = Read-Host "请选择 [1-4] (默认: 1)"
            $choice = if ($choice) { $choice } else { "1" }
            
            switch ($choice) {
                "1" {
                    if ($latestStable) {
                        $script:TargetVersion = $latestStable
                        return
                    } else {
                        Write-Warning "没有找到稳定版本"
                    }
                }
                "2" {
                    if ($latestPre) {
                        $script:TargetVersion = $latestPre
                        return
                    } else {
                        Write-Warning "没有找到预发布版本"
                    }
                }
                "3" {
                    Show-AllVersions $versions
                    return
                }
                "4" {
                    $manualVer = Read-Host "请输入版本号"
                    if ($manualVer) {
                        $script:TargetVersion = $manualVer
                        return
                    } else {
                        Write-Warning "版本号不能为空"
                    }
                }
                default {
                    Write-Warning "请输入 1-4 之间的数字"
                }
            }
        }
    } else {
        Write-Warning "无法获取版本信息，将安装最新版本"
        $script:TargetVersion = ""
        return
    }
}

# 显示所有版本列表
function Show-AllVersions {
    param($Versions)
    
    $versionList = @()
    
    Write-Host ""
    Write-Host "=== 可用版本列表 ===" -ForegroundColor Cyan
    Write-Host ""
    
    $index = 1
    foreach ($ver in $Versions) {
        $versionList += $ver.Version
        
        # 格式化版本显示
        if ($ver.IsPre) {
            $versionText = "$($ver.Version) [预发布]"
            Write-Host "  $index. $versionText  ($($ver.Date))" -ForegroundColor Yellow
        } else {
            $versionText = $ver.Version
            Write-Host "  $index. $versionText  ($($ver.Date))" -ForegroundColor Green
        }
        
        $index++
        
        if ($index -gt 15) {
            break
        }
    }
    
    Write-Host ""
    
    # 选择版本
    while ($true) {
        $input = Read-Host "请输入版本序号 [1-$index] 或版本号"
        
        # 检查是否是数字
        if ($input -match '^\d+$') {
            $idx = [int]$input - 1
            if ($idx -ge 0 -and $idx -lt $versionList.Count) {
                $script:TargetVersion = $versionList[$idx]
                return
            } else {
                Write-Warning "请输入有效的序号"
            }
        } else {
            # 检查版本号是否存在
            if ($input -in $versionList) {
                $script:TargetVersion = $input
                return
            } else {
                Write-Warning "请输入有效的序号或版本号"
            }
        }
    }
}

# 检查Python版本
function Test-Python {
    $pyCmd = ""
    
    if (Test-Command "python3") {
        $pyCmd = "python3"
    } elseif (Test-Command "python") {
        $pyCmd = "python"
    } elseif (Test-Command "py") {
        $pyCmd = "py"
    } else {
        Write-Error "未找到 Python，请先安装 Python 3.10 或更高版本"
        Write-Info "下载地址: https://www.python.org/downloads/"
        return $false
    }
    
    # 检查版本
    try {
        $pyVersion = & $pyCmd -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>$null
        if (-not $pyVersion) {
            Write-Error "无法检测 Python 版本"
            return $false
        }
        
        Write-Success "检测到 Python $pyVersion"
        
        # 检查是否满足要求（>= 3.10）
        $major, $minor = $pyVersion.Split('.')
        if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
            Write-Warning "Python 版本过低，建议使用 3.10 或更高版本"
            $continueChoice = Read-Host "是否继续？ [y/N]"
            if ($continueChoice -notmatch '^[yY]$') {
                return $false
            }
        }
        
        $script:PythonCmd = $pyCmd
        return $true
        
    } catch {
        Write-Error "无法检测 Python 版本"
        return $false
    }
}

# 安装 uv
function Install-Uv {
    Write-Info "正在安装 uv..."
    
    if (Test-Command "uv") {
        Write-Success "uv 已安装"
        return $true
    }
    
    try {
        # 使用 PowerShell 安装
        irm https://astral.sh/uv/install.ps1 | iex
        
        if (Test-Command "uv") {
            Write-Success "uv 安装成功"
            return $true
        } else {
            Write-Warning "uv 安装可能未完成，请尝试重启终端"
            return $false
        }
    } catch {
        Write-Error "uv 安装失败: $_"
        return $false
    }
}

# 创建虚拟环境
function New-VirtualEnvironment {
    Write-Info "正在创建虚拟环境..."
    
    if (Test-Path $script:VenvDir) {
        Write-Warning "虚拟环境已存在"
        $recreate = Read-Host "是否删除并重新创建？ [y/N]"
        if ($recreate -match '^[yY]$') {
            Remove-Item -Path $script:VenvDir -Recurse -Force
        } else {
            Write-Info "使用现有虚拟环境"
            return $true
        }
    }
    
    $venvCmd = "$($script:PythonCmd) -m venv"
    
    if ($script:UseUv -and (Test-Command "uv")) {
        $venvCmd = "uv venv"
    }
    
    try {
        Invoke-Expression "$venvCmd $script:VenvDir"
        Write-Success "虚拟环境创建成功"
        return $true
    } catch {
        Write-Error "虚拟环境创建失败: $_"
        return $false
    }
}

# 激活虚拟环境
function Activate-VirtualEnvironment {
    $activateScript = Join-Path $script:VenvDir "Scripts\activate.ps1"
    
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Success "虚拟环境已激活"
        return $true
    } else {
        Write-Error "虚拟环境激活脚本不存在"
        return $false
    }
}

# 安装 ErisPulse
function Install-ErisPulse {
    param([string]$Version)
    
    Write-Info "正在安装 ErisPulse..."
    
    $pkgSpec = "ErisPulse"
    if ($Version) {
        $pkgSpec = "ErisPulse==$Version"
        Write-Info "安装版本: $Version"
    } else {
        Write-Info "安装最新版本"
    }
    
    $installCmd = "pip install $pkgSpec"
    
    if ($script:UseUv -and (Test-Command "uv")) {
        $installCmd = "uv pip install $pkgSpec"
    }
    
    try {
        Invoke-Expression $installCmd
        Write-Success "ErisPulse 安装成功"
        return $true
    } catch {
        Write-Error "ErisPulse 安装失败: $_"
        return $false
    }
}

# 显示完成信息
function Show-Completion {
    Write-Host ""
    Write-Header "安装完成"
    
    Write-Host "如何激活虚拟环境:" 
    Write-Host ""
    Write-Host "  在当前终端运行: .\.venv\Scripts\activate.ps1" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "快速开始:" 
    Write-Host ""
    Write-Host "  1. 激活虚拟环境: .\.venv\Scripts\activate.ps1" -ForegroundColor Green
    Write-Host "  2. 查看帮助: epsdk -h" -ForegroundColor Green
    Write-Host "  3. 初始化项目: epsdk init" -ForegroundColor Green
    Write-Host "  4. 查看可用包: epsdk list-remote" -ForegroundColor Green
    Write-Host "  5. 安装模块: epsdk install <模块名>" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "提示:" 
    Write-Host "  - 每次打开新终端时，需要先进入项目目录并运行激活命令"
    Write-Host "  - 虚拟环境就像'独立的工作空间'，所有安装的包都在里面"
    Write-Host "  - 输入 deactivate 可以退出虚拟环境" -ForegroundColor Green
    Write-Host "  - 更新框架使用: epsdk self-update" -ForegroundColor Green
    Write-Host ""
    
    # 激活虚拟环境
    $activateScript = Join-Path $script:VenvDir "Scripts\activate.ps1"
    if (Test-Path $activateScript) {
        Write-Info "正在激活虚拟环境..."
        & $activateScript
        Write-Success "虚拟环境已激活"
        Write-Host "当前Python路径: $((Get-Command python).Source)" -ForegroundColor Yellow
    }
}

# 主流程
function Main {
    Write-Header "ErisPulse 安装程序"
    
    # 检查 Python
    if (-not (Test-Python)) {
        exit 1
    }
    
    # 询问是否使用 uv
    if (-not (Test-Command "uv")) {
        Write-Host ""
        Write-Host "uv 是一个快速的 Python 工具链，可以加速安装过程（推荐使用）" -ForegroundColor Cyan
        $installUvChoice = Read-Host "是否安装 uv？ [y/N]"
        if ($installUvChoice -match '^[yY]$') {
            if (Install-Uv) {
                $script:UseUv = $true
            } else {
                Write-Warning "uv 安装失败，将使用标准 pip"
            }
        } else {
            Write-Info "将使用标准 pip 进行安装"
        }
    } else {
        Write-Success "检测到 uv 已安装"
        $script:UseUv = $true
    }
    
    # 选择版本
    Show-VersionMenu
    
    Write-Host ""
    if ($script:TargetVersion) {
        Write-Host "将安装 ErisPulse $($script:TargetVersion)" -ForegroundColor Cyan 
    } else {
        Write-Host "将安装 ErisPulse 最新版本" -ForegroundColor Cyan 
    }
    
    $confirm = Read-Host "确认安装？ [Y/n]"
    if ($confirm -match '^[nN]$') {
        Write-Info "操作已取消"
        exit 0
    }
    
    # 创建虚拟环境
    if (-not (New-VirtualEnvironment)) {
        exit 1
    }
    
    # 激活虚拟环境
    if (-not (Activate-VirtualEnvironment)) {
        exit 1
    }
    
    # 安装 ErisPulse
    if (-not (Install-ErisPulse $script:TargetVersion)) {
        exit 1
    }
    
    # 显示完成信息
    Show-Completion
}

# 检查是否以管理员身份运行
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "不建议使用管理员身份运行此脚本"
    $continueAsAdmin = Read-Host "是否继续？ [y/N]"
    if ($continueAsAdmin -notmatch '^[yY]$') {
        exit 1
    }
}

# 运行主流程
Main

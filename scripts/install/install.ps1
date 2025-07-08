<#
.SYNOPSIS
ErisPulse ��װ�ű� - PowerShell ר�ð�

.DESCRIPTION
�˽ű����Զ���Ⲣ��װ ErisPulse ����Ļ�����������
1. ��װ uv (Python ����������)
2. ��װ Python 3.12 (ͨ�� uv)
3. �������⻷��
4. ��װ ErisPulse ���

.NOTES
��Ҫ PowerShell 5.1 ����߰汾
#>

# ��ɫ����
$ESC = [char]27
$RED = "$ESC[31m"
$GREEN = "$ESC[32m"
$YELLOW = "$ESC[33m"
$BLUE = "$ESC[34m"
$NC = "$ESC[0m"

# ���������Python�汾�Ƿ����Ҫ��
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

# ��������װuv
function Install-UV {
    Write-Host "${YELLOW}���ڰ�װ uv...${NC}"
    
    # ����Ƿ��Ѱ�װ
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-Host "${GREEN}uv �Ѱ�װ${NC}"
        return
    }
    
    # ��װuv
    try {
        Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" | Invoke-Expression
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            # �������PATH�У�������ӵ�PATH
            $uvPath = Join-Path $HOME ".cargo\bin"
            if (Test-Path $uvPath) {
                $env:PATH = "$uvPath;$env:PATH"
            }
        }
        
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            Write-Host "${GREEN}uv ��װ�ɹ�${NC}"
        } else {
            throw "uv ��װ���Բ�����"
        }
    } catch {
        Write-Host "${RED}uv ��װʧ��: $_${NC}"
        exit 1
    }
}

# ������ʹ��uv��װPython 3.12
function Install-PythonWithUV {
    Write-Host "${YELLOW}����ʹ�� uv ��װ Python 3.12...${NC}"
    
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "${RED}����: uv δ��װ${NC}"
        exit 1
    }
    
    try {
        uv python install 3.12
        if ($LASTEXITCODE -ne 0) {
            throw "uv python install ����ִ��ʧ��"
        }
        
        # ���Python�Ƿ�װ�ɹ�
        $pythonPath = uv python find 3.12
        if (-not $pythonPath) {
            throw "�޷��ҵ���װ��Python 3.12"
        }
        
        # ��ӵ�PATH
        $pythonDir = Split-Path $pythonPath
        $env:PATH = "$pythonDir;$env:PATH"
        
        Write-Host "${GREEN}Python 3.12 ��װ�ɹ�${NC}"
    } catch {
        Write-Host "${RED}Python 3.12 ��װʧ��: $_${NC}"
        exit 1
    }
}

# �������������⻷��
function New-VirtualEnvironment {
    Write-Host "${YELLOW}���ڴ������⻷��...${NC}"
    
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "${RED}����: uv δ��װ${NC}"
        exit 1
    }
    
    try {
        uv venv
        if ($LASTEXITCODE -ne 0) {
            throw "uv venv ����ִ��ʧ��"
        }
        
        # �������⻷��
        $activatePath = Join-Path (Get-Location) ".venv\Scripts\Activate.ps1"
        if (Test-Path $activatePath) {
            . $activatePath
            Write-Host "${GREEN}���⻷������������ɹ�${NC}"
        } else {
            throw "�޷��ҵ����⻷������ű�"
        }
    } catch {
        Write-Host "${RED}���⻷������ʧ��: $_${NC}"
        exit 1
    }
}

# ��������װErisPulse
function Install-ErisPulse {
    Write-Host "${YELLOW}���ڰ�װ ErisPulse...${NC}"
    
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "${RED}����: uv δ��װ${NC}"
        exit 1
    }
    
    try {
        uv pip install ErisPulse --upgrade
        if ($LASTEXITCODE -ne 0) {
            throw "uv pip install ����ִ��ʧ��"
        }
        
        Write-Host "${GREEN}ErisPulse ��װ�ɹ�${NC}"
    } catch {
        Write-Host "${RED}ErisPulse ��װʧ��: $_${NC}"
        exit 1
    }
}

# ����װ����
function Main {
    Write-Host "${BLUE}=== ErisPulse ��װ���� ===${NC}"
    
    # ���Python�汾
    $hasValidPython = Test-PythonVersion
    if ($hasValidPython) {
        Write-Host "${GREEN}��⵽����Ҫ��� Python �汾${NC}"
        $useCurrentPython = Read-Host "�Ƿ����ʹ�õ�ǰ Python �汾��[Y/n]"
        if ($useCurrentPython -match "^[nN]$") {
            $installPython = $true
        } else {
            $installPython = $false
        }
    } else {
        Write-Host "${YELLOW}δ��⵽����Ҫ��� Python �汾 (��Ҫ 3.9+)${NC}"
        $installPython = $true
    }
    
    # ��װuv
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "${YELLOW}δ��⵽ uv ��װ${NC}"
        $installUV = Read-Host "�Ƿ�װ uv��[Y/n]"
        if ($installUV -match "^[nN]$") {
            Write-Host "${RED}��Ҫ uv ���ܼ�����װ${NC}"
            exit 1
        }
        Install-UV
    } else {
        Write-Host "${GREEN}��⵽ uv �Ѱ�װ${NC}"
    }
    
    # ��װPython 3.12
    if ($installPython) {
        $installPythonChoice = Read-Host "�Ƿ�ʹ�� uv ��װ Python 3.12��[Y/n]"
        if ($installPythonChoice -match "^[nN]$") {
            Write-Host "${RED}��Ҫ Python 3.12 ���ܼ�����װ${NC}"
            exit 1
        }
        Install-PythonWithUV
    }
    
    # �������⻷��
    $createVenvChoice = Read-Host "�Ƿ񴴽����⻷����[Y/n]"
    if (-not ($createVenvChoice -match "^[nN]$")) {
        New-VirtualEnvironment
    }
    
    Install-ErisPulse
    
    Write-Host ""
    Write-Host "${GREEN}=== ��װ��� ===${NC}"
    Write-Host "����������:"
    Write-Host "1. �鿴����: ${BLUE}epsdk -h${NC}"
    Write-Host "2. ��ʼ������Ŀ: ${BLUE}epsdk init${NC}"
    Write-Host "3. ����Դ: ${BLUE}epsdk update${NC}"
    Write-Host "4. ��װģ��: ${BLUE}epsdk install ģ����${NC}"
    Write-Host "5. ����ʾ������: ${BLUE}epsdk run main.py${NC}"
    Write-Host ""
    Write-Host "${GREEN}=== ����ָ�� ===${NC}"
    Write-Host "1. ������ĿĿ¼: ${BLUE}cd $(Get-Location)${NC}"
    Write-Host "2. �������⻷��: ${BLUE}.\.venv\Scripts\Activate.ps1${NC}"
    Write-Host "3. ���г���: ${BLUE}epsdk run main.py${NC}"
    Write-Host ""
    Write-Host "${YELLOW}ע��:${NC}"
    Write-Host "- ��ȷ���� PowerShell ��������Щ����"
    Write-Host "- �������Ȩ�����⣬����ִ��: ${BLUE}Set-ExecutionPolicy RemoteSigned -Scope CurrentUser${NC}"
    Write-Host "- ÿ�δ����ն�ʱ����Ҫ���¼������⻷��"
}

$executionPolicy = Get-ExecutionPolicy
if ($executionPolicy -eq "Restricted") {
    Write-Host "${YELLOW}��ǰִ�в���Ϊ Restricted����������Ϊ RemoteSigned${NC}"
    $changePolicy = Read-Host "�Ƿ�Ҫ����ִ�в��ԣ�[Y/n]"
    if ($changePolicy -notmatch "^[nN]$") {
        Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    }
}

Main
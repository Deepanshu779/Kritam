$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot
try {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw 'Python 3.11 or newer is required to build the backend runtime.' }
    $backendPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $backendPython)) {
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the isolated backend build environment.' }
    }
    $pythonVersion = & $backendPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($LASTEXITCODE -ne 0 -or [version]$pythonVersion -lt [version]'3.11') {
        throw 'Python 3.11 or newer is required in the repository .venv.'
    }

    Write-Host 'Installing backend and PyInstaller build dependencies...'
    & $backendPython -m pip install -r backend/requirements-runtime.txt
    if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
    & $backendPython -m pip install 'pyinstaller>=6,<7'
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller installation failed.' }

    Write-Host 'Building the standalone KRITAM backend runtime...'
    & $backendPython -m PyInstaller --noconfirm --onedir --name kritam-backend `
        --paths backend `
        --distpath apps/desktop/backend-dist `
        --workpath .pyinstaller-work `
        --collect-all app `
        --collect-all fastapi `
        --collect-all uvicorn `
        --collect-all sqlalchemy `
        --collect-all faster_whisper `
        --collect-all ctranslate2 `
        --collect-all av `
        --collect-all huggingface_hub `
        backend/launcher.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed to create the backend runtime.' }

    Write-Host 'Installing locked Electron dependencies...'
    & npm ci --prefix apps/desktop
    if ($LASTEXITCODE -ne 0) { throw 'Electron dependency installation failed.' }

    Write-Host 'Building the Windows portable application...'
    & npm --prefix apps/desktop run dist:portable
    if ($LASTEXITCODE -ne 0) { throw 'electron-builder failed to create the Windows package.' }

    Write-Host 'Build commands completed. Test the generated package on a clean Windows machine before distribution.'
}
finally {
    Pop-Location
}

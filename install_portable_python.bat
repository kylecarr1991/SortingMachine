@echo off
:: Self-contained installer - Everything stays in the batch file's directory
:: 1. Portable Python       -> .\PythonPortable
:: 2. Tesseract (if needed) -> System default (requires admin) or warns
:: 3. All dependencies      -> Isolated in this folder

setlocal
set BAT_DIR=%~dp0
cd /d "%BAT_DIR%"

set PYTHON_VERSION=3.13.2
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set INSTALL_DIR=PythonPortable

:: Check if Python is already available in our portable folder
if exist "%INSTALL_DIR%\python.exe" (
    echo Found portable Python in %INSTALL_DIR%
    goto ENV_SETUP
)

:: Portable Python Installation
echo.
echo [1/3] Installing Python %PYTHON_VERSION% to %INSTALL_DIR%...
curl -o python.zip %PYTHON_URL% || (
    echo Using PowerShell as fallback...
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('%PYTHON_URL%', 'python.zip')" || (
        echo Error: Download failed. Manually download from:
        echo https://www.python.org/downloads/
        echo and place python-%PYTHON_VERSION%-embed-amd64.zip here
        pause
        exit /b
    )
)

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
powershell -Command "Expand-Archive -Path python.zip -DestinationPath .\%INSTALL_DIR%" || (
    echo Extraction failed. Check write permissions in:
    echo %BAT_DIR%
    pause
    exit /b
)
del python.zip

:ENV_SETUP
echo.
echo [2/3] Configuring local environment...
set PATH=%BAT_DIR%%INSTALL_DIR%;%PATH%
set PYTHONPATH=%BAT_DIR%%INSTALL_DIR%

:: Verify/Install Tesseract
echo.
echo [3/3] Checking Tesseract OCR...
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Tesseract not found. Attempting installer...
    python -c "import os, subprocess; subprocess.run([os.path.join(os.path.dirname(__file__), 'installer.py')], shell=True)" || (
        echo.
        echo Tesseract installation failed. You'll need to either:
        echo 1) Run this as Administrator, or
        echo 2) Manually install from:
        echo    https://github.com/UB-Mannheim/tesseract/wiki
        echo.
    )
) else (
    echo Tesseract is available at:
    where tesseract
)

: RUN_INSTALLER
echo.
echo Starting main installation...
python -c "import os, subprocess; subprocess.run([os.path.join(os.path.dirname(__file__), 'installer.py')], shell=True)"
pause
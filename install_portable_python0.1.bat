@echo off
:: Combined Python Portable + Installer Setup
:: 1. Installs portable Python if needed
:: 2. Sets up environment
:: 3. Checks/installs Tesseract
:: 4. Runs installer.py

set PYTHON_VERSION=3.13.2
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set INSTALL_DIR=PythonPortable

:: Check if Python is already available
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python is already installed.
    goto ENV_SETUP
)

:: Portable Python Installation
echo.
echo [1/3] Downloading portable Python %PYTHON_VERSION%...
curl -o python.zip %PYTHON_URL% || (
    echo Using PowerShell as fallback...
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('%PYTHON_URL%', 'python.zip')" || (
        echo Error: Download failed. Please download manually from:
        echo https://www.python.org/downloads/
        pause
        exit /b
    )
)

echo.
echo [2/3] Extracting Python...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
powershell -Command "Expand-Archive -Path python.zip -DestinationPath .\%INSTALL_DIR%" || (
    echo Error: Extraction failed.
    pause
    exit /b
)

:ENV_SETUP
echo.
echo [3/3] Setting up environment...
:: Temporarily add Python to PATH for this session
set PATH=%cd%\%INSTALL_DIR%;%PATH%
:: Permanently add to user PATH (no admin needed)
setx PATH "%PATH%;%cd%\%INSTALL_DIR%" > nul
del python.zip > nul 2>&1

:: Verify/Install Tesseract
echo.
echo Checking Tesseract OCR...
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Tesseract...
    python -c "import os, subprocess; subprocess.run([os.path.join(os.path.dirname(__file__), 'installer.py')], shell=True)"
) else (
    echo Tesseract is already installed.
)

:RUN_INSTALLER
echo.
echo Running main installer...
python -c "import os, subprocess; subprocess.run([os.path.join(os.path.dirname(__file__), 'installer.py')], shell=True)"
pause
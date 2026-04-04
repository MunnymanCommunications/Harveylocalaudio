@echo off
REM ========================================================
REM Harvey AI - Automated One-Click Installer for Windows
REM No internet required - Everything bundled on flash drive
REM ========================================================

title Harvey AI Installer
color 0B

echo.
echo ========================================================
echo              HARVEY AI INSTALLER
echo        Voice Conversational AI - Local Setup
echo ========================================================
echo.
echo This will install Harvey AI on your computer.
echo Everything is included - no internet needed!
echo.
echo Installation will take 10-30 minutes.
echo.
pause

REM Get the directory where this script is located (flash drive)
set INSTALL_DIR=%~dp0
set DEST_DIR=%USERPROFILE%\Harvey-AI
set DESKTOP=%USERPROFILE%\Desktop

echo.
echo [1/7] Checking system requirements...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Not running as administrator.
    echo Some features may not work correctly.
    echo Please right-click and select "Run as Administrator"
    echo.
    pause
)

REM Check Windows version
ver | find "10." >nul
if %errorLevel% == 0 (
    echo [OK] Windows 10 detected
) else (
    ver | find "11." >nul
    if %errorLevel% == 0 (
        echo [OK] Windows 11 detected
    ) else (
        echo [WARNING] Windows 7/8 detected - may have compatibility issues
    )
)

echo.
echo [2/7] Installing Python 3.10...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python already installed
    python --version
) else (
    echo Installing Python from bundled installer...

    REM Check if bundled Python installer exists
    if exist "%INSTALL_DIR%installers\python-3.10-installer.exe" (
        echo Found bundled Python installer
        "%INSTALL_DIR%installers\python-3.10-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        echo Waiting for Python installation...
        timeout /t 30 /nobreak >nul

        REM Refresh PATH
        call RefreshEnv.cmd >nul 2>&1

        python --version >nul 2>&1
        if %errorLevel% == 0 (
            echo [OK] Python installed successfully
        ) else (
            echo [ERROR] Python installation failed
            echo Please install Python 3.10+ manually from python.org
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] Python installer not found in installers folder
        echo.
        echo Please download Python 3.10+ and place in:
        echo %INSTALL_DIR%installers\python-3.10-installer.exe
        echo.
        echo Or download from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo.
echo [3/7] Installing Ollama AI Runtime...
echo.

REM Check if Ollama is installed
where ollama >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Ollama already installed
) else (
    echo Installing Ollama from bundled installer...

    if exist "%INSTALL_DIR%installers\OllamaSetup.exe" (
        echo Found bundled Ollama installer
        start /wait "%INSTALL_DIR%installers\OllamaSetup.exe" /S
        timeout /t 10 /nobreak >nul

        REM Refresh PATH
        call RefreshEnv.cmd >nul 2>&1

        where ollama >nul 2>&1
        if %errorLevel% == 0 (
            echo [OK] Ollama installed successfully
        ) else (
            echo [ERROR] Ollama installation failed
            echo Please install manually from ollama.com
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] Ollama installer not found
        echo.
        echo Please download Ollama installer and place in:
        echo %INSTALL_DIR%installers\OllamaSetup.exe
        echo.
        echo Or download from: https://ollama.com/download
        pause
        exit /b 1
    )
)

REM Start Ollama service
echo Starting Ollama service...
start /B ollama serve >nul 2>&1
timeout /t 3 /nobreak >nul

echo.
echo [4/7] Loading AI Model (Nemotron 3 Nano 30B)...
echo This may take 10-20 minutes if not already installed...
echo.

REM Check if model is already loaded
ollama list | find "nemotron-3-nano:30b" >nul
if %errorLevel% == 0 (
    echo [OK] AI model already loaded
) else (
    REM Check for bundled model
    if exist "%INSTALL_DIR%models\nemotron-3-nano-30b.gguf" (
        echo Loading model from flash drive...
        echo This is a large file (~17GB) - please be patient...

        REM Create Ollama models directory if it doesn't exist
        if not exist "%USERPROFILE%\.ollama\models" mkdir "%USERPROFILE%\.ollama\models"

        REM Copy model to Ollama directory
        echo Copying model file...
        copy "%INSTALL_DIR%models\nemotron-3-nano-30b.gguf" "%USERPROFILE%\.ollama\models\" /Y

        REM Create modelfile
        echo FROM nemotron-3-nano-30b.gguf > "%TEMP%\Modelfile"

        REM Load into Ollama
        ollama create nemotron-3-nano:30b -f "%TEMP%\Modelfile"

        echo [OK] Model loaded successfully
    ) else (
        echo Model not found on flash drive.
        echo Downloading from internet (requires connection)...
        ollama pull nemotron-3-nano:30b

        if %errorLevel% == 0 (
            echo [OK] Model downloaded successfully
        ) else (
            echo [WARNING] Model download failed
            echo You can download it later by running:
            echo   ollama pull nemotron-3-nano:30b
        )
    )
)

echo.
echo [5/7] Copying Harvey AI files...
echo.

REM Create destination directory
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"

echo Copying application files...
xcopy /E /I /Y "%INSTALL_DIR%backend" "%DEST_DIR%\backend" >nul
xcopy /E /I /Y "%INSTALL_DIR%desktop-app" "%DEST_DIR%\desktop-app" >nul
xcopy /E /I /Y "%INSTALL_DIR%web-client" "%DEST_DIR%\web-client" >nul
xcopy /Y "%INSTALL_DIR%*.sh" "%DEST_DIR%\" >nul
xcopy /Y "%INSTALL_DIR%*.bat" "%DEST_DIR%\" >nul
xcopy /Y "%INSTALL_DIR%*.md" "%DEST_DIR%\" >nul

echo [OK] Files copied to: %DEST_DIR%

echo.
echo [6/7] Installing Python dependencies...
echo.

REM Install backend dependencies
echo Installing backend dependencies (this may take 5-10 minutes)...
cd "%DEST_DIR%\backend"

REM Check for bundled wheels
if exist "%INSTALL_DIR%wheels\*.whl" (
    echo Installing from bundled packages...
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --no-index --find-links="%INSTALL_DIR%wheels" -r requirements.txt
) else (
    echo Installing from PyPI (requires internet)...
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)

if %errorLevel% == 0 (
    echo [OK] Backend dependencies installed
) else (
    echo [WARNING] Some dependencies failed to install
    echo Harvey may not work correctly
)
call deactivate

REM Install desktop app dependencies
echo Installing desktop app dependencies...
cd "%DEST_DIR%\desktop-app"
python -m venv venv
call venv\Scripts\activate.bat

if exist "%INSTALL_DIR%wheels\*.whl" (
    python -m pip install --no-index --find-links="%INSTALL_DIR%wheels" -r requirements.txt
) else (
    python -m pip install -r requirements.txt
)

call deactivate

echo.
echo [7/7] Creating desktop shortcut...
echo.

REM Create VBS script to create shortcut
set SHORTCUT_VBS=%TEMP%\CreateShortcut.vbs
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SHORTCUT_VBS%"
echo sLinkFile = "%DESKTOP%\Harvey AI.lnk" >> "%SHORTCUT_VBS%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SHORTCUT_VBS%"
echo oLink.TargetPath = "%DEST_DIR%\LAUNCH-HARVEY.bat" >> "%SHORTCUT_VBS%"
echo oLink.WorkingDirectory = "%DEST_DIR%" >> "%SHORTCUT_VBS%"
echo oLink.Description = "Harvey AI - Voice Conversational AI" >> "%SHORTCUT_VBS%"
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll,165" >> "%SHORTCUT_VBS%"
echo oLink.Save >> "%SHORTCUT_VBS%"

cscript //nologo "%SHORTCUT_VBS%"
del "%SHORTCUT_VBS%"

REM Create launcher batch file
echo @echo off > "%DEST_DIR%\LAUNCH-HARVEY.bat"
echo cd /d "%%~dp0desktop-app" >> "%DEST_DIR%\LAUNCH-HARVEY.bat"
echo call venv\Scripts\activate.bat >> "%DEST_DIR%\LAUNCH-HARVEY.bat"
echo python app.py >> "%DEST_DIR%\LAUNCH-HARVEY.bat"

echo [OK] Desktop shortcut created

echo.
echo ========================================================
echo              INSTALLATION COMPLETE!
echo ========================================================
echo.
echo Harvey AI has been successfully installed!
echo.
echo Location: %DEST_DIR%
echo.
echo To start Harvey AI:
echo   1. Double-click "Harvey AI" icon on your desktop
echo   OR
echo   2. Run: %DEST_DIR%\LAUNCH-HARVEY.bat
echo.
echo IMPORTANT: Keep your flash drive safe!
echo It contains the original files and can be used
echo to install Harvey on other computers.
echo.
echo ========================================================
echo.
echo Press any key to launch Harvey AI now...
pause >nul

REM Launch Harvey AI
start "" "%DEST_DIR%\LAUNCH-HARVEY.bat"

exit /b 0

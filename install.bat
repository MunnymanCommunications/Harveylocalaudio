@echo off
REM Harvey Local Audio - Windows Installation Script

echo =======================================
echo Harvey Local Audio - Installation
echo =======================================
echo.

REM Check Python version
echo Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo Error: Python 3.10+ is required
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo Python detected
echo.

REM Check Ollama
echo Checking Ollama installation...
where ollama >nul 2>nul
if errorlevel 1 (
    echo Ollama not found. Please install Ollama from https://ollama.com/download
    echo After installation, run this script again.
    pause
    exit /b 1
)
echo Ollama installed
echo.

REM Pull Gemma 3 14B
echo Pulling Gemma 3 14B model (this may take a while)...
ollama pull gemma3:14b
echo Gemma 3 14B ready
echo.

REM Install Piper TTS
echo Installing Piper TTS...
pip install piper-tts
echo Piper TTS installed
echo.

REM Setup backend
echo Setting up backend environment...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
echo Backend environment ready
echo.

REM Setup desktop app
echo Setting up desktop app environment...
cd desktop-app
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
echo Desktop app environment ready
echo.

REM Create launcher scripts
echo Creating launcher scripts...

REM Desktop app launcher
echo @echo off > run-desktop-app.bat
echo cd /d "%%~dp0\desktop-app" >> run-desktop-app.bat
echo call venv\Scripts\activate.bat >> run-desktop-app.bat
echo python app.py >> run-desktop-app.bat
echo pause >> run-desktop-app.bat

REM Server launcher
echo @echo off > run-server.bat
echo cd /d "%%~dp0\backend" >> run-server.bat
echo call venv\Scripts\activate.bat >> run-server.bat
echo python main.py >> run-server.bat
echo pause >> run-server.bat

echo Launcher scripts created
echo.

echo =======================================
echo Installation Complete!
echo =======================================
echo.
echo To start the desktop application:
echo   run-desktop-app.bat
echo.
echo Or to run the server directly:
echo   run-server.bat
echo.
echo The desktop app provides an easy GUI to:
echo   - Start/stop the server
echo   - View WebSocket URL and API key
echo   - Configure voice settings
echo   - Monitor server logs
echo.
pause

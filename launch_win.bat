@echo off
REM ==============================================
REM 1. Check and install dependencies
REM ==============================================
IF EXIST "config.json" (
    echo Dependencies already installed. Launching directly...
    GOTO run_app
)

echo Installation of dependencies...
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Installation of dependencies failed. Error code: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

:run_app
REM ==============================================
REM 2. Run the Python script
REM ==============================================
echo Launching the application...
python main.py
IF %ERRORLEVEL% NEQ 0 (
    echo The Python script failed. Error code: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)
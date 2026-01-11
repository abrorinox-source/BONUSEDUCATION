@echo off
REM Telegram Bot - Quick Start Script for Windows
REM Bu faylni ikki marta bosib ishga tushiring

echo ================================================
echo Telegram Points Management Bot
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment topilmadi!
    echo Yaratyapman...
    python -m venv venv
    echo.
    echo Virtual environment yaratildi!
    echo.
)

REM Activate virtual environment
echo Virtual environment aktivlashtirilmoqda...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
echo.
echo Dependencies tekshirilmoqda...
pip show aiogram >nul 2>&1
if errorlevel 1 (
    echo Dependencies o'rnatilmagan!
    echo O'rnatilmoqda... (Bu 2-3 daqiqa davom etadi)
    echo.
    pip install -r requirements.txt
    echo.
    echo Dependencies o'rnatildi!
    echo.
)

REM Check for serviceAccountKey.json
if not exist "serviceAccountKey.json" (
    echo.
    echo ================================================
    echo XATO: serviceAccountKey.json topilmadi!
    echo ================================================
    echo.
    echo Iltimos, Firebase'dan serviceAccountKey.json faylini yuklab oling
    echo va ushbu papkaga joylashtiring.
    echo.
    echo Ko'rsatma: START_BOT.md faylini o'qing
    echo.
    pause
    exit /b 1
)

REM Start the bot
echo.
echo ================================================
echo Bot ishga tushirilmoqda...
echo ================================================
echo.
python main.py

REM If bot stops
echo.
echo Bot to'xtatildi.
echo.
pause

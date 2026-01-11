#!/bin/bash
# Telegram Bot - Quick Start Script for Linux/Mac
# Make executable: chmod +x start_bot.sh
# Run: ./start_bot.sh

echo "================================================"
echo "Telegram Points Management Bot"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment topilmadi!"
    echo "Yaratyapman..."
    python3 -m venv venv
    echo ""
    echo "Virtual environment yaratildi!"
    echo ""
fi

# Activate virtual environment
echo "Virtual environment aktivlashtirilmoqda..."
source venv/bin/activate

# Check if dependencies are installed
echo ""
echo "Dependencies tekshirilmoqda..."
if ! pip show aiogram > /dev/null 2>&1; then
    echo "Dependencies o'rnatilmagan!"
    echo "O'rnatilmoqda... (Bu 2-3 daqiqa davom etadi)"
    echo ""
    pip install -r requirements.txt
    echo ""
    echo "Dependencies o'rnatildi!"
    echo ""
fi

# Check for serviceAccountKey.json
if [ ! -f "serviceAccountKey.json" ]; then
    echo ""
    echo "================================================"
    echo "XATO: serviceAccountKey.json topilmadi!"
    echo "================================================"
    echo ""
    echo "Iltimos, Firebase'dan serviceAccountKey.json faylini yuklab oling"
    echo "va ushbu papkaga joylashtiring."
    echo ""
    echo "Ko'rsatma: START_BOT.md faylini o'qing"
    echo ""
    exit 1
fi

# Start the bot
echo ""
echo "================================================"
echo "Bot ishga tushirilmoqda..."
echo "================================================"
echo ""
python3 main.py

# If bot stops
echo ""
echo "Bot to'xtatildi."
echo ""

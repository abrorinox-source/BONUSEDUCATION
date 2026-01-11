# 📦 Installation Guide

## Quick Start (5 Minutes)

### 1️⃣ Install Python Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2️⃣ Get Firebase Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (or create new)
3. Click ⚙️ **Settings** → **Project Settings**
4. Go to **Service Accounts** tab
5. Click **Generate New Private Key**
6. Save as \`serviceAccountKey.json\` in project root

### 3️⃣ Set Up Google Sheets

1. Create a new Google Sheet
2. In row 1, add headers:
   \`\`\`
   User_ID | Full_Name | Phone | Username | Points | Last_Updated
   \`\`\`
3. Copy Sheet ID from URL:
   \`\`\`
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   \`\`\`
4. Share sheet with service account email:
   - Open \`serviceAccountKey.json\`
   - Find \`"client_email"\`
   - Copy email address
   - Click **Share** in Google Sheets
   - Add this email with **Editor** access

### 4️⃣ Get Telegram Bot Token

1. Open Telegram
2. Message [@BotFather](https://t.me/BotFather)
3. Send \`/newbot\`
4. Follow instructions
5. Copy bot token

### 5️⃣ Update config.py

\`\`\`python
BOT_TOKEN = "paste_your_bot_token_here"
SHEET_ID = "paste_your_sheet_id_here"
TEACHER_CODE = '11991188'  # Change to your secret code
\`\`\`

### 6️⃣ Run Bot

\`\`\`bash
python main.py
\`\`\`

✅ **Done!** Bot is now running.

## First Time Usage

### Register as Teacher:
1. Open your bot in Telegram
2. Send \`/start\`
3. Enter your name
4. When asked for teacher code, enter: \`11991188\` (or your custom code)
5. ✅ You're now a teacher!

### Register as Student:
1. Open bot in Telegram
2. Send \`/start\`
3. Enter your name
4. Click "Skip" when asked for teacher code
5. Share your contact
6. Wait for teacher approval

## Troubleshooting

### ❌ Error: "No module named 'firebase_admin'"
**Solution:**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### ❌ Error: "serviceAccountKey.json not found"
**Solution:**
- Make sure \`serviceAccountKey.json\` is in the project root folder
- Check file name spelling (case-sensitive)

### ❌ Error: "Permission denied" for Google Sheets
**Solution:**
- Share Google Sheet with service account email
- Email found in \`serviceAccountKey.json\` → \`"client_email"\`
- Give **Editor** permissions

### ❌ Bot doesn't respond
**Solution:**
- Check BOT_TOKEN is correct in config.py
- Make sure bot is running (check terminal)
- Try \`/start\` command

### ❌ Sync not working
**Solution:**
- Verify SHEET_ID is correct
- Check Google Sheets is shared with service account
- Enable Sheets API in Google Cloud Console

## Advanced Configuration

### Change Sync Interval
In bot, as teacher:
1. Click **⚙️ Settings**
2. Click **🔄 Sync Control**
3. Click **⏱️ Change Interval**
4. Select desired interval (5s to 15min)

### Change Commission Rate
1. Click **⚙️ Settings**
2. Click **💰 Transfer Commission**
3. Enter new rate (0-50)

### Enable Maintenance Mode
1. Click **⚙️ Settings**
2. Click **🔓 Bot Status**
3. Select **🔧 Maintenance Mode**

## Production Deployment

### Using PM2 (Recommended)
\`\`\`bash
# Install PM2
npm install -g pm2

# Start bot
pm2 start main.py --interpreter python3 --name telegram-bot

# View logs
pm2 logs telegram-bot

# Stop bot
pm2 stop telegram-bot

# Restart bot
pm2 restart telegram-bot
\`\`\`

### Using systemd (Linux)
Create \`/etc/systemd/system/telegram-bot.service\`:
\`\`\`ini
[Unit]
Description=Telegram Points Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 /path/to/bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
\`\`\`

Then:
\`\`\`bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
\`\`\`

## Environment Variables (Optional)

Create \`.env\` file:
\`\`\`env
BOT_TOKEN=your_token_here
SHEET_ID=your_sheet_id_here
TEACHER_CODE=your_code_here
SILENT_START=False
\`\`\`

Modify \`config.py\`:
\`\`\`python
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
SHEET_ID = os.getenv('SHEET_ID')
TEACHER_CODE = os.getenv('TEACHER_CODE', '11991188')
SILENT_START = os.getenv('SILENT_START', 'False') == 'True'
\`\`\`

## Next Steps

1. ✅ Test registration flow
2. ✅ Test points transfer
3. ✅ Test sync functionality
4. ✅ Configure commission rate
5. ✅ Customize rules text
6. ✅ Test all export formats

## Need Help?

Check documentation:
- \`README.md\` - General overview
- \`Bot haqida 2.txt\` - Detailed specifications
- \`Data Consistency Analysis.txt\` - Technical details
- \`Advanced Features.txt\` - Extended features

## 🎉 You're All Set!

Your bot is now ready to use. Enjoy! 🚀

# 🚀 Render.com Deployment Guide

## Webhook Configuration Complete ✅

Bot is now configured to use **webhook mode** for deployment on Render.com.

---

## 📋 Deployment Steps

### 1. Configure Your .env File (Local Development)

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```env
BOT_TOKEN=8466410998:AAFUo6iKrDN8YUTzYUkieJ_eQ76cnC5_Jps
TEACHER_CODE=11991188
SHEET_ID=1SsUnFwqDc1bj46LwHb0OtwPZkCyU3Ip4A96xSjWZzRo
FIREBASE_KEY_PATH=serviceAccountKey.json

# For local testing, set to False
USE_WEBHOOK=False
```

### 2. Push Code to GitHub
```bash
git add .
git commit -m "Configure webhook mode for Render deployment"
git push origin main
```

### 3. Create New Web Service on Render
1. Go to [render.com](https://render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Select your bot repository

### 4. Configure Environment Variables on Render

**Only 4 variables needed!** (Render auto-detects the rest)

| Key | Value | Description |
|-----|-------|-------------|
| `BOT_TOKEN` | `8466410998:AAFUo...` | Your Telegram bot token |
| `TEACHER_CODE` | `11991188` | Teacher registration code |
| `SHEET_ID` | `1SsUnFwqDc1bj4...` | Google Sheets ID |
| `USE_WEBHOOK` | `True` | Enable webhook mode |

✨ **That's it!** No need to enter:
- ❌ `WEBHOOK_HOST` - Auto-detected from `RENDER_EXTERNAL_URL`
- ❌ `PORT` - Automatically set by Render to 10000
- ❌ App name - Render knows this automatically

**Firebase Setup:**
Upload `serviceAccountKey.json` to Render or paste JSON content as `FIREBASE_CREDENTIALS` env var.

### 5. Deploy Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Plan**: Free

### 6. Create serviceAccountKey.json
Since Render needs the Firebase key file:

**Option A: Use FIREBASE_CREDENTIALS env var (Recommended)**
- Paste entire JSON content of `serviceAccountKey.json` as environment variable
- Update `config.py` to read from env var

**Option B: Add to repository (Not recommended for security)**
- Add `serviceAccountKey.json` to repository
- Remove from `.gitignore`

---

## 🔄 Switching Between Modes

### For Local Development (Polling):
Edit `.env` file:
```env
USE_WEBHOOK=False
```
Then run:
```bash
python main.py
```

### For Production (Webhook):
Set environment variable on Render:
```
USE_WEBHOOK=True
```

✨ **That's all!** Render automatically provides:
- `RENDER_EXTERNAL_URL` (your app's webhook URL)
- `PORT` (set to 10000)

**No app name needed!** Bot auto-detects everything.

---

## ✅ Verification

After deployment:
1. Check Render logs for: `✅ Webhook server started`
2. Send `/start` to your bot on Telegram
3. Bot should respond immediately

---

## 🐛 Troubleshooting

### Bot not responding
- Check `WEBHOOK_HOST` is correct (matches your Render URL)
- Verify all environment variables are set
- Check Render logs for errors

### Webhook errors
- Ensure URL is HTTPS (Telegram requires HTTPS)
- Verify port 10000 is used
- Check firewall/network settings

### Firebase errors
- Verify `FIREBASE_CREDENTIALS` JSON is valid
- Check Firebase permissions

---

## 📝 Notes

- Webhook mode uses **less resources** than polling
- **Faster response times** (instant updates)
- Required for **free Render deployment**
- Automatically handles SSL/HTTPS

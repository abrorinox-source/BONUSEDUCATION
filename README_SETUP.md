# 🚀 Quick Setup Guide

## Local Development (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example to .env
cp .env.example .env
```

### 3. Edit .env for Local Testing
```env
BOT_TOKEN=8466410998:AAFUo6iKrDN8YUTzYUkieJ_eQ76cnC5_Jps
TEACHER_CODE=11991188
SHEET_ID=1SsUnFwqDc1bj46LwHb0OtwPZkCyU3Ip4A96xSjWZzRo
FIREBASE_KEY_PATH=serviceAccountKey.json

# IMPORTANT: Set to False for local development
USE_WEBHOOK=False
```

### 4. Add Firebase Key
Place your `serviceAccountKey.json` file in the project root.

### 5. Run Bot
```bash
python main.py
```

You should see:
```
🚀 TELEGRAM BOT - POINTS MANAGEMENT SYSTEM
Mode: POLLING
✅ Bot startup complete!
```

---

## Production Deployment (Render.com)

### Quick Deploy Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push
   ```

2. **On Render Dashboard**
   - Create new Web Service
   - Connect GitHub repo
   - Add only 4 environment variables:
     - `BOT_TOKEN` (from .env)
     - `TEACHER_CODE` (from .env)
     - `SHEET_ID` (from .env)
     - `USE_WEBHOOK=True`
   - Click "Deploy"

✨ **No app name needed!** Render auto-detects webhook URL via `RENDER_EXTERNAL_URL`

📖 **Full deployment guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Environment Variables Checklist

### Required for All:
- ✅ `BOT_TOKEN` - Telegram bot token
- ✅ `TEACHER_CODE` - Teacher registration code
- ✅ `SHEET_ID` - Google Sheets ID
- ✅ `FIREBASE_KEY_PATH` - Path to Firebase key

### For Production Only:
- ✅ `USE_WEBHOOK=True` - Enable webhook mode

**Auto-detected by Render:**
- 🤖 `RENDER_EXTERNAL_URL` - Webhook URL (no need to set)
- 🤖 `PORT` - Server port (automatically 10000)

---

## Testing

### Local Test (Polling Mode):
```bash
# Make sure .env has USE_WEBHOOK=False
python main.py
```

### Production Test (Webhook Mode):
```bash
# Set .env: USE_WEBHOOK=True
# Set WEBHOOK_HOST to localhost for testing
python main.py
```

---

## Troubleshooting

### Bot not starting?
- Check `BOT_TOKEN` is correct
- Verify `serviceAccountKey.json` exists
- Check all required env vars are set

### Webhook errors on Render?
- Verify `WEBHOOK_HOST` matches your Render URL
- Check PORT is 10000
- Ensure HTTPS (not HTTP)

### Firebase errors?
- Verify `serviceAccountKey.json` is valid JSON
- Check Firebase permissions
- On Render: paste entire JSON as env var

---

## File Structure

```
.
├── .env                    # Your local config (DO NOT COMMIT)
├── .env.example           # Template for .env
├── config.py              # Reads from .env
├── main.py                # Bot entry point (webhook/polling)
├── serviceAccountKey.json # Firebase credentials (DO NOT COMMIT)
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── DEPLOYMENT.md         # Full deployment guide
└── README_SETUP.md       # This file
```

---

## Next Steps

1. ✅ Test locally with polling mode
2. ✅ Deploy to Render with webhook mode
3. ✅ Verify bot responds on Telegram
4. ✅ Check Render logs for errors

**Need help?** Read [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

# 🚀 Deploy Your Telegram Bot to Render

## Why Render?

- ✅ **Free tier available** - $0/month for background workers
- ✅ **Always online** - Bot runs 24/7
- ✅ **Easy deployment** - Connect GitHub and deploy
- ✅ **Auto-restart** - If bot crashes, it restarts automatically
- ✅ **Environment variables** - Secure credential storage

---

## 📋 Prerequisites

1. **GitHub account** - To connect with Render
2. **Render account** - Sign up at https://render.com (free)
3. Your bot files (you already have them!)

---

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository

1. **Create a GitHub repository** (if you haven't already)
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Important**: Make sure `serviceAccountKey.json` is NOT pushed to GitHub!
   - Check `.gitignore` - it should exclude `serviceAccountKey.json` ✅ (already configured)

---

### Step 2: Sign Up on Render

1. Go to: https://render.com
2. Click **"Get Started"**
3. Sign up with GitHub (recommended)
4. Authorize Render to access your repositories

---

### Step 3: Create a New Background Worker

1. **Dashboard** → Click **"New +"** → Select **"Background Worker"**

2. **Connect your repository**:
   - Select your bot repository
   - Click **"Connect"**

3. **Configure the service**:
   - **Name**: `telegram-points-bot` (or any name you like)
   - **Region**: Choose closest to you (e.g., Oregon, Frankfurt)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Select **"Free"** ($0/month)

---

### Step 4: Set Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these variables:

| Key | Value | Where to get it |
|-----|-------|-----------------|
| `PYTHON_VERSION` | `3.11.0` | (Just type this) |
| `BOT_TOKEN` | `8332724613:AAGc...` | From `config.py` |
| `SHEET_ID` | `1SsUnFwqDc1bj46Lw...` | From `config.py` |
| `TEACHER_CODE` | `11991188` | From `config.py` |
| `FIREBASE_CREDENTIALS` | (see below) | From `serviceAccountKey.json` |

#### For FIREBASE_CREDENTIALS:

1. Open `serviceAccountKey.json`
2. Copy **entire content** (all the JSON)
3. Paste it as the value for `FIREBASE_CREDENTIALS`
4. Make sure it's valid JSON (one line is fine)

**Example**:
```json
{"type":"service_account","project_id":"your-project",...}
```

---

### Step 5: Update Your Bot Code (Optional)

If you want to read credentials from environment variables instead of files:

**Option A**: Keep using files (simpler, no code changes needed)
- Upload `serviceAccountKey.json` manually after deployment
- Use Render's file upload feature

**Option B**: Use environment variables (more secure)
- I can help you modify `config.py` and `database.py` to read from environment variables

---

### Step 6: Deploy!

1. Click **"Create Background Worker"**
2. Render will:
   - Clone your repository
   - Install dependencies
   - Start your bot
3. Monitor logs in the **"Logs"** tab

---

## ✅ Verify Deployment

1. **Check Logs**:
   - Go to your service → **"Logs"** tab
   - You should see:
     ```
     🤖 Bot starting...
     ✅ Settings loaded
     ✅ Bot startup complete!
     ```

2. **Test the bot**:
   - Open Telegram
   - Send `/start` to your bot
   - Should respond in 1-6 seconds (polling mode)

---

## 🔧 Troubleshooting

### Bot not starting?

**Check logs for errors**:

1. **Firebase credentials error**:
   - Make sure `FIREBASE_CREDENTIALS` environment variable is set
   - Or upload `serviceAccountKey.json` file

2. **Missing dependencies**:
   - Make sure `requirements.txt` is correct
   - Check build logs

3. **Bot token invalid**:
   - Verify `BOT_TOKEN` environment variable

### Bot keeps restarting?

- Check if there's an error in startup
- Review logs for the actual error message

---

## 💡 Alternative: Use Dockerfile (Optional)

If you want more control, you can use Docker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Then select **"Docker"** as the environment in Render.

---

## 🎯 What Do You Want To Do?

**Option A**: I'll help you set up environment variables in your code
- Modify `config.py` to read from environment variables
- More secure, better for production

**Option B**: Deploy as-is with file upload
- Simpler, but need to upload `serviceAccountKey.json` manually

**Option C**: Show me step-by-step with screenshots
- I'll guide you through the Render interface

Which option would you like?

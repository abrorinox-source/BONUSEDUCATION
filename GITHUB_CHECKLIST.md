# ✅ GitHub to Render - Quick Checklist

Use this as your step-by-step guide while following the detailed instructions.

---

## 📋 Part 1: GitHub Setup (10 minutes)

### ☐ Step 1.1: Create GitHub Account
- [ ] Go to https://github.com
- [ ] Click "Sign up"
- [ ] Enter email, password, username
- [ ] Verify email
- [ ] ✅ Account created!

---

### ☐ Step 1.2: Install Git
- [ ] Download from https://git-scm.com
- [ ] Run installer (click Next → Next → Finish)
- [ ] Open Command Prompt/Terminal
- [ ] Type: `git --version`
- [ ] See version number?
- [ ] ✅ Git installed!

---

### ☐ Step 1.3: Configure Git
Open Command Prompt and type:

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

- [ ] Configured name
- [ ] Configured email
- [ ] ✅ Git configured!

---

### ☐ Step 1.4: Initialize Git in Your Bot Folder

```bash
cd C:\path\to\your\bot\folder
git init
git add .
git commit -m "Initial commit"
```

- [ ] Navigated to bot folder
- [ ] Ran `git init`
- [ ] Ran `git add .`
- [ ] Ran `git commit -m "Initial commit"`
- [ ] ✅ Code ready for upload!

---

### ☐ Step 1.5: Create GitHub Repository
- [ ] Go to https://github.com
- [ ] Click green "New" button
- [ ] Repository name: `telegram-points-bot`
- [ ] Choose Private
- [ ] DON'T check "Initialize with README"
- [ ] Click "Create repository"
- [ ] ✅ Repository created!

---

### ☐ Step 1.6: Get Personal Access Token
- [ ] GitHub → Profile picture → Settings
- [ ] Developer settings → Personal access tokens
- [ ] Generate new token (classic)
- [ ] Name: "Render deployment"
- [ ] Check: `repo`
- [ ] Generate token
- [ ] **COPY TOKEN** (save it somewhere!)
- [ ] ✅ Token created!

---

### ☐ Step 1.7: Upload Code to GitHub

```bash
git remote add origin https://github.com/YOUR-USERNAME/telegram-points-bot.git
git branch -M main
git push -u origin main
```

- [ ] Replaced YOUR-USERNAME with actual username
- [ ] Ran the commands
- [ ] Entered username when asked
- [ ] Entered TOKEN (not password) when asked
- [ ] Upload completed?
- [ ] Refresh GitHub page - see your files?
- [ ] ✅ Code uploaded to GitHub!

---

## 🚀 Part 2: Deploy to Render (5 minutes)

### ☐ Step 2.1: Sign Up on Render
- [ ] Go to https://render.com
- [ ] Click "Get Started"
- [ ] Sign up with GitHub (easiest)
- [ ] Authorize Render
- [ ] ✅ Render account ready!

---

### ☐ Step 2.2: Create Background Worker
- [ ] Dashboard → "New +"
- [ ] Select "Background Worker"
- [ ] Find your repository: `telegram-points-bot`
- [ ] Click "Connect"
- [ ] ✅ Repository connected!

---

### ☐ Step 2.3: Configure Settings
- [ ] Name: `telegram-bot`
- [ ] Region: Oregon (or closest)
- [ ] Branch: `main`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `python main.py`
- [ ] Instance Type: **Free**
- [ ] ✅ Settings configured!

---

### ☐ Step 2.4: Add Environment Variables

Click "Advanced" → "Add Environment Variable"

**Variable 1:**
- [ ] Key: `BOT_TOKEN`
- [ ] Value: `8332724613:AAGcV0-zFYgx4wnAib76qV5sO6hmac9_-1E`

**Variable 2:**
- [ ] Key: `SHEET_ID`
- [ ] Value: `1SsUnFwqDc1bj46LwHb0OtwPZkCyU3Ip4A96xSjWZzRo`

**Variable 3:**
- [ ] Key: `TEACHER_CODE`
- [ ] Value: `11991188`

**Variable 4:**
- [ ] Key: `FIREBASE_CREDENTIALS`
- [ ] Open `serviceAccountKey.json`
- [ ] Copy entire JSON content
- [ ] Paste as value
- [ ] ✅ All variables added!

---

### ☐ Step 2.5: Deploy!
- [ ] Click "Create Background Worker"
- [ ] Wait 2-3 minutes
- [ ] Watch "Logs" tab
- [ ] See "Bot startup complete!"?
- [ ] ✅ Bot deployed!

---

### ☐ Step 2.6: Test Bot
- [ ] Open Telegram
- [ ] Find: @scoresharebot
- [ ] Send: `/start`
- [ ] Bot responds?
- [ ] 🎉 **SUCCESS! YOUR BOT IS LIVE 24/7!**

---

## 🔍 Quick Troubleshooting

### ❌ Git not recognized
```bash
# Close and reopen Command Prompt
# Or restart computer
```

### ❌ Permission denied (GitHub push)
- Use Personal Access Token, NOT password
- Token must have `repo` permission checked

### ❌ Build failed on Render
- Check logs for error message
- Common issue: Missing environment variable

### ❌ Bot not responding
- Check Render logs for errors
- Verify BOT_TOKEN in environment variables
- Make sure FIREBASE_CREDENTIALS is valid JSON (no extra spaces)

---

## 📞 Need Help?

Tell me which step you're on:
- "I'm on Step 1.3" - I'll help with that specific step
- "Error at Step 2.4" - I'll troubleshoot
- "Everything works!" - Congratulations! 🎉

---

## 🎯 Current Status Tracker

**Where are you now?**

- [ ] Haven't started yet
- [ ] Created GitHub account
- [ ] Installed Git
- [ ] Uploaded code to GitHub
- [ ] Signed up on Render
- [ ] Deployed successfully!
- [ ] ✅ Bot is live and working!

---

**Ready to start? Tell me and I'll guide you step by step!** 🚀

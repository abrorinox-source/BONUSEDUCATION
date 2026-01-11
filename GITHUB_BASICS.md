# 📚 GitHub Basics - 15 Minute Crash Course

## 🤔 What is GitHub?

Think of GitHub as **Google Drive for code**:
- 📦 Stores your code online
- 🔄 Tracks all changes you make
- 🌐 Lets you deploy to servers (like Render)
- 🆓 Free for public projects

---

## 🎯 What You'll Learn

1. ✅ Create a GitHub account
2. ✅ Install Git on your computer
3. ✅ Upload your bot to GitHub
4. ✅ Connect GitHub to Render
5. ✅ Deploy your bot (free 24/7!)

**Total time: 15 minutes**

---

## 📝 Step 1: Create GitHub Account (2 minutes)

1. **Go to**: https://github.com
2. **Click**: "Sign up"
3. **Fill in**:
   - Email: your@email.com
   - Password: (choose one)
   - Username: (choose one, e.g., `yourname`)
4. **Verify** email
5. **Done!** You have a GitHub account

---

## 🔧 Step 2: Install Git (3 minutes)

Git is the tool that connects your computer to GitHub.

### For Windows:

1. **Download**: https://git-scm.com/download/win
2. **Run installer**
3. **Click "Next"** through everything (use defaults)
4. **Finish** installation

### For Mac:

1. **Open Terminal**
2. **Type**: `git --version`
3. **If not installed**, it will prompt you to install
4. **Click "Install"**

### Verify Installation:

Open Command Prompt/Terminal and type:
```bash
git --version
```

Should show something like: `git version 2.43.0`

✅ **Git is installed!**

---

## 📤 Step 3: Upload Your Bot to GitHub (5 minutes)

### A. Configure Git (First Time Only)

Open Command Prompt/Terminal:

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

Replace with your actual name and email.

---

### B. Prepare Your Bot Folder

**IMPORTANT**: Make sure these files exist:
- ✅ `.gitignore` (already exists - good!)
- ✅ `requirements.txt` (already exists)
- ✅ Your bot files

**Check .gitignore excludes secrets**:
Your `.gitignore` should have:
```
serviceAccountKey.json
*.json
.env
```

✅ **This is already set up correctly!**

---

### C. Initialize Git in Your Bot Folder

1. **Open Command Prompt** (Windows) or **Terminal** (Mac)
2. **Navigate to your bot folder**:
   ```bash
   cd C:\Users\diyor\YourBotFolder
   ```
   Replace with your actual folder path

3. **Initialize Git**:
   ```bash
   git init
   ```
   You'll see: `Initialized empty Git repository`

4. **Add all files**:
   ```bash
   git add .
   ```
   This stages all your files for upload

5. **Commit (save snapshot)**:
   ```bash
   git commit -m "Initial commit - Telegram bot"
   ```
   You'll see a list of files added

✅ **Your code is ready to upload!**

---

### D. Create Repository on GitHub

1. **Go to**: https://github.com
2. **Click**: Green "New" button (or "+" in top right → "New repository")
3. **Fill in**:
   - **Repository name**: `telegram-points-bot` (or any name)
   - **Description**: "Telegram bot for points management"
   - **Public** or **Private**: Choose Private (more secure)
   - **DON'T** check "Initialize with README" (already have files)
4. **Click**: "Create repository"

✅ **Repository created!**

---

### E. Upload Code to GitHub

GitHub will show you commands. Use these:

```bash
git remote add origin https://github.com/YOUR-USERNAME/telegram-points-bot.git
git branch -M main
git push -u origin main
```

**Replace `YOUR-USERNAME`** with your actual GitHub username!

**It will ask for credentials**:
- Username: your GitHub username
- Password: **NOT your password**, use a **Personal Access Token**

#### How to Get Personal Access Token:

1. GitHub → Click your profile picture → **Settings**
2. Scroll down → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. **Generate new token** → **Generate new token (classic)**
5. **Name**: "Render deployment"
6. **Expiration**: 90 days
7. **Check**: `repo` (gives access to repositories)
8. **Generate token**
9. **Copy the token** (you won't see it again!)

**Use this token as password when pushing to GitHub**

---

After push completes:

✅ **Your code is on GitHub!**

Refresh your GitHub repository page - you'll see all your files!

---

## 🚀 Step 4: Deploy to Render (5 minutes)

Now the magic happens - deploy for free 24/7!

### A. Sign Up on Render

1. **Go to**: https://render.com
2. **Click**: "Get Started"
3. **Sign up with GitHub** (recommended)
4. **Authorize Render** to access your repositories

---

### B. Create Background Worker

1. **Dashboard** → Click **"New +"**
2. Select **"Background Worker"**
3. **Connect your repository**:
   - Find: `telegram-points-bot`
   - Click **"Connect"**

---

### C. Configure Service

Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `telegram-bot` |
| **Region** | Oregon (or closest to you) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python main.py` |
| **Instance Type** | **Free** |

---

### D. Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these 4 variables:

**1. BOT_TOKEN**
```
8332724613:AAGcV0-zFYgx4wnAib76qV5sO6hmac9_-1E
```

**2. SHEET_ID**
```
1SsUnFwqDc1bj46LwHb0OtwPZkCyU3Ip4A96xSjWZzRo
```

**3. TEACHER_CODE**
```
11991188
```

**4. FIREBASE_CREDENTIALS**
- Open your `serviceAccountKey.json` file
- Copy **entire content** (all the JSON)
- Paste as value
- Should look like: `{"type":"service_account","project_id":"...",...}`

---

### E. Deploy!

1. **Click**: "Create Background Worker"
2. **Wait**: 2-3 minutes
3. **Watch logs** in the "Logs" tab

You should see:
```
🤖 Bot starting...
✅ Settings loaded
✅ Initial sync complete
✅ Bot startup complete!
```

🎉 **YOUR BOT IS NOW LIVE 24/7!**

---

## ✅ Verify It's Working

1. **Open Telegram**
2. **Find your bot**: @scoresharebot
3. **Send**: `/start`
4. **Should respond** in 1-6 seconds

If it works - **CONGRATULATIONS!** 🎉

---

## 🔄 Making Updates Later

When you change your code:

```bash
# 1. Save your changes
git add .
git commit -m "Updated feature XYZ"

# 2. Push to GitHub
git push

# 3. Render auto-deploys!
```

Render automatically detects changes and redeploys your bot!

---

## 📊 Summary: What You Did

1. ✅ Created GitHub account
2. ✅ Installed Git
3. ✅ Uploaded code to GitHub
4. ✅ Connected GitHub to Render
5. ✅ Deployed bot (FREE 24/7!)

**Result**: Your bot runs forever, automatically restarts if crashes, costs $0!

---

## 🆘 Troubleshooting

### "git not recognized"
- Restart Command Prompt after installing Git
- Or add Git to PATH manually

### "Permission denied" when pushing
- Use Personal Access Token, not password
- Make sure token has `repo` permission

### "Build failed" on Render
- Check logs for specific error
- Usually missing environment variable

### Bot not responding
- Check Render logs for errors
- Verify BOT_TOKEN is correct
- Check FIREBASE_CREDENTIALS is valid JSON

---

## 🎯 Next Steps

You now know GitHub basics! You can:
- ✅ Deploy to Render (free)
- ✅ Deploy to Railway
- ✅ Deploy to Heroku
- ✅ Share code with others
- ✅ Track all your changes

---

## 🤔 Ready to Try?

Let me know when you're ready and I'll guide you through each step!

**Say:** 
- "Start Step 1" - Create GitHub account
- "Start Step 2" - Install Git  
- "Start Step 3" - Upload code
- "Start Step 4" - Deploy to Render
- "I'm stuck on..." - I'll help you

What would you like to do first? 🚀

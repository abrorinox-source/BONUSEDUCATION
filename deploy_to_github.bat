@echo off
echo ============================================
echo   Git Setup and GitHub Upload Helper
echo ============================================
echo.

REM Check if Git is configured
echo [Step 1] Checking Git configuration...
git config --global user.name >nul 2>&1
if errorlevel 1 (
    echo.
    echo Git is not configured yet. Let's set it up!
    echo.
    set /p USERNAME="Enter your name: "
    set /p EMAIL="Enter your email: "
    git config --global user.name "!USERNAME!"
    git config --global user.email "!EMAIL!"
    echo.
    echo ✓ Git configured!
) else (
    echo ✓ Git already configured
)
echo.

REM Initialize Git repository
echo [Step 2] Initializing Git repository...
git init
if errorlevel 1 (
    echo × Error initializing Git
    pause
    exit /b 1
)
echo ✓ Git initialized
echo.

REM Add all files
echo [Step 3] Adding files to Git...
git add .
if errorlevel 1 (
    echo × Error adding files
    pause
    exit /b 1
)
echo ✓ Files added (warnings about CRLF are normal and safe to ignore)
echo.

REM Commit
echo [Step 4] Creating commit...
git commit -m "Initial commit - Telegram Points Bot"
if errorlevel 1 (
    echo × Error committing
    pause
    exit /b 1
)
echo ✓ Commit created
echo.

REM Instructions for GitHub
echo ============================================
echo   NEXT STEPS - Create GitHub Repository
echo ============================================
echo.
echo 1. Go to: https://github.com/new
echo 2. Repository name: telegram-points-bot
echo 3. Choose: Private
echo 4. DON'T check "Initialize with README"
echo 5. Click "Create repository"
echo.
echo After creating the repository, GitHub will show you commands.
echo Copy the HTTPS URL that looks like:
echo   https://github.com/YOUR-USERNAME/telegram-points-bot.git
echo.
set /p REPO_URL="Paste your repository URL here: "
echo.

REM Add remote
echo [Step 5] Connecting to GitHub...
git remote add origin %REPO_URL%
git branch -M main
echo ✓ Connected to GitHub
echo.

REM Push
echo [Step 6] Uploading to GitHub...
echo.
echo You'll be asked for credentials:
echo - Username: Your GitHub username
echo - Password: Use your Personal Access Token (NOT your password!)
echo.
echo If you don't have a token, get one here:
echo https://github.com/settings/tokens
echo Click "Generate new token (classic)" and select "repo" scope
echo.
pause
echo.
echo Uploading...
git push -u origin main
if errorlevel 1 (
    echo.
    echo × Error pushing to GitHub
    echo.
    echo Common issues:
    echo - Make sure you used Personal Access Token (not password)
    echo - Check the repository URL is correct
    echo - Make sure you have internet connection
    echo.
    pause
    exit /b 1
)
echo.
echo ============================================
echo   ✓ SUCCESS! Code uploaded to GitHub!
echo ============================================
echo.
echo Your code is now at: %REPO_URL%
echo.
echo NEXT STEP: Deploy to Render
echo 1. Go to: https://render.com
echo 2. Sign up with GitHub
echo 3. Create "Background Worker"
echo 4. Connect your repository
echo 5. Follow the instructions in RENDER_QUICK_START.md
echo.
pause

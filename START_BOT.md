# 🚀 Botni Ishga Tushirish - To'liq Qo'llanma

## 📋 QADAM 1: Python O'rnatilganligini Tekshirish

### Windows'da:
```bash
python --version
```

Yoki:
```bash
python3 --version
```

**Natija ko'rinishi:**
```
Python 3.11.0 (yoki undan yuqori)
```

❌ **Agar Python yo'q bo'lsa:**
1. [Python.org](https://www.python.org/downloads/) dan yuklab oling
2. O'rnatishda **"Add Python to PATH"** ni belgilang!
3. O'rnatib bo'lgandan keyin terminalni yoping va qayta oching

---

## 📋 QADAM 2: Virtual Environment Yaratish

### Windows'da:

#### Variant 1: PowerShell (Tavsiya etiladi)
```powershell
# Bot papkasiga o'ting
cd C:\path\to\telegram-points-bot

# Virtual environment yaratish
python -m venv venv

# Aktivlashtirish
.\venv\Scripts\Activate.ps1
```

❌ **Agar "execution policy" xatosi bo'lsa:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Keyin qayta aktivlashtiring:
```powershell
.\venv\Scripts\Activate.ps1
```

#### Variant 2: CMD (Command Prompt)
```cmd
# Bot papkasiga o'ting
cd C:\path\to\telegram-points-bot

# Virtual environment yaratish
python -m venv venv

# Aktivlashtirish
venv\Scripts\activate.bat
```

### Linux/Mac'da:
```bash
# Bot papkasiga o'ting
cd /path/to/telegram-points-bot

# Virtual environment yaratish
python3 -m venv venv

# Aktivlashtirish
source venv/bin/activate
```

---

## 📋 QADAM 3: Virtual Environment Aktivligini Tekshirish

Aktivlashgandan keyin terminalda quyidagicha ko'rinadi:

**Windows:**
```
(venv) PS C:\path\to\telegram-points-bot>
```

**Linux/Mac:**
```
(venv) user@computer:~/telegram-points-bot$
```

✅ **`(venv)` prefiksi ko'rinsa - muvaffaqiyatli aktivlashgan!**

---

## 📋 QADAM 4: Dependencies O'rnatish

Virtual environment ichida:

```bash
pip install -r requirements.txt
```

**O'rnatilishi kerak bo'lgan paketlar:**
- aiogram==3.4.1
- firebase-admin==6.4.0
- google-api-python-client==2.108.0
- openpyxl==3.1.2
- reportlab==4.0.8
- va boshqalar...

⏱️ **Bu 2-3 daqiqa davom etadi. Kutib turing...**

✅ **Muvaffaqiyatli o'rnatildi:** Xatosiz tugallansa tayyor!

---

## 📋 QADAM 5: Firebase Service Account Key Olish

### 5.1 Firebase Console'ga kirish
1. [Firebase Console](https://console.firebase.google.com/) ga kiring
2. Projectingizni tanlang (yoki yangi yarating)

### 5.2 Service Account Key yuklab olish
1. Chap menyudan **⚙️ Settings** → **Project Settings**
2. **Service Accounts** tabiga o'ting
3. **Generate New Private Key** tugmasini bosing
4. **Generate Key** ni tasdiqlang
5. JSON fayl yuklab olinadi (masalan: `my-project-123456.json`)

### 5.3 Faylni joylashtirish
1. Yuklab olingan JSON faylni **`serviceAccountKey.json`** deb nomini o'zgartiring
2. Bot papkasiga (project root'ga) ko'chiring:
   ```
   telegram-points-bot/
   ├── main.py
   ├── config.py
   ├── serviceAccountKey.json  ← SHU YERGA!
   └── ...
   ```

---

## 📋 QADAM 6: Google Sheets Sozlash

### 6.1 Yangi Sheet yaratish
1. [Google Sheets](https://sheets.google.com) ga kiring
2. **+ Blank** bosing (yangi sheet)
3. Nomini o'zgartiring: "Students Database"

### 6.2 Header qo'shish
Birinchi qatorda (row 1) quyidagilarni kiriting:

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| User_ID | Full_Name | Phone | Username | Points | Last_Updated |

### 6.3 Sheet ID olish
Sheet URL'dan Sheet ID ni ko'chiring:
```
https://docs.google.com/spreadsheets/d/SHEET_ID_BU_YERDA/edit
                                         ^^^^^^^^^^^^^^^^^^^
```

### 6.4 Service Account bilan share qilish
1. `serviceAccountKey.json` faylini oching
2. `client_email` ni toping (masalan: `firebase-adminsdk-xyz@project.iam.gserviceaccount.com`)
3. Google Sheets'da **Share** tugmasini bosing
4. Bu emailni qo'shing
5. **Editor** huquqini bering
6. **Send** bosing

---

## 📋 QADAM 7: Config.py Tekshirish

`config.py` faylini oching va tekshiring:

```python
BOT_TOKEN = "8332724613:AAGcV0-zFYgx4wnAib76qV5sO6hmac9_-1E"
FIREBASE_KEY_PATH = 'serviceAccountKey.json'  # ✅ To'g'ri nommi?
SHEET_ID = "1SsUnFwqDc1bj46LwHb0OtwPZkCyU3Ip4A96xSjWZzRo"  # ✅ O'zgartiringmi?
TEACHER_CODE = '11991188'  # ✅ Xohlagan kodingizni kiriting
```

**O'zgartirishlar:**
- `SHEET_ID` - O'zingizning Sheet ID'ngizni kiriting
- `TEACHER_CODE` - Xohlaganingizga o'zgartiring (masalan: `'12345678'`)

---

## 📋 QADAM 8: Botni Ishga Tushirish! 🚀

Virtual environment ichida (venv faol):

```bash
python main.py
```

**✅ Muvaffaqiyatli ishga tushsa ko'rinishi:**
```
==================================================
🚀 TELEGRAM BOT - POINTS MANAGEMENT SYSTEM
==================================================
Bot Token: 8332724613:AAGcV0-z...
Sheet ID: 1SsUnFwqDc1bj46LwHb0...
Silent Start: False
==================================================
🤖 Bot starting...
✅ Settings loaded: {...}
🔄 Performing initial sync...
✅ Initial sync complete
✅ Background sync task started
✅ Bot startup complete!
```

🎉 **Bot ishga tushdi!**

---

## 📋 QADAM 9: Botni Test Qilish

### Telegram'da test:

1. **Telegram'da botingizni toping**
   - Bot username: @your_bot_username
   - Yoki Bot Token'dan URL: `t.me/your_bot_username`

2. **O'qituvchi sifatida test:**
   ```
   /start
   → Ismingizni kiriting: "John Teacher"
   → Teacher code: 11991188
   → ✅ Teacher panel ochiladi!
   ```

3. **Student sifatida test (boshqa akkaunt):**
   ```
   /start
   → Ismingizni kiriting: "Jane Student"
   → "Skip" bosing
   → Kontaktni ulashing
   → O'qituvchi tasdiqini kuting
   ```

---

## 🛑 Botni To'xtatish

Terminal'da:
- **Windows/Linux/Mac:** `Ctrl + C`

Virtual environment'dan chiqish:
```bash
deactivate
```

---

## 🔄 Keyingi safar ishga tushirish

```bash
# 1. Bot papkasiga o'ting
cd C:\path\to\telegram-points-bot

# 2. Virtual environment aktivlashtirish
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# Linux/Mac:
source venv/bin/activate

# 3. Botni ishga tushirish
python main.py
```

---

## ❌ MUAMMOLAR VA YECHIMLAR

### ❌ "ModuleNotFoundError: No module named 'aiogram'"
**Yechim:**
```bash
# Virtual environment aktivmi?
# (venv) ko'rinishini tekshiring

# Agar yo'q bo'lsa aktivlashtiring va qayta o'rnating:
pip install -r requirements.txt
```

### ❌ "FileNotFoundError: serviceAccountKey.json"
**Yechim:**
- Fayl project root'da borligini tekshiring
- Nom to'g'ri yozilganini tekshiring (case-sensitive!)

### ❌ "google.auth.exceptions.RefreshError"
**Yechim:**
- `serviceAccountKey.json` to'g'ri fayl ekanini tekshiring
- Firebase'da Firestore yoqilganini tekshiring

### ❌ "HttpError 403: Permission denied" (Google Sheets)
**Yechim:**
- Google Sheet service account email bilan share qilinganini tekshiring
- Editor huquqi berilganini tasdiqlang

### ❌ "This bot doesn't exist" (Telegram)
**Yechim:**
- `config.py` da BOT_TOKEN to'g'ri ekanini tekshiring
- @BotFather'da bot yaratilganini tasdiqlang

### ❌ Virtual environment aktivlashmaydi (Windows)
**Yechim:**
```powershell
# PowerShell'da execution policy o'zgartirish:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Yoki CMD ishlatish:
venv\Scripts\activate.bat
```

---

## 📊 PRODUCTION DEPLOYMENT (Optional)

### PM2 bilan (Node.js kerak):
```bash
npm install -g pm2
pm2 start main.py --interpreter python --name telegram-bot
pm2 logs telegram-bot
pm2 save
pm2 startup
```

### Systemd bilan (Linux):
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

```ini
[Unit]
Description=Telegram Points Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
ExecStart=/path/to/bot/venv/bin/python /path/to/bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

---

## 🎓 QISQACHA XULOSA

```bash
# 1. Virtual environment yaratish
python -m venv venv

# 2. Aktivlashtirish
.\venv\Scripts\Activate.ps1  # Windows PowerShell
venv\Scripts\activate.bat    # Windows CMD
source venv/bin/activate     # Linux/Mac

# 3. Dependencies o'rnatish
pip install -r requirements.txt

# 4. Credentials sozlash
# - serviceAccountKey.json yuklab oling
# - Google Sheets yarating va share qiling
# - config.py tekshiring

# 5. Botni ishga tushirish
python main.py
```

---

## ✅ TAYYOR!

Botingiz ishga tushdi va foydalanishga tayyor! 🎉

Savollar bo'lsa yoki muammo bo'lsa, INSTALLATION.md va README.md fayllariga qarang.

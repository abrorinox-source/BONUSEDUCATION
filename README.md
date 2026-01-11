# 🤖 Telegram Bot - Points Management System

Advanced points management system for teachers and students with Firebase Firestore and Google Sheets synchronization.

## 📋 Features

### 🔥 Core Features
- ✅ **User Registration** - Automatic approval workflow for students
- ✅ **Points Management** - Add/subtract points with atomic transactions
- ✅ **Points Transfer** - Student-to-student transfers with commission
- ✅ **Real-time Ranking** - Live leaderboard with automatic updates
- ✅ **Transaction Logging** - Complete history of all operations
- ✅ **Google Sheets Sync** - Bidirectional synchronization

### 🛡️ Security & Reliability
- ✅ **Atomic Transactions** - No data loss, guaranteed consistency
- ✅ **Delta Sync Algorithm** - Conflict resolution for concurrent operations
- ✅ **Crash Recovery** - Pending sync queue survives bot restarts
- ✅ **Middleware Security** - Role-based access control
- ✅ **Maintenance Mode** - Graceful system updates

### 📊 Advanced Features
- ✅ **5 Export Formats** - CSV, Excel, JSON, PDF, Google Sheets Link
- ✅ **Data Comparison Tool** - Find discrepancies between Firebase and Sheets
- ✅ **Sync Control Panel** - Enable/pause/disable auto-sync
- ✅ **Transaction History** - Filterable logs for teachers and students
- ✅ **Personal History** - Students can view their transaction timeline

## 🚀 Installation

### Prerequisites
- Python 3.11+
- Firebase project with Firestore enabled
- Google Cloud project with Sheets API enabled
- Telegram Bot Token (from @BotFather)

### Step 1: Clone Repository
\`\`\`bash
git clone <repository-url>
cd telegram-points-bot
\`\`\`

### Step 2: Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### Step 3: Configure Credentials

#### Firebase Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing
3. Enable Firestore Database
4. Go to Project Settings → Service Accounts
5. Generate new private key
6. Save as \`serviceAccountKey.json\` in project root

#### Google Sheets Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Sheets API
3. Use the same service account key (serviceAccountKey.json)
4. Create a new Google Sheet
5. Share the sheet with the service account email (found in serviceAccountKey.json)
6. Copy the Sheet ID from URL

#### Telegram Bot Setup
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create new bot with `/newbot`
3. Copy the bot token

### Step 4: Update Configuration
Edit \`config.py\`:
\`\`\`python
BOT_TOKEN = "your_bot_token_here"
FIREBASE_KEY_PATH = 'serviceAccountKey.json'
SHEET_ID = "your_google_sheet_id"
TEACHER_CODE = '11991188'  # Change this!
\`\`\`

### Step 5: Prepare Google Sheets
Add header row to your Google Sheet (Sheet1, row 1):
\`\`\`
User_ID | Full_Name | Phone | Username | Points | Last_Updated
\`\`\`

### Step 6: Run Bot
\`\`\`bash
python main.py
\`\`\`

## 📖 Usage

### For Teachers

1. **Start Bot**: Send `/start`
2. **Enter Teacher Code**: Use code from config.py (default: 11991188)
3. **Access Teacher Panel**:
   - 🔄 **Force Sync** - Manual sync with Google Sheets
   - 📊 **Rating** - View overall ranking
   - 👤 **Students** - Manage students (add/remove points, delete)
   - ⚙️ **Settings** - Bot configuration

### For Students

1. **Start Bot**: Send `/start`
2. **Register**: Enter name and share contact
3. **Wait for Approval**: Teacher will approve or reject
4. **Access Student Panel**:
   - 🏆 **My Rank** - View personal statistics
   - 💸 **Transfer** - Send points to other students (10% commission)
   - 📊 **Rating** - View overall ranking
   - 📜 **History** - View transaction history
   - 📖 **Rules** - Read system rules
   - 🆘 **Support** - Contact teacher

### Settings Menu (Teacher Only)

- **💰 Transfer Commission** - Change commission rate (0-50%)
- **🔓 Bot Status** - Public/Private/Maintenance mode
- **🔄 Sync Control** - Enable/pause/disable auto-sync
- **📜 Transaction History** - View all logs with filters
- **🔍 Compare Data** - Find discrepancies between Firebase and Sheets
- **📥 Export Data** - Export in 5 formats (CSV, Excel, JSON, PDF, Sheets)
- **📝 Edit Rules** - Update bot rules text
- **📢 Global Broadcast** - Send message to all students

## 🏗️ Architecture

### Project Structure
\`\`\`
telegram-points-bot/
├── main.py                 # Bot entry point
├── config.py               # Configuration & credentials
├── database.py             # Firebase Firestore manager
├── sheets_manager.py       # Google Sheets manager & sync
├── keyboards.py            # All keyboard layouts
├── states.py               # FSM states
├── middleware.py           # Security middleware
├── handlers/
│   ├── __init__.py
│   ├── registration.py     # Registration flow
│   ├── teacher.py          # Teacher handlers
│   └── student.py          # Student handlers
├── requirements.txt        # Dependencies
├── serviceAccountKey.json  # Firebase credentials (not in repo)
└── README.md               # This file
\`\`\`

### Data Flow

\`\`\`
┌─────────────┐
│  Telegram   │
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Aiogram   │  ← Middleware (Security, FSM)
│  Handlers   │
└──────┬──────┘
       │
       ├─────────────────────┬─────────────────────┐
       ▼                     ▼                     ▼
┌─────────────┐      ┌──────────────┐     ┌─────────────┐
│  Firebase   │ ←──→ │ Sync Manager │ ←──→ │   Google    │
│  Firestore  │      │ (Delta Sync) │     │   Sheets    │
└─────────────┘      └──────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│ Transaction │
│    Logs     │
└─────────────┘
\`\`\`

## 🔒 Security Features

### Atomic Transactions
All point operations use Firebase transactions to ensure data consistency:
- Transfer operations are all-or-nothing
- No points can be lost or duplicated
- Automatic rollback on errors

### Delta Sync Algorithm
Resolves conflicts when teacher and student modify points simultaneously:
\`\`\`python
sheets_delta = sheets_points - last_synced_points
new_points = firebase_points + sheets_delta
\`\`\`

### Middleware Protection
Every request passes through security checks:
1. User exists in database?
2. User not deleted?
3. User approved (if student)?
4. Maintenance mode check (except teacher)

## 📊 Export Formats

| Format | Size  | Use Case |
|--------|-------|----------|
| CSV    | ~2KB  | Excel import, universal compatibility |
| Excel  | ~10KB | Professional reports with multiple sheets |
| JSON   | ~5KB  | Backups, API integration, developer-friendly |
| PDF    | ~50KB | Printable reports, presentations |
| Sheets | N/A   | Online sharing, real-time collaboration |

## 🔄 Synchronization

### Auto-Sync (Background Task)
- Runs every 10 seconds (configurable: 5s to 15min)
- Uses Delta Sync Algorithm
- Logs all manual edits from Sheets
- Can be paused or disabled via Settings

### Force Sync
- Manual trigger from teacher menu
- Bypasses interval timer
- Shows detailed sync statistics

### Sync Control
- **Enabled**: Auto-sync active
- **Paused**: Temporarily stopped
- **Disabled**: Completely off (manual sync only)

## 🐛 Troubleshooting

### Bot doesn't start
- Check BOT_TOKEN is correct
- Verify serviceAccountKey.json exists
- Ensure Python 3.11+ is installed

### Sync not working
- Check Google Sheets is shared with service account email
- Verify SHEET_ID is correct
- Check sync is enabled in Settings

### Student can't transfer
- Check student balance (must include commission)
- Verify recipient is active
- Check bot status (not in maintenance mode)

### Data mismatch between Firebase and Sheets
- Use **Compare Data** tool in Settings
- Run **Force Sync** to reconcile
- Check transaction logs for manual edits

## 📝 Configuration Options

### config.py
\`\`\`python
# Bot Settings
DEFAULT_COMMISSION_RATE = 0.10  # 10%
DEFAULT_SYNC_INTERVAL = 10      # seconds
SILENT_START = False            # Set True to skip startup notifications

# Limits
RANKING_PAGE_SIZE = 10
TRANSACTION_LOG_LIMIT = 20
STUDENT_HISTORY_LIMIT = 15
\`\`\`

## 🎯 Production Deployment

### Recommended Setup
1. Use environment variables for credentials
2. Enable logging to file
3. Set up monitoring (uptime, errors)
4. Configure backup strategy
5. Use longer sync intervals (30-60s) to reduce API calls

### Environment Variables (Optional)
\`\`\`bash
export BOT_TOKEN="your_token"
export SHEET_ID="your_sheet_id"
export TEACHER_CODE="your_code"
\`\`\`

## 📄 License

This project is provided as-is for educational purposes.

## 🆘 Support

For issues or questions:
1. Check the documentation in \`Bot haqida 2.txt\`
2. Review \`Data Consistency Analysis.txt\` for technical details
3. See \`Advanced Features.txt\` for extended functionality

## 🎉 Credits

Developed based on comprehensive requirements documentation:
- Bot haqida 2.txt (1500+ lines)
- Data Consistency Analysis.txt (400+ lines)
- Advanced Features.txt (800+ lines)

Total documentation: ~2,800 lines of professional specifications!

"""
Configuration file for Telegram Bot
Contains all credentials and settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CREDENTIALS (from environment variables)
# ═══════════════════════════════════════════════════════════════════════════════

BOT_TOKEN = os.getenv('BOT_TOKEN', "8466410998:AAFUo6iKrDN8YUTzYUkieJ_eQ76cnC5_Jps")
FIREBASE_KEY_PATH = os.getenv('FIREBASE_KEY_PATH', 'serviceAccountKey.json')
SHEET_ID = os.getenv('SHEET_ID', "1SsUnFwqDc1bj46LwHb0OtwPZkCyU3Ip4A96xSjWZzRo")
TEACHER_CODE = os.getenv('TEACHER_CODE', '11991188')

# ═══════════════════════════════════════════════════════════════════════════════
# BOT SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

# Default commission rate (10%)
DEFAULT_COMMISSION_RATE = 0.10

# Sync settings
DEFAULT_SYNC_INTERVAL = 10  # 10 seconds - for real-time sync
MIN_SYNC_INTERVAL = 5  # 5 seconds minimum
MAX_SYNC_INTERVAL = 3600  # 1 hour maximum

# Google Sheets column mapping
SHEET_COLUMNS = {
    'USER_ID': 0,
    'FULL_NAME': 1,
    'PHONE': 2,
    'USERNAME': 3,
    'POINTS': 4,
    'LAST_UPDATED': 5
}

# Pagination
RANKING_PAGE_SIZE = 10
TRANSACTION_LOG_LIMIT = 20
STUDENT_HISTORY_LIMIT = 15

# Bot modes
SILENT_START = False  # Set to True to start without notifications

# Webhook settings (for production deployment)
USE_WEBHOOK = os.getenv('USE_WEBHOOK', 'True').lower() == 'true'
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', "/webhook")
WEBAPP_HOST = "0.0.0.0"  # Listen on all interfaces
WEBAPP_PORT = int(os.getenv('PORT', '10000'))  # Render uses port 10000 by default

# Auto-detect webhook URL from Render environment
# RENDER_EXTERNAL_URL is automatically set by Render
WEBHOOK_HOST = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('WEBHOOK_HOST', "")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else ""

# ═══════════════════════════════════════════════════════════════════════════════
# GOOGLE SHEETS API SCOPES
# ═══════════════════════════════════════════════════════════════════════════════

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# ═══════════════════════════════════════════════════════════════════════════════
# FIREBASE COLLECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

COLLECTIONS = {
    'USERS': 'users',
    'SETTINGS': 'settings',
    'TRANSACTION_LOGS': 'transaction_logs',
    'GROUPS': 'groups'
}

# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

MESSAGES = {
    'welcome_teacher': """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍🏫 TEACHER PANEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Welcome back, {name}!

Active Students: {active_students}
Pending Approvals: {pending_approvals}
Total Points Distributed: {total_points:,}

Use the buttons below to manage.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""",

    'welcome_student': """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👋 Welcome back, {name}!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your Points: {points}
Your Rank: #{rank}

Use buttons to check ranking,
transfer points, or view rules.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""",

    'registration_pending': """⏳ Your registration is pending teacher approval.
Please wait for confirmation.""",

    'registration_approved': """🎉 Your registration has been approved!
You can now use the bot.

Use the buttons below to get started.""",

    'registration_rejected': """❌ Your registration was rejected.
Contact support if you think this is a mistake.""",

    'user_deleted': """⚠️ You have been removed from the system.
Send /start to register again.""",

    'account_restored': """✅ Your account has been restored!
You can continue using the bot.""",

    'maintenance_mode': """⚠️ Bot is under maintenance.
Please try again later.""",

    'insufficient_balance': """❌ Insufficient balance!
Required: {required} pts
Available: {available} pts""",

    'transfer_confirmation': """⚠️ TRANSFER CONFIRMATION
━━━━━━━━━━━━━━━━━━━━━━
To: {recipient_name}
Amount: {amount} pts
Commission ({commission_rate}%): {commission} pts
──────────────────
Total Cost: {total} pts
Your Balance: {current_balance} pts
After Transfer: {after_balance} pts

Confirm transfer?""",

    'transfer_success_sender': """✅ Transfer successful!
Sent {amount} pts to {recipient_name}.
Commission: {commission} pts
New balance: {new_balance} pts""",

    'transfer_success_recipient': """💰 You received {amount} pts from {sender_name}!
New balance: {new_balance} pts""",
}

# ═══════════════════════════════════════════════════════════════════════════════
# BUTTON EMOJIS
# ═══════════════════════════════════════════════════════════════════════════════

EMOJIS = {
    'force_sync': '🔄',
    'rating': '📊',
    'students': '👤',
    'settings': '⚙️',
    'my_rank': '🏆',
    'transfer': '💸',
    'history': '📜',
    'rules': '📖',
    'support': '🆘',
    'approve': '✅',
    'reject': '❌',
    'cancel': '❌',
    'confirm': '✅',
    'back': '«',
    'add': '➕',
    'subtract': '➖',
    'delete': '🗑️',
}

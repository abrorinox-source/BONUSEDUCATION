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

BOT_TOKEN = os.getenv('BOT_TOKEN', "")
FIREBASE_KEY_PATH = os.getenv('FIREBASE_KEY_PATH', 'serviceAccountKey.json')
SHEET_ID = os.getenv('SHEET_ID', "")
TEACHER_CODE = os.getenv('TEACHER_CODE', '')

# ═══════════════════════════════════════════════════════════════════════════════
# BOT SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

# Default commission rate (10%)
DEFAULT_COMMISSION_RATE = 0.10

# Sync settings
DEFAULT_SYNC_INTERVAL = 30  # 30 seconds - balanced cache refresh
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
    'GROUPS': 'groups',
    'TRANSFER_LIMIT_USAGE': 'transfer_limit_usage',
    'TRANSFER_LIMIT_OVERRIDES': 'transfer_limit_overrides'
}

# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

MESSAGES = {
    'welcome_teacher': """????? <b>Teacher Panel</b>

Welcome back, <b>{name}</b>.

<b>Active Students:</b> {active_students}
<b>Pending Approvals:</b> {pending_approvals}
<b>Total Points Distributed:</b> {total_points:,}

<i>Use the buttons below to manage groups, students, and settings.</i>""",

    'welcome_student': """<b>Welcome back, {name}!</b>

<b>Your Points:</b> {points}
<b>Your Rank:</b> #{rank}

<i>Use the buttons below to view ranking, transfer points, or read the rules.</i>""",

    'registration_pending': """<b>Registration Pending</b>

Your account is waiting for teacher approval.
<i>After approval, you will choose your group.</i>""",

    'registration_approved': """<b>Registration Approved</b>

You can now use the bot.
<i>Use the menu below to get started.</i>""",

    'registration_rejected': """<b>Registration Rejected</b>

Contact support if you think this is a mistake.""",

    'user_deleted': """<b>Account Removed</b>

You have been removed from the system.
Send <code>/start</code> to register again.""",

    'account_restored': """<b>Account Restored</b>

You can continue using the bot.""",

    'maintenance_mode': """<b>Maintenance Mode</b>

The bot is temporarily unavailable.
Please try again later.""",

    'insufficient_balance': """<b>Insufficient Balance</b>

Required: <b>{required}</b> pts
Available: <b>{available}</b> pts""",

    'transfer_confirmation': """<b>Transfer Confirmation</b>

<b>To:</b> {recipient_name}
<b>Amount:</b> {amount} pts
<b>Commission ({commission_rate}%):</b> {commission} pts

<b>Total Cost:</b> {total} pts
<b>Your Balance:</b> {current_balance} pts
<b>After Transfer:</b> {after_balance} pts

<i>Please confirm this transfer.</i>""",

    'transfer_success_sender': """<b>Transfer Successful</b>

Sent <b>{amount}</b> pts to <b>{recipient_name}</b>
Commission: <b>{commission}</b> pts
New Balance: <b>{new_balance}</b> pts""",

    'transfer_success_recipient': """<b>You Received Points</b>

<b>{amount}</b> pts arrived from <b>{sender_name}</b>.
New Balance: <b>{new_balance}</b> pts""",
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

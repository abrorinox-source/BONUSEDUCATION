"""
Keyboards for the bot
Reply and Inline keyboards
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict, Any
import config


# ═══════════════════════════════════════════════════════════════════════════════
# REPLY KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════════

def get_teacher_keyboard() -> ReplyKeyboardMarkup:
    """Teacher main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text=f"{config.EMOJIS['force_sync']} Force Sync")
    builder.button(text=f"{config.EMOJIS['rating']} Rating")
    builder.button(text=f"{config.EMOJIS['students']} Students")
    builder.button(text=f"{config.EMOJIS['settings']} Settings")
    
    builder.adjust(2, 2)
    
    return builder.as_markup(resize_keyboard=True)


def get_student_keyboard() -> ReplyKeyboardMarkup:
    """Student main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text=f"{config.EMOJIS['my_rank']} My Rank")
    builder.button(text=f"{config.EMOJIS['transfer']} Transfer")
    builder.button(text=f"{config.EMOJIS['rating']} Rating")
    builder.button(text=f"{config.EMOJIS['history']} History")
    builder.button(text=f"{config.EMOJIS['rules']} Rules")
    builder.button(text=f"{config.EMOJIS['support']} Support")
    
    builder.adjust(2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Request contact keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Share Contact", request_contact=True)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Skip button keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="Skip")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# ═══════════════════════════════════════════════════════════════════════════════
# INLINE KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════════

def get_approval_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Approval keyboard for teacher"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text=f"{config.EMOJIS['approve']} Approve", callback_data=f"approve:{user_id}")
    builder.button(text=f"{config.EMOJIS['reject']} Reject", callback_data=f"reject:{user_id}")
    
    builder.adjust(2)
    
    return builder.as_markup()


def get_restore_approval_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Restore approval keyboard for teacher"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text=f"{config.EMOJIS['approve']} Restore Account", callback_data=f"restore_approve:{user_id}")
    builder.button(text=f"{config.EMOJIS['reject']} Reject (Permanent Ban)", callback_data=f"restore_reject:{user_id}")
    
    builder.adjust(1, 1)
    
    return builder.as_markup()


def get_confirmation_keyboard(action: str, data: str = "") -> InlineKeyboardMarkup:
    """Generic confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text=f"{config.EMOJIS['confirm']} Confirm", callback_data=f"confirm:{action}:{data}")
    builder.button(text=f"{config.EMOJIS['cancel']} Cancel", callback_data=f"cancel:{action}")
    
    builder.adjust(2)
    
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💰 Transfer Commission", callback_data="settings:commission")
    builder.button(text="🔓 Bot Status", callback_data="settings:bot_status")
    builder.button(text="🔄 Sync Control", callback_data="settings:sync_control")
    builder.button(text="📜 Transaction History", callback_data="settings:transaction_history")
    builder.button(text="📥 Export Data", callback_data="settings:export")
    builder.button(text="📝 Edit Rules", callback_data="settings:edit_rules")
    builder.button(text="📢 Global Broadcast", callback_data="settings:broadcast")
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="settings:back")
    
    builder.adjust(2, 2, 2, 1, 1)
    
    return builder.as_markup()


def get_export_keyboard() -> InlineKeyboardMarkup:
    """Export data format selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📋 Excel (XLSX)", callback_data="export:excel")
    builder.button(text="📄 JSON", callback_data="export:json")
    builder.button(text="📈 PDF Report", callback_data="export:pdf")
    builder.button(text="🔗 Sheets Copy", callback_data="export:sheets_copy")
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="settings:back")
    
    builder.adjust(2, 2, 1)
    
    return builder.as_markup()


def get_sync_control_keyboard(sync_enabled: bool) -> InlineKeyboardMarkup:
    """Sync control keyboard"""
    builder = InlineKeyboardBuilder()
    
    # Single toggle button (Pause/Resume)
    toggle_text = "⏸️ Disable Sync" if sync_enabled else "▶️ Enable Sync"
    builder.button(text=toggle_text, callback_data="sync:toggle")
    
    builder.button(text="⏱️ Change Interval", callback_data="sync:interval")
    builder.button(text="📥 Force: Sheets → Firebase", callback_data="sync:force_sheets")
    
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="settings:back")
    
    builder.adjust(1, 2, 1)
    
    return builder.as_markup()


def get_sync_interval_keyboard() -> InlineKeyboardMarkup:
    """Sync interval selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="5 seconds", callback_data="sync:set_interval:5")
    builder.button(text="10 seconds", callback_data="sync:set_interval:10")
    builder.button(text="30 seconds", callback_data="sync:set_interval:30")
    builder.button(text="1 minute", callback_data="sync:set_interval:60")
    builder.button(text="5 minutes", callback_data="sync:set_interval:300")
    builder.button(text="15 minutes", callback_data="sync:set_interval:900")
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="sync:control")
    
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup()


def get_transaction_history_keyboard() -> InlineKeyboardMarkup:
    """Transaction history filter keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📤 All Transactions", callback_data="logs:all")
    builder.button(text="💸 Transfers", callback_data="logs:transfer")
    builder.button(text="➕ Added Points", callback_data="logs:add_points")
    builder.button(text="➖ Subtracted Points", callback_data="logs:subtract_points")
    builder.button(text="✏️ Manual Edits", callback_data="logs:manual_edit")
    builder.button(text="📊 Export Logs", callback_data="logs:export_menu")
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="settings:back")
    
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup()


def get_logs_export_keyboard() -> InlineKeyboardMarkup:
    """Transaction logs export format selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📋 Excel (XLSX)", callback_data="logs:export:excel")
    builder.button(text="📄 JSON", callback_data="logs:export:json")
    builder.button(text="📈 PDF Report", callback_data="logs:export:pdf")
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="settings:transaction_history")
    
    builder.adjust(2, 1, 1)
    
    return builder.as_markup()


def get_students_list_keyboard(students: List[Dict[str, Any]], action: str = "detail") -> InlineKeyboardMarkup:
    """Students list keyboard"""
    builder = InlineKeyboardBuilder()
    
    for student in students[:10]:  # Show first 10
        name = student.get('full_name', 'Unknown')
        points = student.get('points', 0)
        user_id = student.get('user_id', '')
        
        builder.button(
            text=f"👤 {name} ({points} pts)",
            callback_data=f"student_{action}:{user_id}"
        )
    
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="teacher:menu")
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_student_detail_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Student detail actions keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text=f"{config.EMOJIS['add']} Add Points", callback_data=f"add_points:{user_id}")
    builder.button(text=f"{config.EMOJIS['subtract']} Subtract Points", callback_data=f"subtract_points:{user_id}")
    builder.button(text=f"{config.EMOJIS['delete']} Delete Student", callback_data=f"delete_student:{user_id}")
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="students:list")
    
    builder.adjust(2, 1, 1)
    
    return builder.as_markup()


def get_transfer_recipients_keyboard(students: List[Dict[str, Any]], current_user_id: str) -> InlineKeyboardMarkup:
    """Transfer recipients selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    for student in students:
        if student.get('user_id') == current_user_id:
            continue  # Skip self
        
        name = student.get('full_name', 'Unknown')
        points = student.get('points', 0)
        user_id = student.get('user_id', '')
        
        builder.button(
            text=f"👤 {name} ({points} pts)",
            callback_data=f"transfer_to:{user_id}"
        )
    
    builder.button(text=f"{config.EMOJIS['cancel']} Cancel", callback_data="student:menu")
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_ranking_keyboard(user_role: str = "student") -> InlineKeyboardMarkup:
    """Ranking view keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔄 Refresh", callback_data="ranking:refresh")
    
    if user_role == "teacher":
        builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="teacher:menu")
    else:
        builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="student:menu")
    
    builder.adjust(2)
    
    return builder.as_markup()


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Simple back button keyboard"""
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def get_bot_status_keyboard(current_status: str) -> InlineKeyboardMarkup:
    """Bot status selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    statuses = [
        ("✅ Public (Normal)", "public"),
        ("🔧 Maintenance (Teachers Only)", "maintenance")
    ]
    
    for text, status in statuses:
        if status == current_status:
            text = f"{text} ← Current"
        builder.button(text=text, callback_data=f"bot_status:{status}")
    
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="settings:back")
    
    builder.adjust(1, 1, 1)
    
    return builder.as_markup()


def get_commission_keyboard() -> InlineKeyboardMarkup:
    """Commission rate selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    rates = [0, 5, 10, 15, 20, 25, 30, 50]
    
    for rate in rates:
        builder.button(text=f"{rate}%", callback_data=f"commission:set:{rate}")
    
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="settings:back")
    
    builder.adjust(4, 4, 1)
    
    return builder.as_markup()


def get_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Broadcast message keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="👥 All Active Users", callback_data="broadcast:all_active")
    builder.button(text="👨‍🎓 Students Only", callback_data="broadcast:students")
    builder.button(text="👨‍🏫 Teachers Only", callback_data="broadcast:teachers")
    builder.button(text=f"{config.EMOJIS['cancel']} Cancel", callback_data="settings:back")
    
    builder.adjust(1, 2, 1)
    
    return builder.as_markup()


def get_edit_rules_keyboard() -> InlineKeyboardMarkup:
    """Edit rules keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✏️ Edit Rules", callback_data="rules:edit")
    builder.button(text=f"{config.EMOJIS['back']} Back", callback_data="settings:back")
    
    builder.adjust(1, 1)
    
    return builder.as_markup()

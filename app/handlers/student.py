"""
Student handlers
All student-related functionality
"""

import asyncio
import math

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from app.database import db
from app.sheets_manager import sheets_manager
from app import keyboards
from app import states
from app import config

router = Router()
active_transfer_confirms = set()


async def safe_answer_callback(callback: CallbackQuery, text: str = None, show_alert: bool = False):
    """Ignore expired callback query errors."""
    try:
        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "query ID is invalid" in str(e):
            print(f"Callback query expired, ignoring: {callback.data}")
        else:
            raise


async def send_transfer_notifications(
    callback: CallbackQuery,
    recipient_id: str,
    recipient_name: str,
    sender_name: str,
    amount: int,
    commission: int,
    sender_balance: int,
    recipient_balance: int,
    sender_group: str,
    recipient_group: str,
):
    """Send recipient and teacher notifications outside the critical path."""
    try:
        await callback.bot.send_message(
            chat_id=recipient_id,
            text=config.MESSAGES['transfer_success_recipient'].format(
                amount=amount,
                sender_name=sender_name,
                new_balance=recipient_balance
            )
        )
    except Exception:
        pass

    teacher_ids = {
        str(teacher.get('user_id', '')).strip()
        for teacher in db.get_all_users(role='teacher', status='active')
        if str(teacher.get('user_id', '')).strip().isdigit()
    }
    teacher_notification = (
        f"TRANSFER NOTIFICATION\n"
        f"From: {sender_name}\n"
        f"To: {recipient_name}\n"
        f"Amount: {amount} pts\n"
        f"Commission: {commission} pts\n"
        f"Sender Balance: {sender_balance} pts\n"
        f"Recipient Balance: {recipient_balance} pts\n"
        f"From Group: {sender_group}\n"
        f"To Group: {recipient_group}"
    )
    for teacher_id in teacher_ids:
        try:
            await callback.bot.send_message(chat_id=teacher_id, text=teacher_notification)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.contains("My Rank"))
async def show_my_rank(message: Message, user: dict):
    """Show personal rank and stats within student's group"""
    user_id = str(message.from_user.id)
    user = db.get_user(user_id, force_refresh=True) or user
    group_id = user.get('group_id')

    if not group_id:
        await message.answer("❌ <b>No Group Assigned</b>\n\nYou are not assigned to any group yet.")
        return

    group = db.get_group(group_id)
    group_name = group.get('name', 'Unknown Group') if group else 'Unknown Group'
    ranking = db.get_ranking(group_id=group_id)
    rank = next((i + 1 for i, u in enumerate(ranking) if u['user_id'] == user_id), 0)

    text = (
        f"🏆 <b>Your Statistics</b>\n\n"
        f"👥 <b>Group:</b> {group_name}\n"
        f"👤 <b>Name:</b> {user['full_name']}\n"
        f"💎 <b>Points:</b> {user['points']} pts\n"
        f"📊 <b>Rank:</b> #{rank} of {len(ranking)} students"
    )

    await message.answer(text)


@router.message(F.text.contains("Transfer"))
async def start_transfer(message: Message, user: dict = None):
    """Show group selection for transfer"""
    teacher_id = '8017101114'  # TODO: make dynamic
    groups = db.get_teacher_groups(teacher_id)

    if not groups:
        await message.answer("❌ <b>No Groups Found</b>")
        return

    await message.answer(
        "💸 <b>Transfer Points</b>\n\nSelect a group to view available recipients:",
        reply_markup=keyboards.get_group_selection_keyboard(groups, "transfer")
    )


PAGE_SIZE_RANKING = 20


def build_ranking_text(ranking: list, user_id: str, group_name: str, page: int, page_size: int) -> str:
    """Build ranking text for a given page"""
    total = len(ranking)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = page * page_size
    end = start + page_size
    page_ranking = ranking[start:end]

    text = f"🏆 {group_name.upper()} RANKING\n"
    if total_pages > 1:
        text += f"Sahifa {page + 1}/{total_pages}\n"
    text += "\n"

    for i, student in enumerate(page_ranking, start + 1):
        emoji = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        if student['user_id'] == user_id:
            name = f"**{student['full_name']}**"
        else:
            name = student['full_name']
        text += f"{emoji} {name} - {student['points']} pts\n"

    text += f"\nJami o'quvchilar: {total}"
    return text


@router.message(F.text.contains("Rating"))
async def show_rating_student(message: Message, user: dict = None):
    """Show ranking for student's own group"""
    user_id = str(message.from_user.id)
    user = db.get_user(user_id, force_refresh=True) or user
    group_id = user.get('group_id') if user else None

    if not group_id:
        await message.answer("❌ <b>No Group Assigned</b>\n\nYou are not assigned to any group yet.")
        return

    group = db.get_group(group_id)
    group_name = group.get('name', 'Unknown Group') if group else 'Unknown Group'
    ranking = db.get_ranking(group_id=group_id)

    if not ranking:
        await message.answer(f"📉 <b>No Ranking Data</b>\n\nNo students found in <b>{group_name}</b>.")
        return

    page = 0
    total_pages = max(1, (len(ranking) + PAGE_SIZE_RANKING - 1) // PAGE_SIZE_RANKING)
    text = build_ranking_text(ranking, user_id, group_name, page, PAGE_SIZE_RANKING)

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=keyboards.get_ranking_keyboard("student", page, total_pages, group_id)
    )


@router.message(F.text.contains("History"))
async def show_history(message: Message):
    """Show transaction history"""
    user_id = str(message.from_user.id)
    logs = db.get_user_history(user_id, limit=config.STUDENT_HISTORY_LIMIT)

    if not logs:
        await message.answer("📜 <b>No Transaction History</b>\n\nNo records found yet.")
        return

    text = "📜 <b>Your Transaction History</b>\n\n"

    for log in logs:
        log_type = log.get('type')
        timestamp = log.get('timestamp', 'N/A')

        if log_type == 'transfer':
            if log.get('sender_id') == user_id:
                text += f"💸 Sent {log['amount']} pts to {log['recipient_name']}\n"
            else:
                text += f"💰 Received {log['amount']} pts from {log['sender_name']}\n"
        elif log_type == 'add_points':
            text += f"➕ Teacher added {log['amount']} pts\n"
        elif log_type == 'subtract_points':
            text += f"➖ Teacher removed {log['amount']} pts\n"

        text += f"   {timestamp}\n\n"

    await message.answer(text, reply_markup=keyboards.get_back_keyboard("student:menu"))


@router.message(F.text.contains("Rules"))
async def show_rules(message: Message):
    """Show bot rules"""
    settings = db.get_settings()
    rules_text = settings.get('rules_text', "No rules configured.")
    commission_rate = settings.get('commission_rate', config.DEFAULT_COMMISSION_RATE)

    text = (
        f"📘 <b>System Rules</b>\n\n"
        f"{rules_text}\n\n"
        f"💰 <b>Transfer Commission:</b> {int(commission_rate * 100)}%\n"
    )

    await message.answer(text)


@router.message(F.text.contains("Support"))
async def show_support(message: Message):
    """Show support contact"""
    teachers = db.get_all_users(role='teacher', status='active')

    if teachers:
        teacher = teachers[0]
        username = teacher.get('username', 'N/A')
        text = (
            f"🆘 <b>Support</b>\n\n"
            f"<b>Contact teacher:</b>\n@{username}\n\n"
            f"<i>They will assist you with any issues.</i>"
        )
    else:
        text = "🆘 <b>Support</b>\n\nNo support contact is available right now."

    await message.answer(text)


# TRANSFER FLOW
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("transfer:"))
async def select_transfer_group(callback: CallbackQuery):
    """Show students in selected group for transfer"""
    # Format: transfer:group:{group_id}
    parts = callback.data.split(":")
    group_id = parts[2] if len(parts) > 2 else parts[1]  # Handle both formats
    user_id = str(callback.from_user.id)
    
    print(f"💸 Transfer group selected: {group_id}")
    
    # Get students in this group
    students = db.get_all_users(role='student', status='active', group_id=group_id)
    
    # Remove self from list
    students = [s for s in students if s['user_id'] != user_id]
    
    if not students:
        await callback.answer("❌ No students found in this group", show_alert=True)
        return
    
    # Get group name
    group = db.get_group(group_id)
    group_name = group.get('name', group_id) if group else group_id
    
    await callback.message.edit_text(
        f"💸 TRANSFER POINTS\n\n"
        f"Group: {group_name}\n"
        f"Select recipient:",
        reply_markup=keyboards.get_transfer_recipients_keyboard(students, user_id, group_id=group_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("transfer_page:"))
async def transfer_page_handler(callback: CallbackQuery):
    """Handle transfer recipients pagination — Format: transfer_page:{group_id}:{page}"""
    parts = callback.data.split(":")
    group_id = parts[1]
    page = int(parts[2])
    user_id = str(callback.from_user.id)

    students = db.get_all_users(role='student', status='active', group_id=group_id)
    students = [s for s in students if s['user_id'] != user_id]

    group = db.get_group(group_id)
    group_name = group.get('name', group_id) if group else group_id

    if not students:
        await callback.answer("❌ No students found", show_alert=True)
        return

    await callback.message.edit_text(
        f"💸 TRANSFER POINTS\n\nGroup: {group_name}\nSelect recipient:",
        reply_markup=keyboards.get_transfer_recipients_keyboard(students, user_id, group_id=group_id, page=page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("transfer_to:"))
async def select_recipient(callback: CallbackQuery, state: FSMContext):
    """Recipient selected, ask for amount"""
    recipient_id = callback.data.split(":")[1]
    recipient = db.get_user(recipient_id)
    
    if not recipient:
        await callback.answer("❌ Recipient not found!", show_alert=True)
        return

    if recipient.get('is_manual') or not str(recipient.get('user_id', '')).strip().isdigit():
        await callback.answer(
            "Bu foydalanuvchining Telegram IDsi yo'q. Unga ball o'tkazib bo'lmaydi.",
            show_alert=True
        )
        return
    
    await state.update_data(recipient_id=recipient_id, recipient_name=recipient['full_name'])
    await state.set_state(states.TransferStates.waiting_for_amount)
    
    await callback.message.answer(
        f"💸 TRANSFER TO: {recipient['full_name']}\n\n"
        f"Enter amount to transfer (minimum 1 pt):"
    )
    await callback.answer()


@router.message(states.TransferStates.waiting_for_amount)
async def process_transfer_amount(message: Message, state: FSMContext, user: dict):
    """Process transfer amount"""
    try:
        amount = int(message.text.strip())
        
        if amount <= 0:
            await message.answer("❌ Amount must be positive. Try again:")
            return
        
        # Get commission rate
        commission_rate = db.get_commission_rate()
        commission = math.ceil(amount * commission_rate)
        total_cost = amount + commission

        limit_check = db.check_transfer_limits(str(message.from_user.id), amount)
        if not limit_check['allowed']:
            await message.answer(f"Transfer limit reached:\n{limit_check['error']}")
            await state.clear()
            return
        
        # Check balance
        if user['points'] < total_cost:
            await message.answer(
                config.MESSAGES['insufficient_balance'].format(
                    required=total_cost,
                    available=user['points']
                )
            )
            await state.clear()
            return
        
        # Get recipient data
        data = await state.get_data()
        recipient = db.get_user(data['recipient_id'])

        if not recipient or recipient.get('is_manual') or not str(recipient.get('user_id', '')).strip().isdigit():
            await message.answer("Bu foydalanuvchining Telegram IDsi yo'q. Unga ball o'tkazib bo'lmaydi.")
            await state.clear()
            return
        
        # Show confirmation
        text = config.MESSAGES['transfer_confirmation'].format(
            recipient_name=data['recipient_name'],
            amount=amount,
            commission_rate=int(commission_rate * 100),
            commission=commission,
            total=total_cost,
            current_balance=user['points'],
            after_balance=user['points'] - total_cost
        )
        text += (
            "\n\nCommission formula: ceil(amount x rate)\n"
            "The commission is always rounded up to the nearest whole point."
        )
        
        await state.update_data(amount=amount, commission=commission)
        
        await message.answer(
            text,
            reply_markup=keyboards.get_confirmation_keyboard(
                "transfer",
                f"{data['recipient_id']}:{amount}:{commission}"
            )
        )
    
    except ValueError:
        await message.answer("❌ Please enter a valid number:")


@router.callback_query(F.data.startswith("confirm:transfer:"))
async def confirm_transfer(callback: CallbackQuery, state: FSMContext, user: dict):
    """Execute transfer"""
    transfer_key = (str(callback.from_user.id), callback.data)
    if transfer_key in active_transfer_confirms:
        await safe_answer_callback(callback, "Transfer is already being processed.")
        return

    active_transfer_confirms.add(transfer_key)

    try:
        await safe_answer_callback(callback)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        parts = callback.data.split(":")
        recipient_id = parts[2]
        amount = int(parts[3])
        commission = int(parts[4])
        sender_id = str(callback.from_user.id)

        data = await state.get_data()

        result = db.transfer_points(sender_id, recipient_id, amount, commission)

        if result['success']:
            recipient = db.get_user(recipient_id)
            recipient_name = recipient['full_name'] if recipient else data.get('recipient_name', 'Unknown')
            recipient_group = recipient.get('group_id', 'N/A') if recipient else 'N/A'

            db.log_transfer(
                sender_id=sender_id,
                recipient_id=recipient_id,
                amount=amount,
                commission=commission,
                sender_name=user['full_name'],
                recipient_name=recipient_name,
                sender_old_balance=result['sender_balance'] + amount + commission,
                sender_new_balance=result['sender_balance'],
                recipient_old_balance=result['recipient_balance'] - amount,
                recipient_new_balance=result['recipient_balance']
            )

            await callback.message.edit_text(
                config.MESSAGES['transfer_success_sender'].format(
                    amount=amount,
                    recipient_name=data['recipient_name'],
                    commission=commission,
                    new_balance=result['sender_balance']
                )
            )

            asyncio.create_task(
                send_transfer_notifications(
                    callback=callback,
                    recipient_id=recipient_id,
                    recipient_name=recipient_name,
                    sender_name=user['full_name'],
                    amount=amount,
                    commission=commission,
                    sender_balance=result['sender_balance'],
                    recipient_balance=result['recipient_balance'],
                    sender_group=user.get('group_id', 'N/A'),
                    recipient_group=recipient_group,
                )
            )
        else:
            await callback.message.edit_text(f"Transfer failed: {result['error']}")

        await state.clear()
    finally:
        active_transfer_confirms.discard(transfer_key)


# ═══════════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "student:menu")
async def back_to_student_menu(callback: CallbackQuery):
    """Return to student menu"""
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "ranking:refresh")
async def refresh_ranking(callback: CallbackQuery, user: dict):
    """Refresh ranking for student's group only"""
    user_id = str(callback.from_user.id)
    student = db.get_user(user_id)
    group_id = student.get('group_id')
    
    if not group_id:
        await callback.answer("❌ You are not assigned to any group!", show_alert=True)
        return
    
    # Get group info
    group = db.get_group(group_id)
    group_name = group.get('name', 'Unknown Group') if group else 'Unknown Group'
    
    # Get ranking for student's group only
    ranking = db.get_ranking(group_id=group_id)
    
    page = 0
    total_pages = max(1, (len(ranking) + PAGE_SIZE_RANKING - 1) // PAGE_SIZE_RANKING)
    text = build_ranking_text(ranking, user_id, group_name, page, PAGE_SIZE_RANKING)
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboards.get_ranking_keyboard(user.get('role', 'student'), page, total_pages, group_id)
    )
    await callback.answer("✅ Ranking yangilandi!")


@router.callback_query(F.data.startswith("ranking_page:"))
async def ranking_page(callback: CallbackQuery, user: dict):
    """Handle ranking pagination for students"""
    # Format: ranking_page:{role}:{group_id}:{page}
    parts = callback.data.split(":")
    role = parts[1]
    group_id = parts[2]
    page = int(parts[3])
    user_id = str(callback.from_user.id)

    group = db.get_group(group_id)
    group_name = group.get('name', 'Unknown Group') if group else 'Unknown Group'

    ranking = db.get_ranking(group_id=group_id)
    total_pages = max(1, (len(ranking) + PAGE_SIZE_RANKING - 1) // PAGE_SIZE_RANKING)

    # Clamp page
    page = max(0, min(page, total_pages - 1))

    text = build_ranking_text(ranking, user_id, group_name, page, PAGE_SIZE_RANKING)

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboards.get_ranking_keyboard(role, page, total_pages, group_id)
    )
    await callback.answer()

"""
Student handlers
All student-related functionality
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import db
from sheets_manager import sheets_manager
import keyboards
import states
import config

router = Router()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.contains("My Rank"))
async def show_my_rank(message: Message, user: dict):
    """Show personal rank and stats within student's group"""
    user_id = str(message.from_user.id)
    group_id = user.get('group_id')
    
    if not group_id:
        await message.answer("❌ You are not assigned to any group yet.")
        return
    
    # Get group info
    group = db.get_group(group_id)
    group_name = group.get('name', 'Unknown Group') if group else 'Unknown Group'
    
    # Get ranking for student's group only
    ranking = db.get_ranking(group_id=group_id)
    rank = next((i + 1 for i, u in enumerate(ranking) if u['user_id'] == user_id), 0)
    
    text = (
        f"🏆 YOUR STATISTICS\n"
        f"Group: {group_name}\n"
        f"Name: **{user['full_name']}**\n"
        f"Points: {user['points']} pts\n"
        f"Rank: #{rank} of {len(ranking)} students\n"
    )
    
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text.contains("Transfer"))
async def start_transfer(message: Message, user: dict = None):
    """Show group selection for transfer"""
    user_id = str(message.from_user.id)
    
    # Get all groups
    # For students, we show ALL groups so they can transfer to anyone
    teacher_id = '8017101114'  # TODO: make dynamic
    groups = db.get_teacher_groups(teacher_id)
    
    if not groups:
        await message.answer("❌ No groups found.")
        return
    
    await message.answer(
        "💸 TRANSFER POINTS\n\n"
        "Select group to view students:",
        reply_markup=keyboards.get_group_selection_keyboard(groups, "transfer")
    )


@router.message(F.text.contains("Rating"))
async def show_rating_student(message: Message, user: dict = None):
    """Show ranking for student's own group"""
    user_id = str(message.from_user.id)
    
    # Get fresh user data if not provided by middleware
    if not user:
        user = db.get_user(user_id)
    
    group_id = user.get('group_id') if user else None
    
    if not group_id:
        await message.answer("❌ You are not assigned to any group yet.")
        return
    
    # Get group info
    group = db.get_group(group_id)
    group_name = group.get('name', 'Unknown Group') if group else 'Unknown Group'
    
    # Get ranking for this group only
    ranking = db.get_ranking(group_id=group_id)
    
    if not ranking:
        await message.answer(f"📊 No students found in {group_name}.")
        return
    
    text = f"🏆 {group_name.upper()} RANKING\n\n"
    
    for i, student in enumerate(ranking[:20], 1):
        emoji = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        # Bold current user's name
        if student['user_id'] == user_id:
            name = f"**{student['full_name']}**"
        else:
            name = student['full_name']
        
        text += f"{emoji} {name} - {student['points']} pts\n"
    
    text += f"\nTotal Students: {len(ranking)}"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboards.get_ranking_keyboard("student"))


@router.message(F.text.contains("History"))
async def show_history(message: Message):
    """Show transaction history"""
    user_id = str(message.from_user.id)
    logs = db.get_user_history(user_id, limit=config.STUDENT_HISTORY_LIMIT)
    
    if not logs:
        await message.answer("📜 No transaction history found.")
        return
    
    text = "📜 YOUR TRANSACTION HISTORY\n"
    
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
        f"📖 SYSTEM RULES\n"
        f"{rules_text}\n\n"
        f"💰 Transfer Commission: {int(commission_rate * 100)}%\n"
    )
    
    await message.answer(text)


@router.message(F.text.contains("Support"))
async def show_support(message: Message):
    """Show support contact"""
    # Get teacher
    teachers = db.get_all_users(role='teacher', status='active')
    
    if teachers:
        teacher = teachers[0]
        username = teacher.get('username', 'N/A')
        text = (
            f"🆘 SUPPORT\n"
            f"Contact teacher:\n"
            f"@{username}\n\n"
            f"They will assist you with any issues."
        )
    else:
        text = "🆘 No support contact available."
    
    await message.answer(text)


# ═══════════════════════════════════════════════════════════════════════════════
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
        reply_markup=keyboards.get_transfer_recipients_keyboard(students, user_id)
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
        commission = int(amount * commission_rate)
        total_cost = amount + commission
        
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
    parts = callback.data.split(":")
    recipient_id = parts[2]
    amount = int(parts[3])
    commission = int(parts[4])
    sender_id = str(callback.from_user.id)
    
    data = await state.get_data()
    
    # Execute atomic transfer
    result = db.transfer_points(sender_id, recipient_id, amount, commission)
    
    if result['success']:
        # Note: Sheets will be updated by background sync
        
        # Log transaction
        recipient = db.get_user(recipient_id)
        db.log_transfer(
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=amount,
            commission=commission,
            sender_name=user['full_name'],
            recipient_name=recipient['full_name']
        )
        
        # Notify sender
        await callback.message.edit_text(
            config.MESSAGES['transfer_success_sender'].format(
                amount=amount,
                recipient_name=data['recipient_name'],
                commission=commission,
                new_balance=result['sender_balance']
            )
        )
        
        # Notify recipient
        try:
            await callback.bot.send_message(
                chat_id=recipient_id,
                text=config.MESSAGES['transfer_success_recipient'].format(
                    amount=amount,
                    sender_name=user['full_name'],
                    new_balance=result['recipient_balance']
                )
            )
        except:
            pass
        
        await callback.answer("✅ Transfer successful!")
    else:
        await callback.message.edit_text(f"❌ Transfer failed: {result['error']}")
        await callback.answer("❌ Transfer failed!", show_alert=True)
    
    await state.clear()


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
    
    text = f"🏆 {group_name.upper()} RANKING\n\n"
    
    for i, student in enumerate(ranking[:20], 1):
        emoji = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        if student['user_id'] == user_id:
            name = f"**{student['full_name']}**"
        else:
            name = student['full_name']
        
        text += f"{emoji} {name} - {student['points']} pts\n"
    
    text += f"\nTotal Students: {len(ranking)}"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboards.get_ranking_keyboard(user.get('role', 'student'))
    )
    await callback.answer("✅ Ranking refreshed!")

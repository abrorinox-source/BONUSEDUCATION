"""
Registration handlers
Handles user registration flow
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import db
from sheets_manager import sheets_manager
import keyboards
import states
import config
from google.cloud.firestore import SERVER_TIMESTAMP

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    user_id = str(message.from_user.id)
    
    # Check if user exists
    user = db.get_user(user_id)
    
    if user:
        # User exists
        if user.get('status') == 'banned':
            # Permanently banned users cannot register
            await message.answer(
                "🚫 ACCOUNT PERMANENTLY BANNED\n"
                "Your account has been permanently banned.\n\n"
                "You cannot use this bot or register again.\n"
                "Contact support if you believe this is a mistake."
            )
            return
        
        elif user.get('status') == 'deleted':
            # Request restore approval from teacher
            db.update_user(user_id, {'status': 'pending_restore'})
            
            await message.answer(
                "⚠️ ACCOUNT RESTORATION REQUEST\n"
                "Your account was previously deleted.\n\n"
                "A restoration request has been sent to the teacher.\n"
                "Please wait for approval.\n\n"
                "⚠️ Note: Multiple violations may result in permanent ban."
            )
            
            # Notify teacher
            await notify_teacher_restore_request(message.bot, user_id, user)
            return
        
        elif user.get('status') == 'pending_restore':
            await message.answer(
                "⏳ RESTORATION PENDING\n"
                "Your account restoration is awaiting teacher approval.\n\n"
                "Please be patient."
            )
            return
        
        # Show appropriate menu
        if user.get('role') == 'teacher':
            await show_teacher_menu(message, user)
        elif user.get('status') == 'pending':
            await message.answer(config.MESSAGES['registration_pending'])
        elif user.get('status') == 'active':
            await show_student_menu(message, user)
    else:
        # Start registration
        await message.answer(
            "👋 Welcome! Please enter your full name (First + Last):",
            reply_markup=keyboards.get_back_keyboard("cancel:registration")
        )
        await state.set_state(states.RegistrationStates.waiting_for_name)


@router.message(states.RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Process user's name"""
    name = message.text.strip()
    
    # Validation
    if len(name) < 3:
        await message.answer("❌ Name is too short. Please enter your full name:")
        return
    
    if any(char.isdigit() for char in name):
        await message.answer("❌ Name should not contain numbers. Please try again:")
        return
    
    # Save name to FSM data
    await state.update_data(full_name=name)
    
    # Ask for teacher code or skip
    await message.answer(
        "Are you a teacher?\n"
        "Enter teacher code, or press 'Skip' to register as student:",
        reply_markup=keyboards.get_skip_keyboard()
    )
    await state.set_state(states.RegistrationStates.waiting_for_teacher_code)


@router.message(states.RegistrationStates.waiting_for_teacher_code)
async def process_teacher_code(message: Message, state: FSMContext):
    """Process teacher code or skip"""
    code = message.text.strip()
    
    if code.lower() == "skip":
        # Register as student - ask for contact
        await message.answer(
            "📱 Please share your contact:",
            reply_markup=keyboards.get_contact_keyboard()
        )
        await state.set_state(states.RegistrationStates.waiting_for_contact)
    elif code == config.TEACHER_CODE:
        # Valid teacher code - register as teacher
        data = await state.get_data()
        user_id = str(message.from_user.id)
        
        teacher_data = {
            'full_name': data['full_name'],
            'username': message.from_user.username or '',
            'role': 'teacher',
            'status': 'active',
            'points': 0
        }
        
        db.create_user(user_id, teacher_data)
        
        # Check if global default group exists (Sheet1)
        # This should be created only once for ALL teachers
        all_groups = db.groups_ref.where('sheet_name', '==', 'Sheet1').limit(1).stream()
        default_exists = False
        for _ in all_groups:
            default_exists = True
            break
        
        if not default_exists:
            # Create global default group (shared by all teachers)
            default_group = {
                'name': 'Main Group',
                'sheet_name': 'Sheet1',
                'teacher_id': 'global',  # Special marker for shared group
                'status': 'active',
                'created_at': db.get_timestamp()
            }
            db.create_group(default_group)
            print(f"✅ Created global default group 'Main Group' (Sheet1)")
        
        await message.answer(
            "✅ Welcome, Teacher!",
            reply_markup=keyboards.get_teacher_keyboard()
        )
        
        await state.clear()
        await show_teacher_menu(message, teacher_data)
    else:
        await message.answer("❌ Invalid teacher code. Try again or press 'Skip':")


@router.message(states.RegistrationStates.waiting_for_contact)
async def process_contact(message: Message, state: FSMContext):
    """Process contact sharing"""
    if not message.contact:
        await message.answer("❌ Please share your contact using the button below:")
        return
    
    # Save contact to FSM
    await state.update_data(phone=message.contact.phone_number)
    
    # Check if there are any groups
    groups = db.get_all_groups(status='active')
    
    if groups:
        # Show group selection
        await message.answer(
            "📚 SELECT YOUR CLASS/GROUP\n\n"
            "Please select which group you belong to:",
            reply_markup=keyboards.get_group_selection_keyboard(groups)
        )
        await state.set_state(states.RegistrationStates.waiting_for_group)
    else:
        # No groups - complete registration without group
        await complete_registration(message, state, group_id=None)


@router.callback_query(F.data.startswith("select_group:"))
async def process_group_selection(callback: CallbackQuery, state: FSMContext):
    """Process group selection"""
    group_id = callback.data.split(":")[1]
    
    # Verify group exists
    group = db.get_group(group_id)
    if not group:
        await callback.answer("❌ Group not found!", show_alert=True)
        return
    
    # Complete registration with selected group
    await complete_registration(callback.message, state, group_id=group_id, group_name=group['name'])
    await callback.answer(f"✅ Selected: {group['name']}")


async def complete_registration(message: Message, state: FSMContext, group_id: str = None, group_name: str = None):
    """Complete student registration"""
    data = await state.get_data()
    user_id = str(message.from_user.id)
    
    # Create student record
    student_data = {
        'full_name': data['full_name'],
        'phone': data['phone'],
        'username': message.from_user.username or '',
        'role': 'student',
        'status': 'pending',
        'points': 0
    }
    
    # Add group_id if provided
    if group_id:
        student_data['group_id'] = group_id
    
    db.create_user(user_id, student_data)
    
    # Notify student
    group_text = f"\nGroup: {group_name}" if group_name else ""
    await message.answer(
        f"✅ Registration submitted!{group_text}\n"
        "Wait for teacher approval.",
        reply_markup=keyboards.get_student_keyboard()
    )
    
    # Notify teacher
    await notify_teacher_new_registration(message.bot, user_id, student_data, group_name)
    
    await state.clear()


async def notify_teacher_new_registration(bot, user_id: str, student_data: dict, group_name: str = None):
    """Send approval request to teacher"""
    # Get all teachers
    teachers = db.get_all_users(role='teacher', status='active')
    
    if not teachers:
        print("⚠️ No active teachers found!")
        return
    
    group_text = f"Group: {group_name}\n" if group_name else ""
    
    message_text = (
        f"📝 NEW REGISTRATION REQUEST\n"
        f"Name: {student_data['full_name']}\n"
        f"Phone: {student_data['phone']}\n"
        f"Username: @{student_data['username']}\n"
        f"{group_text}"
        f"User ID: {user_id}\n\n"
        f"Approve or reject this registration?"
    )
    
    for teacher in teachers:
        try:
            await bot.send_message(
                chat_id=teacher['user_id'],
                text=message_text,
                reply_markup=keyboards.get_approval_keyboard(user_id)
            )
        except Exception as e:
            print(f"Error notifying teacher {teacher['user_id']}: {e}")


async def notify_teacher_restore_request(bot, user_id: str, user_data: dict):
    """Send restore approval request to teacher"""
    # Get all teachers
    teachers = db.get_all_users(role='teacher', status='active')
    
    if not teachers:
        print("⚠️ No active teachers found!")
        return
    
    # Get deletion info
    deleted_at = user_data.get('deleted_at', 'Unknown')
    
    message_text = (
        f"🔄 ACCOUNT RESTORATION REQUEST\n"
        f"Name: {user_data['full_name']}\n"
        f"Phone: {user_data.get('phone', 'N/A')}\n"
        f"Username: @{user_data.get('username', 'N/A')}\n"
        f"User ID: {user_id}\n"
        f"Previous Points: {user_data.get('points', 0)}\n"
        f"Deleted At: {deleted_at}\n\n"
        f"⚠️ This user was previously deleted.\n"
        f"Approve or reject restoration?"
    )
    
    for teacher in teachers:
        try:
            await bot.send_message(
                chat_id=teacher['user_id'],
                text=message_text,
                reply_markup=keyboards.get_restore_approval_keyboard(user_id)
            )
        except Exception as e:
            print(f"Error notifying teacher {teacher['user_id']}: {e}")


@router.callback_query(F.data.startswith("approve:"))
async def approve_student(callback: CallbackQuery):
    """Approve student registration"""
    user_id = callback.data.split(":")[1]
    
    # Update status
    db.update_user(user_id, {'status': 'active'})
    
    # Note: User will be added to Sheets by background sync
    user = db.get_user(user_id)
    
    # Notify student
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=config.MESSAGES['registration_approved'],
            reply_markup=keyboards.get_student_keyboard()
        )
    except Exception as e:
        print(f"Error notifying student: {e}")
    
    # Update teacher's message
    await callback.message.edit_text(
        f"✅ Approved: {user['full_name']}"
    )
    await callback.answer("✅ Student approved!")


@router.callback_query(F.data.startswith("reject:"))
async def reject_student(callback: CallbackQuery):
    """Reject student registration"""
    user_id = callback.data.split(":")[1]
    
    user = db.get_user(user_id)
    
    # Delete from database
    db.users_ref.document(user_id).delete()
    
    # Notify student
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=config.MESSAGES['registration_rejected']
        )
    except Exception as e:
        print(f"Error notifying student: {e}")
    
    # Update teacher's message
    await callback.message.edit_text(
        f"❌ Rejected: {user['full_name'] if user else 'Unknown'}"
    )
    await callback.answer("❌ Student rejected!")


@router.callback_query(F.data.startswith("restore_approve:"))
async def approve_restore(callback: CallbackQuery):
    """Approve account restoration"""
    user_id = callback.data.split(":")[1]
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ User not found!", show_alert=True)
        return
    
    # Restore account to active status
    db.update_user(user_id, {
        'status': 'active',
        'restored_at': SERVER_TIMESTAMP,
        'restored_by': str(callback.from_user.id)
    })
    
    # Note: User will be restored to Sheets by background sync
    
    # Notify student
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ ACCOUNT RESTORED\n"
                "Your account has been successfully restored!\n\n"
                "You can now use the bot again.\n"
                "Please follow the rules to avoid future suspensions."
            ),
            reply_markup=keyboards.get_student_keyboard()
        )
    except Exception as e:
        print(f"Error notifying student: {e}")
    
    # Update teacher's message
    await callback.message.edit_text(
        f"✅ Account Restored\n"
        f"User: {user['full_name']}\n"
        f"Status: Active\n"
        f"Points: {user.get('points', 0)}"
    )
    await callback.answer("✅ Account restored!")


@router.callback_query(F.data.startswith("restore_reject:"))
async def reject_restore(callback: CallbackQuery):
    """Reject restoration request (permanent ban)"""
    user_id = callback.data.split(":")[1]
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ User not found!", show_alert=True)
        return
    
    # Mark as permanently banned
    db.update_user(user_id, {
        'status': 'banned',
        'banned_at': SERVER_TIMESTAMP,
        'banned_by': str(callback.from_user.id)
    })
    
    # Notify student
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "🚫 ACCOUNT PERMANENTLY BANNED\n"
                "Your restoration request has been rejected.\n\n"
                "Your account is permanently banned due to violations.\n"
                "You cannot register again."
            )
        )
    except Exception as e:
        print(f"Error notifying student: {e}")
    
    # Update teacher's message
    await callback.message.edit_text(
        f"🚫 PERMANENT BAN\n"
        f"User: {user['full_name']}\n"
        f"Status: Banned\n"
        f"This user cannot register again."
    )
    await callback.answer("🚫 User permanently banned!")


async def show_teacher_menu(message: Message, user: dict):
    """Show teacher menu with stats"""
    # Get statistics
    active_students = len(db.get_all_users(role='student', status='active'))
    pending_approvals = len(db.get_pending_approvals())
    
    all_students = db.get_all_users(role='student', status='active')
    total_points = sum(s.get('points', 0) for s in all_students)
    
    text = config.MESSAGES['welcome_teacher'].format(
        name=user['full_name'],
        active_students=active_students,
        pending_approvals=pending_approvals,
        total_points=total_points
    )
    
    await message.answer(text, reply_markup=keyboards.get_teacher_keyboard())


async def show_student_menu(message: Message, user: dict):
    """Show student menu with stats"""
    # Get ranking position
    ranking = db.get_ranking()
    rank = next((i + 1 for i, u in enumerate(ranking) if u['user_id'] == user['user_id']), 0)
    
    text = config.MESSAGES['welcome_student'].format(
        name=user['full_name'],
        points=user.get('points', 0),
        rank=rank
    )
    
    await message.answer(text, reply_markup=keyboards.get_student_keyboard())

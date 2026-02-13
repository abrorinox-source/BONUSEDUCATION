"""
Teacher handlers
All teacher-related functionality
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from database import db
from sheets_manager import sheets_manager
import keyboards
from states import AddPointsStates, SubtractPointsStates, BroadcastStates, EditRulesStates
import config
from datetime import datetime

router = Router()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS FOR ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════════════

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """
    Safely edit message with proper error handling
    Handles 'message is not modified' errors gracefully
    """
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # Message content is the same, just answer the callback
            await safe_answer_callback(callback)
        else:
            raise


async def safe_answer_callback(callback: CallbackQuery, text: str = None, show_alert: bool = False):
    """
    Safely answer callback query with proper error handling
    Handles 'query is too old' errors gracefully
    """
    try:
        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            print(f"Callback query expired, ignoring: {callback.data}")
        else:
            raise


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(F.text.contains("Force Sync"))
async def force_sync(message: Message):
    """Force manual sync - syncs ALL fields from Sheets to Firebase"""
    await message.answer("⏳ Synchronizing with Google Sheets...\n🔄 Updating all student data (names, phones, points)...")
    
    # Perform full sync from Sheets to Firebase (updates ALL fields)
    stats = await sheets_manager.sync_sheets_to_firebase()
    
    result_text = (
        f"✅ Sync complete!\n"
        f"📊 All data updated from Google Sheets:\n"
        f"• Updated: {stats['updated']} students\n"
        f"• Added: {stats['added']} new students\n"
        f"• Errors: {stats['errors']}\n\n"
        f"ℹ️ Names, phones, usernames, and points are now synced!"
    )
    
    await message.answer(result_text)


@router.message(F.text.contains("Rating"))
async def show_rating_teacher(message: Message):
    """Show overall ranking"""
    ranking = db.get_ranking()
    
    if not ranking:
        await message.answer("📊 No students found.")
        return
    
    text = "🏆 OVERALL RANKING\n\n"
    
    for i, student in enumerate(ranking[:20], 1):
        emoji = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{emoji} {student['full_name']} - {student['points']} pts\n"
    
    text += f"\nTotal Students: {len(ranking)}"
    
    await message.answer(text, reply_markup=keyboards.get_ranking_keyboard("teacher"))


@router.message(F.text.contains("Students"))
async def show_students(message: Message):
    """Show students list"""
    students = db.get_all_users(role='student', status='active')
    
    if not students:
        await message.answer("👤 No active students found.")
        return
    
    await message.answer(
        f"👤 STUDENTS ({len(students)})\n"
        f"Select a student to manage:",
        reply_markup=keyboards.get_students_list_keyboard(students)
    )


@router.message(F.text.contains("Settings"))
async def show_settings(message: Message):
    """Show settings menu"""
    await message.answer(
        "⚙️ BOT SETTINGS\n"
        "Select an option:",
        reply_markup=keyboards.get_settings_keyboard()
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STUDENT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("student_detail:"))
async def student_detail(callback: CallbackQuery):
    """Show student details"""
    user_id = callback.data.split(":")[1]
    student = db.get_user(user_id)
    
    if not student:
        await callback.answer("❌ Student not found!", show_alert=True)
        return
    
    text = (
        f"👤 STUDENT DETAILS\n"
        f"Name: {student['full_name']}\n"
        f"Phone: {student.get('phone', 'N/A')}\n"
        f"Username: @{student.get('username', 'N/A')}\n"
        f"Points: {student['points']}\n"
        f"Status: {student['status']}\n"
        f"What would you like to do?"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.get_student_detail_keyboard(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_points:"))
async def add_points_start(callback: CallbackQuery, state: FSMContext):
    """Start add points flow"""
    user_id = callback.data.split(":")[1]
    student = db.get_user(user_id)
    
    if not student:
        await callback.answer("❌ Student not found!", show_alert=True)
        return
    
    await state.update_data(target_user_id=user_id, target_user_name=student['full_name'])
    await state.set_state(AddPointsStates.waiting_for_amount)
    
    await callback.message.answer(
        f"➕ ADD POINTS\n"
        f"Student: {student['full_name']}\n\n"
        f"Enter amount to add (1-10000):"
    )
    await callback.answer()


@router.message(AddPointsStates.waiting_for_amount)
async def add_points_amount(message: Message, state: FSMContext):
    """Process add points amount"""
    try:
        amount = int(message.text.strip())
        
        if amount <= 0 or amount > 10000:
            await message.answer("❌ Amount must be between 1 and 10000. Try again:")
            return
        
        data = await state.get_data()
        student = db.get_user(data['target_user_id'])
        
        text = (
            f"⚠️ CONFIRMATION\n"
            f"Student: {data['target_user_name']}\n"
            f"Action: Add Points\n"
            f"Amount: {amount} pts\n"
            f"Current Balance: {student['points']} pts\n"
            f"New Balance: {student['points'] + amount} pts\n\n"
            f"Confirm this action?"
        )
        
        await state.update_data(amount=amount)
        
        await message.answer(
            text,
            reply_markup=keyboards.get_confirmation_keyboard("add_points", data['target_user_id'])
        )
    
    except ValueError:
        await message.answer("❌ Please enter a valid number:")


@router.callback_query(F.data.startswith("confirm:add_points:"))
async def confirm_add_points(callback: CallbackQuery, state: FSMContext):
    """Confirm and execute add points"""
    user_id = callback.data.split(":")[2]
    data = await state.get_data()
    amount = data['amount']
    teacher_id = str(callback.from_user.id)
    
    # Add points (atomic)
    result = db.add_points(user_id, amount)
    
    if result['success']:
        # Log transaction
        db.log_add_points(
            teacher_id=teacher_id,
            student_id=user_id,
            amount=amount,
            student_name=data['target_user_name']
        )
        
        await callback.message.edit_text(
            f"✅ Points Added!\n"
            f"Student: {data['target_user_name']}\n"
            f"Amount: +{amount} pts\n"
            f"New Balance: {result['new_balance']} pts"
        )
        
        # Notify student
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=f"💰 Teacher added {amount} pts to your account!\n"
                     f"New balance: {result['new_balance']} pts"
            )
        except:
            pass
    else:
        await callback.message.edit_text(f"❌ Error: {result['error']}")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("subtract_points:"))
async def subtract_points_start(callback: CallbackQuery, state: FSMContext):
    """Start subtract points flow"""
    user_id = callback.data.split(":")[1]
    student = db.get_user(user_id)
    
    if not student:
        await callback.answer("❌ Student not found!", show_alert=True)
        return
    
    await state.update_data(
        target_user_id=user_id,
        target_user_name=student['full_name'],
        current_balance=student['points']
    )
    await state.set_state(SubtractPointsStates.waiting_for_amount)
    
    await callback.message.answer(
        f"➖ SUBTRACT POINTS\n"
        f"Student: {student['full_name']}\n"
        f"Current Balance: {student['points']} pts\n\n"
        f"Enter amount to subtract:"
    )
    await callback.answer()


@router.message(SubtractPointsStates.waiting_for_amount)
async def subtract_points_amount(message: Message, state: FSMContext):
    """Process subtract points amount"""
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        
        if amount <= 0:
            await message.answer("❌ Amount must be positive. Try again:")
            return
        
        if amount > data['current_balance']:
            await message.answer(
                f"❌ Amount exceeds current balance ({data['current_balance']} pts).\n"
                f"Try again:"
            )
            return
        
        student = db.get_user(data['target_user_id'])
        
        text = (
            f"⚠️ CONFIRMATION\n"
            f"Student: {data['target_user_name']}\n"
            f"Action: Subtract Points\n"
            f"Amount: {amount} pts\n"
            f"Current Balance: {student['points']} pts\n"
            f"New Balance: {student['points'] - amount} pts\n\n"
            f"Confirm this action?"
        )
        
        await state.update_data(amount=amount)
        
        await message.answer(
            text,
            reply_markup=keyboards.get_confirmation_keyboard("subtract_points", data['target_user_id'])
        )
    
    except ValueError:
        await message.answer("❌ Please enter a valid number:")


@router.callback_query(F.data.startswith("confirm:subtract_points:"))
async def confirm_subtract_points(callback: CallbackQuery, state: FSMContext):
    """Confirm and execute subtract points"""
    user_id = callback.data.split(":")[2]
    data = await state.get_data()
    amount = data['amount']
    teacher_id = str(callback.from_user.id)
    
    # Subtract points (atomic)
    result = db.subtract_points(user_id, amount)
    
    if result['success']:
        # Log transaction
        db.log_subtract_points(
            teacher_id=teacher_id,
            student_id=user_id,
            amount=amount,
            student_name=data['target_user_name']
        )
        
        await callback.message.edit_text(
            f"✅ Points Subtracted!\n"
            f"Student: {data['target_user_name']}\n"
            f"Amount: -{amount} pts\n"
            f"New Balance: {result['new_balance']} pts"
        )
        
        # Notify student
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=f"⚠️ Teacher removed {amount} pts from your account.\n"
                     f"New balance: {result['new_balance']} pts"
            )
        except:
            pass
    else:
        await callback.message.edit_text(f"❌ Error: {result['error']}")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("delete_student:"))
async def delete_student_confirm(callback: CallbackQuery):
    """Show delete confirmation"""
    user_id = callback.data.split(":")[1]
    student = db.get_user(user_id)
    
    if not student:
        await callback.answer("❌ Student not found!", show_alert=True)
        return
    
    text = (
        f"⚠️ WARNING\n"
        f"Are you sure you want to delete this student?\n\n"
        f"Name: {student['full_name']}\n"
        f"Points: {student['points']} (will be lost)\n\n"
        f"This action CANNOT be undone!"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.get_confirmation_keyboard("delete_student", user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:delete_student:"))
async def confirm_delete_student(callback: CallbackQuery):
    """Execute student deletion"""
    user_id = callback.data.split(":")[2]
    student = db.get_user(user_id)
    
    if not student:
        await callback.answer("❌ Student not found!", show_alert=True)
        return
    
    # Delete from Firebase (soft delete)
    db.delete_user(user_id)
    
    # Note: Sheets will be updated by background sync
    
    # Notify student
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=config.MESSAGES['user_deleted']
        )
    except:
        pass
    
    await callback.message.edit_text(
        f"✅ Student deleted successfully.\n"
        f"Name: {student['full_name']}"
    )
    await callback.answer("✅ Student deleted!")


# ═══════════════════════════════════════════════════════════════════════════════
# CANCEL HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("cancel:"))
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Cancel current action"""
    await state.clear()
    await callback.message.edit_text("❌ Action cancelled.")
    await callback.answer()


@router.callback_query(F.data == "students:list")
async def back_to_students_list(callback: CallbackQuery):
    """Return to students list"""
    students = db.get_all_users(role='student', status='active')
    
    await callback.message.edit_text(
        f"👤 STUDENTS ({len(students)})\n"
        f"Select a student to manage:",
        reply_markup=keyboards.get_students_list_keyboard(students)
    )
    await callback.answer()


@router.callback_query(F.data == "teacher:menu")
async def back_to_teacher_menu(callback: CallbackQuery):
    """Return to teacher menu"""
    await callback.message.delete()
    await safe_answer_callback(callback)


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("settings:"))
async def handle_settings(callback: CallbackQuery):
    """Handle settings menu actions"""
    action = callback.data.split(":")[1]
    
    if action == "back":
        await callback.message.delete()
        await safe_answer_callback(callback)
        return
    
    if action == "commission":
        settings = db.get_settings()
        commission_rate = settings.get('commission_rate', config.DEFAULT_COMMISSION_RATE)
        
        await safe_edit_message(
            callback,
            f"💰 TRANSFER COMMISSION\n"
            f"Current Rate: {commission_rate * 100}%\n\n"
            f"Select new commission rate:",
            reply_markup=keyboards.get_commission_keyboard()
        )
    
    elif action == "bot_status":
        settings = db.get_settings()
        current_status = settings.get('bot_status', 'public')
        
        status_description = {
            'public': '✅ Normal mode - All users can access bot',
            'maintenance': '🔧 Maintenance mode - Only teachers can access'
        }
        
        await safe_edit_message(
            callback,
            f"🔓 BOT STATUS\n"
            f"Current: {current_status.upper()}\n"
            f"{status_description.get(current_status, '')}\n\n"
            f"Select new status:",
            reply_markup=keyboards.get_bot_status_keyboard(current_status)
        )
    
    elif action == "sync_control":
        # Get current sync settings from database
        settings = db.get_settings()
        sync_enabled = settings.get('sync_enabled', True)
        sync_interval = settings.get('sync_interval', config.DEFAULT_SYNC_INTERVAL)
        
        # Display sync control menu
        await safe_edit_message(
            callback,
            f"🔄 SYNC CONTROL\n\n"
            f"Status: {'✅ Enabled' if sync_enabled else '❌ Disabled'}\n"
            f"Task: {'🟢 Running' if sheets_manager.is_sync_running() else '🔴 Stopped'}\n"
            f"Interval: {sync_interval} seconds\n\n"
            f"Control sync settings:",
            reply_markup=keyboards.get_sync_control_keyboard(sync_enabled)
        )
    
    elif action == "transaction_history":
        await safe_edit_message(
            callback,
            f"📜 TRANSACTION HISTORY\n"
            f"Filter transaction logs:",
            reply_markup=keyboards.get_transaction_history_keyboard()
        )
    
    elif action == "export":
        await safe_edit_message(
            callback,
            f"📥 EXPORT DATA\n"
            f"Select export format:",
            reply_markup=keyboards.get_export_keyboard()
        )
    
    elif action == "edit_rules":
        # Get current rules from database
        settings = db.get_settings()
        current_rules = settings.get('rules_text', 'No rules set yet.')
        
        await safe_edit_message(
            callback,
            f"📝 BOT RULES\n\n"
            f"Current Rules:\n"
            f"{current_rules}\n\n"
            f"Click below to edit rules:",
            reply_markup=keyboards.get_edit_rules_keyboard()
        )
    
    elif action == "broadcast":
        await safe_edit_message(
            callback,
            f"📢 GLOBAL BROADCAST\n"
            f"Select target audience:",
            reply_markup=keyboards.get_broadcast_keyboard()
        )
    
    await safe_answer_callback(callback)


@router.callback_query(F.data.startswith("bot_status:"))
async def change_bot_status(callback: CallbackQuery):
    """Change bot status"""
    new_status = callback.data.split(":")[1]
    
    db.update_settings({'bot_status': new_status})
    
    status_info = {
        'public': '✅ PUBLIC MODE\nAll users can access the bot normally.',
        'maintenance': '🔧 MAINTENANCE MODE\nOnly teachers can access. Students will see maintenance message.'
    }
    
    await safe_edit_message(
        callback,
        f"✅ Bot status updated!\n\n"
        f"{status_info.get(new_status, '')}",
        reply_markup=keyboards.get_back_keyboard("settings:back")
    )
    await safe_answer_callback(callback, f"✅ Changed to {new_status.upper()} mode")


@router.callback_query(F.data.startswith("sync:"))
async def handle_sync_control(callback: CallbackQuery):
    """
    Handle all sync control actions
    Centralized handler for sync-related callbacks
    """
    try:
        # Parse callback data
        parts = callback.data.split(":")
        action = parts[1] if len(parts) > 1 else None
        
        if not action:
            await safe_answer_callback(callback, "❌ Invalid action", show_alert=True)
            return
        
        # Get current settings
        settings = db.get_settings()
        sync_enabled = settings.get('sync_enabled', True)
        sync_interval = settings.get('sync_interval', config.DEFAULT_SYNC_INTERVAL)
        
        # ═══════════════════════════════════════════════════════════════
        # ACTION: Show main sync control menu
        # ═══════════════════════════════════════════════════════════════
        if action == "control":
            await safe_edit_message(
                callback,
                f"🔄 SYNC CONTROL\n"
                f"Status: {'✅ Enabled' if sync_enabled else '❌ Disabled'}\n"
                f"Task: {'🟢 Running' if sheets_manager.is_sync_running() else '🔴 Stopped'}\n"
                f"Interval: {sync_interval} seconds\n\n"
                f"Control sync settings:",
                reply_markup=keyboards.get_sync_control_keyboard(sync_enabled)
            )
            await safe_answer_callback(callback)
        
        # ═══════════════════════════════════════════════════════════════
        # ACTION: Toggle sync on/off
        # ═══════════════════════════════════════════════════════════════
        elif action == "toggle":
            new_state = not sync_enabled
            db.update_settings({'sync_enabled': new_state})
            
            # Start or stop the background sync task
            if new_state:
                sheets_manager.start_background_sync()
                status_text = "enabled and started"
                status_emoji = "✅"
            else:
                sheets_manager.stop_background_sync()
                status_text = "disabled and stopped"
                status_emoji = "⏸️"
            
            await safe_answer_callback(callback, f"{status_emoji} Sync {status_text}!", show_alert=False)
            
            # Refresh the sync control menu with updated state
            await safe_edit_message(
                callback,
                f"🔄 SYNC CONTROL\n"
                f"Status: {'✅ Enabled' if new_state else '❌ Disabled'}\n"
                f"Task: {'🟢 Running' if sheets_manager.is_sync_running() else '🔴 Stopped'}\n"
                f"Interval: {sync_interval} seconds\n\n"
                f"Control sync settings:",
                reply_markup=keyboards.get_sync_control_keyboard(new_state)
            )
        
        # ═══════════════════════════════════════════════════════════════
        # ACTION: Show interval selection menu
        # ═══════════════════════════════════════════════════════════════
        elif action == "interval":
            await safe_edit_message(
                callback,
                f"⏱️ SYNC INTERVAL\n"
                f"Current: {sync_interval} seconds\n\n"
                f"Select new interval:",
                reply_markup=keyboards.get_sync_interval_keyboard()
            )
            await safe_answer_callback(callback)
        
        # ═══════════════════════════════════════════════════════════════
        # ACTION: Set specific interval
        # ═══════════════════════════════════════════════════════════════
        elif action == "set_interval":
            # This is now handled here directly
            if len(parts) < 3:
                await safe_answer_callback(callback, "❌ Invalid interval format", show_alert=True)
                return
            
            try:
                interval = int(parts[2])
                
                # Validate interval
                if interval < 5 or interval > 3600:
                    await safe_answer_callback(callback, "❌ Interval must be between 5s and 1 hour", show_alert=True)
                    return
                
                # Get old interval
                old_interval = sync_interval
                
                # Update settings
                success = db.update_settings({'sync_interval': interval})
                
                if success:
                    # Verify update
                    new_settings = db.get_settings()
                    new_interval = new_settings.get('sync_interval', interval)
                    print(f"⚙️ Sync interval changed to {new_interval} seconds")
                    
                    await safe_answer_callback(callback, f"✅ Interval set to {interval}s")
                    
                    # Show updated sync control menu
                    await safe_edit_message(
                        callback,
                        f"✅ SYNC INTERVAL UPDATED\n\n"
                        f"Previous: {old_interval}s\n"
                        f"New: {new_interval}s\n"
                        f"Status: {'✅ Enabled' if sync_enabled else '❌ Disabled'}\n\n"
                        f"Next sync will use the new interval.",
                        reply_markup=keyboards.get_back_keyboard("sync:control")
                    )
                else:
                    await safe_answer_callback(callback, "❌ Failed to update interval", show_alert=True)
            
            except ValueError:
                await safe_answer_callback(callback, "❌ Invalid interval value", show_alert=True)
        
        # ═══════════════════════════════════════════════════════════════
        # ACTION: Force sync from Sheets to Firebase (ignore timestamps)
        # ═══════════════════════════════════════════════════════════════
        elif action == "force_sheets":
            await safe_answer_callback(callback, "🔄 Forcing Sheets → Firebase sync...", show_alert=False)
            
            try:
                stats = await sheets_manager.sync_sheets_to_firebase()
                
                await safe_edit_message(
                    callback,
                    f"✅ FORCED SHEETS → FIREBASE SYNC\n\n"
                    f"📊 Results:\n"
                    f"• Updated: {stats.get('updated', 0)}\n"
                    f"• Added: {stats.get('added', 0)}\n"
                    f"• Errors: {stats.get('errors', 0)}\n\n"
                    f"⚠️ All Sheets data has been copied to Firebase.\n"
                    f"Timestamps were ignored during this sync.",
                    reply_markup=keyboards.get_back_keyboard("sync:control")
                )
            except Exception as e:
                await safe_edit_message(
                    callback,
                    f"❌ Force sync failed:\n{str(e)}",
                    reply_markup=keyboards.get_back_keyboard("sync:control")
                )
        
        # ═══════════════════════════════════════════════════════════════
        # ACTION: Unknown action
        # ═══════════════════════════════════════════════════════════════
        else:
            await safe_answer_callback(callback, f"❌ Unknown action: {action}", show_alert=True)
    
    except Exception as e:
        print(f"Error in handle_sync_control: {e}")
        await safe_answer_callback(callback, f"❌ Error: {str(e)}", show_alert=True)
    




@router.callback_query(F.data.startswith("logs:"))
async def handle_transaction_logs(callback: CallbackQuery):
    """Handle transaction logs"""
    parts = callback.data.split(":")
    action = parts[1]
    
    if action == "export_menu":
        # Show export format menu
        await safe_edit_message(
            callback,
            f"📊 EXPORT TRANSACTION LOGS\n"
            f"Select export format:",
            reply_markup=keyboards.get_logs_export_keyboard()
        )
        await safe_answer_callback(callback)
        return
    
    if action == "export":
        # Handle export based on format
        export_format = parts[2] if len(parts) > 2 else "json"
        await callback.answer(f"📥 Generating {export_format.upper()} export...")
        
        try:
            # Get all logs
            logs = db.get_transaction_logs(limit=500)  # Get more logs for export
            
            if not logs:
                await callback.message.edit_text(
                    "📜 No transaction logs found to export.",
                    reply_markup=keyboards.get_back_keyboard("settings:transaction_history")
                )
                await callback.answer()
                return
            
            from aiogram.types import FSInputFile
            import os
            
            if export_format == "json":
                # Generate JSON export
                import json
                report_data = {
                    "export_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "total_transactions": len(logs),
                    "transactions": logs
                }
                
                filename = f"transaction_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
                
                await callback.message.answer_document(
                    FSInputFile(filename),
                    caption=(
                        f"📜 Transaction Logs Export (JSON)\n"
                        f"Total: {len(logs)} transactions\n"
                        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                )
                os.remove(filename)
            
            elif export_format == "excel":
                # Generate Excel export
                from openpyxl import Workbook
                from openpyxl.styles import Font, PatternFill, Alignment
                
                filename = f"transaction_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                wb = Workbook()
                ws = wb.active
                ws.title = "Transaction Logs"
                
                # Header style
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_font = Font(bold=True, color="FFFFFF")
                
                # Headers
                headers = ['Date', 'Type', 'Description', 'Amount', 'Commission', 'Status']
                ws.append(headers)
                
                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Data
                for log in logs:
                    log_type = log.get('type', 'unknown')
                    timestamp = log.get('timestamp', 'N/A')
                    
                    if log_type == "transfer":
                        description = f"From: {log.get('sender_name', 'Unknown')} → To: {log.get('recipient_name', 'Unknown')}"
                        amount = log.get('amount', 0)
                        commission = log.get('commission', 0)
                    elif log_type == "add_points":
                        description = f"Added to: {log.get('student_name', 'Unknown')} | Reason: {log.get('reason', 'N/A')}"
                        amount = log.get('amount', 0)
                        commission = 0
                    elif log_type == "subtract_points":
                        description = f"Subtracted from: {log.get('student_name', 'Unknown')} | Reason: {log.get('reason', 'N/A')}"
                        amount = -log.get('amount', 0)
                        commission = 0
                    elif log_type == "manual_edit":
                        description = f"User: {log.get('user_name', 'Unknown')} | {log.get('old_points', 0)} → {log.get('new_points', 0)}"
                        amount = log.get('delta', 0)
                        commission = 0
                    else:
                        description = "Unknown transaction"
                        amount = 0
                        commission = 0
                    
                    ws.append([
                        str(timestamp),
                        log_type.replace('_', ' ').title(),
                        description,
                        amount,
                        commission,
                        log.get('status', 'completed')
                    ])
                
                # Auto-adjust column widths
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter].width = adjusted_width
                
                wb.save(filename)
                
                await callback.message.answer_document(
                    FSInputFile(filename),
                    caption=(
                        f"📋 Transaction Logs Export (Excel)\n"
                        f"Total: {len(logs)} transactions\n"
                        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                )
                os.remove(filename)
            
            elif export_format == "pdf":
                # Generate PDF export
                from reportlab.lib.pagesizes import A4, landscape
                from reportlab.lib import colors
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.enums import TA_CENTER
                
                filename = f"transaction_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    textColor=colors.HexColor('#366092'),
                    spaceAfter=30,
                    alignment=TA_CENTER
                )
                title = Paragraph("Transaction Logs Report", title_style)
                elements.append(title)
                
                # Summary
                summary_text = (
                    f"<b>Export Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
                    f"<b>Total Transactions:</b> {len(logs)}<br/>"
                    f"<b>Report Period:</b> All time"
                )
                summary = Paragraph(summary_text, styles['Normal'])
                elements.append(summary)
                elements.append(Spacer(1, 0.3*inch))
                
                # Table data
                data = [['Date', 'Type', 'Description', 'Amount', 'Status']]
                
                for log in logs[:100]:  # Limit to 100 for PDF
                    log_type = log.get('type', 'unknown')
                    timestamp = str(log.get('timestamp', 'N/A'))[:19]
                    
                    if log_type == "transfer":
                        description = f"{log.get('sender_name', 'Unknown')[:15]} → {log.get('recipient_name', 'Unknown')[:15]}"
                        amount = f"+{log.get('amount', 0)}"
                    elif log_type == "add_points":
                        description = f"Added: {log.get('student_name', 'Unknown')[:20]}"
                        amount = f"+{log.get('amount', 0)}"
                    elif log_type == "subtract_points":
                        description = f"Removed: {log.get('student_name', 'Unknown')[:20]}"
                        amount = f"-{log.get('amount', 0)}"
                    elif log_type == "manual_edit":
                        description = f"Edit: {log.get('user_name', 'Unknown')[:20]}"
                        amount = f"{log.get('delta', 0):+d}"
                    else:
                        description = "Unknown"
                        amount = "0"
                    
                    data.append([
                        timestamp,
                        log_type.replace('_', ' ').title(),
                        description,
                        amount,
                        log.get('status', 'completed')[:10]
                    ])
                
                # Create table
                table = Table(data, colWidths=[1.8*inch, 1.2*inch, 3*inch, 0.8*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
                ]))
                
                elements.append(table)
                
                if len(logs) > 100:
                    elements.append(Spacer(1, 0.2*inch))
                    note = Paragraph(f"<i>Note: Showing first 100 of {len(logs)} transactions</i>", styles['Normal'])
                    elements.append(note)
                
                doc.build(elements)
                
                await callback.message.answer_document(
                    FSInputFile(filename),
                    caption=(
                        f"📈 Transaction Logs Export (PDF)\n"
                        f"Total: {len(logs)} transactions\n"
                        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                )
                os.remove(filename)
            
            await callback.message.edit_text(
                f"✅ Transaction logs exported successfully as {export_format.upper()}!\n"
                f"Total: {len(logs)} transactions",
                reply_markup=keyboards.get_back_keyboard("settings:transaction_history")
            )
        
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Error exporting logs:\n{str(e)}",
                reply_markup=keyboards.get_back_keyboard("settings:transaction_history")
            )
        
        return
    
    # Get logs based on filter
    await callback.answer("🔍 Loading logs...")
    
    try:
        if action == "all":
            logs = db.get_transaction_logs(limit=config.TRANSACTION_LOG_LIMIT)
            filter_name = "ALL"
        elif action == "transfer":
            logs = db.get_transaction_logs(limit=config.TRANSACTION_LOG_LIMIT, transaction_type="transfer")
            filter_name = "TRANSFERS"
        elif action == "add_points":
            logs = db.get_transaction_logs(limit=config.TRANSACTION_LOG_LIMIT, transaction_type="add_points")
            filter_name = "ADDED POINTS"
        elif action == "subtract_points":
            logs = db.get_transaction_logs(limit=config.TRANSACTION_LOG_LIMIT, transaction_type="subtract_points")
            filter_name = "SUBTRACTED POINTS"
        elif action == "manual_edit":
            logs = db.get_transaction_logs(limit=config.TRANSACTION_LOG_LIMIT, transaction_type="manual_edit")
            filter_name = "MANUAL EDITS"
        else:
            await callback.answer("❌ Unknown action", show_alert=True)
            return
        
        if not logs:
            await callback.message.edit_text(
                f"📜 No transaction logs found for: {filter_name}",
                reply_markup=keyboards.get_back_keyboard("settings:transaction_history")
            )
            return
        
        # Format logs
        text = f"📜 TRANSACTION LOGS ({filter_name})\n"
        
        for log in logs[:15]:
            log_type = log.get('type', 'unknown')
            
            if log_type == "transfer":
                text += (
                    f"💸 Transfer\n"
                    f"From: {log.get('sender_name', 'Unknown')}\n"
                    f"To: {log.get('recipient_name', 'Unknown')}\n"
                    f"Amount: {log.get('amount', 0)} pts\n"
                    f"Commission: {log.get('commission', 0)} pts\n\n"
                )
            elif log_type == "add_points":
                text += (
                    f"➕ Added Points\n"
                    f"Student: {log.get('student_name', 'Unknown')}\n"
                    f"Amount: +{log.get('amount', 0)} pts\n"
                    f"Reason: {log.get('reason', 'N/A')}\n\n"
                )
            elif log_type == "subtract_points":
                text += (
                    f"➖ Subtracted Points\n"
                    f"Student: {log.get('student_name', 'Unknown')}\n"
                    f"Amount: -{log.get('amount', 0)} pts\n"
                    f"Reason: {log.get('reason', 'N/A')}\n\n"
                )
            elif log_type == "manual_edit":
                text += (
                    f"✏️ Manual Edit\n"
                    f"User: {log.get('user_name', 'Unknown')}\n"
                    f"Old: {log.get('old_points', 0)} pts\n"
                    f"New: {log.get('new_points', 0)} pts\n"
                    f"Delta: {log.get('delta', 0):+d} pts\n\n"
                )
        
        if len(logs) > 15:
            text += f"\n... and {len(logs) - 15} more transactions\n"
        
        text += f"\nTotal: {len(logs)} transactions"
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboards.get_back_keyboard("settings:transaction_history")
        )
    
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Error loading transaction logs:\n{str(e)}",
            reply_markup=keyboards.get_back_keyboard("settings:transaction_history")
        )


@router.callback_query(F.data.startswith("commission:"))
async def handle_commission(callback: CallbackQuery):
    """Handle commission rate changes"""
    action = callback.data.split(":")[1]
    
    if action == "set":
        rate = int(callback.data.split(":")[2])
        rate_decimal = rate / 100.0
        
        # Validate rate
        if rate < 0 or rate > 50:
            await callback.answer("❌ Rate must be between 0-50%")
            return
        
        # Update settings
        db.update_settings({'commission_rate': rate_decimal})
        
        await callback.answer(f"✅ Commission rate set to {rate}%")
        
        await callback.message.edit_text(
            f"✅ COMMISSION UPDATED\n"
            f"New Rate: {rate}%\n\n"
            f"This rate will apply to all future transfers.",
            reply_markup=keyboards.get_back_keyboard("settings:back")
        )


@router.callback_query(F.data.startswith("broadcast:"))
async def handle_broadcast(callback: CallbackQuery, state: FSMContext):
    """Handle broadcast message"""
    target = callback.data.split(":")[1]
    
    await state.set_state(BroadcastStates.waiting_for_message)
    await state.update_data(target=target)
    
    target_text = {
        'all_active': '👥 All Active Users',
        'students': '👨‍🎓 Students Only',
        'teachers': '👨‍🏫 Teachers Only'
    }.get(target, 'Unknown')
    
    await callback.message.edit_text(
        f"📢 BROADCAST MESSAGE\n"
        f"Target: {target_text}\n\n"
        f"Send your message now:\n"
        f"(Text, photo, video, or document)\n\n"
        f"Send /cancel to abort."
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Process and send broadcast message"""
    data = await state.get_data()
    target = data.get('target')
    
    # Get target users
    if target == 'all_active':
        users = db.get_all_users(status='active')
    elif target == 'students':
        users = db.get_all_users(role='student', status='active')
    elif target == 'teachers':
        users = db.get_all_users(role='teacher', status='active')
    else:
        await message.answer("❌ Invalid target")
        await state.clear()
        return
    
    # Send broadcast
    success_count = 0
    fail_count = 0
    
    status_msg = await message.answer(f"📢 Broadcasting to {len(users)} users...")
    
    for user in users:
        try:
            if message.text:
                await message.bot.send_message(user['user_id'], f"📢 Broadcast:\n\n{message.text}")
            elif message.photo:
                await message.bot.send_photo(user['user_id'], message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await message.bot.send_video(user['user_id'], message.video.file_id, caption=message.caption)
            elif message.document:
                await message.bot.send_document(user['user_id'], message.document.file_id, caption=message.caption)
            
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Failed to send to {user['user_id']}: {e}")
    
    await status_msg.edit_text(
        f"✅ BROADCAST COMPLETE\n"
        f"✅ Sent: {success_count}\n"
        f"❌ Failed: {fail_count}\n"
        f"📊 Total: {len(users)}"
    )
    
    await state.clear()


@router.callback_query(F.data.startswith("rules:"))
async def handle_rules(callback: CallbackQuery, state: FSMContext):
    """Handle rules editing"""
    action = callback.data.split(":")[1]
    
    if action == "edit":
        # Start edit rules flow
        settings = db.get_settings()
        current_rules = settings.get('rules_text', 'No rules set yet.')
        
        await state.set_state(EditRulesStates.waiting_for_rules)
        
        await callback.message.edit_text(
            f"📝 EDIT BOT RULES\n\n"
            f"Current Rules:\n"
            f"{current_rules}\n\n"
            f"Send new rules text now.\n"
            f"You can use formatting:\n"
            f"• Line breaks for new lines\n"
            f"• Emojis 😊\n"
            f"• Keep it clear and concise\n\n"
            f"Send /cancel to abort."
        )
        await callback.answer()


@router.message(EditRulesStates.waiting_for_rules)
async def process_rules_text(message: Message, state: FSMContext):
    """Process new rules text"""
    new_rules = message.text.strip()
    
    if len(new_rules) < 10:
        await message.answer("❌ Rules text is too short (minimum 10 characters). Try again:")
        return
    
    if len(new_rules) > 2000:
        await message.answer("❌ Rules text is too long (maximum 2000 characters). Try again:")
        return
    
    # Save to database
    db.update_settings({'rules_text': new_rules})
    
    await message.answer(
        f"✅ RULES UPDATED SUCCESSFULLY!\n\n"
        f"New Rules:\n"
        f"{new_rules[:500]}{'...' if len(new_rules) > 500 else ''}\n\n"
        f"Students will see these rules when they click 'Rules' button."
    )
    
    await state.clear()


@router.callback_query(F.data.startswith("compare:"))
async def handle_compare(callback: CallbackQuery):
    """Handle data comparison"""
    action = callback.data.split(":")[1]
    
    if action == "refresh":
        await callback.answer("🔍 Comparing data...")
        
        # Get Firebase data
        fb_users = db.get_all_users(role='student')
        
        # Get Sheets data
        sheet_data = await sheets_manager.get_all_users_from_sheets()
        
        # Compare
        fb_ids = {u['user_id'] for u in fb_users}
        sheet_ids = {u['user_id'] for u in sheet_data}
        
        only_fb = fb_ids - sheet_ids
        only_sheet = sheet_ids - fb_ids
        common = fb_ids & sheet_ids
        
        # Check differences in points
        differences = []
        for user_id in common:
            fb_user = next(u for u in fb_users if u['user_id'] == user_id)
            sheet_user = next(u for u in sheet_data if u['user_id'] == user_id)
            
            fb_points = fb_user.get('points', 0)
            sheet_points = sheet_user.get('points', 0)
            
            if fb_points != sheet_points:
                differences.append({
                    'user_id': user_id,
                    'name': fb_user.get('full_name', 'Unknown'),
                    'fb_points': fb_points,
                    'sheet_points': sheet_points,
                    'diff': fb_points - sheet_points
                })
        
        text = f"🔍 DATA COMPARISON\n"
        text += f"📊 Statistics:\n"
        text += f"• Common: {len(common)}\n"
        text += f"• Only in Firebase: {len(only_fb)}\n"
        text += f"• Only in Sheets: {len(only_sheet)}\n"
        text += f"• Point differences: {len(differences)}\n\n"
        
        if differences:
            text += f"⚠️ Points Mismatch:\n"
            for diff in differences[:5]:
                text += f"• {diff['name']}: FB={diff['fb_points']}, Sheet={diff['sheet_points']}\n"
            
            if len(differences) > 5:
                text += f"\n... and {len(differences) - 5} more\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboards.get_comparison_keyboard()
        )
    
    elif action == "sync_fb_to_sh":
        await callback.answer("🔄 Syncing Firebase → Sheets...")
        stats = await sheets_manager.sync_firebase_to_sheets()
        
        await callback.message.edit_text(
            f"✅ FIREBASE → SHEETS SYNC COMPLETE\n"
            f"• Updated: {stats['updated']}\n"
            f"• Added: {stats['added']}\n"
            f"• Deleted: {stats['deleted']}\n"
            f"• Errors: {stats['errors']}\n\n"
            f"All Firebase data has been synced to Google Sheets.",
            reply_markup=keyboards.get_comparison_keyboard()
        )
        
    elif action == "sync_sh_to_fb":
        await callback.answer("🔄 Syncing Sheets → Firebase...")
        stats = await sheets_manager.sync_sheets_to_firebase()
        
        await callback.message.edit_text(
            f"✅ SHEETS → FIREBASE SYNC COMPLETE\n"
            f"• Updated: {stats['updated']}\n"
            f"• Added: {stats['added']}\n"
            f"• Errors: {stats['errors']}\n\n"
            f"All data from Google Sheets has been synced to Firebase.",
            reply_markup=keyboards.get_comparison_keyboard()
        )
    
    elif action == "export":
        await callback.answer("📥 Generating comparison report...")
        
        try:
            # Get Firebase data
            fb_users = db.get_all_users(role='student')
            
            # Get Sheets data
            sheet_data = await sheets_manager.get_all_users_from_sheets()
            
            # Compare
            fb_ids = {u['user_id'] for u in fb_users}
            sheet_ids = {u['user_id'] for u in sheet_data}
            
            only_fb = fb_ids - sheet_ids
            only_sheet = sheet_ids - fb_ids
            common = fb_ids & sheet_ids
            
            # Check differences in points
            differences = []
            for user_id in common:
                fb_user = next(u for u in fb_users if u['user_id'] == user_id)
                sheet_user = next(u for u in sheet_data if u['user_id'] == user_id)
                
                fb_points = fb_user.get('points', 0)
                sheet_points = sheet_user.get('points', 0)
                
                if fb_points != sheet_points:
                    differences.append({
                        'user_id': user_id,
                        'name': fb_user.get('full_name', 'Unknown'),
                        'fb_points': fb_points,
                        'sheet_points': sheet_points,
                        'diff': fb_points - sheet_points
                    })
            
            # Generate detailed report as JSON
            import json
            report_data = {
                "report_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "statistics": {
                    "total_common": len(common),
                    "only_in_firebase": len(only_fb),
                    "only_in_sheets": len(only_sheet),
                    "point_differences": len(differences)
                },
                "users_only_in_firebase": [
                    {
                        "user_id": uid,
                        "name": next((u['full_name'] for u in fb_users if u['user_id'] == uid), "Unknown"),
                        "points": next((u['points'] for u in fb_users if u['user_id'] == uid), 0)
                    } for uid in only_fb
                ],
                "users_only_in_sheets": [
                    {
                        "user_id": uid,
                        "name": next((u['full_name'] for u in sheet_data if u['user_id'] == uid), "Unknown"),
                        "points": next((u['points'] for u in sheet_data if u['user_id'] == uid), 0)
                    } for uid in only_sheet
                ],
                "point_mismatches": differences
            }
            
            # Save to file
            filename = f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            # Send file
            from aiogram.types import FSInputFile
            await callback.message.answer_document(
                FSInputFile(filename),
                caption=(
                    f"📊 Data Comparison Report\n"
                    f"• Common users: {len(common)}\n"
                    f"• Only in Firebase: {len(only_fb)}\n"
                    f"• Only in Sheets: {len(only_sheet)}\n"
                    f"• Point differences: {len(differences)}"
                )
            )
            
            # Delete temp file
            import os
            os.remove(filename)
            
            await callback.message.edit_text(
                f"✅ Comparison report exported successfully!",
                reply_markup=keyboards.get_comparison_keyboard()
            )
        
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Error exporting comparison report:\n{str(e)}",
                reply_markup=keyboards.get_comparison_keyboard()
            )


@router.callback_query(F.data.startswith("export:"))
async def handle_export(callback: CallbackQuery):
    """Handle data export"""
    format_type = callback.data.split(":")[1]
    
    if format_type == "sheets_copy":
        await callback.answer("🔗 Opening Google Sheets...")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{config.SHEET_ID}"
        await callback.message.edit_text(
            f"📊 GOOGLE SHEETS\n"
            f"Access your data:\n\n"
            f"🔗 {sheet_url}\n\n"
            f"Use File → Make a copy to create your own version.",
            reply_markup=keyboards.get_back_keyboard("settings:export")
        )
        return
    
    await callback.answer(f"📥 Preparing {format_type.upper()} export...")
    
    # Get all users
    users = db.get_all_users(role='student', status='active')
    
    if format_type == "json":
        import json
        data = {
            "export_date": datetime.now().isoformat(),
            "total_students": len(users),
            "students": users
        }
        
        # Save to file
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        # Send file
        from aiogram.types import FSInputFile
        await callback.message.answer_document(
            FSInputFile(filename),
            caption=f"📥 JSON Export\nTotal: {len(users)} students"
        )
        
        # Delete temp file
        import os
        os.remove(filename)
        
        await callback.message.edit_text(
            f"✅ JSON export complete!",
            reply_markup=keyboards.get_back_keyboard("settings:export")
        )
    
    
    elif format_type == "excel":
        from openpyxl import Workbook
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Students"
        
        # Headers
        ws.append(['User ID', 'Full Name', 'Username', 'Phone', 'Points', 'Status'])
        
        # Data
        for user in users:
            ws.append([
                user.get('user_id', ''),
                user.get('full_name', ''),
                user.get('username', ''),
                user.get('phone', ''),
                user.get('points', 0),
                user.get('status', '')
            ])
        
        wb.save(filename)
        
        from aiogram.types import FSInputFile
        await callback.message.answer_document(
            FSInputFile(filename),
            caption=f"📥 Excel Export\nTotal: {len(users)} students"
        )
        
        import os
        os.remove(filename)
        
        await callback.message.edit_text(
            f"✅ Excel export complete!",
            reply_markup=keyboards.get_back_keyboard("settings:export")
        )
    
    elif format_type == "pdf":
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Points Management System - Student Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary
        summary_text = f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Total Students: {len(users)}"
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.3*inch))
        
        # Table data
        data = [['#', 'Name', 'Username', 'Points', 'Status']]
        for idx, user in enumerate(users, 1):
            data.append([
                str(idx),
                user.get('full_name', '')[:20],
                user.get('username', '')[:15],
                str(user.get('points', 0)),
                user.get('status', '')
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        from aiogram.types import FSInputFile
        await callback.message.answer_document(
            FSInputFile(filename),
            caption=f"📥 PDF Report\nTotal: {len(users)} students"
        )
        
        import os
        os.remove(filename)
        
        await callback.message.edit_text(
            f"✅ PDF export complete!",
            reply_markup=keyboards.get_back_keyboard("settings:export")
        )
    

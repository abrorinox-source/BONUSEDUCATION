"""
Middleware for security and access control
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Union
from database import db
import config


class SecurityMiddleware(BaseMiddleware):
    """
    Global security middleware
    Checks user status and maintenance mode before processing
    """
    
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        """Process update through security checks"""
        
        # Get user_id from event
        if isinstance(event, Message):
            user_id = str(event.from_user.id)
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            user_id = str(event.from_user.id)
            chat_id = event.message.chat.id
        else:
            return await handler(event, data)
        
        # Skip checks for /start command
        if isinstance(event, Message) and event.text and event.text.startswith('/start'):
            return await handler(event, data)
        
        # Skip checks if user is in registration flow (FSM state active)
        state = data.get('state')
        if state:
            current_state = await state.get_state()
            if current_state and 'RegistrationStates' in current_state:
                return await handler(event, data)
        
        # Check 1: User exists in database?
        user = db.get_user(user_id)
        
        if not user:
            # User not registered
            if isinstance(event, Message):
                await event.answer("⚠️ You are not registered. Send /start to register.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ You are not registered. Send /start to register.", show_alert=True)
            return
        
        # Check 2: Is user deleted?
        if user.get('status') == 'deleted':
            if isinstance(event, Message):
                await event.answer(config.MESSAGES['user_deleted'])
            elif isinstance(event, CallbackQuery):
                await event.answer(config.MESSAGES['user_deleted'], show_alert=True)
            return
        
        # Check 3: Is user pending approval?
        if user.get('status') == 'pending' and user.get('role') == 'student':
            if isinstance(event, Message):
                await event.answer(config.MESSAGES['registration_pending'])
            elif isinstance(event, CallbackQuery):
                await event.answer(config.MESSAGES['registration_pending'], show_alert=True)
            return
        
        # Check 4: Maintenance mode (block students, allow teachers)
        settings = db.get_settings()
        bot_status = settings.get('bot_status', 'public')
        
        if bot_status == 'maintenance' and user.get('role') != 'teacher':
            maintenance_msg = (
                "🔧 MAINTENANCE MODE\n\n"
                "Bot is currently under maintenance.\n"
                "Only teachers have access.\n\n"
                "Please try again later."
            )
            
            if isinstance(event, Message):
                await event.answer(maintenance_msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(maintenance_msg, show_alert=True)
            return
        
        # Store user data in context for handlers
        data['user'] = user
        data['user_id'] = user_id
        
        # All checks passed - continue to handler
        return await handler(event, data)


class FSMCancelMiddleware(BaseMiddleware):
    """
    Middleware to handle FSM state cancellation when user presses other buttons
    """
    
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        """Clear FSM state if user switches context"""
        
        state = data.get('state')
        
        # If user presses a main menu button while in FSM state, clear the state
        if isinstance(event, Message) and state:
            current_state = await state.get_state()
            
            if current_state and event.text:
                # List of main menu buttons that should cancel FSM
                cancel_buttons = [
                    "Force Sync", "Rating", "Students", "Settings",
                    "My Rank", "Transfer", "History", "Rules", "Support"
                ]
                
                if any(button in event.text for button in cancel_buttons):
                    await state.clear()
                    await event.answer("❌ Previous action cancelled.")
        
        return await handler(event, data)

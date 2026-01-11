"""
Main bot file
Telegram Bot - Points Management System
"""

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

# Import configuration
import config

# Import database and sheets manager
from database import db
from sheets_manager import sheets_manager

# Import middleware
from middleware import SecurityMiddleware, FSMCancelMiddleware

# Import handlers
from handlers import registration, teacher, student

# Import for sync
from sheets_manager import sheets_manager


async def on_startup(bot: Bot):
    """Actions on bot startup"""
    print("🤖 Bot starting...")
    
    # Initialize settings
    settings = db.get_settings()
    print(f"✅ Settings loaded: {settings}")
    
    # Perform initial sync from Sheets to Firebase
    print("🔄 Performing initial sync...")
    await sheets_manager.smart_delta_sync()
    print("✅ Initial sync complete")
    
    # Start background sync task
    if db.is_sync_enabled():
        asyncio.create_task(sheets_manager.background_sync_loop())
        print("✅ Background sync task started")
    
    # Notify teacher (if not silent mode)
    if not config.SILENT_START:
        teachers = db.get_all_users(role='teacher', status='active')
        for teacher in teachers:
            try:
                await bot.send_message(
                    chat_id=teacher['user_id'],
                    text="📢 Bot is now ONLINE and ready to use!"
                )
            except Exception as e:
                print(f"Could not notify teacher {teacher['user_id']}: {e}")
    
    print("✅ Bot startup complete!")


async def on_shutdown(bot: Bot):
    """Actions on bot shutdown"""
    print("🛑 Bot shutting down...")
    
    # Notify teacher
    teachers = db.get_all_users(role='teacher', status='active')
    for teacher in teachers:
        try:
            await bot.send_message(
                chat_id=teacher['user_id'],
                text="⚠️ Bot is going OFFLINE."
            )
        except Exception as e:
            print(f"Could not notify teacher {teacher['user_id']}: {e}")
    
    print("✅ Bot shutdown complete")


async def main():
    """Main function to start the bot"""
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register middleware
    dp.message.middleware(SecurityMiddleware())
    dp.callback_query.middleware(SecurityMiddleware())
    dp.message.middleware(FSMCancelMiddleware())
    
    # Register routers
    dp.include_router(registration.router)
    dp.include_router(teacher.router)
    dp.include_router(student.router)
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    print("=" * 50)
    print("🚀 TELEGRAM BOT - POINTS MANAGEMENT SYSTEM")
    print("=" * 50)
    print(f"Bot Token: {config.BOT_TOKEN[:20]}...")
    print(f"Sheet ID: {config.SHEET_ID}")
    print(f"Silent Start: {config.SILENT_START}")
    print("\n⚡ Polling Optimizations:")
    print("  • Fast polling timeout: 10s (faster response)")
    print("  • Request timeout: 30s (reliable connection)")
    print("=" * 50)
    
    try:
        # OPTIMIZED POLLING - Faster response times
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            polling_timeout=10,  # Check for updates every 10s (default: 30s)
            request_timeout=30,  # Wait max 30s for server response
            handle_signals=True  # Proper shutdown on Ctrl+C
        )
    except KeyboardInterrupt:
        print("\n⚠️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Bot stopped!")

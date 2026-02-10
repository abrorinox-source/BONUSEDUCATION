"""
Main bot file
Telegram Bot - Points Management System
"""

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

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
    
    # Start background sync task
    if db.is_sync_enabled():
        sheets_manager.start_background_sync()
        print("✅ Background sync enabled and started")
    
    print("✅ Bot startup complete!")


async def on_shutdown(bot: Bot):
    """Actions on bot shutdown"""
    print("🛑 Bot shutting down...")
    print("✅ Bot shutdown complete")


async def on_startup_webhook(bot: Bot):
    """Set webhook on startup"""
    await on_startup(bot)
    await bot.set_webhook(
        url=config.WEBHOOK_URL,
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )
    print(f"✅ Webhook set to: {config.WEBHOOK_URL}")


async def on_shutdown_webhook(bot: Bot):
    """Remove webhook on shutdown"""
    await on_shutdown(bot)
    await bot.delete_webhook()
    print("✅ Webhook removed")


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
    
    # Print startup info
    print("=" * 50)
    print("🚀 TELEGRAM BOT - POINTS MANAGEMENT SYSTEM")
    print("=" * 50)
    print(f"Bot Token: {config.BOT_TOKEN[:20]}...")
    print(f"Sheet ID: {config.SHEET_ID}")
    print(f"Silent Start: {config.SILENT_START}")
    print(f"Mode: {'WEBHOOK' if config.USE_WEBHOOK else 'POLLING'}")
    
    if config.USE_WEBHOOK:
        print(f"Webhook URL: {config.WEBHOOK_URL}")
        print(f"Listening on: {config.WEBAPP_HOST}:{config.WEBAPP_PORT}")
    else:
        print("\n⚡ Polling Optimizations:")
        print("  • Fast polling timeout: 10s (faster response)")
        print("  • Request timeout: 30s (reliable connection)")
    print("=" * 50)
    
    try:
        if config.USE_WEBHOOK:
            # WEBHOOK MODE - For production (Render)
            dp.startup.register(on_startup_webhook)
            dp.shutdown.register(on_shutdown_webhook)
            
            # Create aiohttp application
            app = web.Application()
            
            # Setup webhook handler
            webhook_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot
            )
            webhook_handler.register(app, path=config.WEBHOOK_PATH)
            
            # Setup application
            setup_application(app, dp, bot=bot)
            
            # Start web server
            print("🌐 Starting webhook server...")
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(
                runner,
                host=config.WEBAPP_HOST,
                port=config.WEBAPP_PORT
            )
            await site.start()
            print(f"✅ Webhook server started on {config.WEBAPP_HOST}:{config.WEBAPP_PORT}")
            
            # Keep running
            await asyncio.Event().wait()
            
        else:
            # POLLING MODE - For local development
            dp.startup.register(on_startup)
            dp.shutdown.register(on_shutdown)
            
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                polling_timeout=10,
                request_timeout=30,
                handle_signals=True
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

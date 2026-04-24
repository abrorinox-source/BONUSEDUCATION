"""
Launcher for the BonusEducation bot.
"""

import asyncio

from app.main import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nBot stopped!")

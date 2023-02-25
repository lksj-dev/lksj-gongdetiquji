import asyncio
import logging

from . import bot

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(threadName)s/%(levelname)s] [%(name)s]: %(message)s')

bot.run()
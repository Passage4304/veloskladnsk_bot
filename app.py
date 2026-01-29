import os
import logging
import asyncio

from aiogram import Bot, Dispatcher, types

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from handlers.user_private import user_private_router

from middleware.album import AlbumMiddleware

from common.bot_cmds_list import private


logging.basicConfig(level=logging.DEBUG)


bot = Bot(token=os.getenv('TOKEN'))

dp = Dispatcher()

dp.message.middleware(AlbumMiddleware())

dp.include_router(user_private_router)


async def main():
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)

asyncio.run(main())
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardRemove
from typing import Final
from aiogram.fsm.storage.memory import MemoryStorage

import commands

TOKEN : Final = '7827932477:AAEJhhSuRLk11lors5UyGgUYk6ilNMkXxWI'
bot = Bot(token = TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(commands.router)

@dp.message(F.text & ~F.text.startswith("/") & ~F.text.in_(["🇬🇧 English", "🇺🇦 Українська"]))
async def anime_name(message:Message):
    await message.answer(message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
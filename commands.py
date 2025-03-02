from aiogram.filters import CommandStart, Command
from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
import database

lang_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🇬🇧 English"), KeyboardButton(text="🇺🇦 Українська")]
    ],
    resize_keyboard=True
)

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    lang = database.get_language(user_id)

    if lang:
        if lang == "🇬🇧 English":
            await message.answer("Now you can start! Write the name of the anime you want to watch:")
        else:
            await message.answer("Тепер ти можеш почати! Напиши назву аніме, яке хочеш подивитися:")
    else:
        await message.answer("🔹 Choose your language:", reply_markup=lang_keyboard)

@router.message(Command("change_language"))
async def change_language(message: Message):
    user_id = message.from_user.id
    lang = database.get_language(user_id)
    if 'English' in lang:
        await message.answer("🌍 Choose a language", reply_markup=lang_keyboard)
    else:
        await message.answer("🌍 Обери мову:", reply_markup=lang_keyboard)

@router.message(F.text.in_(["🇬🇧 English", "🇺🇦 Українська"]))
async def set_language(message: Message):
    user_id = message.from_user.id
    lang = message.text

    database.save_language(user_id, lang)

    if lang == "🇬🇧 English":
        await message.answer(f"✅ Your language has been changed to: {lang}!", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(f"✅ Твоя мова була змінена на: {lang}!", reply_markup=ReplyKeyboardRemove())
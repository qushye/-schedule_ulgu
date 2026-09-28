import json
import logging
import asyncio
import socket
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from aiogram.client.session.aiohttp import AiohttpSession

from src.config import BOT_TOKEN, USERS_FILE
from src.downloader import download_schedule
from src.parser import get_available_groups, parse_week_schedule
from src.renderer import render_schedule_image
from src.keyboards import get_main_keyboard, get_group_selection_keyboard

# Для Windows включаем стабильный селектор сетевых событий
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Настраиваем сессию на принудительный IPv4 (устраняет ошибку семафора на Windows)
session = AiohttpSession()
session._connector_init["family"] = socket.AF_INET

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

def load_users() -> dict:
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_group(user_id: int, group: str):
    users = load_users()
    users[str(user_id)] = group
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user_group(user_id: int) -> str:
    users = load_users()
    return users.get(str(user_id), "Ст-26/1а")

def get_week_info(offset_weeks=0):
    today = datetime.now() + timedelta(weeks=offset_weeks)
    mon = today - timedelta(days=today.weekday())
    sat = mon + timedelta(days=5)

    # Нечетная неделя = 1, четная = 2
    iso_week = today.isocalendar()[1]
    week_num = 1 if (iso_week % 2 != 0) else 2

    date_range = f"{mon.strftime('%d.%m')} - {sat.strftime('%d.%m')}"
    dates_list = [(mon + timedelta(days=i)).strftime("%d.%m") for i in range(6)]
    return week_num, date_range, dates_list

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    groups = get_available_groups()
    if not groups:
        download_schedule()
        groups = get_available_groups()

    await message.answer(
        "👋 Привет! Выберите вашу подгруппу:",
        reply_markup=get_group_selection_keyboard(groups)
    )

@dp.callback_query(F.data.startswith("setgroup:"))
async def cq_set_group(callback: types.CallbackQuery):
    group = callback.data.split(":")[1]
    save_user_group(callback.from_user.id, group)
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Выбрана группа: <b>{group}</b>\nИспользуйте меню снизу для просмотра:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "👥 Сменить группу")
async def cmd_change_group(message: types.Message):
    groups = get_available_groups()
    await message.answer("Выберите группу:", reply_markup=get_group_selection_keyboard(groups))

@dp.message(F.text == "🔄 Обновить файл")
async def cmd_refresh(message: types.Message):
    await message.answer("⏳ Скачиваю свежий файл из OneDrive...")
    if download_schedule():
        await message.answer("✅ Расписание успешно обновлено!")
    else:
        await message.answer("❌ Не удалось скачать файл из OneDrive.")

@dp.message(F.text.in_(["📅 Текущая неделя", "⏭ Следующая неделя"]))
async def cmd_schedule(message: types.Message):
    group = get_user_group(message.from_user.id)
    offset = 0 if message.text == "📅 Текущая неделя" else 1
    week_num, date_range, dates_list = get_week_info(offset_weeks=offset)

    await message.answer("⏳ Генерирую расписание...")

    data = parse_week_schedule(group, week_num)
    if not data:
        await message.answer("❌ Не найдены данные для вашей группы.")
        return

    img_path = render_schedule_image(group, week_num, data, date_range, dates_list)
    await message.answer_photo(
        photo=FSInputFile(img_path),
        caption=f"Расписание для {group} ({date_range})"
    )

async def main():
    logging.info("Инициализация: скачиваем файл расписания...")
    download_schedule()
    logging.info("Бот готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
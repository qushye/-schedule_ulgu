import os
import json
import logging
import asyncio
import sys
import time
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from src.config import BOT_TOKEN, USERS_FILE
from src.downloader import download_schedule
from src.parser import get_available_groups, parse_week_schedule
from src.renderer import render_schedule_image
from src.keyboards import (
    get_main_keyboard,
    get_course_selection_keyboard,
    get_group_selection_keyboard,
    get_theme_keyboard,
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.WARNING)

api_server = TelegramAPIServer.from_base("https://tg-proxy.kairagleb1910.workers.dev")
session = AiohttpSession(api=api_server)

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

user_cooldowns = {}

def log_activity(text: str):
    """Выводит действие в консоль и сохраняет в data/activity.txt"""
    print(text)
    with open("data/activity.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

async def auto_update_loop():
    while True:
        await asyncio.sleep(4 * 3600)
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(f"\n[{now}] ⏳ Фоновое обновление: скачиваем файлы из OneDrive...")
        if download_schedule():
            print(f"[{now}] ✅ Все файлы расписания успешно обновлены!\n")
        else:
            print(f"[{now}] ⚠️ Часть файлов не обновилась, используем локальные копии.\n")

def load_users() -> dict:
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user_settings(user_id: int) -> dict:
    users = load_users()
    data = users.get(str(user_id), {})
    if isinstance(data, str):
        return {"course": 1, "group": data, "theme": "dark"}
    return {
        "course": int(data.get("course", 1)),
        "group": data.get("group", "Ст-26/1а"),
        "theme": data.get("theme", "dark")
    }

def update_user_setting(user_id: int, key: str, value):
    users = load_users()
    uid = str(user_id)
    if uid not in users or isinstance(users[uid], str):
        current_group = users.get(uid, "Ст-26/1а") if isinstance(users.get(uid), str) else "Ст-26/1а"
        users[uid] = {"course": 1, "group": current_group, "theme": "dark"}
    users[uid][key] = value
    save_users(users)

def get_week_info(offset_weeks=0):
    today = datetime.now() + timedelta(weeks=offset_weeks)
    mon = today - timedelta(days=today.weekday())
    sat = mon + timedelta(days=5)

    iso_week = today.isocalendar()[1]
    week_num = 2 if (iso_week % 2 != 0) else 1

    date_range = f"{mon.strftime('%d.%m')} - {sat.strftime('%d.%m')}"
    dates_list = [(mon + timedelta(days=i)).strftime("%d.%m") for i in range(6)]
    return week_num, date_range, dates_list

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        "Добро пожаловать в бота расписания занятий 🎓\n\n"
        "📌 <b>Возможности:</b>\n"
        "• <b>📅 Текущая неделя</b> — пары на эту неделю\n"
        "• <b>⏭ Следующая неделя</b> — пары на следующую неделю\n"
        "• <b>🎨 Сменить тему</b> — переключение между 🌙 тёмной и ☀️ светлой темами\n"
        "• <b>👥 Сменить группу</b> — выбор курса и подгруппы\n\n"
        "👇 <i>Для начала работы выберите ваш курс:</i>"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_course_selection_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "👥 Сменить группу")
async def cmd_change_group(message: types.Message):
    await message.answer("Выберите ваш курс:", reply_markup=get_course_selection_keyboard())

@dp.callback_query(F.data == "back_to_courses")
async def cq_back_to_courses(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите ваш курс:",
        reply_markup=get_course_selection_keyboard()
    )

@dp.callback_query(F.data.startswith("setcourse:"))
async def cq_set_course(callback: types.CallbackQuery):
    course = int(callback.data.split(":")[1])
    groups = get_available_groups(course)
    if not groups:
        download_schedule()
        groups = get_available_groups(course)

    await callback.message.edit_text(
        f"🎓 Выбран <b>{course} курс</b>.\nТеперь выберите вашу подгруппу:",
        reply_markup=get_group_selection_keyboard(groups, course=course),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("setgroup:"))
async def cq_set_group(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) == 3:
        course = int(parts[1])
        group = parts[2]
    else:
        course = 1
        group = parts[1]

    update_user_setting(callback.from_user.id, "course", course)
    update_user_setting(callback.from_user.id, "group", group)

    now = datetime.now().strftime("%d.%m %H:%M")
    tag = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
    log_activity(f"[{now}] 👥 {callback.from_user.first_name} ({tag}) -> выбрал(а): {course} курс, {group}")

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Выбрана группа: <b>{group} ({course} курс)</b>\nИспользуйте меню снизу для просмотра:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "🎨 Сменить тему")
async def cmd_change_theme(message: types.Message):
    current_theme = get_user_settings(message.from_user.id)["theme"]
    name = "🌙 Тёмная" if current_theme == "dark" else "☀️ Светлая"
    await message.answer(
        f"Текущая тема: <b>{name}</b>\nВыберите тему оформления таблицы:",
        reply_markup=get_theme_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("settheme:"))
async def cq_set_theme(callback: types.CallbackQuery):
    theme = callback.data.split(":")[1]
    update_user_setting(callback.from_user.id, "theme", theme)
    name = "🌙 Тёмная" if theme == "dark" else "☀️ Светлая"

    now = datetime.now().strftime("%d.%m %H:%M")
    tag = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
    log_activity(f"[{now}] 🎨 {callback.from_user.first_name} ({tag}) -> сменил(а) тему на: {name}")

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Тема изменена на: <b>{name}</b>!\nТеперь расписание будет формироваться в этом стиле.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text == "🔄 Обновить файл")
async def cmd_refresh(message: types.Message):
    await message.answer("⏳ Скачиваю свежие файлы расписания (1, 2, 3 курс) из OneDrive...")
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    print(f"[{now}] 🔄 Запрос на ручное обновление расписания из Telegram...")

    if download_schedule():
        print(f"[{now}] ✅ Все файлы успешно обновлены!\n")
        await message.answer("✅ Расписание всех курсов успешно обновлено!")
    else:
        print(f"[{now}] ⚠️ Часть файлов не обновилась.\n")
        await message.answer("✅ Доступные файлы обновлены!")

@dp.message(F.text.in_(["📅 Текущая неделя", "⏭ Следующая неделя"]))
async def cmd_schedule(message: types.Message):
    user_id = message.from_user.id
    now_ts = time.time()

    if now_ts - user_cooldowns.get(user_id, 0) < 4:
        await message.answer("⏳ Подождите пару секунд, картинка уже генерируется...")
        return
    user_cooldowns[user_id] = now_ts

    settings = get_user_settings(user_id)
    course = settings["course"]
    group = settings["group"]
    theme = settings["theme"]

    offset = 0 if message.text == "📅 Текущая неделя" else 1
    week_num, date_range, dates_list = get_week_info(offset_weeks=offset)

    await message.answer("⏳ Генерирую расписание...")

    data = parse_week_schedule(group, week_num, course=course)
    if not data:
        await message.answer("❌ Не найдены данные для вашей группы. Попробуйте нажать «👥 Сменить группу».")
        return

    img_path = render_schedule_image(group, week_num, data, date_range, dates_list, theme=theme)
    await message.answer_photo(
        photo=FSInputFile(img_path),
        caption=f"Расписание для {group} ({course} курс, {date_range})"
    )

    tag = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    log_activity(f"[{datetime.now().strftime('%d.%m %H:%M')}] 👤 {message.from_user.first_name} ({tag}) | {course}к {group} | {message.text}")

async def main():
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    print(f"[{now}] 🚀 Запуск бота. Скачиваем расписание 1, 2 и 3 курсов...")

    download_schedule()
    asyncio.create_task(auto_update_loop())

    print(f"[{now}] 🤖 Бот успешно запущен и ожидает сообщений!")
    print("=" * 60 + "\n")

    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
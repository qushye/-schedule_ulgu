import os
import json
import logging
import asyncio
import sys
import time
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from src.config import BOT_TOKEN, USERS_FILE, DATA_DIR
from src.downloader import download_schedule
from src.parser import get_available_groups, parse_week_schedule
from src.renderer import render_schedule_image
from src.keyboards import (
    get_main_keyboard,
    get_profile_keyboard,
    get_course_selection_keyboard,
    get_group_selection_keyboard,
    get_theme_keyboard,
)

# Безопасный парсинг ADMIN_ID (защита от пустой строки в .env)
raw_admin_id = os.getenv("ADMIN_ID", "1433828029")
ADMIN_ID = int(raw_admin_id) if raw_admin_id and raw_admin_id.strip().isdigit() else 1433828029

ACTIVITY_LOG_FILE = DATA_DIR / "activity.txt"

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.WARNING)

api_server = TelegramAPIServer.from_base("https://tg-proxy.kairagleb1910.workers.dev")
session = AiohttpSession(api=api_server)

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

user_cooldowns = {}

def log_activity(text: str):
    """Выводит действие в консоль и сохраняет по надежному пути DATA_DIR"""
    print(text)
    try:
        with open(ACTIVITY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception as e:
        logging.error(f"Не удалось записать лог активности: {e}")

async def auto_update_loop():
    """Фоновое обновление файлов всех курсов каждые 4 часа"""
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

def update_user_settings_bulk(user_id: int, updates: dict):
    """Обновляет сразу несколько настроек за одну запись на диск"""
    users = load_users()
    uid = str(user_id)
    if uid not in users or isinstance(users[uid], str):
        current_group = users.get(uid, "Ст-26/1а") if isinstance(users.get(uid), str) else "Ст-26/1а"
        users[uid] = {"course": 1, "group": current_group, "theme": "dark"}
    users[uid].update(updates)
    save_users(users)

def is_user_registered(user_id: int) -> bool:
    users = load_users()
    return str(user_id) in users

def get_week_info(offset_weeks=0):
    today = datetime.now() + timedelta(weeks=offset_weeks)
    mon = today - timedelta(days=today.weekday())
    sat = mon + timedelta(days=5)

    iso_week = today.isocalendar()[1]
    week_num = 2 if (iso_week % 2 != 0) else 1

    date_range = f"{mon.strftime('%d.%m')} - {sat.strftime('%d.%m')}"
    dates_list = [(mon + timedelta(days=i)).strftime("%d.%m") for i in range(6)]
    return week_num, date_range, dates_list

def build_profile_text(settings: dict) -> str:
    theme_title = "🌙 Тёмная" if settings["theme"] == "dark" else "☀️ Светлая"
    return (
        f"👤 <b>Ваш профиль:</b>\n"
        f"• Курс: <b>{settings['course']} курс</b>\n"
        f"• Группа: <b>{settings['group']}</b>\n"
        f"• Тема оформления: <b>{theme_title}</b>\n\n"
        f"<i>Что хотите настроить?</i>"
    )

# ================= ХЭНДЛЕРЫ =================

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    if is_user_registered(user_id):
        settings = get_user_settings(user_id)
        await message.answer(
            f"👋 <b>С возвращением, {message.from_user.first_name}!</b>\n\n"
            f"Ваш профиль: <b>{settings['course']} курс, группа {settings['group']}</b>.\n"
            f"Используйте кнопки ниже для просмотра расписания:",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        welcome_text = (
            f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
            "Добро пожаловать в бота расписания занятий 🎓\n\n"
            "Для начала работы выберите ваш курс:"
        )
        await message.answer(
            welcome_text,
            reply_markup=get_course_selection_keyboard(show_back_to_profile=False),
            parse_mode="HTML"
        )

@dp.message(F.text == "⚙️ Мой профиль и настройки")
async def cmd_profile(message: types.Message):
    settings = get_user_settings(message.from_user.id)
    await message.answer(
        build_profile_text(settings),
        reply_markup=get_profile_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "back_to_profile")
async def cq_back_to_profile(callback: types.CallbackQuery):
    await callback.answer()
    settings = get_user_settings(callback.from_user.id)
    await callback.message.edit_text(
        build_profile_text(settings),
        reply_markup=get_profile_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "change_course_group")
async def cq_change_course_group(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Выберите курс:",
        reply_markup=get_course_selection_keyboard(show_back_to_profile=True)
    )

@dp.callback_query(F.data == "change_theme")
async def cq_change_theme(callback: types.CallbackQuery):
    await callback.answer()
    settings = get_user_settings(callback.from_user.id)
    current = "🌙 Тёмная" if settings["theme"] == "dark" else "☀️ Светлая"
    await callback.message.edit_text(
        f"Текущая тема: <b>{current}</b>\nВыберите тему оформления таблицы:",
        reply_markup=get_theme_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "back_to_courses")
async def cq_back_to_courses(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Выберите курс:",
        reply_markup=get_course_selection_keyboard(show_back_to_profile=True)
    )

@dp.callback_query(F.data.startswith("setcourse:"))
async def cq_set_course(callback: types.CallbackQuery):
    await callback.answer()
    course = int(callback.data.split(":")[1])
    groups = get_available_groups(course)
    if not groups:
        download_schedule()
        groups = get_available_groups(course)

    if not groups:
        await callback.message.edit_text(
            f"❌ Не удалось загрузить группы {course} курса. Попробуйте позже.",
            reply_markup=get_course_selection_keyboard(show_back_to_profile=True)
        )
        return

    await callback.message.edit_text(
        f"🎓 Выбран <b>{course} курс</b>.\nВыберите вашу подгруппу:",
        reply_markup=get_group_selection_keyboard(groups, course=course),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("setgroup:"))
async def cq_set_group(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split(":")
    course = int(parts[1]) if len(parts) == 3 else 1
    group = parts[2] if len(parts) == 3 else parts[1]

    # Пакетное сохранение курса и группы за одну операцию ввода-вывода
    update_user_settings_bulk(callback.from_user.id, {"course": course, "group": group})

    now = datetime.now().strftime("%d.%m %H:%M")
    tag = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
    log_activity(f"[{now}] 👥 {callback.from_user.first_name} ({tag}) -> выбрал: {course} курс, {group}")

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Сохранено: <b>{course} курс, группа {group}</b>\n"
        f"Используйте меню снизу для просмотра расписания:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("settheme:"))
async def cq_set_theme(callback: types.CallbackQuery):
    await callback.answer()
    theme = callback.data.split(":")[1]
    update_user_settings_bulk(callback.from_user.id, {"theme": theme})
    name = "🌙 Тёмная" if theme == "dark" else "☀️ Светлая"

    now = datetime.now().strftime("%d.%m %H:%M")
    tag = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
    log_activity(f"[{now}] 🎨 {callback.from_user.first_name} ({tag}) -> сменил тему: {name}")

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Тема изменена на: <b>{name}</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(Command("update"))
async def cmd_admin_update(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("⏳ Обновляю файлы 1, 2 и 3 курса из OneDrive...")
    if download_schedule():
        await message.answer("✅ Таблицы всех курсов успешно скачаны и обновлены!")
    else:
        await message.answer("⚠️ Не все файлы удалось скачать, проверьте логи сервера.")

@dp.message(F.text.in_(["📅 Текущая неделя", "⏭ Следующая неделя"]))
async def cmd_schedule(message: types.Message):
    user_id = message.from_user.id
    now_ts = time.time()

    if now_ts - user_cooldowns.get(user_id, 0) < 4:
        await message.answer("⏳ Подождите пару секунд, картинка уже формируется...")
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
        await message.answer("❌ Не найдены данные для вашей группы. Проверьте настройки в «⚙️ Мой профиль и настройки».")
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
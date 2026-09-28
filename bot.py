import os
import time
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
from src.keyboards import get_main_keyboard, get_group_selection_keyboard, get_theme_keyboard


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Словарь для защиты от спама: {user_id: timestamp}
user_cooldowns = {}
# Отключаем лишний мусор из логов, чтобы в консоли всё было чисто
logging.basicConfig(level=logging.WARNING)

session = AiohttpSession()
session._connector_init["family"] = socket.AF_INET

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()


# Фоновое обновление каждые 4 часа с выводом в консоль PyCharm
async def auto_update_loop():
    while True:
        await asyncio.sleep(4 * 3600)  # Ждем 4 часа

        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(f"\n[{now}] ⏳ Фоновое обновление: скачиваем файл из OneDrive...")

        if download_schedule():
            print(f"[{now}] ✅ Файл расписания успешно обновлен из OneDrive!\n")
        else:
            print(f"[{now}] ❌ Ошибка: не удалось скачать файл из OneDrive!\n")


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
        return {"group": data, "theme": "dark"}
    return {
        "group": data.get("group", "Ст-26/1а"),
        "theme": data.get("theme", "dark")
    }


def update_user_setting(user_id: int, key: str, value: str):
    users = load_users()
    uid = str(user_id)
    if uid not in users or isinstance(users[uid], str):
        current_group = users.get(uid, "Ст-26/1а") if isinstance(users.get(uid), str) else "Ст-26/1а"
        users[uid] = {"group": current_group, "theme": "dark"}
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
    update_user_setting(callback.from_user.id, "group", group)
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
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Тема изменена на: <b>{name}</b>!\nТеперь расписание будет формироваться в этом стиле.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@dp.message(F.text == "🔄 Обновить файл")
async def cmd_refresh(message: types.Message):
    await message.answer("⏳ Скачиваю свежий файл из OneDrive...")
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    print(f"[{now}] 🔄 Запрос на ручное обновление расписания из Telegram...")

    if download_schedule():
        print(f"[{now}] ✅ Файл успешно обновлен!\n")
        await message.answer("✅ Расписание успешно обновлено!")
    else:
        print(f"[{now}] ❌ Ошибка: не удалось скачать файл!\n")
        await message.answer("❌ Не удалось скачать файл из OneDrive.")


@dp.message(F.text.in_(["📅 Текущая неделя", "⏭ Следующая неделя"]))
async def cmd_schedule(message: types.Message):
    # --- ЗАЩИТА ОТ СПАМА (КУЛДАУН 4 СЕКУНДЫ) ---
    user_id = message.from_user.id
    now = time.time()

    if now - user_cooldowns.get(user_id, 0) < 4:
        # Если кликает слишком часто — просто мягко предупреждаем и выходим
        await message.answer("⏳ Подождите пару секунд, картинка уже генерируется...")
        return

    user_cooldowns[user_id] = now
    # --------------------------------------------

    settings = get_user_settings(message.from_user.id)
    group = settings["group"]
    theme = settings["theme"]

    offset = 0 if message.text == "📅 Текущая неделя" else 1
    week_num, date_range, dates_list = get_week_info(offset_weeks=offset)

    await message.answer("⏳ Генерирую расписание...")

    data = parse_week_schedule(group, week_num)
    if not data:
        await message.answer("❌ Не найдены данные для вашей группы.")
        return

    img_path = render_schedule_image(group, week_num, data, date_range, dates_list, theme=theme)
    await message.answer_photo(
        photo=FSInputFile(img_path),
        caption=f"Расписание для {group} ({date_range})"
    )


async def main():
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    print(f"[{now}] 🚀 Запуск бота. Скачиваем актуальное расписание...")

    if download_schedule():
        print(f"[{now}] ✅ Файл расписания успешно скачан!")
    else:
        print(f"[{now}] ⚠️ Используем имеющуюся локальную копию schedule.xlsx")

    # Фоновая задача обновления каждые 4 часа
    asyncio.create_task(auto_update_loop())

    print(f"[{now}] 🤖 Бот успешно запущен и ожидает сообщений!")
    print("=" * 60 + "\n")

    await dp.start_polling(bot, drop_pending_updates=True)



if __name__ == "__main__":
    asyncio.run(main())
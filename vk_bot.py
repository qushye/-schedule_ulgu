import os
import json
import logging
import asyncio
import time
from datetime import datetime, timedelta

from vkbottle.bot import Bot, Message
from vkbottle import PhotoMessageUploader

from src.config import VK_TOKEN, VK_USERS_FILE, DATA_DIR
from src.downloader import download_schedule
from src.parser import get_available_groups, parse_week_schedule
from src.renderer import render_schedule_image
from src.vk_keyboards import (
    get_vk_main_keyboard,
    get_vk_profile_keyboard,
    get_vk_course_keyboard,
    get_vk_group_keyboard,
    get_vk_theme_keyboard,
)

if not VK_TOKEN:
    raise ValueError("VK_TOKEN не найден в .env! Укажите токен группы ВК.")

logging.basicConfig(level=logging.WARNING)

bot = Bot(token=VK_TOKEN)
uploader = PhotoMessageUploader(bot.api)

user_cooldowns = {}
ACTIVITY_LOG_FILE = DATA_DIR / "vk_activity.txt"

def log_vk_activity(text: str):
    print(text)
    try:
        with open(ACTIVITY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception as e:
        logging.error(f"Не удалось записать VK лог: {e}")

def load_vk_users() -> dict:
    if VK_USERS_FILE.exists():
        with open(VK_USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_vk_users(users: dict):
    with open(VK_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_vk_user_settings(user_id: int) -> dict:
    users = load_vk_users()
    data = users.get(str(user_id), {})
    return {
        "course": int(data.get("course", 1)),
        "group": data.get("group", "Ст-26/1а"),
        "theme": data.get("theme", "light")
    }

def update_vk_user_settings(user_id: int, updates: dict):
    users = load_vk_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"course": 1, "group": "Ст-26/1а", "theme": "light"}
    users[uid].update(updates)
    save_vk_users(users)

def is_vk_user_registered(user_id: int) -> bool:
    users = load_vk_users()
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

def build_vk_profile_text(settings: dict) -> str:
    theme_title = "🌙 Тёмная" if settings["theme"] == "dark" else "☀️ Светлая"
    return (
        f"👤 Ваш профиль:\n"
        f"• Курс: {settings['course']} курс\n"
        f"• Группа: {settings['group']}\n"
        f"• Тема оформления: {theme_title}\n\n"
        f"Что хотите настроить?"
    )

def extract_payload(message: Message) -> dict:
    """Безопасно извлекает payload в любом виде (dict или json-string)"""
    payload = message.payload
    if not payload:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return {}
    return {}

async def upload_vk_photo_safe(img_path: str, peer_id: int):
    """Безопасная загрузка фото в ВК: передаёт байты и делает до 3 попыток при сбоях серверов ВК"""
    for attempt in range(3):
        try:
            with open(img_path, "rb") as f:
                photo_bytes = f.read()
            return await uploader.upload(photo_bytes, peer_id=peer_id)
        except Exception as e:
            logging.warning(f"Попытка {attempt + 1} загрузки в ВК не удалась: {e}")
            await asyncio.sleep(0.4)
    return None

# ================= ХЭНДЛЕРЫ ВК =================

@bot.on.message(text=["Начать", "начать", "Start", "start", "/start"])
async def vk_start_handler(message: Message):
    user_id = message.from_id

    if is_vk_user_registered(user_id):
        settings = get_vk_user_settings(user_id)
        await message.answer(
            f"👋 С возвращением!\n\n"
            f"Ваш профиль: {settings['course']} курс, группа {settings['group']}.\n"
            f"Используйте кнопки ниже для просмотра расписания:",
            keyboard=get_vk_main_keyboard()
        )
    else:
        await message.answer(
            "👋 Привет! Добро пожаловать в бота расписания занятий 🎓\n\n"
            "Для начала работы выберите ваш курс:",
            keyboard=get_vk_course_keyboard()
        )

@bot.on.message(text=["⚙️ Мой профиль и настройки", "Профиль", "профиль", "Настройки", "настройки"])
async def vk_profile_handler(message: Message):
    settings = get_vk_user_settings(message.from_id)
    await message.answer(
        build_vk_profile_text(settings),
        keyboard=get_vk_profile_keyboard()
    )

@bot.on.message()
async def vk_payload_router(message: Message):
    data = extract_payload(message)
    user_id = message.from_id

    # Если нажали обычную текстовую кнопку снизу (расписание)
    if not data:
        return await vk_text_fallback(message)

    # 1. Нажата "🎓 Сменить курс и группу"
    if data.get("action") == "change_course":
        return await message.answer("Выберите ваш курс:", keyboard=get_vk_course_keyboard())

    # 2. Возврат в главное меню из выбора курса
    if data.get("action") == "back_to_main":
        return await message.answer("Главное меню:", keyboard=get_vk_main_keyboard())

    # 3. Нажата "🎨 Сменить тему"
    if data.get("action") == "change_theme":
        settings = get_vk_user_settings(user_id)
        current = "🌙 Тёмная" if settings["theme"] == "dark" else "☀️ Светлая"
        return await message.answer(
            f"Текущая тема: {current}\nВыберите тему оформления таблицы:",
            keyboard=get_vk_theme_keyboard()
        )

    # 4. Нажата "⬅️ Назад в профиль"
    if data.get("action") == "back_to_profile":
        settings = get_vk_user_settings(user_id)
        return await message.answer(build_vk_profile_text(settings), keyboard=get_vk_profile_keyboard())

    # 5. Выбран курс
    if "course" in data:
        course = int(data["course"])
        groups = get_available_groups(course)
        if not groups:
            download_schedule()
            groups = get_available_groups(course)

        if not groups:
            return await message.answer(f"❌ Не удалось найти группы для {course} курса.", keyboard=get_vk_course_keyboard())

        return await message.answer(
            f"🎓 Выбран {course} курс.\nВыберите вашу подгруппу:",
            keyboard=get_vk_group_keyboard(groups, course=course)
        )

    # 6. Выбрана конкретная группа
    if "set_group" in data:
        course = int(data.get("set_course", 1))
        group = data["set_group"]
        update_vk_user_settings(user_id, {"course": course, "group": group})

        now = datetime.now().strftime("%d.%m %H:%M")
        log_vk_activity(f"[{now}] 👥 VK id{user_id} -> выбрал: {course} курс, {group}")

        return await message.answer(
            f"✅ Сохранено: {course} курс, группа {group}\n"
            f"Используйте кнопки снизу для просмотра расписания:",
            keyboard=get_vk_main_keyboard()
        )

    # 7. Выбрана тема
    if "set_theme" in data:
        theme = data["set_theme"]
        update_vk_user_settings(user_id, {"theme": theme})
        name = "🌙 Тёмная" if theme == "dark" else "☀️ Светлая"

        now = datetime.now().strftime("%d.%m %H:%M")
        log_vk_activity(f"[{now}] 🎨 VK id{user_id} -> сменил тему: {name}")

        return await message.answer(f"✅ Тема изменена на: {name}", keyboard=get_vk_main_keyboard())

async def vk_text_fallback(message: Message):
    text = (message.text or "").strip()

    if text not in ["📅 Текущая неделя", "⏭ Следующая неделя"]:
        return

    user_id = message.from_id

    if not is_vk_user_registered(user_id):
        return await message.answer(
            "👋 Вы ещё не выбрали свой курс и группу!\nПожалуйста, выберите ваш курс:",
            keyboard=get_vk_course_keyboard()
        )

    start_time = time.time()

    now_ts = time.time()
    if now_ts - user_cooldowns.get(user_id, 0) < 4:
        return await message.answer("⏳ Подождите пару секунд, картинка уже формируется...")
    user_cooldowns[user_id] = now_ts

    settings = get_vk_user_settings(user_id)
    course = settings["course"]
    group = settings["group"]
    theme = settings["theme"]

    offset = 0 if text == "📅 Текущая неделя" else 1
    week_num, date_range, dates_list = get_week_info(offset_weeks=offset)

    data = parse_week_schedule(group, week_num, course=course)
    if not data:
        return await message.answer("❌ Не найдены данные для вашей группы. Проверьте настройки в профиле.")

    img_path = render_schedule_image(group, week_num, data, date_range, dates_list, theme=theme)

    photo = await upload_vk_photo_safe(img_path, peer_id=message.peer_id)
    if not photo:
        return await message.answer(
            "⚠️ Временный сбой серверов ВКонтакте при загрузке фото. Пожалуйста, нажмите кнопку ещё раз.",
            keyboard=get_vk_main_keyboard()
        )

    await message.answer(
        message=f"Расписание для {group} ({course} курс, {date_range})",
        attachment=photo,
        keyboard=get_vk_main_keyboard()
    )

    elapsed = round(time.time() - start_time, 2)
    now_str = datetime.now().strftime("%d.%m %H:%M:%S")
    log_vk_activity(f"[{now_str}] 👤 VK id{user_id} | {course}к {group} | {text} (⏱ {elapsed} сек)")

if __name__ == "__main__":
    print("⏳ Проверяем файлы расписания...")
    download_schedule()
    print("🤖 ВК-бот запущен и ожидает сообщений!")
    bot.run()
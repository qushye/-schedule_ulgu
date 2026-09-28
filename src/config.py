import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ONEDRIVE_URL = os.getenv("ONEDRIVE_URL")

EXCEL_PATH = DATA_DIR / "schedule.xlsx"
USERS_FILE = DATA_DIR / "users.json"

LESSON_TIMES = [
    (1, "8:00-9:20"),
    (2, "9:30-10:50"),
    (3, "11:00-12:20"),
    (4, "12:45-14:05"),
    (5, "14:15-15:35"),
    (6, "15:45-17:00"),
    (7, "17:10-18:30"),
    (8, "18:40-20:05"),
]

DAYS_CONFIG = [
    ("Понедельник", "Пн", 2),
    ("Вторник", "Вт", 10),
    ("Среда", "Ср", 18),
    ("Четверг", "Чт", 26),
    ("Пятница", "Пт", 34),
    ("Суббота", "Сб", 42),
]
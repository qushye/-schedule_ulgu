import logging
import requests
from pathlib import Path
from src.config import COURSES

logger = logging.getLogger(__name__)

def download_single_file(url: str, output_path: Path) -> bool:
    try:
        download_url = url.replace("?e=", "?download=1&e=")
        if "download=1" not in download_url:
            download_url += "&download=1" if "?" in download_url else "?download=1"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        res = requests.get(download_url, headers=headers, allow_redirects=True, timeout=25)

        if res.status_code == 200 and res.content.startswith(b"PK\x03\x04"):
            with open(output_path, "wb") as f:
                f.write(res.content)
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при скачивании {output_path.name}: {e}")
        return False

def download_schedule() -> bool:
    """Скачивает расписание для всех курсов (1, 2, 3)"""
    all_ok = True
    for course_num, info in COURSES.items():
        ok = download_single_file(info["url"], info["path"])
        if ok:
            logger.info(f"Расписание {course_num} курса успешно скачано!")
        else:
            logger.warning(f"Не удалось обновить {course_num} курс, используем локальную копию.")
            all_ok = False
    return all_ok
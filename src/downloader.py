import logging
import requests
from src.config import ONEDRIVE_URL, EXCEL_PATH

logger = logging.getLogger(__name__)


def download_schedule() -> bool:
    try:
        # Прямая ссылка на скачивание для OneDrive Consumer (заменяем параметры на принудительную отдачу)
        download_url = ONEDRIVE_URL.replace("?e=", "?download=1&e=")
        if "download=1" not in download_url:
            download_url += "&download=1" if "?" in download_url else "?download=1"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        res = requests.get(download_url, headers=headers, allow_redirects=True, timeout=25)

        # Проверяем сигнатуру настоящего ZIP/XLSX файла (первые 4 байта: 'PK\x03\x04')
        if res.status_code == 200 and res.content.startswith(b"PK\x03\x04"):
            with open(EXCEL_PATH, "wb") as f:
                f.write(res.content)
            logger.info("Настоящий Excel-файл успешно скачан из OneDrive!")
            return True
        else:
            logger.warning("OneDrive вернул не Excel-файл (вероятно, веб-интерфейс). Используем локальную копию.")
            return False

    except Exception as e:
        logger.error(f"Исключение при скачивании из OneDrive: {e}")
        return False
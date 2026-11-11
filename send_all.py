import json
import asyncio
import sys
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from src.config import BOT_TOKEN, USERS_FILE

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Твой текст сообщения:
TEXT = (
    "Дорогие ребята, я залил бота на хостинг и теперь он доступен КРУГЛОСУТОЧНО (УРАААА) 🎉\n\n"
    "Пожалуйста, делитесь ботом с другими группами, чтобы бот развивался (несмотря на то что у вас есть личный кабинет) 🚀"
)

async def main():
    api_server = TelegramAPIServer.from_base("https://tg-proxy.kairagleb1910.workers.dev")
    session = AiohttpSession(api=api_server)
    bot = Bot(token=BOT_TOKEN, session=session)

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)

    print(f"📢 Начинаем рассылку для {len(users)} человек...\n")

    count = 0
    for user_id in users.keys():
        try:
            await bot.send_message(user_id, TEXT)
            print(f"✅ Отправлено: {user_id}")
            count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"❌ Не доставлено {user_id}: {e}")

    await bot.session.close()
    print(f"\n🎉 Готово! Успешно доставлено: {count} из {len(users)}")

if __name__ == "__main__":
    asyncio.run(main())
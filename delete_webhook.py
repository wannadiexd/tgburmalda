import asyncio
from aiogram import Bot
from config import TOKEN

async def delete_webhook():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook удалён! Теперь можно запускать бота локально.")
    await bot.session.close()

if __name__ == '__main__':
    asyncio.run(delete_webhook())

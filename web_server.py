"""
Простой веб-сервер для поддержания бота активным на Render
"""
from aiohttp import web
import asyncio
import logging

logger = logging.getLogger(__name__)

async def health_check(request):
    """Endpoint для проверки состояния бота"""
    return web.Response(text="Bot is running! 🎰", status=200)

async def start_web_server(port=8080):
    """Запуск веб-сервера"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 Веб-сервер запущен на порту {port}")
    
    return runner

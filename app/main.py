import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.bot.instance import bot, dp
from app.scheduler import start_scheduler
from app.dashboard import router as dashboard_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("sogo.main")

polling_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SOGO Style Sentinel...")
    start_scheduler()

    global polling_task
    if settings.use_webhook:
        webhook_url = f"{settings.webhook_base_url.rstrip('/')}/telegram/webhook/{settings.webhook_secret}"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("Webhook set to %s", webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        polling_task = asyncio.create_task(dp.start_polling(bot))
        logger.info("Started polling mode")

    yield

    if polling_task:
        polling_task.cancel()
    await bot.session.close()


app = FastAPI(title="SOGO Style Sentinel", lifespan=lifespan)
app.include_router(dashboard_router, prefix="/dashboard")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != settings.webhook_secret:
        return JSONResponse({"error": "invalid secret"}, status_code=403)
    update_data = await request.json()
    from aiogram.types import Update
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

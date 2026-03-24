# main.py
import logging
import asyncio
import os
from schools.config import SCHOOL_CONFIGS, SchoolConfig
from schools.rollcall import handle_rollcall

logger = logging.getLogger(__name__)


def build_bot_app(active: asyncio.Event):
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        return None

    from telegram.ext import Application, CommandHandler

    app = Application.builder().token(token).build()

    async def cmd_start(update, context):
        active.set()
        await update.message.reply_text("已開始監聽點名")

    async def cmd_stop(update, context):
        active.clear()
        await update.message.reply_text("已暫停監聽點名")

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    return app


async def rollcall_loop(config: SchoolConfig, session, active: asyncio.Event) -> None:
    while True:
        await active.wait()
        await handle_rollcall(
            auth_session=session,
            endpoint=config.endpoint,
            latitude=config.latitude,
            longitude=config.longitude,
        )


async def main() -> None:
    school_key = "tku"
    config: SchoolConfig | None = SCHOOL_CONFIGS.get(school_key)
    if config is None:
        logger.error("Unsupported school: %s", school_key)
        return

    session = await config.auth_func()
    logger.info("Authenticated session for school: %s", school_key)

    if not config.endpoint:
        logger.info("School %s has no rollcall endpoint configured.", school_key)
        return

    active = asyncio.Event()
    active.set()

    bot_app = build_bot_app(active)

    if bot_app:
        async with bot_app:
            await bot_app.start()
            await bot_app.updater.start_polling()
            await rollcall_loop(config, session, active)
            await bot_app.updater.stop()
            await bot_app.stop()
    else:
        await rollcall_loop(config, session, active)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

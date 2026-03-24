import os
import logging
from telegram import Bot

logger = logging.getLogger(__name__)

_token = os.getenv("TG_BOT_TOKEN")
_chat_id = os.getenv("TG_CHAT_ID")


async def notify(message: str) -> None:
    if not _token or not _chat_id:
        logger.warning("TG_BOT_TOKEN or TG_CHAT_ID not set, skipping notification")
        return
    await Bot(_token).send_message(chat_id=_chat_id, text=message)

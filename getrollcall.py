import asyncio
import logging
import os
import requests

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))

if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

logger = logging.getLogger(__name__)


async def wait_for_rollcall(
    session: requests.Session,
    sec: int = POLL_INTERVAL,
    endpoint: str = "https://iclass.tku.edu.tw",
) -> tuple[int, str]:
    """
    Polls the iClass rollcall API until the specified rollcall_id is found.

    Args:
        session (requests.Session): The session with proper headers set.
        target_rollcall_id (int): The rollcall_id to wait for.
        endpoint (str): The API endpoint to poll.

    Returns:
        tuple: (rollcall_id, source) when found.
    """
    url = f"{endpoint}/api/radar/rollcalls?api_version=1.1.0"

    while True:
        try:
            logger.debug("Session object type: %s", type(session))
            logger.debug("Session object: %s", repr(session))
            response = session.get(url)
            logger.debug("Response type: %s", type(response))
            logger.debug("Response object: %s", repr(response))
            response.raise_for_status()
            data = response.json()
            previous_rollcall_id = None
            rollcalls = data.get("rollcalls", [])
            for rollcall in rollcalls:
                if (
                    rollcall.get("rollcall_id")
                    and rollcall["rollcall_id"] != previous_rollcall_id
                ):
                    logger.info(
                        "Found rollcall: ID = %s, Source = %s",
                        rollcall["rollcall_id"],
                        rollcall["source"],
                    )
                    previous_rollcall_id = rollcall["rollcall_id"]
                    return rollcall["rollcall_id"], rollcall["source"]

            logger.info("Rollcall not found yet. Waiting %s seconds...", sec)
            await asyncio.sleep(sec)

        except Exception as e:
            logger.error("Error occurred while waiting for rollcall: %s", e)
            await asyncio.sleep(5)

# schools/rollcall.py
import logging
from getrollcall import wait_for_rollcall
from sendRadar import answer_rollcall_Radar
from sendNum import answer_rollcall_number_async
from notify import notify

logger = logging.getLogger(__name__)


async def handle_rollcall(
    auth_session, endpoint: str, latitude: float, longitude: float
) -> None:
    try:
        logger.info("Starting rollcall handling for endpoint: %s", endpoint)
        rollcall_id, source = await wait_for_rollcall(
            session=auth_session, endpoint=endpoint
        )
        logger.info("Returned: rollcall_id=%s, source=%s", rollcall_id, source)
    except Exception as e:
        logger.error("Error in rollcall handling: %s", str(e))
        await notify(f"Rollcall error: {e}")
        return

    if source == "number":
        code = await answer_rollcall_number_async(
            session=auth_session,
            rollcall_id=rollcall_id,
            endpoint=endpoint,
        )
        if code is not None:
            logger.info("Number rollcall success: %s", code)
            await notify(f"Rollcall success (number) - Code: {code}")
        else:
            logger.error("Number rollcall failed: no valid code found")
            await notify("Rollcall failed (number) - no valid code found")

    elif source == "radar":
        radar_response = await answer_rollcall_Radar(
            session=auth_session,
            rollcall_id=rollcall_id,
            endpoint=endpoint,
            latitude=latitude,
            longitude=longitude,
        )
        logger.info("Radar rollcall response: %s", radar_response.text)
        await notify("Rollcall success (radar)")

    else:
        logger.warning("Unknown rollcall source: %s", source)
        await notify(f"Unknown rollcall type: {source}")

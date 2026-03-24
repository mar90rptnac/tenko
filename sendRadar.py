import json
import logging

from schools.http_headers import radar_headers

if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

logger = logging.getLogger(__name__)


async def answer_rollcall_Radar(session, rollcall_id, endpoint="https://iclass.tku.edu.tw", latitude=25.174269373936202, longitude=121.45422774303604):
    url = (
        f"{endpoint}/api/rollcall/{rollcall_id}/answer?api_version=1.1.2"
    )

    headers = radar_headers()
    headers.update({
        "host": endpoint.replace("https://", "").replace("http://", ""),
    })

    payload = {
        "deviceId": "7eba2081f77e5525",  # 7eba2081f77e5527
        "latitude": latitude,
        "longitude": longitude,
        "speed": None,
        "accuracy": 34.400001525878906,
        "altitude": 77.69999694824219,
        "altitudeAccuracy": None,
        "heading": None,
    }

    response = session.put(url, headers=headers, data=json.dumps(payload))
    logger.info("Radar response: %s - %s", response.status_code, response.text)
    return response

# schools/config.py
from dataclasses import dataclass
from typing import Callable, Optional, Union, Awaitable
import logging
import os
import requests
from schools.http_headers import session_headers

logger = logging.getLogger(__name__)

Session = requests.Session  # 視你實際用的型別而定


@dataclass(frozen=True)
class SchoolConfig:
    key: str  # "tku", "fju", ...
    auth_func: Callable[
        [], Awaitable[Union[Session, dict]]
    ]  # 不吃參數，回傳已登入的 session 或錯誤 dict
    endpoint: Optional[str] = None  # 有些學校可能不需要 endpoint（只登入）
    latitude: float = 25.174269373936202  # default latitude
    longitude: float = 121.45422774303604  # default longitude


async def tku_auth() -> Union[Session, dict]:
    from schools.tku.auth import Authenticator
    auth = await Authenticator.create()
    session = auth.perform_auth()
    session.headers.update(session_headers())
    return session


SCHOOL_CONFIGS: dict[str, SchoolConfig] = {
    "tku": SchoolConfig(
        key="tku",
        auth_func=tku_auth,
        endpoint="https://iclass.tku.edu.tw",
        latitude=float(os.getenv("LATITUDE", "25.174269373936202")),
        longitude=float(os.getenv("LONGITUDE", "121.45422774303604")),
    ),
}

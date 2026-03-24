# auth_module.py
import os
import requests
import urllib3
import re
import logging
from dotenv import load_dotenv

urllib3.disable_warnings()

logger = logging.getLogger(__name__)


class Authenticator:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({"Referer": "https://iclass.tku.edu.tw/"})
        adapter = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.auth_url = (
            "https://sso.tku.edu.tw/auth/realms/TKU/protocol/openid-connect/auth"
            "?client_id=pdsiclass&response_type=code&redirect_uri=https%3A//iclass.tku.edu.tw/login"
            "&state=L2lwb3J0YWw=&scope=openid,public_profile,email"
        )

    @classmethod
    async def create(cls) -> "Authenticator":
        """
        建立 Authenticator
        1. 優先讀 .env 中 USERNAMEID / PASSWORD
        2. 若沒設，就用 Textual TUI 互動式輸入
        """
        load_dotenv()
        username = os.getenv("USERNAMEID")
        password = os.getenv("PASSWORD")

        if not username or not password:
            raise ValueError("USERNAMEID and PASSWORD must be set in environment variables.")

        logger.info("Creating TKU authenticator for user: %s", username)
        return cls(username, password)

    def check_login_success(self, response):
        content = response.text
        match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)

        if match and match.group(1) == "淡江大學單一登入(SSO)":
            logger.warning("Login failed")
            return False
        else:
            logger.info("🔐 Authentication successful")
            return True

    def perform_auth(self):
        logger.info("Starting TKU authentication process")
        self.session.get("https://iclass.tku.edu.tw/login?next=/iportal&locale=zh_TW")
        logger.info("Accessed TKU login page")
        self.session.get(self.auth_url)
        logger.info("Accessed TKU SSO auth URL")
        login_page_url = (
            f"https://sso.tku.edu.tw/NEAI/logineb.jsp?myurl={self.auth_url}"
        )
        login_page = self.session.get(login_page_url)
        jsessionid = login_page.cookies.get("AMWEBJCT!%2FNEAI!JSESSIONID")
        if not jsessionid:
            logger.error("JSESSIONID cookie not found.")
            raise ValueError("無法取得 JSESSIONID")

        image_headers = {
            "Referer": "https://sso.tku.edu.tw/NEAI/logineb.jsp",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        self.session.get(
            "https://sso.tku.edu.tw/NEAI/ImageValidate", headers=image_headers
        )
        post_headers = {
            "Origin": "https://sso.tku.edu.tw",
            "Referer": "https://sso.tku.edu.tw/NEAI/logineb.jsp",
        }
        body = {"outType": "2"}
        response = self.session.post(
            "https://sso.tku.edu.tw/NEAI/ImageValidate", headers=post_headers, data=body
        )
        vidcode = response.text.strip()

        payload = {
            "myurl": self.auth_url,
            "ln": "zh_TW",
            "embed": "No",
            "vkb": "No",
            "logintype": "logineb",
            "username": self.username,
            "password": self.password,
            "vidcode": vidcode,
            "loginbtn": "登入",
        }
        login_url = (
            f"https://sso.tku.edu.tw/NEAI/login2.do;jsessionid={jsessionid}?action=EAI"
        )

        response = self.session.post(login_url, data=payload)

        if self.check_login_success(response) != True:
            return {"error": "user name or password maybe not currect on the os level"}
        headers = {"Referer": login_url, "Upgrade-Insecure-Requests": "1"}
        user_redirect_url = (
            f"https://sso.tku.edu.tw/NEAI/eaido.jsp?"
            f"am-eai-user-id={self.username}&am-eai-redir-url={self.auth_url}"
        )
        self.session.get(user_redirect_url, headers=headers)

        return self.session

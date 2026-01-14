from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from pathlib import Path
import time

class BrowserController:
    def __init__(self):
        self.p = sync_playwright().start()

        # Persistent user data directory (cookies, localStorage, cache)
        user_data = Path("browser_state")
        user_data.mkdir(parents=True, exist_ok=True)

        # Launch Chromium with persistent profile
        self.context = self.p.chromium.launch_persistent_context(
            user_data_dir=str(user_data),
            headless=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
        )
        self.page = self.context.new_page()

    def safe_get_content(self):
        try:
            # ждём пока страница стабилизируется
            self.page.wait_for_load_state("domcontentloaded", timeout=5000)
        except PlaywrightTimeout:
            pass  # если таймаут — просто продолжаем

        try:
            return self.page.content()
        except:
            return ""

    def navigate(self, url: str):
        try:
            self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
            return {"status": "ok", "url": self.page.url}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def click(self, text: str):
        try:
            self.page.get_by_text(text).first.click(timeout=30000)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def type(self, text: str, content: str):
        try:
            self.page.get_by_placeholder(text).first.fill(content)
            return {"status": "ok"}
        except Exception:
            # fallback: click by text then type
            try:
                self.page.get_by_text(text).first.click()
                self.page.keyboard.type(content)
                return {"status": "ok", "fallback": True}
            except Exception as e:
                return {"status": "error", "error": str(e)}

    def get_html(self) -> str:
        return self.safe_get_content()

    def get_url(self) -> str:
        return self.page.url

    def is_captcha(self) -> bool:
        # 1. Recaptcha iframe
        if self.page.query_selector('iframe[src*="recaptcha"]'):
            return True

        # 2. Яндекс checkbox captcha
        if self.page.query_selector('input.CheckboxCaptcha-Button'):
            return True

        # 3. "Я не робот" — только если видимый
        elem = self.page.get_by_text("Я не робот", exact=False)
        try:
            if elem.is_visible():
                return True
        except:
            pass

        return False

    def wait_for_captcha_solved(self, timeout_sec=180):
        for _ in range(timeout_sec):
            html = self.safe_get_content().lower()
            if html and not self.is_captcha():
                return True
            time.sleep(1)

        return False
    
    def get_dom(self):
        return self.safe_get_content()

    def close(self):
        self.context.close()
        self.p.stop()
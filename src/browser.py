import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys


class BrowserController:
    def __init__(self):
        # Chrome профиль пользователя (macOS)
        home = os.path.expanduser("~")
        chrome_profile = os.path.join(
            home,
            "Library", "Application Support", "Google", "Chrome", "Default"
        )

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument(f"--user-data-dir={chrome_profile}")
        options.add_argument("--disable-blink-features=AutomationControlled")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    # ===== Playwright-style wrappers =====
    def safe_get_content(self):
        try:
            time.sleep(0.3)
            return self.driver.page_source
        except:
            return ""

    def get_dom(self):
        return self.safe_get_content()

    def get_url(self):
        return self.driver.current_url

    # ===== Actions =====
    def navigate(self, url: str):
        try:
            self.driver.get(url)
            time.sleep(1)
            return {"status": "ok", "url": self.driver.current_url}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def click(self, text: str, role=None, aria=None, exact=False):
        from selenium.common.exceptions import StaleElementReferenceException

        def matches(elem):
            try:
                if not elem.is_displayed():
                    return False
                t = elem.text.strip()
                if exact:
                    return t == text
                return text.lower() in t.lower()
            except StaleElementReferenceException:
                return False

        # 1) Gmail subject click (span.bog)
        try:
            if "mail.google.com" in self.driver.current_url:
                subjects = self.driver.find_elements(By.CSS_SELECTOR, "span.bog")
                for s in subjects:
                    try:
                        if matches(s):
                            s.click()
                            time.sleep(0.4)
                            return {"status": "ok", "clicked": text, "gmail_subject": True}
                    except:
                        pass
        except:
            pass

        # 2) Generic strategies
        strategies = [
            (By.XPATH, f"//*[contains(normalize-space(text()), '{text}')]"),
            (By.CSS_SELECTOR, f"[aria-label*='{text}']"),
            (By.CSS_SELECTOR, f"[title*='{text}']"),
            (By.CSS_SELECTOR, f"[value*='{text}']"),
            (By.CSS_SELECTOR, f"[placeholder*='{text}']"),
        ]

        # 3) role / aria filters
        if role:
            strategies.insert(0, (By.CSS_SELECTOR, f"[role='{role}']"))
        if aria:
            strategies.insert(0, (By.CSS_SELECTOR, f"[aria-label='{aria}']"))

        # 4) search & filter fresh elements
        for by, selector in strategies:
            try:
                elems = self.driver.find_elements(by, selector)
            except:
                elems = []

            fresh = []
            for e in elems:
                try:
                    if matches(e):
                        fresh.append(e)
                except StaleElementReferenceException:
                    pass

            if fresh:
                try:
                    fresh[0].click()
                    time.sleep(0.3)
                    return {"status": "ok", "clicked": text, "by": f"{by}:{selector}", "exact": exact, "role": role, "aria": aria}
                except:
                    pass

        # 5) try iframes
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for frame in iframes:
                try:
                    self.driver.switch_to.frame(frame)
                    for by, selector in strategies:
                        try:
                            elems = self.driver.find_elements(by, selector)
                            fresh = []
                            for e in elems:
                                try:
                                    if matches(e):
                                        fresh.append(e)
                                except StaleElementReferenceException:
                                    pass

                            if fresh:
                                fresh[0].click()
                                self.driver.switch_to.default_content()
                                time.sleep(0.3)
                                return {"status": "ok", "clicked_iframe": text}
                        except:
                            pass
                    self.driver.switch_to.default_content()
                except:
                    self.driver.switch_to.default_content()
        except:
            pass

        # 6) Fallback JS-force click
        try:
            elem = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
            self.driver.execute_script("arguments[0].click();", elem)
            return {"status": "ok", "js_force": True, "clicked": text}
        except:
            pass

        return {"status": "error", "error": f"CLICK no match: text={text}, role={role}, aria={aria}, exact={exact}"}

    def type(self, placeholder: str, content: str):
        selectors = [
            (By.CSS_SELECTOR, f"input[placeholder*='{placeholder}']"),
            (By.CSS_SELECTOR, f"textarea[placeholder*='{placeholder}']"),
            (By.CSS_SELECTOR, f"input[aria-label*='{placeholder}']"),
            (By.CSS_SELECTOR, f"textarea[aria-label*='{placeholder}']"),
            (By.CSS_SELECTOR, f"input[name*='{placeholder}']"),
            (By.CSS_SELECTOR, f"textarea[name*='{placeholder}']"),
            (By.XPATH, f"//input[contains(@title, '{placeholder}')]"),
            (By.XPATH, f"//textarea[contains(@title, '{placeholder}')]"),
            (By.XPATH, f"//*[contains(text(), '{placeholder}')]/following::input[1]"),
            (By.XPATH, f"//*[contains(text(), '{placeholder}')]/following::textarea[1]"),
        ]

        # основной документ
        for by, sel in selectors:
            try:
                elem = self.driver.find_element(by, sel)
                elem.clear()
                elem.send_keys(content)
                return {"status": "ok", "typed": content, "selector": sel}
            except:
                pass

        # внутри iframe
        try:
            for frame in self.driver.find_elements(By.TAG_NAME, "iframe"):
                self.driver.switch_to.frame(frame)
                for by, sel in selectors:
                    try:
                        elem = self.driver.find_element(by, sel)
                        elem.clear()
                        elem.send_keys(content)
                        self.driver.switch_to.default_content()
                        return {"status": "ok", "typed_iframe": content, "selector": sel}
                    except:
                        pass
                self.driver.switch_to.default_content()
        except:
            pass

        return {"status": "error", "error": f"TYPE failed: {placeholder}"}
    
    def type_by_selector(self, key, value, content):
        """
        Универсальный обработчик: type_by_selector("aria", "Поиск", "OpenAI")
        """
        css_variants = []

        if key == "aria":
            css_variants = [
                f"[aria-label='{value}']",
                f"[aria-label*='{value}']",
            ]
        elif key == "placeholder":
            css_variants = [
                f"input[placeholder='{value}']",
                f"input[placeholder*='{value}']",
                f"textarea[placeholder='{value}']",
                f"textarea[placeholder*='{value}']",
            ]
        elif key == "role":
            css_variants = [
                f"[role='{value}']",
            ]
        elif key == "name":
            css_variants = [
                f"[name='{value}']",
                f"* [name='{value}']",
            ]
        else:
            return {"status": "error", "error": f"Unknown selector key: {key}"}

        # --- сначала основной документ ---
        for sel in css_variants:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                el.clear()
                el.send_keys(content)
                return {"status": "ok", "into": f"{key}:{value}", "selector": sel}
            except:
                pass

        # --- fallback: искать внутри iframe ---
        try:
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for f in frames:
                self.driver.switch_to.frame(f)
                for sel in css_variants:
                    try:
                        el = self.driver.find_element(By.CSS_SELECTOR, sel)
                        el.clear()
                        el.send_keys(content)
                        self.driver.switch_to.default_content()
                        return {"status": "ok", "into_iframe": f"{key}:{value}", "selector": sel}
                    except:
                        pass
                self.driver.switch_to.default_content()
        except:
            pass

        return {"status": "error", "error": f"TYPE failed: {key}:{value}"}

    def press_enter(self):
        try:
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.ENTER)
            return {"status": "ok", "enter": True}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ===== CAPTCHA =====
    def is_captcha(self) -> bool:
        url = self.driver.current_url.lower()

        # Yandex redirect
        if "showcaptcha" in url:
            return True

        # Google reCAPTCHA iframe
        try:
            if self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']"):
                return True
        except:
            pass

        # Yandex checkbox captcha
        try:
            if self.driver.find_elements(By.CSS_SELECTOR, "input.CheckboxCaptcha-Button"):
                return True
        except:
            pass

        # Visible "Я не робот"
        try:
            items = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Я не робот')]")
            for i in items:
                if i.is_displayed():
                    return True
        except:
            pass

        return False

    def wait_for_captcha_solved(self, timeout_sec=180):
        print("⚠️ CAPTCHA обнаружена! Пожалуйста решите её в браузере...")
        for _ in range(timeout_sec):
            if not self.is_captcha():
                print("🟢 CAPTCHA решена!")
                return True
            time.sleep(1)
        return False
    
    def find_search_field(self):
        selectors = [
            "[type='search']",
            "[placeholder*='поиск']",
            "[aria-label*='search']",
            "[role='searchbox']",
            "input[type='text']"
        ]
        for sel in selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                return elem
            except:
                pass
        return None

    # ===== Close =====
    def close(self):
        try:
            self.driver.quit()
        except:
            pass
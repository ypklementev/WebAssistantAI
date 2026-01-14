from utils import extract_arg, normalize_url
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeout

def execute_action(action_str, browser):
    action_str = action_str.strip()

    # ===== NAVIGATE(url) =====
    if action_str.startswith("NAVIGATE"):
        raw = extract_arg(action_str)
        if not raw:
            return {"status": "error", "error": "Bad NAVIGATE format"}

        url = normalize_url(raw)
        try:
            browser.page.goto(url, timeout=30000, wait_until="domcontentloaded")
        except PlaywrightTimeout:
            # продолжим несмотря на таймаут, потому что часто будет редирект на капчу
            pass
        except Exception as e:
            return {"status": "error", "error": str(e)}

        # ВАЖНО: ждать загрузки сети (или капчи)
        try:
            browser.page.wait_for_load_state("networkidle", timeout=5000)
        except:
            pass

        # Ещё чутка подождать для стабильности DOM
        time.sleep(0.5)

        return {"status": "ok", "url": browser.page.url}

    # ===== CLICK(text) =====
    if action_str.startswith("CLICK"):
        raw = extract_arg(action_str)
        try:
            el = browser.page.get_by_text(raw).first
            el.click(timeout=30000)
            # подождём реакцию страницы
            try:
                browser.page.wait_for_load_state("networkidle", timeout=3000)
            except:
                pass
            time.sleep(0.3)
            return {"status": "clicked", "text": raw}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ===== TYPE(placeholder, content) =====
    if action_str.startswith("TYPE"):
        raw = extract_arg(action_str)
        parts = raw.split(",", 1)
        if len(parts) != 2:
            return {"status": "error", "error": "Bad TYPE format"}

        target = parts[0].strip()
        content = parts[1].strip()

        # пробуем через placeholder
        try:
            field = browser.page.get_by_placeholder(target).first
            field.fill(content, timeout=5000)
            return {"status": "typed", "into": target, "content": content}
        except:
            pass

        # fallback: клик по тексту + keyboard.type()
        try:
            field = browser.page.get_by_text(target).first
            field.click(timeout=30000)
            browser.page.keyboard.type(content)
            return {"status": "typed_fallback", "into": target, "content": content}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ===== ENTER() =====
    if action_str.startswith("ENTER"):
        try:
            browser.page.keyboard.press("Enter")
            try:
                browser.page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            time.sleep(0.3)
            return {"status": "enter"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ===== DONE() =====
    if action_str.startswith("DONE"):
        return {"status": "done"}

    return {"status": "unknown_action", "raw": action_str}
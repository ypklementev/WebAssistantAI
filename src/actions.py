import re
from utils import normalize_url, extract_arg

def execute_action(action_str, browser):
    action = action_str.strip()

    # --- NAVIGATE("https://...") ---
    if action.startswith("NAVIGATE"):
        raw = extract_arg(action)
        url = raw.strip().strip('"').strip("'")
        if "content=" in url:
            return {"status": "error", "error": "Invalid NAVIGATE: contains content="}
        return browser.navigate(normalize_url(url))

    # --- CLICK("text") ---
    if action.startswith("CLICK"):
        raw = extract_arg(action)

        # key=val парсинг
        parts = dict(
            (k, v.strip().strip('"').strip("'"))
            for k, v in re.findall(r'(\w+)=(".*?"|\'.*?\'|[^,]+)', raw)
        )

        text = parts.get("text")
        role = parts.get("role")
        aria = parts.get("aria")
        exact = parts.get("exact") == "true"

        # если text не передали парой — значит весь raw это text
        if not text:
            text = raw.strip().strip('"').strip("'")

        return browser.click(text=text, role=role, exact=exact, aria=aria)

    # --- TYPE(selector="key:value", content="text") ---
    if action.startswith("TYPE"):
        raw = extract_arg(action)

        # к примеру: selector="aria:Поиск", content="MTI ..."
        m = re.findall(r'(\w+)=(".*?"|\'.*?\'|[^,]+)', raw)
        kv = {k: v.strip().strip('"').strip("'") for k, v in m}

        if "selector" not in kv or "content" not in kv:
            return {"status": "error", "error": f"Bad TYPE format: {raw}"}

        selector = kv["selector"]
        content = kv["content"]

        if ":" not in selector:
            return {"status": "error", "error": f"Bad selector format: {selector}"}

        key, value = selector.split(":", 1)
        key, value = key.strip(), value.strip()

        return browser.type_by_selector(key, value, content)

    # --- ENTER() ---
    if action.startswith("ENTER"):
        return browser.press_enter()

    # --- DONE("result") ---
    if action.startswith("DONE"):
        return {"status": "done"}

    return {"status": "unknown_action", "raw": action}
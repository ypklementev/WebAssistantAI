import re
from utils.utils import normalize_url, extract_arg

def execute_action(action_str, browser):
    action = action_str.strip()

    # NAVIGATE("https://...")
    if action.startswith("NAVIGATE"):
        raw = extract_arg(action)
        url = raw.strip().strip('"').strip("'")
        return browser.navigate(normalize_url(url))

    # CLICK("text", ...)
    if action.startswith("CLICK"):
        raw = extract_arg(action)
        parts = dict(
            (k, v.strip().strip('"').strip("'"))
            for k, v in re.findall(r'(\w+)=(".*?"|\'.*?\'|[^,]+)', raw.replace('", ', ', ').replace("', ", ', '))
        )

        text = parts.get("text")
        role = parts.get("role")
        aria = parts.get("aria")
        exact = (parts.get("exact") == "true")

        if not text:
            text = raw.strip().strip('"').strip("'")

        return browser.click(text=text, role=role, aria=aria, exact=exact)

    # TYPE(selector="key:value", content="...")
    if action.startswith("TYPE"):
        raw = extract_arg(action)
        kv = dict((k, v.strip().strip('"').strip("'")) for k, v in re.findall(r'(\w+)=(".*?"|\'.*?\'|[^,]+)', raw))
        if "selector" not in kv or "content" not in kv:
            return {"status": "error", "error": f"Bad TYPE format: {raw}"}

        selector = kv["selector"]
        content = kv["content"]
        if ":" not in selector:
            return {"status": "error", "error": f"Bad selector: {selector}"}

        key, value = selector.split(":",1)
        return browser.type_by_selector(key.strip(), value.strip(), content)

    # ENTER()
    if action.startswith("ENTER"):
        return browser.press_enter()

    # CONFIRM("text")
    if action.startswith("CONFIRM"):
        raw = extract_arg(action)
        msg = raw.strip().strip('"').strip("'")
        return {"status": "confirm", "message": msg}

    # DONE("result")
    if action.startswith("DONE"):
        return {"status": "done"}

    return {"status": "unknown_action", "raw": action}
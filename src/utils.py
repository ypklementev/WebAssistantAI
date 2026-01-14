import re

def extract_arg(action_str: str):
    m = re.search(r'\((.*)\)', action_str, flags=re.DOTALL)
    if not m:
        return None
    raw = m.group(1).strip()
    return raw

def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url
from bs4 import BeautifulSoup

def extract_text(dom: str, limit=2000) -> str:
    soup = BeautifulSoup(dom, "html.parser")
    txt = soup.get_text(separator=" ", strip=True)
    return txt[:limit]

def extract_inputs(dom: str, limit=20):
    soup = BeautifulSoup(dom, "html.parser")
    fields = []

    # <input>
    for inp in soup.find_all("input"):
        fields.append({
            "tag": inp.name,
            "type": inp.get("type"),
            "placeholder": inp.get("placeholder"),
            "aria": inp.get("aria-label"),
            "name": inp.get("name"),
            "role": inp.get("role"),
        })

    # <textarea>
    for ta in soup.find_all("textarea"):
        fields.append({
            "tag": ta.name,
            "placeholder": ta.get("placeholder"),
            "aria": ta.get("aria-label"),
            "name": ta.get("name"),
            "role": ta.get("role"),
        })

    # combobox role (например Gmail)
    for elem in soup.find_all(attrs={"role": "combobox"}):
        fields.append({
            "tag": elem.name,
            "placeholder": elem.get("placeholder"),
            "aria": elem.get("aria-label"),
            "name": elem.get("name"),
            "role": "combobox",
        })

    return fields[:limit]

def extract_buttons(dom: str, limit=20):
    soup = BeautifulSoup(dom, "html.parser")
    btns = []

    for btn in soup.find_all("button"):
        text = btn.get_text(strip=True)
        if text:
            btns.append(text)

    for inp in soup.find_all("input", attrs={"type": ["button", "submit"]}):
        val = inp.get("value", "").strip()
        if val:
            btns.append(val)

    return btns[:limit]

def extract_headings(dom: str, limit=10):
    soup = BeautifulSoup(dom, "html.parser")
    out = []
    for tag in ["h1", "h2", "h3", "h4"]:
        for hg in soup.find_all(tag):
            txt = hg.get_text(strip=True)
            if txt:
                out.append(txt)
    return out[:limit]

def extract_list_items(dom, limit=20):
    soup = BeautifulSoup(dom, "html.parser")
    items = []

    for li in soup.find_all("li"):
        txt = li.get_text(strip=True)
        if txt:
            items.append(txt)

    for tr in soup.find_all("tr"):
        txt = tr.get_text(strip=True)
        if txt:
            items.append(txt)

    return items[:limit]

def extract_all(dom: str):
    return {
        "text": extract_text(dom),
        "inputs": extract_inputs(dom),
        "buttons": extract_buttons(dom),
        "headings": extract_headings(dom),
        "list_items": extract_list_items(dom),
    }
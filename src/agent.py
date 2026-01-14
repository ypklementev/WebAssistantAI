from llm import ask_llm
from perception.extract import extract_all
from memory import Memory
from actions import execute_action
import time

class Agent:
    def __init__(self, browser):
        self.browser = browser
        self.memory = Memory()

    def step(self, goal):
        # CAPTCHA
        if self.browser.is_captcha():
            solved = self.browser.wait_for_captcha_solved()
            if not solved:
                print("⛔ CAPTCHA timeout")
                return "DONE(CAPTCHA timeout)", {"status": "captcha_timeout"}
            time.sleep(1)
            return "WAITING_FOR_USER", {"status": "captcha_solved"}

        dom = self.browser.get_dom()
        url = self.browser.get_url()
        data = extract_all(dom)
        text = data["text"][:2000]

        hist = self.memory.format()
        attempted_search = self.memory.has_attempted_search()
        last_search = self.memory.last_search_query()

        prompt = f"""
You are an autonomous web agent.

Goal: {goal}
Current URL: {url}
ATTEMPTED_SEARCH: {attempted_search}
LAST_SEARCH: {last_search}

PAGE_TEXT_SNIPPET:
{text}

AVAILABLE_INPUTS:
{data['inputs']}

AVAILABLE_BUTTONS:
{data['buttons']}

AVAILABLE_HEADINGS:
{data['headings']}

AVAILABLE_LIST_ITEMS:
{data['list_items']}

RECENT_ACTIONS:
{hist}

-------------------------------------------------------
INTERNAL CONTEXT (DO NOT OUTPUT):
-------------------------------------------------------
Determine site context from URL pattern:
- If URL contains terms related to mail/inbox → context = EMAIL
- If URL contains terms related to search engine → context = SEARCH
- If URL contains terms related to maps/navigation → context = MAP
- Otherwise → context = OTHER

Determine goal domain:
- If goal contains terms related to email/mail/inbox/message → domain = EMAIL
- If goal contains terms related to finding/locating/searching/browsing → domain = WEB_SEARCH
- Otherwise → domain = GENERIC

Do NOT output this determination.

-------------------------------------------------------
NAVIGATION POLICY (MANDATORY, INTERNAL):
-------------------------------------------------------
If domain != context:
  - If domain = WEB_SEARCH and context != SEARCH:
      → NAVIGATE to a general search page (example: "https://...")
  - If domain = EMAIL and context != EMAIL:
      → NAVIGATE to an email page (example: "https://...")
  - If no suitable URL known → ask user via DONE("need user URL")

Do NOT output this reasoning.

-------------------------------------------------------
NO RESULTS DETECTION (INTERNAL):
-------------------------------------------------------
Treat situation as NO_RESULTS if:
- PAGE_TEXT_SNIPPET contains phrases like:
  "нет результатов", "ничего не найдено",
  "не найдено", "no results", "not found",
  "did not match", "no matches", "empty"
OR
- AVAILABLE_LIST_ITEMS is empty AND previous action was search

If NO_RESULTS and ATTEMPTED_SEARCH=false:
  → attempt simplified search query (new TYPE + ENTER)
If NO_RESULTS and ATTEMPTED_SEARCH=true:
  → DONE("no results")

-------------------------------------------------------
STRICT ACTION SYNTAX (MANDATORY):
-------------------------------------------------------

You may ONLY return exactly ONE of these:

  NAVIGATE("https://example.com")
  CLICK("visible text")
  TYPE(selector="key:value", content="string")
  ENTER()
  DONE("result")

Rules:
- Exactly one action per response
- No JSON
- No code fences
- No reasoning text
- All string values MUST use double quotes

NAVIGATE RULES:
- MUST use https:// or http://
- MUST NOT include anything other than URL string
- MUST NOT embed content=, selector=, or query parameters if not proper URL

CLICK RULES:
- CLICK("text")
Optional disambiguation:
  CLICK("text", exact=true)
  CLICK("text", role="button")
  CLICK("text", aria="Open menu")

TYPE RULES:
- ONLY format allowed:
    TYPE(selector="key:value", content="string")
- key MUST be one of: placeholder, aria, role, name
- selector MUST contain exactly one ":"
- After TYPE on a search field → ENTER on next turn

DONE RULES:
- Format: DONE("short result")
- Result must be short and human-readable

-------------------------------------------------------
END CONDITIONS (MANDATORY):
-------------------------------------------------------
If goal achieved → DONE("description")
If domain mismatch and no NAVIGATE yet → NAVIGATE("https://...")
If NO_RESULTS and ATTEMPTED_SEARCH=true → DONE("no results")

-------------------------------------------------------
REMINDERS (DO NOT OUTPUT):
-------------------------------------------------------
- Do not explain reasoning
- Do not fabricate arguments
- Do not output multiple actions
- Do not wrap the action in backticks
"""

        action = ask_llm(prompt)
        result = execute_action(action, self.browser)
        self.memory.add(action, result)
        return action, result
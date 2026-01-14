from llm import ask_llm
from perception.extract import extract_all
from memory import Memory
from actions import execute_action
import time

class Agent:
    def __init__(self, browser, logger=None):
        self.browser = browser
        self.memory = Memory()
        self.logger = logger

    def decide_dangerous_action(self, msg):
      msg_low = msg.lower()
      
      # удаление email
      if "delete" in msg_low or "удал" in msg_low:
          return 'CLICK("Удалить")'

      # отправка
      if "send" in msg_low or "отправ" in msg_low:
          return 'CLICK("Отправить")'

      # оплата
      if "pay" in msg_low or "оплат" in msg_low:
          return 'CLICK("Оплатить")'

      # fallback — ничего не знаем → DONE
      return 'DONE("confirmed but no actionable step")'

    def step(self, goal, step_num=None):
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
        dangerous_mode = self.memory.dangerous_mode

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

          DANGEROUS_MODE:
          {dangerous_mode}

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
                → NAVIGATE to a general search page
            - If domain = EMAIL and context != EMAIL:
                → NAVIGATE to an email page
            - If no suitable URL known → DONE("need user URL")

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
          DANGEROUS ACTION POLICY (MANDATORY):
          -------------------------------------------------------
          Before executing potentially dangerous actions, you MUST ask the user for confirmation using:

            CONFIRM("description")

          Dangerous actions include (but are not limited to):
          - Deleting, removing, trashing, archiving items
          - Sending or submitting irreversible forms
          - Forwarding or sharing data
          - Financial operations (payments, checkout, subscriptions)
          - Any irreversible configuration changes

          When a dangerous action is detected:
          1. DO NOT execute it yet.
          2. Return CONFIRM("short human-friendly description")

          After CONFIRM("..."), wait for user response:
          - If user says "yes" → on next turns, act normally (DO NOT produce CONFIRM again)
          - If user says "no" → DONE("cancelled by user")

          CONFIRM RULES:
          - Must be exactly: CONFIRM("description")
          - Description must be brief and human-readable
          - After CONFIRM, DO NOT produce DONE until the dangerous action is actually completed.
          - After user confirmation, you MUST NOT stop thinking — continue selecting appropriate CLICK/TYPE actions.
          If DANGEROUS_MODE = true:
          - Do NOT issue CONFIRM() again
          - Perform the dangerous action directly

          -------------------------------------------------------
          DANGEROUS ACTION EXECUTION RULES (MANDATORY):
          -------------------------------------------------------
          If DANGEROUS_MODE = true:
            - DO NOT produce CONFIRM() anymore
            - You MUST execute the irreversible action directly using CLICK()
            - BEFORE choosing CLICK text:
                * Inspect AVAILABLE_BUTTONS
                * Match the intended irreversible action to an existing button
                * Adapt to UI language (e.g., "Delete" → "Удалить" if AVAILABLE_BUTTONS contains "Удалить")
                * Prefer exact matches over partial matches
            - Valid irreversible button meanings include (examples, multilingual allowed):
                "Delete", "Удалить", "В корзину", "Move to trash", "Trash",
                "Send", "Отправить", "Submit", "Оплатить", "Pay"
            - After executing the irreversible action, keep acting normally until goal is achieved,
              DO NOT stop thinking and DO NOT prematurely return DONE().

          -------------------------------------------------------
          STRICT ACTION SYNTAX (MANDATORY):
          -------------------------------------------------------

          You may ONLY return exactly ONE of these:

            NAVIGATE("https://example.com")
            CLICK("visible text")
            TYPE(selector="key:value", content="string")
            ENTER()
            CONFIRM("description")
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
          - MUST NOT embed content=, selector=, or other arguments

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

          ENTER RULES:
          - Format MUST be exactly: ENTER()

          DONE RULES:
          - Format MUST be exactly: DONE("result")
          - MUST NOT be used after CONFIRM unless goal is objectively completed.
          - MUST NOT be used to indicate waiting (for example forbidden):
            DONE("awaiting user confirmation")
            DONE("awaiting")
            DONE("confirmed")
            DONE("continue")

          -------------------------------------------------------
          END CONDITIONS (MANDATORY):
          -------------------------------------------------------
          If goal achieved → DONE("description")
          If domain mismatch and no NAVIGATE yet → NAVIGATE("https://...")
          If NO_RESULTS and ATTEMPTED_SEARCH=true → DONE("no results")
          If user denied a dangerous action → DONE("cancelled by user")
          If user confirmed a dangerous action → continue acting normally until goal achieved.

          -------------------------------------------------------
          REMINDERS (DO NOT OUTPUT):
          -------------------------------------------------------
          - Do not explain reasoning
          - Do not fabricate arguments or parameters
          - Do not output multiple actions
          - Do not wrap the action in backticks
          """
        
        if self.logger:
            self.logger.write_section(
                f"STEP {step_num} PROMPT",
                prompt
            )
        action = ask_llm(prompt)

        if self.logger:
            self.logger.write_section(
                f"STEP {step_num} ACTION",
                action
            )

        result = execute_action(action, self.browser)

        if self.logger:
            self.logger.write_section(
                f"STEP {step_num} RESULT",
                str(result)
            )

        self.memory.add(action, result)
        if action.startswith("CONFIRM"):
          self.memory.awaiting_user_confirmation = True
          return action, result
        return action, result
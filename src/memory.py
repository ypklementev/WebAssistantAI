class Memory:
    def __init__(self):
        self.history = []

    def add(self, action, result):
        self.history.append((action, result))

    def clear(self):
        self.history = []

    def format(self):
        out = []
        for a, r in self.history[-10:]:
            out.append(f"{a} -> {r}")
        return "\n".join(out)

    def has_attempted_search(self):
        """
        Определяем, был ли выполнен поиск
        """
        # A) TYPE + ENTER pattern
        for i in range(len(self.history) - 1):
            a1, _ = self.history[i]
            a2, _ = self.history[i + 1]
            if a1.startswith("TYPE(") and a2.startswith("ENTER"):
                return True

        # B) NAVIGATE with search params
        for action, _ in self.history:
            if action.startswith("NAVIGATE("):
                url = action.lower()
                if any(q in url for q in ["search", "query", "q=", "s="]):
                    return True

        return False
    
    def last_search_query(self):
        for action, result in reversed(self.history):
            if action.startswith("TYPE") and "content=" in action:
                return action
        return None
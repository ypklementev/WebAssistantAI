class Memory:
    def __init__(self):
        self.history = []
        
        self.awaiting_user_confirmation = False
        
        self.dangerous_mode = False

    def add(self, action, result):
        self.history.append((action, result))

    def clear(self):
        self.history = []
        self.awaiting_user_confirmation = False
        self.dangerous_mode = False

    def format(self):
        out = []
        for a, r in self.history[-10:]:
            out.append(f"{a} -> {r}")
        return "\n".join(out)

    def has_attempted_search(self):
        for i in range(len(self.history) - 1):
            a1, _ = self.history[i]
            a2, _ = self.history[i + 1]
            if a1.startswith("TYPE(") and a2.startswith("ENTER"):
                return True
        return False
    
    def last_search_query(self):
        for action, result in reversed(self.history):
            if action.startswith("TYPE") and "content=" in action:
                return action
        return None
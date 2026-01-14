from browser import BrowserController
from agent import Agent

def main():
    print("=== Браузерный агент ===")
    print("Введите 'exit' чтобы выйти.\n")

    browser = BrowserController()

    while True:
        goal = input("Введите задачу агента: ").strip()
        if goal.lower() == "exit":
            print("Выход. Закройте браузер вручную.")
            return

        agent = Agent(browser)

        agent.memory.clear()

        for step in range(50):
            action, result = agent.step(goal)
            print(f"STEP {step+1}")
            print("LLM ACTION:", action)
            print("EXEC RESULT:", result)
            print()

            if action == "WAITING_FOR_USER":
                # не считаем это шагом, просто продолжаем
                continue

            if action.startswith("DONE"):
                print("✓ Задача выполнена агентом.")
                print("Можно вручную взаимодействовать со страницей.\n")
                break

        print("Готов к новой задаче!\n")

if __name__ == "__main__":
    main()
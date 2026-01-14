from utils.logger import Logger
from browser import BrowserController
from agent import Agent

def main():
    print("=== Браузерный агент ===")
    print("Введите 'exit' чтобы выйти.\n")

    logger = Logger()
    browser = BrowserController()

    while True:
        goal = input("Введите задачу агента: ").strip()
        if goal.lower() == "exit":
            print("Выход. Закройте браузер вручную.")
            return

        logger.write(f"\n\n===== NEW GOAL: {goal} =====\n")
        agent = Agent(browser, logger=logger)
        agent.memory.clear()

        for step in range(50):
            action, result = agent.step(goal, step_num=step+1)

            print(f"STEP {step+1}")
            print("LLM ACTION:", action)
            print("EXEC RESULT:", result)
            print()

            if result.get("status") == "confirm":
                msg = result.get("message", "Confirm?")
                print(f"⚠️ Требуется подтверждение: {msg}")
                ans = input("Введите yes/no: ").strip().lower()
                if ans not in ("yes","y","да","д"):
                    print("❌ Пользователь отменил действие.")
                    logger.write("USER CHOICE: cancelled")
                    break
                print("🟢 Подтверждено пользователем, продолжаю...")
                logger.write("USER CHOICE: confirmed")
                agent.memory.dangerous_mode = True
                continue

            if action.startswith("DONE"):
                print("✓ Задача выполнена агентом.")
                print("Можно вручную взаимодействовать со страницей.\n")
                logger.write("DONE: Task completed")
                break

        print("Готов к новой задаче!\n")

if __name__ == "__main__":
    main()
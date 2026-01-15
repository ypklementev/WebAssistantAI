## WebAssistantAI — Autonomous Browser Agent (Selenium + LLM)

#### WebAssistantAI — это автономный браузерный агент, который управляет реальным браузером через Selenium и принимает решения с помощью LLM. Он способен понимать задачи, искать информацию, нажимать кнопки, заполнять формы, выполнять поисковые запросы, обрабатывать отсутствие результатов и запрашивать подтверждение перед опасными операциями (удаление, отправка, оплата).

### Возможности
	•	Управление реальным Chrome через Selenium
	•	Сохранение сессии, куки и авторизации (Chrome User Data)
	•	Контекстная навигация (Email / Search / Maps / Other)
	•	Обработка CAPTCHA (ожидание решения вручную)
	•	Обработка поиска + fallback, если нет результатов
	•	Подтверждение опасных действий через CONFIRM()
	•	История действий и состояние агента через Memory
	•	Логирование всех LLM запросов/ответов в файл

### Стек
	•	Python 3.10+
	•	Selenium WebDriver + webdriver-manager
	•	OpenAI / другие LLM провайдеры
	•	Chrome (persistent user profile)
	•	Custom prompt engineering

### Структура проекта
```
src/
  main.py                → CLI + user loop
  agent.py               → логика принятия решений
  browser.py             → Selenium-обертка
  actions.py             → парсинг действий модели
  memory.py              → память агента
  llm.py                 → вызов LLM
  perception/
    extract.py           → извлечение текста и элементов
  utils/
    logger.py            → запись логов LLM
logs/
  agent.log              → лог запросов/ответов
```

### Формат команд для LLM

Модель может возвращать ровно одну из следующих команд:

	•	NAVIGATE("https://example.com")
	•	CLICK("text")
	•	CLICK("text", exact=true)
	•	CLICK("text", role="button")
	•	CLICK("text", aria="label")
	•	TYPE(selector="key:value", content="string")
	•	ENTER()
	•	CONFIRM("description")
	•	DONE("result")

Где selector.key может быть: placeholder, aria, role, name.

### Подтверждения опасных действий

Агент автоматически использует CONFIRM("...") перед:

	•	удалением
	•	отправкой
	•	оплатой
	•	подпиской
	•	пересылкой
	•	любыми необратимыми действиями

Пользователь отвечает yes/no.

После yes агент продолжает без повторных CONFIRM.

### Обработка “нет результатов”

Если текст страницы содержит:

	•	нет результатов
	•	ничего не найдено
	•	not found
	•	no results
	•	did not match

или список пуст — агент:

	1.	Если поиск еще не делали → делает новый запрос
	2.	Если уже пытался → DONE("no results")
    
### CAPTCHA

При обнаружении:
```
⚠ CAPTCHA detected — please solve it manually…
```
Агент ожидает решения и продолжает.

### Установка
```
git clone https://github.com/<yourname>/WebAssistantAI.git
cd WebAssistantAI
```

### Ручной запуск
```
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Автозапуск на MacOS/Linux
```sh
./run.sh
```
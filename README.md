# Telegram Bot

Это пример телеграм-бота на Python, использующего библиотеку `python-telegram-bot` для управления событиями, подписками и взаимодействием с пользователями в определённых чатах.

## Функционал

Этот бот включает следующие функции:

- **Пинг всех участников** (`/pingall`) — пингует всех участников в чате.
- **Создание ASCII арта** (`/art`) — генерирует ASCII-арт.
- **Список событий** (`/le`) — выводит список добавленных событий.
- **Добавление события** (`/addevent`) — позволяет добавлять события.
- **Удаление события** (`/deleteevent`) — позволяет удалять события.
- **Подписка на уведомления о событиях** — подписка на оповещения о событиях.
- **Только разрешённые пользователи могут добавлять и удалять события**.
- **Приветственное сообщение для новых участников** (`/greeting`).

## Как запустить

Для того чтобы запустить бота локально или на сервере, выполните следующие шаги:

1. **Клонировать репозиторий:**

   ```bash
   git clone https://github.com/tsests/telegram-bot.git
   cd telegram-bot
   ```

2. **Установить зависимости:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Настроить файл конфигурации:**
   
   В директории `config/` есть файл `config.py`, где нужно указать:
   - **`TOKEN`**: Токен, который можно получить у [BotFather](https://core.telegram.org/bots#botfather).
   - **`AUTHORIZED_USERS`**: ID пользователей, которые могут добавлять и удалять события.
   - **`OWNER_ID`**: ID владельца бота.
   - **`ALLOWED_CHAT_IDS`**: Список ID чатов, в которых бот будет работать.
   - **`DATABASE_PATH`**: Путь до БД (Оставлять по умолчанию)

4. **Запуск бота:**

   Для того чтобы запустить бота, выполните команду:

   ```bash
   python bot/main.py
   ```

5. **Использование Docker:**

   Для использования Docker, создайте контейнер с помощью:

   ```bash
   docker-compose up --build
   ```

## Получение вашего ID и ID чатов

Чтобы получить свой **ID**, используйте бота [userinfobot](https://t.me/userinfobot). Напишите боту, и он ответит вашим ID.

Для получения **ID чатов**:

1. Добавьте бота в нужный чат.
2. Напишите в чат что-то, например, команду `/start`.
3. Откройте [https://api.telegram.org/bot<ваш_токен>/getUpdates](https://api.telegram.org/bot<ваш_токен>/getUpdates), чтобы увидеть последние обновления, включая ID чатов, в которых присутствует бот.

## Важные замечания

- Токен и данные не следует размещать в публичных репозиториях. Используйте переменные окружения или конфигурационные файлы, которые не загружаются в GitHub (например, через `.gitignore`).
- Все параметры, такие как **AUTHORIZED_USERS**, **OWNER_ID**, **ALLOWED_CHAT_IDS** и **DATABASE_PATH**, можно настраивать через переменные окружения.



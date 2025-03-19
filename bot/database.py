import sqlite3
from config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        last_used_timestamp INTEGER
    )
    ''')
    # Таблица подписок на уведомления
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notification_subscriptions (
        user_id INTEGER,
        timing TEXT,
        PRIMARY KEY (user_id, timing)
    )
    ''')
    # Таблица событий
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT,
        event_time TEXT,
        event_name TEXT,
        indicator_24h INTEGER DEFAULT 0,
        indicator_1h INTEGER DEFAULT 0,
        indicator_10m INTEGER DEFAULT 0
    )
    ''')
    # Таблица чатов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,
        chat_title TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_or_update_user(user_id, username, timestamp):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE users SET username = ?, last_used_timestamp = ? WHERE user_id = ?",
                       (username, timestamp, user_id))
    else:
        cursor.execute("INSERT INTO users (user_id, username, last_used_timestamp) VALUES (?, ?, ?)",
                       (user_id, username, timestamp))
    conn.commit()
    conn.close()

def add_notification_subscription(user_id, timing):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO notification_subscriptions (user_id, timing) VALUES (?, ?)",
                   (user_id, timing))
    conn.commit()
    conn.close()

def get_notification_subscriptions(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timing FROM notification_subscriptions WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row['timing'] for row in rows]

def add_event(event_date, event_time, event_name):
    conn = get_connection()
    cursor = conn.cursor()
    # Проверка на дублирование события
    cursor.execute("SELECT * FROM events WHERE event_date = ? AND event_time = ? AND event_name = ?",
                   (event_date, event_time, event_name))
    if cursor.fetchone():
        conn.close()
        return False  # событие уже существует
    cursor.execute(
        "INSERT INTO events (event_date, event_time, event_name, indicator_24h, indicator_1h, indicator_10m) VALUES (?, ?, ?, 0, 0, 0)",
        (event_date, event_time, event_name)
    )
    conn.commit()
    conn.close()
    return True

def delete_event(event_date, event_time, event_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE event_date = ? AND event_time = ? AND event_name = ?",
                   (event_date, event_time, event_name))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def list_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT event_date, event_time, event_name FROM events ORDER BY event_date, event_time")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_due_events(current_time):
    # Возвращает все события – дальнейшую фильтрацию по времени делаем в коде
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_event_indicators(event_id, indicator_24h, indicator_1h, indicator_10m):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE events SET indicator_24h = ?, indicator_1h = ?, indicator_10m = ? WHERE id = ?",
                   (indicator_24h, indicator_1h, indicator_10m, event_id))
    conn.commit()
    conn.close()

def add_chat(chat_id, chat_title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO chats (chat_id, chat_title) VALUES (?, ?)",
                   (str(chat_id), chat_title))
    conn.commit()
    conn.close()


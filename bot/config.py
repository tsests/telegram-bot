import os

TOKEN = os.getenv('BOT_TOKEN', 'default_token')
AUTHORIZED_USERS = set(map(int, os.getenv('AUTHORIZED_USERS', '1111111111').split(',')))
OWNER_ID = int(os.getenv('OWNER_ID', '1111111111'))
ALLOWED_CHAT_IDS = set(map(int, os.getenv('ALLOWED_CHAT_IDS', '-1111111111111,1111111111').split(',')))
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot.db')

# Вывод конфигурации для отладки
print(f"AUTHORIZED_USERS: {AUTHORIZED_USERS}")
print(f"OWNER_ID: {OWNER_ID}")
print(f"ALLOWED_CHAT_IDS: {ALLOWED_CHAT_IDS}")
print(f"DATABASE_PATH: {DATABASE_PATH}")

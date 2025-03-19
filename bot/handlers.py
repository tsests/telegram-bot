import io
import base64
import asyncio
import datetime
import time
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler, JobQueue
from PIL import Image, ImageDraw, ImageFont
from transliterate import translit
import logging
import pyfiglet

from config import AUTHORIZED_USERS, OWNER_ID
import database
import utils

logger = logging.getLogger(__name__)

async def generate_and_send_ascii_art(update: Update, context: CallbackContext, original_message_id: int = None) -> None:
    username = update.effective_user.username or update.effective_user.first_name
    user_id = update.effective_user.id
    timestamp = int(time.time()) - 7200
    database.add_or_update_user(user_id, username, timestamp)
    
    if re.search(r'[а-яА-ЯёЁ]', username):
        username = translit(username, 'ru', reversed=True)
    
    ascii_art = pyfiglet.figlet_format(username)

    # Создаем изображение с ASCII-артом
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    # Используем стандартный шрифт (можно изменить на другой)
    font = ImageFont.load_default()

    # Определяем координаты для текста
    text_x = 10
    text_y = 10

    # Добавляем текст на изображение
    d.text((text_x, text_y), ascii_art, fill=(0, 0, 0), font=font)

    # Получаем размер текста
    text_width, text_height = utils.get_multiline_text_size(ascii_art, font)

    # Определяем границы для обрезки
    left = text_x
    upper = text_y
    right = text_x + text_width
    lower = text_y + text_height

    # Обрезаем изображение до нужного размера
    img_cropped = img.crop((left, upper, right, lower))

    # Сохраняем обрезанное изображение в буфер
    buf = io.BytesIO()
    img_cropped.save(buf, format='PNG')
    buf.seek(0)

    # Читаем данные изображения из буфера
    image_data = buf.getvalue()

    # Создаем новый буфер, куда запишем изображение и скрытый текст
    final_buffer = io.BytesIO()
    final_buffer.write(image_data)  # Пишем данные изображения
    final_buffer.seek(0)  # Возвращаем курсор в начало

    # Определяем сообщение для ответа
    reply_to_message_id = original_message_id if original_message_id else update.message.message_id

    # Отправляем изображение в ответ на исходное сообщение пользователя
    if update.message:
        await update.message.reply_photo(photo=final_buffer, reply_to_message_id=reply_to_message_id)
    elif update.callback_query:
        await update.callback_query.message.reply_photo(photo=final_buffer, reply_to_message_id=reply_to_message_id)




async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    timestamp = int(time.time()) - 7200
    database.add_or_update_user(user_id, username, timestamp)
    logger.info(f'Пользователь {user_id} ({username}) отправил сообщение.')

async def new_member(update: Update, context: CallbackContext) -> None:
    for user in update.message.new_chat_members:
        username = user.username or user.first_name
        database.add_or_update_user(user.id, username, int(time.time()))
        logger.info(f'Пользователь {user.id} ({username}) присоединился к чату.')

async def ask_notification_timing(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    subscriptions = database.get_notification_subscriptions(user_id)
    if subscriptions:
        timings = ", ".join(subscriptions)
        await context.bot.send_message(chat_id=update.effective_user.id, text=f"Вы уже подписаны на уведомления: {timings}.")
    else:
        keyboard = [
            [InlineKeyboardButton("За 10 минут", callback_data='notif_10m')],
            [InlineKeyboardButton("За час", callback_data='notif_1h')],
            [InlineKeyboardButton("За день", callback_data='notif_24h')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_user.id, text="Когда вам напомнить о начале занятия?", reply_markup=reply_markup)

def save_notification_time(user_id: int, timing: str):
    database.add_notification_subscription(user_id, timing)
    logger.info(f"Пользователь {user_id} подписан на уведомления за {timing}.")

async def send_notification(context: CallbackContext, user_id: int, event_name: str, event_time: datetime.datetime):
    formatted_time = event_time.strftime("%H:%M")
    formatted_date = event_time.strftime("%d-%m-%Y")
    message = f"Уведомление о скором начале события {event_name}, которое назначено \nв {formatted_time} {formatted_date}."
    await context.bot.send_message(chat_id=user_id, text=message)

async def send_notifications(context: CallbackContext):
    now = datetime.datetime.now()
    events = database.get_due_events(now)
    for event in events:
        event_datetime_str = f"{event['event_date']} {event['event_time']}"
        try:
            event_time_obj = datetime.datetime.strptime(event_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError as e:
            logger.error(f"Ошибка разбора времени события '{event_datetime_str}': {e}")
            continue
        if event_time_obj < now:
            logger.info(f"Событие '{event['event_name']}' прошло.")
            continue
        time_diff = (event_time_obj - now).total_seconds()
        indicator_24h = event['indicator_24h']
        indicator_1h = event['indicator_1h']
        indicator_10m = event['indicator_10m']
        if time_diff <= 24 * 60 * 60 and indicator_24h == 0:
            # Отправляем уведомления для подписчиков на 24ч
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM notification_subscriptions WHERE timing = ?", ("24h",))
            users = [row["user_id"] for row in cursor.fetchall()]
            conn.close()
            for uid in users:
                await send_notification(context, uid, event['event_name'], event_time_obj)
            indicator_24h = 1
        if time_diff <= 60 * 60 and indicator_1h == 0:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM notification_subscriptions WHERE timing = ?", ("1h",))
            users = [row["user_id"] for row in cursor.fetchall()]
            conn.close()
            for uid in users:
                await send_notification(context, uid, event['event_name'], event_time_obj)
            indicator_1h = 1
        if time_diff <= 10 * 60 and indicator_10m == 0:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM notification_subscriptions WHERE timing = ?", ("10m",))
            users = [row["user_id"] for row in cursor.fetchall()]
            conn.close()
            for uid in users:
                await send_notification(context, uid, event['event_name'], event_time_obj)
            indicator_10m = 1
        database.update_event_indicators(event['id'], indicator_24h, indicator_1h, indicator_10m)

async def greeting(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Привет! Давайте настроим уведомления.")
    await ask_notification_timing(update, context)

async def show_menu(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    timestamp = int(time.time())
    database.add_or_update_user(user_id, username, timestamp)
    bot_username = context.bot.username
    greeting_url = f"https://t.me/{bot_username}?start=Greeting"
    keyboard = [
        [InlineKeyboardButton("Помощь", callback_data='help')],
        [InlineKeyboardButton("Пинг всех", callback_data='ping_all')],
        [InlineKeyboardButton("Создать арт", callback_data='art')],
        [InlineKeyboardButton("Уведомления", url=greeting_url)],
        [InlineKeyboardButton("Закрыть", callback_data='close')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите команду:', reply_markup=reply_markup)

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    timestamp = int(time.time())
    database.add_or_update_user(user_id, username, timestamp)
    if context.args and context.args[0] == 'Greeting':
        await update.message.reply_text("Привет! Давайте настроим уведомления.")
        await ask_notification_timing(update, context)
    else:
        await show_menu(update, context)

async def ping_all(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    timestamp = int(time.time())
    database.add_or_update_user(user_id, username, timestamp)
    chat_id = update.effective_chat.id
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    batch_size = 25
    users_list = [f"|| [{utils.escape_markdown(row['username'])}](tg://user?id={row['user_id']})||" for row in users]
    for i in range(0, len(users_list), batch_size):
        batch = users_list[i:i+batch_size]
        message = " ".join(batch)
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN_V2)

async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    timestamp = int(time.time())
    database.add_or_update_user(user_id, username, timestamp)
    await query.edit_message_reply_markup(reply_markup=None)
    if query.data == 'help':
        help_text = (
            "Привет. Я создан для помощи с напоминаниями и упоминаниями\n"
            "У меня есть несколько команд для взаимодействия:\n"
            "/pingall - Пинг всех: отправляет упоминание о всех пользователях.\n"
            "/art - Создать арт: генерирует ASCII-арт.\n"
            "- Уведомления: настройка времени уведомлений.\n"
            "/le - показать список текущих событий, которые запланированы\n"
            "Если у вас есть вопросы, то сами разберётесь)."
        )
        await query.edit_message_text(help_text)
    elif query.data == 'ping_all':
        await ping_all(update, context)
    elif query.data == 'art':
        await generate_and_send_ascii_art(update, context, original_message_id=query.message.message_id)
    elif query.data == 'notif_10m':
        save_notification_time(user_id, '10m')
    elif query.data == 'notif_1h':
        save_notification_time(user_id, '1h')
    elif query.data == 'notif_24h':
        save_notification_time(user_id, '24h')
    elif query.data == 'close':
        await query.edit_message_reply_markup(reply_markup=None)

def sanitize_event_name(event_name: str) -> str:
    sanitized_name = re.sub(r'[;&|"\n\r]', '', event_name)
    sanitized_name = re.sub(r'\s+', ' ', sanitized_name)
    return sanitized_name.strip()

async def add_event(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.effective_user.id
        if user_id not in AUTHORIZED_USERS:
            await update.message.reply_text("У вас нет прав для добавления события.")
            return
        if len(context.args) < 3:
            raise ValueError("Недостаточно аргументов для добавления события.")
        event_date = context.args[0]
        event_time = context.args[1]
        raw_event_name = " ".join(context.args[2:])
        event_name = sanitize_event_name(raw_event_name)
        event_datetime_str = f"{event_date} {event_time}"
        event_datetime = datetime.datetime.strptime(event_datetime_str, "%Y-%m-%d %H:%M")
        current_time = datetime.datetime.now()
        if event_datetime < current_time:
            await update.message.reply_text("Нельзя добавить событие в прошлом. Укажите будущую дату.")
            return
        success = database.add_event(event_date, event_time, event_name)
        if not success:
            await update.message.reply_text("Событие с такими же данными уже существует.")
            return
        await update.message.reply_text(f"Событие '{event_name}' добавлено на {event_datetime_str}.")
        logger.info(f"Событие '{event_name}' добавлено на {event_datetime_str}.")
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка добавления события: {e}")
        await update.message.reply_text("Использование: /addevent <YYYY-MM-DD> <HH:MM> <название события>")
    except Exception as e:
        logger.error(f"Ошибка добавления события: {e}")
        await update.message.reply_text("Произошла ошибка при добавлении события.")

async def delete_event(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.effective_user.id
        if user_id not in AUTHORIZED_USERS:
            await update.message.reply_text("У вас нет прав для удаления события.")
            return
        if len(context.args) < 3:
            raise ValueError("Недостаточно аргументов для удаления события. Использование: /deleteevent <дата> <время> <название события>")
        event_date = context.args[0]
        event_time = context.args[1]
        raw_event_name = " ".join(context.args[2:])
        event_name = sanitize_event_name(raw_event_name)
        success = database.delete_event(event_date, event_time, event_name)
        if success:
            await update.message.reply_text(f"Событие '{event_name}' на {event_date} в {event_time} удалено.")
            logger.info(f"Событие '{event_name}' на {event_date} в {event_time} удалено.")
        else:
            await update.message.reply_text(f"Событие '{event_name}' на {event_date} в {event_time} не найдено.")
    except Exception as e:
        logger.error(f"Ошибка при удалении события: {e}")
        await update.message.reply_text("Произошла ошибка при удалении события.")

async def list_events(update: Update, context: CallbackContext) -> None:
    try:
        events = database.list_events()
        if not events:
            await update.message.reply_text("Список событий пуст.")
        else:
            events_list = [f"{event['event_date']} {event['event_time']} - {event['event_name']}" for event in events]
            events_output = "\n".join(events_list)
            await update.message.reply_text(f"Список событий:\n{events_output}")
    except Exception as e:
        logger.error(f"Ошибка при получении списка событий: {e}")
        await update.message.reply_text("Произошла ошибка при получении списка событий.")

async def log_chat_id(update: Update, context: CallbackContext):
    chat = update.effective_chat
    if chat.type != "private":
        chat_id = chat.id
        chat_title = chat.title or "Без названия"
        database.add_chat(chat_id, chat_title)
        logger.info(f"Добавлен новый чат: {chat_id} ({chat_title})")

async def leave_all_chats(update: Update, context: CallbackContext):
    await update.message.reply_text("Команда вызвана!")
    user_id = update.effective_user.id
    logger.info(f"Команда leave_all_chats вызвана пользователем ID: {user_id}")
    if user_id != OWNER_ID:
        await update.message.reply_text("У вас нет прав для использования этой команды.")
        return
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM chats")
    chat_ids = [row["chat_id"] for row in cursor.fetchall()]
    conn.close()
    for chat_id in chat_ids:
        try:
            await context.bot.leave_chat(chat_id)
        except Exception as e:
            logger.error(f"Не удалось покинуть чат {chat_id}: {e}")


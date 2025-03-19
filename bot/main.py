import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler, JobQueue
from setproctitle import setproctitle
import database
import handlers
from config import TOKEN, ALLOWED_CHAT_IDS

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def command_wrapper(handler_func):
    async def wrapped_handler(update, context):
        chat_id = update.effective_chat.id
        if chat_id not in ALLOWED_CHAT_IDS:
            await context.bot.send_message(chat_id=chat_id, text="Этот бот работает только в определённых беседах.")
            return
        await handlers.log_chat_id(update, context)
        await handler_func(update, context)
    return wrapped_handler

def main():
    setproctitle("Telegram bot roarP")
    database.init_db()
    job_queue = JobQueue()
    application = Application.builder().token(TOKEN).job_queue(job_queue).build()
    job_queue.run_repeating(handlers.send_notifications, interval=60, first=0)
    application.add_handler(CommandHandler("zvezda_smerti", command_wrapper(handlers.leave_all_chats)))
    application.add_handler(CommandHandler("start", command_wrapper(handlers.start)))
    application.add_handler(CommandHandler("pingall", command_wrapper(handlers.ping_all)))
    application.add_handler(CommandHandler("art", command_wrapper(handlers.generate_and_send_ascii_art)))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handlers.new_member))
    application.add_handler(CallbackQueryHandler(handlers.button_callback))
    application.add_handler(CommandHandler("addevent", command_wrapper(handlers.add_event)))
    application.add_handler(CommandHandler("deleteevent", command_wrapper(handlers.delete_event)))
    application.add_handler(CommandHandler("le", command_wrapper(handlers.list_events)))
    application.add_handler(CommandHandler("greeting", command_wrapper(handlers.greeting)))
    application.add_handler(MessageHandler(filters.ALL, handlers.log_chat_id))
    application.run_polling()

if __name__ == '__main__':
    main()


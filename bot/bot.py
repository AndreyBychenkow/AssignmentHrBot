from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from bot.config import (
    INTRO, RESEARCH, PRESENTATION, INVITATION, CONFIRMATION,
    TOKEN, logger
)
from bot.handlers.command_handlers import CommandHandlers
from bot.handlers.dialog_handlers import DialogHandlers
from bot.database.storage import DataStorage

class HRBot:
    """Основной класс HR-бота."""
    
    def __init__(self, token):
        """Инициализация бота с указанным токеном."""
        self.token = token
        self.application = None
    
    def setup(self):
        """Настройка бота: регистрация обработчиков команд и сообщений."""
        # Инициализируем приложение
        self.application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики команд
        self.application.add_handler(CommandHandler("start", CommandHandlers.start))
        self.application.add_handler(CommandHandler("vacancies", CommandHandlers.show_vacancies))
        self.application.add_handler(CommandHandler("status", CommandHandlers.set_status))
        self.application.add_handler(CommandHandler("rejection", CommandHandlers.set_rejection_reason))
        self.application.add_handler(CommandHandler("analytics", CommandHandlers.show_analytics))
        
        # Добавляем обработчик для кнопки "Вернуться в начало" (обрабатывает callback_data="/start")
        self.application.add_handler(CallbackQueryHandler(
            lambda update, context: CommandHandlers.start(update, context), 
            pattern="^/start$"
        ))
        
        # Регистрируем обработчик диалога
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("dialog", DialogHandlers.start_dialog)],
            states={
                INTRO: [
                    CallbackQueryHandler(DialogHandlers.handle_intro_response, pattern="^intro_")
                ],
                RESEARCH: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, DialogHandlers.handle_research),
                    CallbackQueryHandler(DialogHandlers.handle_back_button, pattern="^back_")
                ],
                PRESENTATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, DialogHandlers.handle_presentation),
                    CallbackQueryHandler(DialogHandlers.handle_back_button, pattern="^back_")
                ],
                INVITATION: [
                    CallbackQueryHandler(DialogHandlers.handle_presentation_response, pattern="^presentation_"),
                    CallbackQueryHandler(DialogHandlers.handle_invitation_response, pattern="^invitation_"),
                    CallbackQueryHandler(DialogHandlers.handle_back_button, pattern="^back_")
                ],
                CONFIRMATION: [
                    CallbackQueryHandler(DialogHandlers.handle_confirmation, pattern="^confirmation_"),
                    CallbackQueryHandler(DialogHandlers.handle_back_button, pattern="^back_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, DialogHandlers.handle_confirmation)
                ],
            },
            fallbacks=[
                CommandHandler("start", CommandHandlers.start),
                CommandHandler("vacancies", CommandHandlers.show_vacancies),
                CommandHandler("status", CommandHandlers.set_status),
                CommandHandler("rejection", CommandHandlers.set_rejection_reason),
                CommandHandler("analytics", CommandHandlers.show_analytics),
            ],
            per_chat=True,     # Учитываем разные чаты
            name="hr_dialog",  # Уникальное имя для обработчика диалога
            allow_reentry=True  # Разрешаем повторное использование обработчика
        )
        # Добавляем диалог первым, чтобы он имел приоритет над общим обработчиком кнопок
        self.application.add_handler(conv_handler)
        
        # Регистрируем обработчик колбэков от инлайн-кнопок
        self.application.add_handler(CallbackQueryHandler(CommandHandlers.button_callback))
    
    def run(self):
        """Запуск бота."""
        if not self.application:
            self.setup()
        
        try:
            # Добавляем drop_pending_updates=True чтобы сбросить ожидающие обновления
            self.application.run_polling(drop_pending_updates=True, allowed_updates=["message", "callback_query"])
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            # Если бот уже запущен, пробуем перезапустить
            if "make sure that only one bot instance is running" in str(e):
                logger.warning("Обнаружен конфликт с другим экземпляром бота. Попытка перезапуска...")
                # Ждем 5 секунд чтобы предыдущий экземпляр освободил ресурсы
                import time
                time.sleep(5)
                self.application.run_polling(drop_pending_updates=True, allowed_updates=["message", "callback_query"])


def create_bot():
    """Создает и возвращает экземпляр бота."""
    if not TOKEN:
        logger.error("Токен бота не найден в переменных окружения. Проверьте файл .env")
        return None
    
    # Создаем экземпляр бота
    bot = HRBot(TOKEN)
    return bot 
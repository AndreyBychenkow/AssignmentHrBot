from bot.bot import create_bot
from bot.config import logger, COMPANY_NAME

if __name__ == "__main__":
    logger.info(f"Запуск HR-бота с именем компании: {COMPANY_NAME}")
    
    # Создаем бота
    hr_bot = create_bot()
    
    if hr_bot:
        # Запускаем бота
        hr_bot.run()
    else:
        logger.error("Не удалось создать бота. Проверьте настройки и токен.") 
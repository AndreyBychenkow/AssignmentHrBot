import os
import logging
import dotenv

# Загружаем переменные окружения
dotenv.load_dotenv()

# Константы для состояний диалога
INTRO, RESEARCH, PRESENTATION, INVITATION, CONFIRMATION = range(5)

# Константы для колбэков кнопок
STATUS_CALLBACK, REASON_CALLBACK = "status", "reason"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
)
logger = logging.getLogger(__name__)

# Токен Telegram бота
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Имя компании
COMPANY_NAME = os.getenv('COMPANY_NAME', '')

# Пути к файлам данных
CANDIDATES_FILE = 'candidates.json'
VACANCIES_FILE = 'vacancies.json'
ANALYTICS_FILE = 'analytics.csv'

# Статусы кандидатов
CANDIDATE_STATUSES = [
    "Недоступен", 
    "Телефонное интервью", 
    "Обдумывает после интервью", 
    "HR интервью"
]

# Причины отказа со стороны компании
COMPANY_REJECTION_REASONS = [
    "Недостаточная квалификация",
    "Несоответствие требованиям",
    "Не подходит по soft skills",
    "Не прошел технический этап"
]

# Причины отказа со стороны кандидата
CANDIDATE_REJECTION_REASONS = [
    "Низкая зарплата",
    "Не устроил график",
    "Нашел другую работу",
    "Не заинтересовала вакансия"
]

# Примеры вакансий для первого запуска
DEFAULT_VACANCIES = [
    {
        "title": "Оператор линии производства",
        "description": "Контроль за наклеиванием этикетки, закупорки бутылки крышкой, работа на палетообмотчике",
        "salary": "39000-45000 + премии"
    },
    {
        "title": "Python-разработчик",
        "description": "Разработка и поддержка серверной части приложений на Python",
        "salary": "120000-180000"
    },
    {
        "title": "Frontend-разработчик",
        "description": "Разработка пользовательских интерфейсов на React.js",
        "salary": "100000-160000"
    }
] 
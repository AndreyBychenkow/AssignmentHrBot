import json
import os
import csv
from datetime import datetime
from bot.config import logger, CANDIDATES_FILE, VACANCIES_FILE, ANALYTICS_FILE, DEFAULT_VACANCIES

class DataStorage:
    """Класс для управления хранением данных."""
    
    @staticmethod
    def load_data(filename, default=None):
        """Загружает данные из JSON-файла."""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    return json.load(file)
            return default or {}
        except Exception as e:
            logger.error(f"Ошибка загрузки данных из {filename}: {e}")
            return default or {}

    @staticmethod
    def save_data(filename, data):
        """Сохраняет данные в JSON-файл."""
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения данных в {filename}: {e}")
            return False
    
    @classmethod
    def get_candidates(cls):
        """Получает список кандидатов."""
        return cls.load_data(CANDIDATES_FILE, [])
    
    @classmethod
    def save_candidates(cls, candidates):
        """Сохраняет список кандидатов."""
        return cls.save_data(CANDIDATES_FILE, candidates)
    
    @classmethod
    def add_candidate(cls, candidate_data):
        """Добавляет нового кандидата."""
        candidates = cls.get_candidates()
        candidates.append(candidate_data)
        return cls.save_candidates(candidates)
    
    @classmethod
    def update_candidate(cls, index, candidate_data):
        """Обновляет данные кандидата."""
        candidates = cls.get_candidates()
        if 0 <= index < len(candidates):
            candidates[index] = candidate_data
            return cls.save_candidates(candidates)
        return False
    
    @classmethod
    def clear_candidates(cls):
        """Полностью очищает список кандидатов."""
        return cls.save_candidates([])
    
    @classmethod
    def get_vacancies(cls):
        """Получает список вакансий."""
        vacancies = cls.load_data(VACANCIES_FILE, [])
        if not vacancies:
            # Если файл с вакансиями пуст, используем примеры
            cls.save_data(VACANCIES_FILE, DEFAULT_VACANCIES)
            return DEFAULT_VACANCIES
        return vacancies
    
    @classmethod
    def export_analytics_to_csv(cls):
        """Экспортирует данные кандидатов в CSV-файл."""
        try:
            candidates = cls.get_candidates()
            
            with open(ANALYTICS_FILE, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Имя", "Вакансия", "Статус", "Причина отказа", "Дата"])
                
                for candidate in candidates:
                    rejection_reason = "-"
                    if candidate.get('rejection_reason'):
                        rejection_reason = f"{candidate['rejection_reason']['type']}: {candidate['rejection_reason']['reason']}"
                    
                    # Форматируем дату
                    date = datetime.fromisoformat(candidate['date']).strftime("%Y-%m-%d")
                    
                    writer.writerow([
                        candidate['name'],
                        candidate['vacancy'],
                        candidate['status'],
                        rejection_reason,
                        date
                    ])
                    
            return True
        except Exception as e:
            logger.error(f"Ошибка экспорта аналитики: {e}")
            return False 
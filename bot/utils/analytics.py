from bot.database.storage import DataStorage
from bot.config import CANDIDATE_STATUSES

class AnalyticsHelper:
    """Класс для работы с аналитикой."""
    
    @staticmethod
    def calculate_statistics():
        """Вычисляет статистику по кандидатам."""
        candidates = DataStorage.get_candidates()
        
        if not candidates:
            return None
            
        # Общее количество кандидатов
        total_candidates = len(candidates)
        
        # Считаем по статусам
        status_count = {}
        for status in CANDIDATE_STATUSES:
            status_count[status] = sum(1 for c in candidates if c['status'] == status)
            
        # Считаем по причинам отказа
        rejection_count = {
            'Компания': sum(1 for c in candidates if c.get('rejection_reason') and c['rejection_reason']['type'] == 'Компания'),
            'Кандидат': sum(1 for c in candidates if c.get('rejection_reason') and c['rejection_reason']['type'] == 'Кандидат')
        }
        
        return {
            'total': total_candidates,
            'status_count': status_count,
            'rejection_count': rejection_count
        }
    
    @staticmethod
    def generate_analytics_text():
        """Формирует текст аналитики для отправки пользователю."""
        stats = AnalyticsHelper.calculate_statistics()
        
        if not stats:
            return "Нет данных для аналитики."
            
        total_candidates = stats['total']
        status_count = stats['status_count']
        rejection_count = stats['rejection_count']
        
        # Формируем текст аналитики
        analytics_text = "📊 Аналитика по кандидатам:\n\n"
        analytics_text += f"Всего кандидатов: {total_candidates}\n\n"
        
        analytics_text += "Статусы кандидатов:\n"
        for status, count in status_count.items():
            if count > 0:
                percentage = round((count / total_candidates) * 100, 1)
                analytics_text += f"- {status}: {count} ({percentage}%)\n"
        
        analytics_text += "\nПричины отказа:\n"
        for reason_type, count in rejection_count.items():
            if count > 0:
                percentage = round((count / total_candidates) * 100, 1)
                analytics_text += f"- {reason_type}: {count} ({percentage}%)\n"
                
        return analytics_text
    
    @staticmethod
    def export_analytics():
        """Экспортирует аналитику в CSV и возвращает успешность операции."""
        return DataStorage.export_analytics_to_csv() 
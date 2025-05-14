from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
import traceback

from bot.config import (
    STATUS_CALLBACK, REASON_CALLBACK, 
    CANDIDATE_STATUSES, COMPANY_REJECTION_REASONS, CANDIDATE_REJECTION_REASONS,
    logger, COMPANY_NAME
)
from bot.database.storage import DataStorage
from bot.utils.analytics import AnalyticsHelper

class CommandHandlers:
    """Класс для обработки основных команд бота."""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        # Если это callback-запрос, то нужно ответить на него
        if update.callback_query:
            await update.callback_query.answer()
        
        # Подготавливаем текст приветствия
        greeting_text = f"Приветствую Вас! Я HR-бот компании '{COMPANY_NAME}' Чем могу помочь?\n\n" \
            "Доступные команды:\n" \
            "/start - Начать взаимодействие\n" \
            "/vacancies - Просмотр вакансий\n" \
            "/dialog - Начать диалог с кандидатом\n" \
            "/status - Установить статус кандидата\n" \
            "/rejection - Указать причину отказа\n" \
            "/analytics - Просмотр аналитики"
            
        # Отправляем логотип компании с приветственным сообщением
        logo_path = os.path.join('images', 'родан.jpg')
            
        if update.callback_query:
            # Если это callback-запрос, редактируем сообщение
            if os.path.exists(logo_path):
                # Отправим новое сообщение, так как редактировать фото нельзя
                await update.callback_query.message.reply_photo(
                    photo=open(logo_path, 'rb'),
                    caption=greeting_text
                )
                # Удалим старое сообщение
                await update.callback_query.message.delete()
            else:
                # Если логотип не найден, отправляем только текст
                await update.callback_query.message.reply_text(greeting_text)
                # Удалим старое сообщение
                await update.callback_query.message.delete()
        else:
            # Если это обычное сообщение, отправляем новое сообщение
            if os.path.exists(logo_path):
                try:
                    with open(logo_path, 'rb') as photo_file:
                        await update.message.reply_photo(
                            photo=photo_file,
                            caption=greeting_text
                        )
                        logger.info(f"Отправлен логотип из {logo_path}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке логотипа: {e}")
                    await update.message.reply_text(greeting_text)
            else:
                # Если логотип не найден, отправляем только текст
                logger.error(f"Файл логотипа не найден: {logo_path}")
                await update.message.reply_text(greeting_text)
    
    @staticmethod
    async def show_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отображает список вакансий."""
        vacancies = DataStorage.get_vacancies()
        
        if not vacancies:
            await update.message.reply_text("Сейчас нет доступных вакансий.")
            return
        
        vacancy_text = "📋 Доступные вакансии:\n\n"
        for vacancy in vacancies:
            vacancy_text += f"* {vacancy['title']}\n"
            vacancy_text += f"💼 {vacancy['description']}\n"
            vacancy_text += f"💰 Зарплата: {vacancy['salary']}\n\n"
            
        # Создаем клавиатуру с кнопкой возврата в начало
        keyboard = [
            [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
            
        await update.message.reply_text(vacancy_text, reply_markup=reply_markup)
    
    @staticmethod
    async def set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установка статуса кандидата."""
        # Формируем список кандидатов с кнопками
        candidates = DataStorage.get_candidates()
        
        if not candidates:
            await update.message.reply_text("Нет данных о кандидатах.")
            return
            
        await update.message.reply_text("Выберите кандидата для установки статуса:")
        
        keyboard = []
        for i, candidate in enumerate(candidates):
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {candidate['name']} - {candidate['vacancy']}",
                    callback_data=f"candidate_{i}_status"
                )
            ])
        
        # Добавляем кнопку для очистки списка
        keyboard.append([InlineKeyboardButton("🗑️ Очистить список", callback_data="clear_candidates")])
        
        # Добавляем кнопку для возврата в главное меню
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Кандидаты:", reply_markup=reply_markup)
    
    @staticmethod
    async def set_rejection_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установка причины отказа."""
        candidates = DataStorage.get_candidates()
        
        if not candidates:
            await update.message.reply_text("Нет данных о кандидатах.")
            return
            
        await update.message.reply_text("Выберите кандидата для указания причины отказа:")
        
        keyboard = []
        for i, candidate in enumerate(candidates):
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {candidate['name']} - {candidate['vacancy']}",
                    callback_data=f"candidate_{i}_reason"
                )
            ])
            
        # Добавляем кнопку для возврата в главное меню
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Кандидаты:", reply_markup=reply_markup)
    
    @staticmethod
    async def show_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отображает аналитику по кандидатам."""
        # Формируем текст аналитики
        analytics_text = AnalyticsHelper.generate_analytics_text()
        
        # Если нет данных, выводим сообщение
        if analytics_text == "Нет данных для аналитики.":
            await update.message.reply_text(analytics_text)
            return
        
        # Экспортируем данные в CSV
        export_success = AnalyticsHelper.export_analytics()
        
        # Создаем клавиатуру с кнопкой возврата в главное меню с красивой иконкой
        keyboard = [
            [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем результаты
        await update.message.reply_text(analytics_text, reply_markup=reply_markup)
        
        if export_success:
            await update.message.reply_text(
                "📊 Данные аналитики экспортированы в файл analytics.csv"
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось экспортировать данные аналитики."
            )
    
    @staticmethod
    async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки."""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data.split('_')
            logger.info(f"Получены данные callback: {query.data}")
            
            # Обрабатываем специальный случай для /start
            if len(data) < 2:  
                if data[0] == "/start":
                    return await CommandHandlers.start(update, context)
                return
                
            # Очистка списка кандидатов
            if data[0] == "clear" and len(data) > 1 and data[1] == "candidates":
                await CommandHandlers.handle_clear_candidates(query)
                return
                
            # Подтверждение очистки списка кандидатов
            if data[0] == "confirm" and len(data) > 1 and data[1] == "clear" and len(data) > 2 and data[2] == "candidates":
                await CommandHandlers.handle_confirm_clear_candidates(query)
                return
            
            # Обработка кнопок "Назад" - особый случай
            if data[0] == "back":
                logger.info(f"Обработка кнопки 'Назад': {query.data}")
                await CommandHandlers.handle_back_button(query, data, context)
                return
            
            # Обработка выбора кандидата
            if data[0] == "candidate":
                await CommandHandlers.handle_candidate_selection(query, data, context)
                return
                
            # Обработка установки статуса
            elif data[0] == "set" and data[1] == "status" and len(data) >= 4:
                await CommandHandlers.handle_status_setting(query, data, context)
                return
                
            # Обработка типа причины отказа
            elif data[0] == "reason" and data[1] == "type":
                await CommandHandlers.handle_reason_type_selection(query, data, context)
                return
                
            # Обработка установки причины отказа
            elif data[0] == "set" and data[1] == "reason" and len(data) >= 5:
                await CommandHandlers.handle_reason_setting(query, data, context)
                return
                
            # Если ни один из вариантов не сработал
            logger.warning(f"Неизвестный формат callback_data: {query.data}")
            await query.edit_message_text("Неизвестная команда. Пожалуйста, начните с команды /start")
                
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Ошибка при обработке нажатия кнопки: {e}\n{error_details}")
            await query.edit_message_text(f"Произошла ошибка при обработке запроса. Пожалуйста, начните действие заново с команды /start.")
    
    @staticmethod
    async def handle_back_button(query, data, context):
        """Обработка кнопок 'Назад'"""
        try:
            if data[1] == "to" and len(data) > 2 and data[2] == "candidates":
                if len(data) > 3:
                    action = data[3]  # status, reason или list
                    logger.info(f"Кнопка 'Назад', действие: {action}")
                    
                    candidates = DataStorage.get_candidates()
                    
                    if action == "list":
                        # Возвращаемся к общему списку кандидатов
                        keyboard = [
                            [InlineKeyboardButton("📋 Установить статус", callback_data="back_to_candidates_status")],
                            [InlineKeyboardButton("❌ Указать причину отказа", callback_data="back_to_candidates_reason")],
                            [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)
                        
                    elif action == "status":
                        # Показываем список кандидатов для установки статуса
                        keyboard = []
                        for i, candidate in enumerate(candidates):
                            keyboard.append([
                                InlineKeyboardButton(
                                    f"👤 {candidate['name']} - {candidate['vacancy']}",
                                    callback_data=f"candidate_{i}_status"
                                )
                            ])
                        
                        # Добавляем кнопку для очистки списка
                        keyboard.append([InlineKeyboardButton("🗑️ Очистить список", callback_data="clear_candidates")])
                        
                        # Добавляем кнопку возврата в главное меню
                        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")])
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text("Выберите кандидата для установки статуса:", reply_markup=reply_markup)
                        
                    elif action == "reason":
                        # Показываем список кандидатов для указания причины отказа
                        keyboard = []
                        for i, candidate in enumerate(candidates):
                            keyboard.append([
                                InlineKeyboardButton(
                                    f"👤 {candidate['name']} - {candidate['vacancy']}",
                                    callback_data=f"candidate_{i}_reason"
                                )
                            ])
                        
                        # Добавляем кнопку возврата в главное меню
                        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")])
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text("Выберите кандидата для указания причины отказа:", reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Ошибка при обработке кнопки 'Назад': {e}")
            await query.edit_message_text("Произошла ошибка. Пожалуйста, начните с команды /start")
    
    @staticmethod
    async def handle_candidate_selection(query, data, context):
        """Обработка выбора кандидата"""
        try:
            candidate_idx = int(data[1])
            action_type = data[2]  # status или reason
            
            candidates = DataStorage.get_candidates()
            if candidate_idx >= len(candidates):
                await query.edit_message_text("Ошибка: кандидат не найден.")
                return
            
            candidate = candidates[candidate_idx]
            context.user_data['current_candidate_idx'] = candidate_idx
            
            if action_type == "status":
                # Показываем кнопки со статусами
                keyboard = []
                
                # Добавляем эмодзи к статусам
                status_emojis = ["📞", "📝", "✅", "❌", "🕒"]
                
                for i, status in enumerate(CANDIDATE_STATUSES):
                    emoji = status_emojis[i] if i < len(status_emojis) else "📌"
                    keyboard.append([InlineKeyboardButton(f"{emoji} {status}", callback_data=f"set_status_{candidate_idx}_{i}")])
                
                # Добавляем кнопку "Назад"
                keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_candidates_status")])
                    
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"Выберите статус для кандидата {candidate['name']}:",
                    reply_markup=reply_markup
                )
                logger.info(f"Отображены статусы для кандидата с индексом {candidate_idx}")
            
            elif action_type == "reason":
                # Показываем кнопки с типами причин отказа
                keyboard = [
                    [InlineKeyboardButton("🏢 Отказ компании", callback_data=f"reason_type_{candidate_idx}_company")],
                    [InlineKeyboardButton("👨‍💼 Отказ кандидата", callback_data=f"reason_type_{candidate_idx}_candidate")],
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_candidates_reason")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"Укажите тип отказа для кандидата {candidate['name']}:",
                    reply_markup=reply_markup
                )
                logger.info(f"Отображены типы отказа для кандидата с индексом {candidate_idx}")
        except ValueError as e:
            logger.error(f"Ошибка при преобразовании индекса кандидата: {e}")
            await query.edit_message_text("Ошибка: некорректный формат данных. Пожалуйста, начните заново.")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обработке выбора кандидата: {e}")
            await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
    
    @staticmethod
    async def handle_status_setting(query, data, context):
        """Обработка установки статуса"""
        try:
            candidate_idx = int(data[2])
            
            # Восстанавливаем статус из значений константы CANDIDATE_STATUSES
            status_index = int(data[3])
            logger.info(f"Выбор статуса: индекс кандидата={candidate_idx}, индекс статуса={status_index}")
            
            if 0 <= status_index < len(CANDIDATE_STATUSES):
                status = CANDIDATE_STATUSES[status_index]
            else:
                await query.edit_message_text(f"Ошибка: недопустимый статус (индекс {status_index}).")
                return
            
            candidates = DataStorage.get_candidates()
            if candidate_idx < len(candidates):
                candidate = candidates[candidate_idx]
                candidate['status'] = status
                DataStorage.update_candidate(candidate_idx, candidate)
                
                # Создаем клавиатуру с кнопками для возврата или новой операции
                keyboard = [
                    [InlineKeyboardButton("📋 Вернуться к списку кандидатов", callback_data="back_to_candidates_status")],
                    [InlineKeyboardButton("🔄 Установить другой статус", callback_data=f"candidate_{candidate_idx}_status")],
                    [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ Статус кандидата {candidate['name']} изменен на: {status}",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(f"Ошибка: кандидат с индексом {candidate_idx} не найден.")
        except ValueError as e:
            logger.error(f"Ошибка при преобразовании индексов: {e}")
            await query.edit_message_text("Ошибка: некорректный формат данных. Пожалуйста, начните заново.")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обновлении статуса: {e}")
            await query.edit_message_text("Произошла ошибка при обновлении статуса. Пожалуйста, попробуйте еще раз.")
    
    @staticmethod
    async def handle_reason_type_selection(query, data, context):
        """Обработка выбора типа причины отказа"""
        try:
            candidate_idx = int(data[2])
            reason_type = data[3]  # company или candidate
            
            candidates = DataStorage.get_candidates()
            if candidate_idx >= len(candidates):
                await query.edit_message_text("Ошибка: кандидат не найден.")
                return
                
            keyboard = []
            reasons_list = COMPANY_REJECTION_REASONS if reason_type == "company" else CANDIDATE_REJECTION_REASONS
            
            # Добавляем эмодзи к причинам отказа
            company_reason_emojis = ["💰", "👨‍💼", "📊", "🏢", "⏱️"]
            candidate_reason_emojis = ["💰", "📍", "👨‍👩‍👧‍👦", "🏢", "🕒"]
            
            reason_emojis = company_reason_emojis if reason_type == "company" else candidate_reason_emojis
            
            for i, reason in enumerate(reasons_list):
                emoji = reason_emojis[i] if i < len(reason_emojis) else "❌"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{emoji} {reason}", 
                        callback_data=f"set_reason_{candidate_idx}_{reason_type}_{i}"
                    )
                ])
            
            # Добавляем кнопку "Назад"
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"candidate_{candidate_idx}_reason")])
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"Выберите причину отказа для кандидата {candidates[candidate_idx]['name']}:",
                reply_markup=reply_markup
            )
        except ValueError as e:
            logger.error(f"Ошибка при преобразовании индексов: {e}")
            await query.edit_message_text("Ошибка: некорректный формат данных. Пожалуйста, начните заново.")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при отображении причин отказа: {e}")
            await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
    
    @staticmethod
    async def handle_reason_setting(query, data, context):
        """Обработка установки причины отказа"""
        try:
            candidate_idx = int(data[2])
            reason_type = data[3]  # company или candidate
            reason_idx = int(data[4])
            
            candidates = DataStorage.get_candidates()
            if candidate_idx >= len(candidates):
                await query.edit_message_text("Ошибка: кандидат не найден.")
                return
                
            reasons_list = COMPANY_REJECTION_REASONS if reason_type == "company" else CANDIDATE_REJECTION_REASONS
            if reason_idx >= len(reasons_list):
                await query.edit_message_text("Ошибка: причина отказа не найдена.")
                return
                
            reason = reasons_list[reason_idx]
            
            candidate = candidates[candidate_idx]
            candidate['rejection_reason'] = {
                'type': 'Компания' if reason_type == "company" else 'Кандидат',
                'reason': reason
            }
            DataStorage.update_candidate(candidate_idx, candidate)
            
            # Создаем клавиатуру с кнопками для возврата
            keyboard = [
                [InlineKeyboardButton("📋 Вернуться к списку кандидатов", callback_data="back_to_candidates_reason")],
                [InlineKeyboardButton("🔄 Установить другую причину", callback_data=f"candidate_{candidate_idx}_reason")],
                [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ Причина отказа для кандидата {candidate['name']} установлена: {reason}",
                reply_markup=reply_markup
            )
        except ValueError as e:
            logger.error(f"Ошибка при преобразовании индексов: {e}")
            await query.edit_message_text("Ошибка: некорректный формат данных. Пожалуйста, начните заново.")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при установке причины отказа: {e}")
            await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
    
    @staticmethod
    async def handle_clear_candidates(query):
        """Обработка очистки списка кандидатов"""
        try:
            # Создаем клавиатуру для подтверждения действия
            keyboard = [
                [InlineKeyboardButton("✅ Да, очистить список", callback_data="confirm_clear_candidates")],
                [InlineKeyboardButton("❌ Нет, отменить", callback_data="back_to_candidates_status")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "⚠️ Вы действительно хотите очистить весь список кандидатов? Это действие нельзя отменить.",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Ошибка при запросе подтверждения очистки списка: {e}")
            await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
    
    @staticmethod
    async def handle_confirm_clear_candidates(query):
        """Подтверждение очистки списка кандидатов"""
        try:
            # Очищаем список кандидатов
            DataStorage.clear_candidates()
            
            # Создаем клавиатуру для возврата в главное меню
            keyboard = [
                [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "✅ Список кандидатов успешно очищен.",
                reply_markup=reply_markup
            )
            logger.info("Список кандидатов очищен")
        except Exception as e:
            logger.error(f"Ошибка при очистке списка кандидатов: {e}")
            await query.edit_message_text("Произошла ошибка при очистке списка. Пожалуйста, попробуйте еще раз.") 
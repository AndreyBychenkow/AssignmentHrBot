from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.config import (
    INTRO, RESEARCH, PRESENTATION, INVITATION, CONFIRMATION,
    COMPANY_NAME, logger
)
from bot.scripts.dialog import DIALOG_SCRIPTS
from bot.database.storage import DataStorage

class DialogHandlers:
    """Класс для обработки диалога с кандидатом."""
    
    @staticmethod
    async def start_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает диалог с кандидатом."""
        try:
            # Очищаем данные предыдущего диалога, если такие есть
            for key in list(context.user_data.keys()):
                if key.startswith(('candidate_', 'dialog_', 'interest', 'invitation', 'confirmation', 'preferred_time', 'vacancy_id')):
                    del context.user_data[key]
            
            intro_message = DIALOG_SCRIPTS[INTRO].format(company=COMPANY_NAME)
            
            # Создаем кнопки Да/Нет
            keyboard = [
                [InlineKeyboardButton("✅ Да", callback_data="intro_yes")],
                [InlineKeyboardButton("❌ Нет", callback_data="intro_no")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(intro_message, reply_markup=reply_markup)
            
            # Сохраняем время начала диалога
            context.user_data['dialog_start_time'] = datetime.now().isoformat()
            context.user_data['vacancy_id'] = 0  # Выбираем первую вакансию по умолчанию
            logger.info(f"Начат новый диалог с кандидатом, chat_id: {update.effective_chat.id}")
            return INTRO
        except Exception as e:
            logger.error(f"Ошибка при запуске диалога: {e}")
            await update.message.reply_text(
                "Извините, произошла ошибка при запуске диалога. Пожалуйста, попробуйте еще раз через несколько минут."
            )
            return ConversationHandler.END

    @staticmethod
    async def handle_intro_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ответ на начальное приветствие."""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "intro_yes":
                await query.edit_message_text("Отлично! Введите ваше имя и фамилия?")
                return RESEARCH
            elif query.data == "intro_no":
                keyboard = [
                    [InlineKeyboardButton("✅ Да, откликнулся", callback_data="intro_called_back")],
                    [InlineKeyboardButton("❌ Возможно позже", callback_data="intro_still_no")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "Понял Вас, а когда я могу с Вами связаться?", 
                    reply_markup=reply_markup
                )
                return INTRO
            elif query.data == "intro_called_back":
                await query.edit_message_text("Отлично! Как ваше имя?")
                return RESEARCH
            elif query.data == "intro_still_no":
                # Завершаем диалог, если кандидат недоступен
                keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "Понял, тогда хочу пожелать хорошего дня, до свидания!",
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
        except Exception as e:
            logger.error(f"Ошибка при обработке ответа на приветствие: {e}")
            if update.callback_query:
                keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    "Произошла ошибка. Пожалуйста, начните диалог заново с помощью команды /dialog.",
                    reply_markup=reply_markup
                )
            return ConversationHandler.END

    @staticmethod
    async def handle_research(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка имени кандидата и переход к исследованию."""
        # Сохраняем имя кандидата
        context.user_data['candidate_name'] = update.message.text
        
        # Задаем вопрос из скрипта для этапа исследования
        research_message = DIALOG_SCRIPTS[RESEARCH].format(name=context.user_data['candidate_name'])
        
        # Добавляем кнопку "Назад" для возврата к началу диалога
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_intro")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(research_message, reply_markup=reply_markup)
        return PRESENTATION

    @staticmethod
    async def handle_presentation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ответа кандидата и переход к презентации возможностей."""
        # Сохраняем ответ кандидата о его предпочтениях
        context.user_data['preferences'] = update.message.text
        
        # Выбираем вакансию для презентации
        vacancies = DataStorage.get_vacancies()
        vacancy_id = context.user_data.get('vacancy_id', 0)
        if 0 <= vacancy_id < len(vacancies):
            vacancy = vacancies[vacancy_id]
        else:
            vacancy = vacancies[0]
        
        # Формируем текст презентации
        presentation_message = DIALOG_SCRIPTS[PRESENTATION].format(
            name=context.user_data['candidate_name']
        )
        
        # Создаем кнопки Да/Нет для ответа на вопрос о заинтересованности, добавляем кнопку "Назад"
        keyboard = [
            [InlineKeyboardButton("✅ Да", callback_data="presentation_yes")],
            [InlineKeyboardButton("❌ Нет", callback_data="presentation_no")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_research")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(presentation_message, reply_markup=reply_markup)
        return INVITATION

    @staticmethod
    async def handle_presentation_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ответ на презентацию вакансии."""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "presentation_yes":
                # Если кандидат заинтересовался, переходим к приглашению на собеседование
                invitation_message = DIALOG_SCRIPTS[INVITATION].format(
                    name=context.user_data.get('candidate_name', 'Кандидат')
                )
                
                # Создаем кнопки Да/Нет для ответа на приглашение, добавляем кнопку "Назад"
                keyboard = [
                    [InlineKeyboardButton("✅ Да", callback_data="invitation_yes")],
                    [InlineKeyboardButton("❌ Нет, не получается", callback_data="invitation_no")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_presentation")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(invitation_message, reply_markup=reply_markup)
                context.user_data['interest'] = "Да, заинтересован"
                return INVITATION
            else:
                # Если кандидат не заинтересовался
                name = context.user_data.get('candidate_name', 'Кандидат')
                keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"Спасибо за ваше время, {name}! "
                    "Если у вас возникнут вопросы или вы передумаете, вы всегда можете связаться с нами. Моб. тел.: 8 920 902 2901 (Telegram, WhatsApp)",
                    reply_markup=reply_markup
                )
                context.user_data['interest'] = "Нет, не заинтересован"
                
                # Сохраняем данные о кандидате
                DialogHandlers.save_candidate_data(context)
                return ConversationHandler.END
        except Exception as e:
            logger.error(f"Ошибка при обработке ответа на презентацию: {e}")
            if update.callback_query:
                keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    "Произошла ошибка. Пожалуйста, начните диалог заново с помощью команды /dialog.",
                    reply_markup=reply_markup
                )
            return ConversationHandler.END

    @staticmethod
    async def handle_invitation_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ответ на приглашение на собеседование."""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "invitation_yes":
                # Если кандидат согласен прийти на собеседование
                confirmation_message = DIALOG_SCRIPTS[CONFIRMATION]
                
                # Создаем кнопки для подтверждения, добавляем кнопку "Назад"
                keyboard = [
                    [InlineKeyboardButton("✅ Да", callback_data="confirmation_yes")],
                    [InlineKeyboardButton("❌ Нет", callback_data="confirmation_no")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_invitation")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(confirmation_message, reply_markup=reply_markup)
                context.user_data['invitation_accepted'] = "Да"
                return CONFIRMATION
            else:
                # Если кандидат не может прийти
                name = context.user_data.get('candidate_name', 'Кандидат')
                keyboard = [[InlineKeyboardButton("🏠 В главное меню", callback_data="/start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"{name}, тогда обдумайте и сообщите свой ответ удобным для вас способом.  "
                    "Наши контакты: Моб.Тел.: 8 920 902 2901 (Telegram, WhatsApp). Будем ждать от Вас обратной связи.",
                    reply_markup=reply_markup
                )
                context.user_data['invitation_accepted'] = "Нет, предложена альтернатива"
                return CONFIRMATION
        except Exception as e:
            logger.error(f"Ошибка при обработке ответа на приглашение: {e}")
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "Произошла ошибка. Пожалуйста, начните диалог заново с помощью команды /dialog."
                )
            return ConversationHandler.END

    @staticmethod
    async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Завершение диалога после получения подтверждения."""
        try:
            if update.callback_query:
                query = update.callback_query
                await query.answer()
                
                if query.data == "confirmation_yes":
                    name = context.user_data.get('candidate_name', 'Кандидат')
                    keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"Отлично, {name}! Ждем вас на собеседовании. До встречи!",
                        reply_markup=reply_markup
                    )
                    context.user_data['confirmation'] = "Да, подтверждено"
                else:
                    name = context.user_data.get('candidate_name', 'Кандидат')
                    keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"Понял, тогда хочу пожелать хорошего дня, до свидания!",
                        reply_markup=reply_markup
                    )
                    context.user_data['confirmation'] = "Нет, отменено"
            else:
                # Если это текстовый ответ с предпочтительным временем
                context.user_data['preferred_time'] = update.message.text
                name = context.user_data.get('candidate_name', 'Кандидат')
                keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"Спасибо, {name}! Будем ждать вас в указанное время. До встречи!",
                    reply_markup=reply_markup
                )
                context.user_data['confirmation'] = "Да, назначено альтернативное время"
            
            # Сохраняем данные о кандидате
            DialogHandlers.save_candidate_data(context)
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Ошибка при обработке подтверждения: {e}")
            message = (update.callback_query.message if update.callback_query else update.message)
            if message:
                keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="/start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await message.reply_text(
                    "Произошла ошибка. Пожалуйста, начните диалог заново с помощью команды /dialog.",
                    reply_markup=reply_markup
                )
            return ConversationHandler.END

    @staticmethod
    def save_candidate_data(context):
        """Сохраняет данные кандидата в хранилище."""
        try:
            # Получаем данные о кандидате из контекста
            name = context.user_data.get('candidate_name', 'Неизвестный')
            interest = context.user_data.get('interest', 'Неизвестно')
            invitation = context.user_data.get('invitation_accepted', 'Неизвестно')
            confirmation = context.user_data.get('confirmation', 'Неизвестно')
            preferred_time = context.user_data.get('preferred_time', '')
            start_time = context.user_data.get('dialog_start_time', datetime.now().isoformat())
            
            # Формируем вакансию (пока берем первую из списка)
            vacancies = DataStorage.get_vacancies()
            vacancy_id = context.user_data.get('vacancy_id', 0)
            if 0 <= vacancy_id < len(vacancies):
                vacancy_title = vacancies[vacancy_id]['title']
            else:
                vacancy_title = "Неизвестная вакансия"
                
            # Определяем статус
            if confirmation == "Да, подтверждено" or confirmation == "Да, назначено альтернативное время":
                status = "Приглашен на собеседование"
            elif interest == "Нет, не заинтересован":
                status = "Отказался"
            else:
                status = "Обдумывает"
                
            # Формируем данные кандидата
            candidate_data = {
                'name': name,
                'vacancy': vacancy_title,
                'status': status,
                'date': start_time,
                'interest': interest,
                'invitation': invitation,
                'confirmation': confirmation,
                'preferred_time': preferred_time
            }
            
            # Сохраняем кандидата
            DataStorage.add_candidate(candidate_data)
            logger.info(f"Сохранены данные кандидата: {name} ({vacancy_title})")
            
            # Очищаем данные диалога из контекста
            for key in list(context.user_data.keys()):
                if key.startswith(('candidate_', 'dialog_', 'interest', 'invitation', 'confirmation', 'preferred_time', 'vacancy_id')):
                    del context.user_data[key]
                    
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных кандидата: {e}")
            return False

    @staticmethod
    async def handle_back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатие на кнопку 'Назад'."""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "back_to_intro":
                # Возвращаемся к начальному приветствию
                intro_message = DIALOG_SCRIPTS[INTRO].format(company=COMPANY_NAME)
                
                keyboard = [
                    [InlineKeyboardButton("✅ Да", callback_data="intro_yes")],
                    [InlineKeyboardButton("❌ Нет", callback_data="intro_no")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(intro_message, reply_markup=reply_markup)
                return INTRO
            
            elif query.data == "back_to_research":
                # Возвращаемся к этапу исследования
                name = context.user_data.get('candidate_name', 'Кандидат')
                research_message = DIALOG_SCRIPTS[RESEARCH].format(name=name)
                
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_intro")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(research_message, reply_markup=reply_markup)
                return PRESENTATION
                
            elif query.data == "back_to_presentation":
                # Возвращаемся к этапу презентации
                name = context.user_data.get('candidate_name', 'Кандидат')
                presentation_message = DIALOG_SCRIPTS[PRESENTATION].format(name=name)
                
                keyboard = [
                    [InlineKeyboardButton("✅ Да", callback_data="presentation_yes")],
                    [InlineKeyboardButton("❌ Нет", callback_data="presentation_no")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_research")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(presentation_message, reply_markup=reply_markup)
                return INVITATION
                
            elif query.data == "back_to_invitation":
                # Возвращаемся к этапу приглашения
                name = context.user_data.get('candidate_name', 'Кандидат')
                invitation_message = DIALOG_SCRIPTS[INVITATION].format(name=name)
                
                keyboard = [
                    [InlineKeyboardButton("✅ Да", callback_data="invitation_yes")],
                    [InlineKeyboardButton("❌ Нет, не получается", callback_data="invitation_no")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_presentation")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(invitation_message, reply_markup=reply_markup)
                return INVITATION
        except Exception as e:
            logger.error(f"Ошибка при обработке кнопки 'Назад': {e}")
            return ConversationHandler.END 
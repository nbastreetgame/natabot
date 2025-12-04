import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ID администратора (замените на свой Telegram ID)
ADMIN_ID = 7014721682  # Ваш ID

# Множество для хранения ID пользователей, которые уже запускали бота
registered_users = set()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение с главными кнопками"""
    
    user = update.effective_user
    
    # Уведомляем администратора ТОЛЬКО о новых пользователях
    if user.id not in registered_users:
        registered_users.add(user.id)
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"👤 Новый пользователь:\n\n"
                     f"Имя: {user.first_name} {user.last_name or ''}\n"
                     f"Username: @{user.username or 'нет'}\n"
                     f"ID: {user.id}"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу: {e}")
    
    # Создаем главные кнопки
    keyboard = [
        [KeyboardButton("💸 Тарифы"), KeyboardButton("⏳ Моя подписка")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    # Отправляем приветственное сообщение
    await update.message.reply_text(
        "Добро пожаловать! Выберите нужный раздел:",
        reply_markup=reply_markup
    )

# Обработчик кнопки "Тарифы"
async def show_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список тарифов"""
    
    # Создаем клавиатуру с тарифами
    keyboard = [
        [KeyboardButton("День")],
        [KeyboardButton("Месяц")],
        [KeyboardButton("Неделя")],
        [KeyboardButton("Год")],
        [KeyboardButton("2 месяца")],
        [KeyboardButton("👈 НАЗАД")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await update.message.reply_text(
        "Чтобы ознакомиться с тарифом, выберите необходимый, нажав на соответствующую кнопку",
        reply_markup=reply_markup
    )

# Обработчик кнопки "Моя подписка"
async def show_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает информацию о подписке"""
    
    # Создаем кнопку "Купить подписку"
    keyboard = [
        [KeyboardButton("✅ КУПИТЬ ПОДПИСКУ")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await update.message.reply_text(
        "⏳ У Вас нет действующей подписки.\n\n"
        "Ознакомьтесь с тарифами, нажав на соответствующую кнопку.",
        reply_markup=reply_markup
    )

# Обработчик нажатий на кнопки
async def handle_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор тарифа"""
    
    tariff = update.message.text
    
    # Информация о тарифах с длительностью
    tariff_info = {
        "День": {
            "price": "500.00",
            "duration": "1 день"
        },
        "Неделя": {
            "price": "1 000.00",
            "duration": "7 дней"
        },
        "Месяц": {
            "price": "2 000.00",
            "duration": "30 дней"
        },
        "2 месяца": {
            "price": "5 000.00",
            "duration": "60 дней"
        },
        "Год": {
            "price": "10 000.00",
            "duration": "365 дней"
        }
    }
    
    # Создаем кнопки для оплаты
    keyboard = [
        [KeyboardButton("💳 ОПЛАТИТЬ")],
        [KeyboardButton("👈 НАЗАД")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    info = tariff_info.get(tariff)
    if info:
        response = (
            f"Тариф: {tariff} 💋💋\n"
            f"Стоимость: {info['price']} 🇷🇺RUB\n"
            f"Срок действия: {info['duration']}\n\n"
            f"Вы получите доступ к следующим ресурсам:\n"
            f"• ❤️NATALY_GOODPORNO♨️🔞‼️ (канал)"
        )
    else:
        response = "Неизвестный тариф"
    
    # Сохраняем выбранный тариф
    context.user_data['selected_tariff'] = tariff
    
    await update.message.reply_text(response, reply_markup=reply_markup)

# Обработчик кнопки "Я ОПЛАТИЛ"
async def handle_paid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает подтверждение оплаты"""
    
    # Создаем кнопку "ОТМЕНА"
    keyboard = [
        [KeyboardButton("🚫 ОТМЕНА")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    message_text = """🤷 Оплатили?

👌 Тогда отправьте сюда картинкой (не документом!) квитанцию платежа: скриншот или фото.

На квитанции должны быть четко видны: дата, время и сумма платежа.
__________________________
За спам вы можете быть заблокированы!"""
    
    await update.message.reply_text(message_text, reply_markup=reply_markup)

# Обработчик фото (чеков)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает отправку фото чека"""
    
    user = update.effective_user
    selected_tariff = context.user_data.get('selected_tariff', 'Не указан')
    
    # Получаем фото в лучшем качестве
    photo = update.message.photo[-1]
    
    # Отправляем администратору
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=f"💳 Новый чек об оплате:\n\n"
                    f"👤 Пользователь: {user.first_name} {user.last_name or ''}\n"
                    f"Username: @{user.username or 'нет'}\n"
                    f"ID: {user.id}\n"
                    f"Тариф: {selected_tariff}"
        )
        
        # Подтверждаем пользователю
        await update.message.reply_text(
            "✅ Ваш чек получен!\n"
            "Ожидайте подтверждения от администратора."
        )
        
        # Возвращаем к началу
        await start(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка отправки чека админу: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже или свяжитесь с администратором."
        )

# Обработчик кнопки "ОТМЕНА"
async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отменяет процесс оплаты"""
    await start(update, context)

# Обработчик кнопки "НАЗАД"
async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возвращает к выбору тарифа"""
    await start(update, context)

# Обработчик кнопки "ОПЛАТИТЬ"
async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает оплату"""
    selected_tariff = context.user_data.get('selected_tariff', 'Не выбран')
    
    # Цены для каждого тарифа
    prices = {
        "День": "500.00",
        "Неделя": "1 000.00",
        "Месяц": "2 000.00",
        "2 месяца": "5 000.00",
        "Год": "10 000.00"
    }
    
    price = prices.get(selected_tariff, "0.00")
    
    payment_text = f"""Способ оплаты: На карту Т-Банк
К оплате: {price} 🇷🇺RUB
Реквизиты для оплаты:
2200701046225592
Т-банк
Наталия💖
__________________________
Вы платите физическому лицу.
Деньги поступят на счёт получателя."""
    
    # Создаем кнопки после показа реквизитов
    keyboard = [
        [KeyboardButton("⏳ Я ОПЛАТИЛ")],
        [KeyboardButton("👈 НАЗАД")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await update.message.reply_text(payment_text, reply_markup=reply_markup)

def main() -> None:
    """Запуск бота"""
    
    # Вставьте сюда токен вашего бота от @BotFather
    TOKEN = "8573720666:AAFY2LmmO8i4-MSXZuthGLh8fL2-_bjfmZc"
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    
    # Главные кнопки
    application.add_handler(MessageHandler(
        filters.Regex("^💸 Тарифы$"), 
        show_tariffs
    ))
    application.add_handler(MessageHandler(
        filters.Regex("^⏳ Моя подписка$"), 
        show_subscription
    ))
    application.add_handler(MessageHandler(
        filters.Regex("^✅ КУПИТЬ ПОДПИСКУ$"), 
        show_tariffs
    ))
    
    # Тарифы
    application.add_handler(MessageHandler(
        filters.Regex("^(День|Месяц|Неделя|Год|2 месяца)$"), 
        handle_tariff
    ))
    application.add_handler(MessageHandler(
        filters.Regex("^👈 НАЗАД$"), 
        handle_back
    ))
    application.add_handler(MessageHandler(
        filters.Regex("^💳 ОПЛАТИТЬ$"), 
        handle_payment
    ))
    application.add_handler(MessageHandler(
        filters.Regex("^⏳ Я ОПЛАТИЛ$"), 
        handle_paid
    ))
    application.add_handler(MessageHandler(
        filters.Regex("^🚫 ОТМЕНА$"), 
        handle_cancel
    ))
    
    # Обработчик фото (должен быть в конце)
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

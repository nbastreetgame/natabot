import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ID администратора
ADMIN_ID = 7014721682

# ID канала
CHANNEL_ID = -1001002199610557

# Множество для хранения ID пользователей
registered_users = set()

# Словарь для хранения активных подписок (user_id: task)
active_subscriptions = {}

# Статистика
stats_data = {
    'total_users': 0,
    'total_purchases': 0,
    'tariff_purchases': {
        "1 день ❤️": 0,
        "Неделя ❤️❤️": 0,
        "1 Месяц 💋💋": 0,
        "6 Месяцев 😇🥰🔥": 0,
        "Год🔥🍌💦👍🏻": 0,
        "НАВСЕГДА 🤩🔥😇👅🍌💦😍👍🏻": 0
    },
    'revenue': {
        "1 день ❤️": 0,
        "Неделя ❤️❤️": 0,
        "1 Месяц 💋💋": 0,
        "6 Месяцев 😇🥰🔥": 0,
        "Год🔥🍌💦👍🏻": 0,
        "НАВСЕГДА 🤩🔥😇👅🍌💦😍👍🏻": 0
    }
}

# Цены тарифов
TARIFF_PRICES = {
    "1 день ❤️": 500,
    "Неделя ❤️❤️": 1000,
    "1 Месяц 💋💋": 2000,
    "6 Месяцев 😇🥰🔥": 6000,
    "Год🔥🍌💦👍🏻": 10000,
    "НАВСЕГДА 🤩🔥😇👅🍌💦😍👍🏻": 15000
}

# Длительность тарифов в днях
TARIFF_DAYS = {
    "1 день ❤️": 1,
    "Неделя ❤️❤️": 7,
    "1 Месяц 💋💋": 30,
    "6 Месяцев 😇🥰🔥": 180,
    "Год🔥🍌💦👍🏻": 365,
    "НАВСЕГДА 🤩🔥😇👅🍌💦😍👍🏻": None  # None = навсегда
}

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение с главными кнопками"""
    
    user = update.effective_user
    
    # Уведомляем администратора только о новых пользователях
    if user.id not in registered_users:
        registered_users.add(user.id)
        stats_data['total_users'] += 1
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
    
    await update.message.reply_text(
        "Добро пожаловать! Выберите нужный раздел:",
        reply_markup=reply_markup
    )

# Обработчик кнопки "Тарифы"
async def show_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список тарифов"""
    
    keyboard = [
        [KeyboardButton("1 день ❤️")],
        [KeyboardButton("Неделя ❤️❤️")],
        [KeyboardButton("1 Месяц 💋💋")],
        [KeyboardButton("6 Месяцев 😇🥰🔥")],
        [KeyboardButton("Год🔥🍌💦👍🏻")],
        [KeyboardButton("НАВСЕГДА 🤩🔥😇👅🍌💦😍👍🏻")],
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

# Обработчик нажатий на кнопки тарифов
async def handle_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор тарифа"""
    
    tariff = update.message.text
    
    tariff_info = {
        "1 день ❤️": {
            "price": "500.00",
            "duration": "1 день"
        },
        "Неделя ❤️❤️": {
            "price": "1 000.00",
            "duration": "7 дней"
        },
        "1 Месяц 💋💋": {
            "price": "2 000.00",
            "duration": "30 дней"
        },
        "6 Месяцев 😇🥰🔥": {
            "price": "6 000.00",
            "duration": "180 дней"
        },
        "Год🔥🍌💦👍🏻": {
            "price": "10 000.00",
            "duration": "365 дней"
        },
        "НАВСЕГДА 🤩🔥😇👅🍌💦😍👍🏻": {
            "price": "15 000.00",
            "duration": "Навсегда"
        }
    }
    
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
            f"Тариф: {tariff}\n"
            f"Стоимость: {info['price']} 🇷🇺RUB\n"
            f"Срок действия: {info['duration']}\n\n"
            f"Вы получите доступ к следующим ресурсам:\n"
            f"• ❤️NATALY_GOODPORNO♨️🔞‼️ (канал)"
        )
    else:
        response = "Неизвестный тариф"
    
    context.user_data['selected_tariff'] = tariff
    
    await update.message.reply_text(response, reply_markup=reply_markup)

# Обработчик кнопки "ОПЛАТИТЬ"
async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает оплату"""
    selected_tariff = context.user_data.get('selected_tariff', 'Не выбран')
    
    prices = {
        "1 день ❤️": "500.00",
        "Неделя ❤️❤️": "1 000.00",
        "1 Месяц 💋💋": "2 000.00",
        "6 Месяцев 😇🥰🔥": "6 000.00",
        "Год🔥🍌💦👍🏻": "10 000.00",
        "НАВСЕГДА 🤩🔥😇👅🍌💦😍👍🏻": "15 000.00"
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

# Обработчик кнопки "Я ОПЛАТИЛ"
async def handle_paid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает подтверждение оплаты"""
    
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
    
    photo = update.message.photo[-1]
    
    # Создаем инлайн-кнопки для админа
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user.id}_{selected_tariff}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=f"💳 Новый чек об оплате:\n\n"
                    f"👤 Пользователь: {user.first_name} {user.last_name or ''}\n"
                    f"Username: @{user.username or 'нет'}\n"
                    f"ID: `{user.id}`\n"
                    f"Тариф: {selected_tariff}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(
            "✅ Ваш чек получен!\n"
            "Ожидайте подтверждения от администратора."
        )
        
        await start(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка отправки чека админу: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже или свяжитесь с администратором."
        )

# Функция автоматического удаления пользователя
async def remove_user_after_delay(context: ContextTypes.DEFAULT_TYPE, user_id: int, days: int):
    """Удаляет пользователя из канала через указанное количество дней"""
    await asyncio.sleep(days * 24 * 60 * 60)  # Конвертируем дни в секунды
    
    try:
        await context.bot.ban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        # Сразу разбаниваем чтобы можно было добавить снова
        await context.bot.unban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        
        # Уведомляем админа
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⏰ Подписка пользователя {user_id} истекла.\n"
                 f"Пользователь удален из канала."
        )
        
        # Удаляем из активных подписок
        if user_id in active_subscriptions:
            del active_subscriptions[user_id]
            
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя {user_id}: {e}")

# Обработчик callback кнопок (Одобрить/Отклонить)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[0]
    user_id = int(data[1])
    
    if action == "approve":
        tariff = '_'.join(data[2:])  # Собираем название тарифа обратно
        
        try:
            # Создаем invite link для пользователя
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                member_limit=1
            )
            
            # Отправляем ссылку пользователю
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Ваша оплата подтверждена!\n\n"
                     f"Тариф: {tariff}\n"
                     f"Ссылка на канал: {invite_link.invite_link}\n\n"
                     f"⚠️ Ссылка одноразовая, используйте её для входа в канал."
            )
            
            # Обновляем сообщение админа
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ ОДОБРЕНО",
                reply_markup=None
            )
            
            # Обновляем статистику
            stats_data['total_purchases'] += 1
            stats_data['tariff_purchases'][tariff] += 1
            stats_data['revenue'][tariff] += TARIFF_PRICES[tariff]
            
            # Планируем удаление если не навсегда
            days = TARIFF_DAYS.get(tariff)
            if days is not None:
                # Отменяем предыдущую подписку если была
                if user_id in active_subscriptions:
                    active_subscriptions[user_id].cancel()
                
                # Создаем новую задачу на удаление
                task = asyncio.create_task(
                    remove_user_after_delay(context, user_id, days)
                )
                active_subscriptions[user_id] = task
                
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"⏰ Пользователь {user_id} будет автоматически удален через {days} дн."
                )
            
        except Exception as e:
            logger.error(f"Ошибка одобрения: {e}")
            await query.edit_message_caption(
                caption=query.message.caption + f"\n\n❌ Ошибка: {e}",
                reply_markup=None
            )
    
    elif action == "reject":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ К сожалению, ваша оплата не подтверждена.\n"
                     "Пожалуйста, свяжитесь с администратором."
            )
            
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ ОТКЛОНЕНО",
                reply_markup=None
            )
        except Exception as e:
            logger.error(f"Ошибка отклонения: {e}")

# Обработчик команды /stats (только для админа)
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статистику (только для админа)"""
    
    user = update.effective_user
    
    # Проверяем что это админ
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    # Считаем общую выручку
    total_revenue = sum(stats_data['revenue'].values())
    
    # Считаем конверсию
    conversion = 0
    if stats_data['total_users'] > 0:
        conversion = (stats_data['total_purchases'] / stats_data['total_users']) * 100
    
    # Формируем сообщение
    stats_message = f"""📊 СТАТИСТИКА БОТА

👥 Всего пользователей: {stats_data['total_users']}
💰 Всего покупок: {stats_data['total_purchases']}
📈 Конверсия: {conversion:.1f}%
💵 Общая выручка: {total_revenue:,}₽

━━━━━━━━━━━━━━━━━━
📋 СТАТИСТИКА ПО ТАРИФАМ:

"""
    
    # Добавляем статистику по каждому тарифу
    for tariff_name, purchases in stats_data['tariff_purchases'].items():
        revenue = stats_data['revenue'][tariff_name]
        if purchases > 0:
            stats_message += f"\n{tariff_name}\n"
            stats_message += f"  Покупок: {purchases}\n"
            stats_message += f"  Выручка: {revenue:,}₽\n"
    
    await update.message.reply_text(stats_message)

# Обработчик кнопки "ОТМЕНА"
async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отменяет процесс оплаты"""
    await start(update, context)

# Обработчик кнопки "НАЗАД"
async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возвращает к выбору тарифа"""
    await start(update, context)

def main() -> None:
    """Запуск бота"""
    
    # Токен бота
    TOKEN = "8573720666:AAFY2LmmO8i4-MSXZuthGLh8fL2-_bjfmZc"
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", show_stats))
    
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
        filters.Regex("^(1 день ❤️|Неделя ❤️❤️|1 Месяц 💋💋|6 Месяцев 😇🥰🔥|Год🔥🍌💦👍🏻|НАВСЕГДА 🤩🔥😇👅🍌💦😍👍🏻)$"), 
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
    
    # Обработчик фото
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Обработчик callback кнопок
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

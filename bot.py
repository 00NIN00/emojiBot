import logging
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Замени на токен своего бота
ADMIN_USERNAME = "O_NIN_O"  # Замени на свой username БЕЗ @
CONFIG_FILE = "bot_config.json"


class ReactionBot:
    def __init__(self):
        self.current_emoji = "🎄"  # Эмоция по умолчанию
        self.load_config()

    def load_config(self):
        """Загрузка настроек из файла"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.current_emoji = config.get('emoji', '🎄')
                logger.info(f"Загружена эмоция: {self.current_emoji}")
        except FileNotFoundError:
            logger.info("Файл конфигурации не найден, используется эмоция по умолчанию")
            self.save_config()
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")

    def save_config(self):
        """Сохранение настроек в файл"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({'emoji': self.current_emoji}, f, ensure_ascii=False)
            logger.info(f"Сохранена эмоция: {self.current_emoji}")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")


bot_instance = ReactionBot()


async def set_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_emoji"""
    user = update.effective_user

    # Проверка, что команду отправил админ
    if user.username != ADMIN_USERNAME:
        logger.warning(f"Попытка смены эмоции от {user.username}")
        return

    # Проверка наличия аргумента
    if not context.args:
        await update.message.reply_text(
            "Использование: /set_emoji <эмоция>\n"
            f"Текущая эмоция: {bot_instance.current_emoji}"
        )
        return

    # Установка новой эмоции
    new_emoji = context.args[0]
    bot_instance.current_emoji = new_emoji
    bot_instance.save_config()

    await update.message.reply_text(f"✅ Эмоция изменена на: {new_emoji}")
    logger.info(f"Эмоция изменена на: {new_emoji}")


async def react_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление реакции на каждое сообщение"""
    try:
        # Не реагируем на собственные сообщения бота
        if update.effective_user.is_bot:
            return

        # Устанавливаем реакцию
        await update.message.set_reaction(bot_instance.current_emoji)
        logger.info(f"Реакция {bot_instance.current_emoji} на сообщение от {update.effective_user.username}")

    except Exception as e:
        logger.error(f"Ошибка при установке реакции: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Бот запущен!\n\n"
        "Я буду ставить реакции на все сообщения в группе.\n"
        f"Текущая эмоция: {bot_instance.current_emoji}\n\n"
        "Команды:\n"
        "/set_emoji <эмоция> - изменить эмоцию (только для админа)\n"
        "/current - показать текущую эмоцию"
    )


async def current_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущую эмоцию"""
    await update.message.reply_text(f"Текущая эмоция: {bot_instance.current_emoji}")


def main():
    """Запуск бота"""
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("set_emoji", set_emoji_command))
    application.add_handler(CommandHandler("current", current_emoji_command))

    # Обработчик всех сообщений (кроме команд)
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        react_to_message
    ))

    # Запуск бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()



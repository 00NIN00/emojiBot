import os
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
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USERNAME = "O_NIN_O"
CONFIG_FILE = "bot_config.json"


class ReactionBot:
    def __init__(self):
        self.current_emoji = "🎄"
        self.target_users = []  # Список пользователей (user_id или username)
        self.react_to_all = True  # Реагировать на всех или только на выбранных
        self.load_config()

    def load_config(self):
        """Загрузка настроек из файла"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.current_emoji = config.get('emoji', '🎄')
                self.target_users = config.get('target_users', [])
                self.react_to_all = config.get('react_to_all', True)
                logger.info(f"Загружена эмоция: {self.current_emoji}")
                logger.info(f"Целевые пользователи: {self.target_users}")
                logger.info(f"Режим: {'все пользователи' if self.react_to_all else 'выбранные пользователи'}")
        except FileNotFoundError:
            logger.info("Файл конфигурации не найден, используется настройки по умолчанию")
            self.save_config()
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")

    def save_config(self):
        """Сохранение настроек в файл"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'emoji': self.current_emoji,
                    'target_users': self.target_users,
                    'react_to_all': self.react_to_all
                }, f, ensure_ascii=False, indent=2)
            logger.info("Конфигурация сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")

    def should_react(self, user_id, username):
        """Проверка, нужно ли реагировать на сообщение пользователя"""
        if self.react_to_all:
            return True
        
        # Проверяем по user_id и username
        return (user_id in self.target_users or 
                username in self.target_users or 
                f"@{username}" in self.target_users)


bot_instance = ReactionBot()


async def set_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_emoji"""
    user = update.effective_user

    if user.username != ADMIN_USERNAME:
        logger.warning(f"Попытка смены эмоции от {user.username}")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /set_emoji <эмоция>\n"
            f"Текущая эмоция: {bot_instance.current_emoji}"
        )
        return

    new_emoji = context.args[0]
    bot_instance.current_emoji = new_emoji
    bot_instance.save_config()

    await update.message.reply_text(f"✅ Эмоция изменена на: {new_emoji}")
    logger.info(f"Эмоция изменена на: {new_emoji}")


async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить пользователя в список для реакций"""
    user = update.effective_user

    if user.username != ADMIN_USERNAME:
        logger.warning(f"Попытка добавления пользователя от {user.username}")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /add_user <username или user_id>\n"
            "Примеры:\n"
            "/add_user @username\n"
            "/add_user 123456789\n"
            "\nДля получения user_id попросите пользователя написать команду /my_id"
        )
        return

    user_identifier = context.args[0]
    
    # Убираем @ если есть
    if user_identifier.startswith('@'):
        user_identifier = user_identifier[1:]
    
    # Пытаемся преобразовать в int если это ID
    try:
        user_identifier = int(user_identifier)
    except ValueError:
        pass  # Остается строкой (username)

    if user_identifier not in bot_instance.target_users:
        bot_instance.target_users.append(user_identifier)
        bot_instance.react_to_all = False  # Автоматически переключаем в режим выбранных пользователей
        bot_instance.save_config()
        await update.message.reply_text(f"✅ Пользователь {context.args[0]} добавлен в список")
        logger.info(f"Добавлен пользователь: {user_identifier}")
    else:
        await update.message.reply_text(f"⚠️ Пользователь {context.args[0]} уже в списке")


async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить пользователя из списка"""
    user = update.effective_user

    if user.username != ADMIN_USERNAME:
        logger.warning(f"Попытка удаления пользователя от {user.username}")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /remove_user <username или user_id>\n"
            "Пример: /remove_user @username"
        )
        return

    user_identifier = context.args[0]
    
    # Убираем @ если есть
    if user_identifier.startswith('@'):
        user_identifier = user_identifier[1:]
    
    # Пытаемся преобразовать в int
    try:
        user_identifier = int(user_identifier)
    except ValueError:
        pass

    if user_identifier in bot_instance.target_users:
        bot_instance.target_users.remove(user_identifier)
        bot_instance.save_config()
        await update.message.reply_text(f"✅ Пользователь {context.args[0]} удален из списка")
        logger.info(f"Удален пользователь: {user_identifier}")
    else:
        await update.message.reply_text(f"⚠️ Пользователь {context.args[0]} не найден в списке")


async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список пользователей"""
    user = update.effective_user

    if user.username != ADMIN_USERNAME:
        return

    if not bot_instance.target_users:
        message = "📝 Список пользователей пуст\n\nРежим: реакции на всех"
    else:
        users_list = "\n".join([f"• {u}" for u in bot_instance.target_users])
        message = f"📝 Список пользователей для реакций:\n\n{users_list}\n\nРежим: только выбранные пользователи"
    
    await update.message.reply_text(message)


async def toggle_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключить режим: все/выбранные пользователи"""
    user = update.effective_user

    if user.username != ADMIN_USERNAME:
        return

    bot_instance.react_to_all = not bot_instance.react_to_all
    bot_instance.save_config()
    
    mode = "реакции на всех" if bot_instance.react_to_all else "только выбранные пользователи"
    await update.message.reply_text(f"✅ Режим изменен: {mode}")
    logger.info(f"Режим изменен: {mode}")


async def my_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать user_id пользователя"""
    user = update.effective_user
    username_info = f"@{user.username}" if user.username else "нет username"
    await update.message.reply_text(
        f"👤 Ваша информация:\n"
        f"ID: {user.id}\n"
        f"Username: {username_info}\n"
        f"Имя: {user.first_name}"
    )


async def react_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление реакции на сообщения"""
    try:
        if update.effective_user.is_bot:
            return

        user_id = update.effective_user.id
        username = update.effective_user.username

        # Проверяем, нужно ли реагировать на этого пользователя
        if not bot_instance.should_react(user_id, username):
            return

        await update.message.set_reaction(bot_instance.current_emoji)
        logger.info(f"Реакция {bot_instance.current_emoji} на сообщение от {username} (ID: {user_id})")

    except Exception as e:
        logger.error(f"Ошибка при установке реакции: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    mode = "на всех" if bot_instance.react_to_all else f"на {len(bot_instance.target_users)} пользователей"
    
    await update.message.reply_text(
        "👋 Бот запущен!\n\n"
        f"Текущая эмоция: {bot_instance.current_emoji}\n"
        f"Режим: реакции {mode}\n\n"
        "📋 Команды для всех:\n"
        "/current - показать текущую эмоцию\n"
        "/my_id - узнать свой user_id\n\n"
        "🔧 Команды для админа:\n"
        "/set_emoji <эмоция> - изменить эмоцию\n"
        "/add_user <username|id> - добавить пользователя\n"
        "/remove_user <username|id> - удалить пользователя\n"
        "/list_users - список пользователей\n"
        "/toggle_mode - переключить режим (все/выбранные)"
    )


async def current_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущую эмоцию"""
    mode = "на всех пользователей" if bot_instance.react_to_all else f"на {len(bot_instance.target_users)} пользователей"
    await update.message.reply_text(
        f"Текущая эмоция: {bot_instance.current_emoji}\n"
        f"Режим: реакции {mode}"
    )


def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("set_emoji", set_emoji_command))
    application.add_handler(CommandHandler("current", current_emoji_command))
    application.add_handler(CommandHandler("add_user", add_user_command))
    application.add_handler(CommandHandler("remove_user", remove_user_command))
    application.add_handler(CommandHandler("list_users", list_users_command))
    application.add_handler(CommandHandler("toggle_mode", toggle_mode_command))
    application.add_handler(CommandHandler("my_id", my_id_command))

    # Обработчик всех сообщений (кроме команд)
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        react_to_message
    ))

    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

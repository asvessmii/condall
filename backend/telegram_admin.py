import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import base64
import io
from PIL import Image
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

# Импорт модуля резервного копирования
try:
    from database_backup import DatabaseBackup
except ImportError:
    DatabaseBackup = None

# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\', level=logging.INFO)
logger = logging.getLogger(__name__)

# Admin configuration
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
BOT_TOKEN = os.environ.get(\'BOT_TOKEN\')
MONGO_URL = os.environ.get(\'MONGO_URL\')
DB_NAME = os.environ.get(\'DB_NAME\')

# Initialize MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


class AdminState:
    """Manage admin session states"""
    def __init__(self):
        self.states: Dict[int, Dict[str, Any]] = {}
    
    def get_state(self, user_id: int) -> Dict[str, Any]:
        return self.states.get(user_id, {})
    
    def set_state(self, user_id: int, key: str, value: Any):
        if user_id not in self.states:
            self.states[user_id] = {}
        self.states[user_id][key] = value
    
    def clear_state(self, user_id: int):
        if user_id in self.states:
            del self.states[user_id]
    
    def get_action(self, user_id: int) -> Optional[str]:
        return self.get_state(user_id).get(\'action\')
    
    def set_action(self, user_id: int, action: str):
        self.set_state(user_id, \'action\', action)


# Global state manager
admin_state = AdminState()


async def check_admin(update: Update) -> bool:
    """Check if user is admin"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    first_name = update.effective_user.first_name or "Unknown"
    
    # Log user info for debugging
    logger.info(f"User trying to access: ID={user_id}, Username=@{username}, Name={first_name}")
    
    if user_id != ADMIN_ID:
        await update.message.reply_text(
            f"❌ У вас нет прав доступа к админ панели\n\n"
            f"🆔 Ваш ID: {user_id}\n"
            f"👤 Имя: {first_name}\n"
            f"📞 Обратитесь к администратору для получения доступа"
        )
        return False
    return True


def get_main_menu_keyboard():
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🌐 Открыть сайт", web_app=WebAppInfo(url="https://admin-dashboard-24.emergent.host"))],
        [InlineKeyboardButton("📦 Управление товарами", callback_data="manage_products")],
        [InlineKeyboardButton("🏗️ Управление проектами", callback_data="manage_projects")],
        [InlineKeyboardButton("💾 Резервные копии", callback_data="backup_menu")],
        [InlineKeyboardButton("📊 Статистика", callback_data="statistics")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_products_menu_keyboard():
    """Get products management menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton("📝 Редактировать товар", callback_data="edit_product")],
        [InlineKeyboardButton("🗑️ Удалить товар", callback_data="delete_product")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_projects_menu_keyboard():
    """Get projects management menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить проект", callback_data="add_project")],
        [InlineKeyboardButton("📝 Редактировать проект", callback_data="edit_project")],
        [InlineKeyboardButton("🗑️ Удалить проект", callback_data="delete_project")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Get back to main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_products_menu_keyboard():
    """Get products management keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton("📝 Редактировать товар", callback_data="edit_product")],
        [InlineKeyboardButton("🗑️ Удалить товар", callback_data="delete_product")],
        [InlineKeyboardButton("📋 Список товаров", callback_data="list_products")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_projects_menu_keyboard():
    """Get projects management keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить проект", callback_data="add_project")],
        [InlineKeyboardButton("📝 Редактировать проект", callback_data="edit_project")],
        [InlineKeyboardButton("🗑️ Удалить проект", callback_data="delete_project")],
        [InlineKeyboardButton("📋 Список проектов", callback_data="list_projects")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard():
    """Get back button keyboard"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler for regular users"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    first_name = update.effective_user.first_name or "Unknown"
    
    # Log user info
    logger.info(f"User started bot: ID={user_id}, Username=@{username}, Name={first_name}")
    
    welcome_text = """
🏪 **Добро пожаловать в COMFORT КЛИМАТ**

Интернет-магазин кондиционеров и климатической техники!

🌐 Перейдите в наш каталог для выбора и заказа товаров:
    """
    
    keyboard = [
        [InlineKeyboardButton("🌐 Открыть каталог", web_app=WebAppInfo(url="https://admin-dashboard-24.emergent.host"))],
        [InlineKeyboardButton("📞 Связаться с нами", web_app=WebAppInfo(url="https://admin-dashboard-24.emergent.host/#contact"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command handler"""
    if not await check_admin(update):
        return
    
    admin_state.clear_state(update.effective_user.id)
    
    welcome_text = """
🔧 **Админ панель COMFORT КЛИМАТ**

Добро пожаловать в панель управления интернет-магазином кондиционеров!

Вы можете:
• Управлять каталогом товаров
• Редактировать проекты в разделе "О нас"
• Просматривать статистику

Выберите действие:
    """
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )


async def show_products_menu(query):
    """Show products management menu"""
    await query.edit_message_text(
        "📦 **Управление товарами**\n\nВыберите действие:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_products_menu_keyboard()
    )

async def start_product_creation(query, user_id):
    """Start product creation process"""
    admin_state.set_action(user_id, "add_product_name")
    admin_state.set_state(user_id, "new_product", {})
    await query.edit_message_text(
        "➕ **Добавление нового товара**\n\n📝 Введите название товара:",
        parse_mode=ParseMode.MARKDOWN
    )

async def show_products_list(query, action_type):
    """Show list of products for editing or deletion"""
    products = await db.products.find().to_list(1000)
    
    if not products:
        await query.edit_message_text(
            "❌ Товары не найдены",
            reply_markup=get_back_keyboard()
        )
        return
    
    keyboard = []
    for product in products:
        button_text = f"{\'📝\' if action_type == \'edit\' else \'🗑️\'} {product[\'name\]}"
        callback_data = f"{\'edit\' if action_type == \'edit\' else \'delete\'}_product_{product[\'id\]}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="manage_products")])
    
    await query.edit_message_text(
        f"{\'📝\' if action_type == \'edit\' else \'🗑️\'} **Выберите товар:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_product_confirm(query, product_id):
    """Show confirmation for product deletion"""
    product = await db.products.find_one({"id": product_id})
    if not product:
        await query.answer("❌ Товар не найден", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_product_{product_id}")],
        [InlineKeyboardButton("❌ Нет, отменить", callback_data="manage_products")]
    ]
    
    await query.edit_message_text(
        f"🗑️ Вы уверены, что хотите удалить товар \'{product[\'name\]}\'?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_projects_menu(query):
    """Show projects management menu"""
    await query.edit_message_text(
        "🏗️ **Управление проектами**\n\nВыберите действие:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_projects_menu_keyboard()
    )

async def show_projects_list(query, action_type):
    """Show list of projects for editing or deletion"""
    projects = await db.projects.find().to_list(1000)
    
    if not projects:
        await query.edit_message_text(
            "❌ Проекты не найдены",
            reply_markup=get_back_keyboard()
        )
        return
    
    keyboard = []
    for project in projects:
        button_text = f"{\'📝\' if action_type == \'edit\' else \'🗑️\'} {project[\'title\]}"
        callback_data = f"{\'edit\' if action_type == \'edit\' else \'delete\'}_project_{project[\'id\]}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="manage_projects")])
    
    await query.edit_message_text(
        f"{\'📝\' if action_type == \'edit\' else \'🗑️\'} **Выберите проект:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_project_confirm(query, project_id):
    """Show confirmation for project deletion"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        await query.answer("❌ Проект не найден", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_project_{project_id}")],
        [InlineKeyboardButton("❌ Нет, отменить", callback_data="manage_projects")]
    ]
    
    await query.edit_message_text(
        f"🗑️ Вы уверены, что хотите удалить проект \'{project[\'title\]}\'?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_project(query, project_id):
    """Delete a project"""
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count > 0:
        await query.edit_message_text(
            "✅ Проект успешно удален!",
            reply_markup=get_back_keyboard()
        )
    else:
        await query.edit_message_text(
            "❌ Ошибка при удалении проекта",
            reply_markup=get_back_keyboard()
        )

async def delete_product(query, product_id):
    """Delete a product"""
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count > 0:
        await query.edit_message_text(
            "✅ Товар успешно удален!",
            reply_markup=get_back_keyboard()
        )
    else:
        await query.edit_message_text(
            "❌ Ошибка при удалении товара",
            reply_markup=get_back_keyboard()
        )

async def show_backup_menu(query):
    """Show backup management menu"""
    keyboard = [
        [InlineKeyboardButton("📥 Создать резервную копию", callback_data="create_backup")],
        [InlineKeyboardButton("📤 Восстановить из копии", callback_data="restore_backup")],
        [InlineKeyboardButton("📊 Статус резервных копий", callback_data="backup_status")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        "💾 **Управление резервными копиями**\n\nВыберите действие:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_project_creation(query, user_id):
    """Start project creation process"""
    admin_state.set_action(user_id, "add_project_title")
    admin_state.set_state(user_id, "new_project", {})
    await query.edit_message_text(
        "➕ **Добавление нового проекта**\n\n📝 Введите название проекта:",
        parse_mode=ParseMode.MARKDOWN
    )

async def create_backup_handler(query):
    """Handle backup creation"""
    if DatabaseBackup is None:
        await query.edit_message_text(
            "❌ Модуль резервного копирования недоступен",
            reply_markup=get_back_keyboard()
        )
        return
    
    try:
        backup = DatabaseBackup()
        filename = await backup.create_backup()
        await query.edit_message_text(
            f"✅ Резервная копия создана успешно!\nФайл: {filename}",
            reply_markup=get_back_keyboard()
        )
    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка при создании резервной копии: {str(e)}",
            reply_markup=get_back_keyboard()
        )

async def restore_backup_handler(query):
    """Handle backup restoration"""
    if DatabaseBackup is None:
        await query.edit_message_text(
            "❌ Модуль резервного копирования недоступен",
            reply_markup=get_back_keyboard()
        )
        return
    
    try:
        backup = DatabaseBackup()
        backups = await backup.list_backups()
        if not backups:
            await query.edit_message_text(
                "❌ Резервные копии не найдены",
                reply_markup=get_back_keyboard()
            )
            return
        
        keyboard = []
        for b in backups:
            keyboard.append([InlineKeyboardButton(b, callback_data=f"restore_{b}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="backup_menu")])
        
        await query.edit_message_text(
            "📤 Выберите резервную копию для восстановления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка при получении списка резервных копий: {str(e)}",
            reply_markup=get_back_keyboard()
        )

async def show_backup_status(query):
    """Show backup status"""
    if DatabaseBackup is None:
        await query.edit_message_text(
            "❌ Модуль резервного копирования недоступен",
            reply_markup=get_back_keyboard()
        )
        return
    
    try:
        backup = DatabaseBackup()
        status = await backup.get_status()
        await query.edit_message_text(
            f"📊 **Статус резервных копий**\n\n{status}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard()
        )
    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка при получении списка резервных копий: {str(e)}",
            reply_markup=get_back_keyboard()
        )


async def edit_product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("edit_product_"):
        product_id = data.replace("edit_product_", "")
        product = await db.products.find_one({"id": product_id})
        if not product:
            await query.edit_message_text("❌ Товар не найден", reply_markup=get_back_keyboard())
            return

        keyboard = [
            [InlineKeyboardButton(f"📝 Название: {product.get(\'name\', \'Не указано\')}", callback_data=f"edit_product_name_{product_id}")],
            [InlineKeyboardButton(f"📝 Краткое описание: {product.get(\'short_description\', \'Не указано\')}", callback_data=f"edit_product_short_desc_{product_id}")],
            [InlineKeyboardButton(f"📝 Описание: {product.get(\'description\', \'Не указано\')}", callback_data=f"edit_product_desc_{product_id}")],
            [InlineKeyboardButton(f"💰 Цена: {product.get(\'price\', \'Не указано\')}", callback_data=f"edit_product_price_{product_id}")],
            [InlineKeyboardButton("⚙️ Характеристики", callback_data=f"edit_product_specs_{product_id}")],
            [InlineKeyboardButton("📷 Изображение", callback_data=f"edit_product_image_{product_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="manage_products")]
        ]
        await query.edit_message_text(
            f"📝 **Редактирование товара: {product.get(\'name\', \'\')}**\n\nВыберите, что хотите изменить:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def edit_project_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("edit_project_"):
        project_id = data.replace("edit_project_", "")
        project = await db.projects.find_one({"id": project_id})
        if not project:
            await query.edit_message_text("❌ Проект не найден", reply_markup=get_back_keyboard())
            return

        keyboard = [
            [InlineKeyboardButton(f"📝 Название: {project.get(\'title\', \'Не указано\')}", callback_data=f"edit_project_title_{project_id}")],
            [InlineKeyboardButton(f"📝 Описание: {project.get(\'description\', \'Не указано\')}", callback_data=f"edit_project_desc_{project_id}")],
            [InlineKeyboardButton(f"📍 Адрес: {project.get(\'address\', \'Не указано\')}", callback_data=f"edit_project_address_{project_id}")],
            [InlineKeyboardButton("📷 Изображения", callback_data=f"edit_project_images_{project_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="manage_projects")]
        ]
        await query.edit_message_text(
            f"📝 **Редактирование проекта: {project.get(\'title\', \'\')}**\n\nВыберите, что хотите изменить:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "manage_products":
        await show_products_menu(query)
    elif data == "manage_projects":
        await show_projects_menu(query)
    elif data == "main_menu":
        await admin_command(update, context)
    elif data == "add_product":
        await start_product_creation(query, user_id)
    elif data == "edit_product":
        await show_products_list(query, "edit")
    elif data == "delete_product":
        await show_products_list(query, "delete")
    elif data.startswith("delete_product_"):
        product_id = data.replace("delete_product_", "")
        await delete_product_confirm(query, product_id)
    elif data.startswith("confirm_delete_product_"):
        product_id = data.replace("confirm_delete_product_", "")
        await delete_product(query, product_id)
    elif data == "add_project":
        await start_project_creation(query, user_id)
    elif data == "edit_project":
        await show_projects_list(query, "edit")
    elif data == "delete_project":
        await show_projects_list(query, "delete")
    elif data.startswith("delete_project_"):
        project_id = data.replace("delete_project_", "")
        await delete_project_confirm(query, project_id)
    elif data.startswith("confirm_delete_project_"):
        project_id = data.replace("confirm_delete_project_", "")
        await delete_project(query, project_id)
    elif data == "backup_menu":
        await show_backup_menu(query)
    elif data == "create_backup":
        await create_backup_handler(query)
    elif data == "restore_backup":
        await restore_backup_handler(query)
    elif data == "backup_status":
        await show_backup_status(query)
    elif data.startswith("restore_"):
        filename = data.replace("restore_", "")
        if DatabaseBackup is None:
            await query.edit_message_text(
                "❌ Модуль резервного копирования недоступен",
                reply_markup=get_back_keyboard()
            )
            return
        try:
            backup = DatabaseBackup()
            await backup.restore_backup(filename)
            await query.edit_message_text(
                f"✅ База данных успешно восстановлена из {filename}!",
                reply_markup=get_back_keyboard()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка при восстановлении резервной копии: {str(e)}",
                reply_markup=get_back_keyboard()
            )
    elif data == "statistics":
        await query.edit_message_text("📊 Статистика пока недоступна.", reply_markup=get_back_keyboard())

    # Product editing handlers
    elif data.startswith("edit_product_name_"):
        product_id = data.replace("edit_product_name_", "")
        admin_state.set_action(user_id, f"edit_product_name_{product_id}")
        await query.edit_message_text("📝 Введите новое название товара:")
    
    elif data.startswith("edit_product_short_desc_"):
        product_id = data.replace("edit_product_short_desc_", "")
        admin_state.set_action(user_id, f"edit_product_short_desc_{product_id}")
        await query.edit_message_text("📝 Введите новое краткое описание товара:")
    
    elif data.startswith("edit_product_desc_"):
        product_id = data.replace("edit_product_desc_", "")
        admin_state.set_action(user_id, f"edit_product_desc_{product_id}")
        await query.edit_message_text("📝 Введите новое подробное описание товара:")
    
    elif data.startswith("edit_product_price_"):
        product_id = data.replace("edit_product_price_", "")
        admin_state.set_action(user_id, f"edit_product_price_{product_id}")
        await query.edit_message_text("💰 Введите новую цену товара:")
    
    elif data.startswith("edit_product_specs_"):
        product_id = data.replace("edit_product_specs_", "")
        admin_state.set_action(user_id, f"edit_product_specs_{product_id}")
        await query.edit_message_text(
            "⚙️ Введите новые характеристики товара в формате:\n"
            "Характеристика1: Значение1\n"
            "Характеристика2: Значение2"
        )
    
    elif data.startswith("edit_product_image_"):
        product_id = data.replace("edit_product_image_", "")
        admin_state.set_action(user_id, f"edit_product_image_{product_id}")
        await query.edit_message_text("📷 Отправьте новое изображение товара:")
    
    # Project editing handlers
    elif data.startswith("edit_project_title_"):
        project_id = data.replace("edit_project_title_", "")
        admin_state.set_action(user_id, f"edit_project_title_{project_id}")
        await query.edit_message_text("📝 Введите новое название проекта:")
    
    elif data.startswith("edit_project_desc_"):
        project_id = data.replace("edit_project_desc_", "")
        admin_state.set_action(user_id, f"edit_project_desc_{project_id}")
        await query.edit_message_text("📝 Введите новое описание проекта:")
    
    elif data.startswith("edit_project_address_"):
        project_id = data.replace("edit_project_address_", "")
        admin_state.set_action(user_id, f"edit_project_address_{project_id}")
        await query.edit_message_text("📍 Введите новый адрес проекта:")
    
    elif data.startswith("edit_project_images_"):
        project_id = data.replace("edit_project_images_", "")
        admin_state.set_action(user_id, f"edit_project_images_{project_id}")
        admin_state.set_state(user_id, "new_project_images", [])
        await query.edit_message_text("📷 Отправьте новые изображения проекта:")


async def check_admin_callback(query) -> bool:
    """Check if user is admin for callback"""
    user_id = query.from_user.id
    username = query.from_user.username or "Unknown"
    first_name = query.from_user.first_name or "Unknown"
    
    # Log user info for debugging
    logger.info(f"User trying to access via callback: ID={user_id}, Username=@{username}, Name={first_name}")
    
    if user_id != ADMIN_ID:
        await query.answer(
            f"❌ У вас нет прав доступа к админ панели\n"
            f"🆔 Ваш ID: {user_id}\n"
            f"👤 Имя: {first_name}", 
            show_alert=True
        )
        return False
    return True


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    if not await check_admin(update):
        return
    
    user_id = update.effective_user.id
    action = admin_state.get_action(user_id)
    text = update.message.text
    
    if not action:
        await update.message.reply_text(
            "Используйте /admin для открытия админ панели",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Handle product addition
    if action == "add_product_name":
        admin_state.set_state(user_id, "new_product", {"name": text})
        admin_state.set_action(user_id, "add_product_short_description")
        await update.message.reply_text("📝 Введите краткое описание товара:")
    
    elif action == "add_product_short_description":
        product_data = admin_state.get_state(user_id).get("new_product", {})
        product_data["short_description"] = text
        admin_state.set_state(user_id, "new_product", product_data)
        admin_state.set_action(user_id, "add_product_description")
        await update.message.reply_text("📝 Введите подробное описание товара:")
    
    elif action == "add_product_description":
        product_data = admin_state.get_state(user_id).get("new_product", {})
        product_data["description"] = text
        admin_state.set_state(user_id, "new_product", product_data)
        admin_state.set_action(user_id, "add_product_price")
        await update.message.reply_text("💰 Введите цену товара (только число):")
    
    elif action == "add_product_price":
        try:
            price = float(text)
            product_data = admin_state.get_state(user_id).get("new_product", {})
            product_data["price"] = price
            admin_state.set_state(user_id, "new_product", product_data)
            admin_state.set_action(user_id, "add_product_specifications")
            await update.message.reply_text(
                "⚙️ Введите характеристики товара в формате:\n"
                "Характеристика1: Значение1\n"
                "Характеристика2: Значение2\n\n"
                "Например:\n"
                "Мощность охлаждения: 3.5 кВт\n"
                "Площадь помещения: 35 м²"
            )
        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите корректную цену (только число)")
    
    elif action == "add_product_specifications":
        specifications = {}
        for line in text.split(\'\n\'):
            if \':\' in line:
                key, value = line.split(\':\', 1)
                specifications[key.strip()] = value.strip()
        
        product_data = admin_state.get_state(user_id).get("new_product", {})
        product_data["specifications"] = specifications
        admin_state.set_state(user_id, "new_product", product_data)
        admin_state.set_action(user_id, "add_product_image")
        await update.message.reply_text("📷 Отправьте изображение товара:")
    
    # Handle project addition
    elif action == "add_project_title":
        admin_state.set_state(user_id, "new_project", {"title": text})
        admin_state.set_action(user_id, "add_project_description")
        await update.message.reply_text("📝 Введите описание проекта:")
    
    elif action == "add_project_description":
        project_data = admin_state.get_state(user_id).get("new_project", {})
        project_data["description"] = text
        admin_state.set_state(user_id, "new_project", project_data)
        admin_state.set_action(user_id, "add_project_address")
        await update.message.reply_text("📍 Введите адрес проекта:")
    
    elif action == "add_project_address":
        project_data = admin_state.get_state(user_id).get("new_project", {})
        project_data["address"] = text
        admin_state.set_state(user_id, "new_project", project_data)
        admin_state.set_action(user_id, "add_project_images")
        await update.message.reply_text("📷 Отправьте изображения проекта (можно несколько):")
    
    # Handle product editing
    elif action.startswith("edit_product_name_"):
        product_id = action.replace("edit_product_name_", "")
        await db.products.update_one(
            {"id": product_id}, 
            {"$set": {"name": text}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Название товара обновлено!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action.startswith("edit_product_short_desc_"):
        product_id = action.replace("edit_product_short_desc_", "")
        await db.products.update_one(
            {"id": product_id}, 
            {"$set": {"short_description": text}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Краткое описание товара обновлено!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action.startswith("edit_product_desc_"):
        product_id = action.replace("edit_product_desc_", "")
        await db.products.update_one(
            {"id": product_id}, 
            {"$set": {"description": text}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Описание товара обновлено!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action.startswith("edit_product_price_"):
        try:
            price = float(text)
            product_id = action.replace("edit_product_price_", "")
            await db.products.update_one(
                {"id": product_id}, 
                {"$set": {"price": price}}
            )
            admin_state.clear_state(user_id)
            await update.message.reply_text(
                "✅ Цена товара обновлена!",
                reply_markup=get_main_menu_keyboard()
            )
        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите корректную цену (только число)")
    
    elif action.startswith("edit_product_specs_"):
        specifications = {}
        for line in text.split(\'\n\'):
            if \':\' in line:
                key, value = line.split(\':\', 1)
                specifications[key.strip()] = value.strip()
        
        product_id = action.replace("edit_product_specs_", "")
        await db.products.update_one(
            {"id": product_id}, 
            {"$set": {"specifications": specifications}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Характеристики товара обновлены!",
            reply_markup=get_main_menu_keyboard()
        )
    
    # Handle project editing
    elif action.startswith("edit_project_title_"):
        project_id = action.replace("edit_project_title_", "")
        await db.projects.update_one(
            {"id": project_id}, 
            {"$set": {"title": text}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Название проекта обновлено!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action.startswith("edit_project_desc_"):
        project_id = action.replace("edit_project_desc_", "")
        await db.projects.update_one(
            {"id": project_id}, 
            {"$set": {"description": text}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Описание проекта обновлено!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action.startswith("edit_project_address_"):
        project_id = action.replace("edit_project_address_", "")
        await db.projects.update_one(
            {"id": project_id}, 
            {"$set": {"address": text}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Адрес проекта обновлен!",
            reply_markup=get_main_menu_keyboard()
        )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads"""
    if not await check_admin(update):
        return
    
    user_id = update.effective_user.id
    action = admin_state.get_action(user_id)
    
    if action == "add_product_image":
        # Download photo
        photo = update.message.photo[-1]  # Get highest resolution
        file = await context.bot.get_file(photo.file_id)
        
        # Convert to base64
        photo_bytes = await file.download_as_bytearray()
        image_base64 = base64.b64encode(photo_bytes).decode(\'utf-8\')
        
        # Save product
        product_data = admin_state.get_state(user_id).get("new_product", {})
        product_data["image_url"] = f"data:image/jpeg;base64,{image_base64}"
        product_data["created_at"] = datetime.utcnow()
        product_data["id"] = str(db.products.count_documents({}) + 1) # Simple ID generation
        
        await db.products.insert_one(product_data)
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Товар успешно добавлен!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action.startswith("edit_product_image_"):
        product_id = action.replace("edit_product_image_", "")
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        image_base64 = base64.b64encode(photo_bytes).decode(\'utf-8\')
        
        await db.products.update_one(
            {"id": product_id},
            {"$set": {"image_url": f"data:image/jpeg;base64,{image_base64}"}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Изображение товара обновлено!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action == "add_project_images":
        project_data = admin_state.get_state(user_id).get("new_project", {})
        current_images = project_data.get("image_urls", [])
        
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        image_base64 = base64.b64encode(photo_bytes).decode(\'utf-8\')
        current_images.append(f"data:image/jpeg;base64,{image_base64}")
        
        admin_state.set_state(user_id, "new_project", {"image_urls": current_images})
        
        keyboard = [
            [InlineKeyboardButton("✅ Готово", callback_data="finish_add_project_images")],
            [InlineKeyboardButton("➕ Добавить еще", callback_data="add_more_project_images")]
        ]
        await update.message.reply_text(
            "📷 Изображение добавлено. Отправьте еще или нажмите \"Готово\":",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action.startswith("edit_project_images_"):
        project_id = action.replace("edit_project_images_", "")
        project = await db.projects.find_one({"id": project_id})
        if not project:
            await update.message.reply_text("❌ Проект не найден", reply_markup=get_back_keyboard())
            return

        current_images = project.get("image_urls", [])
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        image_base64 = base64.b64encode(photo_bytes).decode(\'utf-8\')
        current_images.append(f"data:image/jpeg;base64,{image_base64}")

        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"image_urls": current_images}}
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Готово", callback_data="finish_edit_project_images")],
            [InlineKeyboardButton("➕ Добавить еще", callback_data="add_more_project_images")]
        ]
        await update.message.reply_text(
            "📷 Изображение добавлено. Отправьте еще или нажмите \"Готово\":",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def finish_add_project_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    project_data = admin_state.get_state(user_id).get("new_project", {})
    project_data["created_at"] = datetime.utcnow()
    project_data["id"] = str(db.projects.count_documents({}) + 1) # Simple ID generation
    
    await db.projects.insert_one(project_data)
    admin_state.clear_state(user_id)
    await query.edit_message_text(
        "✅ Проект успешно добавлен!",
        reply_markup=get_main_menu_keyboard()
    )

async def finish_edit_project_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    admin_state.clear_state(user_id)
    await query.edit_message_text(
        "✅ Изображения проекта обновлены!",
        reply_markup=get_main_menu_keyboard()
    )

async def add_more_project_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = admin_state.get_action(user_id)
    if action == "add_project_images":
        await query.edit_message_text("📷 Отправьте следующее изображение проекта:")
    elif action.startswith("edit_project_images_"):
        await query.edit_message_text("📷 Отправьте следующее изображение проекта:")


async def list_products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = await db.products.find().to_list(1000)

    if not products:
        await query.edit_message_text("❌ Товары не найдены", reply_markup=get_back_keyboard())
        return

    product_list_text = "📋 **Список товаров:**\n\n"
    for product in products:
        product_list_text += f"• **{product.get(\'name\', \'Не указано\')}** (ID: {product.get(\'id\', \'Не указано\')})\n"

    await query.edit_message_text(
        product_list_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_keyboard()
    )

async def list_projects_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    projects = await db.projects.find().to_list(1000)

    if not projects:
        await query.edit_message_text("❌ Проекты не найдены", reply_markup=get_back_keyboard())
        return

    project_list_text = "📋 **Список проектов:**\n\n"
    for project in projects:
        project_list_text += f"• **{project.get(\'title\', \'Не указано\')}** (ID: {project.get(\'id\', \'Не указано\')})\n"

    await query.edit_message_text(
        project_list_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_keyboard()
    )


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("admin", admin_command))

    # Callback queries
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    # Add specific handlers for edit actions
    application.add_handler(CallbackQueryHandler(edit_product_handler, pattern=r\'^edit_product_\w+$\' ))
    application.add_handler(CallbackQueryHandler(edit_project_handler, pattern=r\'^edit_project_\w+$\' ))
    application.add_handler(CallbackQueryHandler(finish_add_project_images, pattern=\'^finish_add_project_images$\' ))
    application.add_handler(CallbackQueryHandler(finish_edit_project_images, pattern=\'^finish_edit_project_images$\' ))
    application.add_handler(CallbackQueryHandler(add_more_project_images, pattern=\'^add_more_project_images$\' ))
    application.add_handler(CallbackQueryHandler(list_products_handler, pattern=\'^list_products$\' ))
    application.add_handler(CallbackQueryHandler(list_projects_handler, pattern=\'^list_projects$\' ))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()



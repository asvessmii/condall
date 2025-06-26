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

# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Admin configuration
ADMIN_ID = 7470811680
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

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
        return self.get_state(user_id).get('action')
    
    def set_action(self, user_id: int, action: str):
        self.set_state(user_id, 'action', action)


# Global state manager
admin_state = AdminState()


async def check_admin(update: Update) -> bool:
    """Check if user is admin"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав доступа к админ панели")
        return False
    return True


def get_main_menu_keyboard():
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🌐 Открыть сайт", web_app=WebAppInfo(url="https://54983115-be26-4c76-b596-72209d35aa19.preview.emergentagent.com"))],
        [InlineKeyboardButton("📦 Управление товарами", callback_data="manage_products")],
        [InlineKeyboardButton("🏗️ Управление проектами", callback_data="manage_projects")],
        [InlineKeyboardButton("📊 Статистика", callback_data="statistics")]
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
    """Start command handler"""
    if not await check_admin(update):
        return
    
    admin_state.clear_state(update.effective_user.id)
    
    welcome_text = """
🔧 **Админ панель КЛИМАТ ТЕХНО**

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


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not await check_admin_callback(query):
        return
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "main_menu":
        admin_state.clear_state(user_id)
        await query.edit_message_text(
            "🔧 **Админ панель КЛИМАТ ТЕХНО**\n\nВыберите действие:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
    
    elif data == "manage_products":
        await query.edit_message_text(
            "📦 **Управление товарами**\n\nВыберите действие:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_products_menu_keyboard()
        )
    
    elif data == "manage_projects":
        await query.edit_message_text(
            "🏗️ **Управление проектами**\n\nВыберите действие:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_projects_menu_keyboard()
        )
    
    elif data == "add_product":
        admin_state.set_action(user_id, "add_product_name")
        admin_state.set_state(user_id, "new_product", {})
        await query.edit_message_text(
            "➕ **Добавление нового товара**\n\n📝 Введите название товара:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "add_project":
        admin_state.set_action(user_id, "add_project_title")
        admin_state.set_state(user_id, "new_project", {})
        await query.edit_message_text(
            "➕ **Добавление нового проекта**\n\n📝 Введите название проекта:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "list_products":
        await list_products(query)
    
    elif data == "list_projects":
        await list_projects(query)
    
    elif data == "edit_product":
        await show_products_for_edit(query)
    
    elif data == "edit_project":
        await show_projects_for_edit(query)
    
    elif data == "delete_product":
        await show_products_for_delete(query)
    
    elif data == "delete_project":
        await show_projects_for_delete(query)
    
    elif data.startswith("edit_product_"):
        product_id = data.replace("edit_product_", "")
        await start_product_edit(query, product_id)
    
    elif data.startswith("edit_project_"):
        project_id = data.replace("edit_project_", "")
        await start_project_edit(query, project_id)
    
    elif data.startswith("delete_product_"):
        product_id = data.replace("delete_product_", "")
        await delete_product(query, product_id)
    
    elif data.startswith("delete_project_"):
        project_id = data.replace("delete_project_", "")
        await delete_project(query, project_id)
    
    elif data == "statistics":
        await show_statistics(query)
    
    elif data == "finish_project":
        user_id = query.from_user.id
        await finish_project_creation(query, user_id)
    
    elif data == "continue_images":
        await query.edit_message_text(
            "📷 Отправьте еще одно изображение проекта:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "finish_project_images":
        user_id = query.from_user.id
        await finish_project_images_edit(query, user_id)
    
    elif data == "continue_project_images":
        await query.edit_message_text(
            "📷 Отправьте еще одно изображение проекта:",
            parse_mode=ParseMode.MARKDOWN
        )


async def check_admin_callback(query) -> bool:
    """Check if user is admin for callback"""
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.answer("❌ У вас нет прав доступа к админ панели", show_alert=True)
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
            "Используйте /start для открытия админ панели",
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
        for line in text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
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
        image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Save product
        product_data = admin_state.get_state(user_id).get("new_product", {})
        product_data["image_url"] = f"data:image/jpeg;base64,{image_base64}"
        product_data["created_at"] = datetime.utcnow()
        
        # Generate UUID for product
        import uuid
        product_data["id"] = str(uuid.uuid4())
        
        # Save to database
        await db.products.insert_one(product_data)
        
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            f"✅ Товар '{product_data['name']}' успешно добавлен!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action == "add_project_images":
        # Download photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Convert to base64
        photo_bytes = await file.download_as_bytearray()
        image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Add to project images
        project_data = admin_state.get_state(user_id).get("new_project", {})
        if "images" not in project_data:
            project_data["images"] = []
        project_data["images"].append(f"data:image/jpeg;base64,{image_base64}")
        admin_state.set_state(user_id, "new_project", project_data)
        
        # Ask for more images or finish
        keyboard = [
            [InlineKeyboardButton("✅ Завершить", callback_data="finish_project")],
            [InlineKeyboardButton("➕ Добавить еще фото", callback_data="continue_images")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📷 Изображение добавлено! Всего: {len(project_data['images'])}\n\n"
            "Хотите добавить еще изображения?",
            reply_markup=reply_markup
        )
    
    elif action.startswith("edit_product_image_"):
        # Download photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Convert to base64
        photo_bytes = await file.download_as_bytearray()
        image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        product_id = action.replace("edit_product_image_", "")
        await db.products.update_one(
            {"id": product_id}, 
            {"$set": {"image_url": f"data:image/jpeg;base64,{image_base64}"}}
        )
        admin_state.clear_state(user_id)
        await update.message.reply_text(
            "✅ Изображение товара обновлено!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif action.startswith("edit_project_images_"):
        # Download photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Convert to base64
        photo_bytes = await file.download_as_bytearray()
        image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Add to new images list
        new_images = admin_state.get_state(user_id).get("new_project_images", [])
        new_images.append(f"data:image/jpeg;base64,{image_base64}")
        admin_state.set_state(user_id, "new_project_images", new_images)
        
        # Ask for more images or finish
        keyboard = [
            [InlineKeyboardButton("✅ Завершить", callback_data="finish_project_images")],
            [InlineKeyboardButton("➕ Добавить еще фото", callback_data="continue_project_images")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📷 Изображение добавлено! Всего: {len(new_images)}\n\n"
            "Хотите добавить еще изображения?",
            reply_markup=reply_markup
        )


async def list_products(query):
    """List all products"""
    products = await db.products.find().to_list(1000)
    
    if not products:
        await query.edit_message_text(
            "📦 **Список товаров**\n\n❌ Товары не найдены",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard()
        )
        return
    
    text = "📦 **Список товаров:**\n\n"
    for i, product in enumerate(products, 1):
        text += f"{i}. **{product['name']}**\n"
        text += f"   💰 {product['price']:,.0f} ₽\n"
        text += f"   📝 {product['short_description']}\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_keyboard()
    )


async def list_projects(query):
    """List all projects"""
    projects = await db.projects.find().to_list(1000)
    
    if not projects:
        await query.edit_message_text(
            "🏗️ **Список проектов**\n\n❌ Проекты не найдены",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard()
        )
        return
    
    text = "🏗️ **Список проектов:**\n\n"
    for i, project in enumerate(projects, 1):
        text += f"{i}. **{project['title']}**\n"
        text += f"   📍 {project['address']}\n"
        text += f"   📷 {len(project.get('images', []))} изображений\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_keyboard()
    )


async def show_products_for_edit(query):
    """Show products for editing"""
    products = await db.products.find().to_list(1000)
    
    if not products:
        await query.edit_message_text(
            "❌ Товары не найдены",
            reply_markup=get_back_keyboard()
        )
        return
    
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(
            f"📝 {product['name']}", 
            callback_data=f"edit_product_{product['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="manage_products")])
    
    await query.edit_message_text(
        "📝 **Выберите товар для редактирования:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_projects_for_edit(query):
    """Show projects for editing"""
    projects = await db.projects.find().to_list(1000)
    
    if not projects:
        await query.edit_message_text(
            "❌ Проекты не найдены",
            reply_markup=get_back_keyboard()
        )
        return
    
    keyboard = []
    for project in projects:
        keyboard.append([InlineKeyboardButton(
            f"📝 {project['title']}", 
            callback_data=f"edit_project_{project['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="manage_projects")])
    
    await query.edit_message_text(
        "📝 **Выберите проект для редактирования:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_products_for_delete(query):
    """Show products for deletion"""
    products = await db.products.find().to_list(1000)
    
    if not products:
        await query.edit_message_text(
            "❌ Товары не найдены",
            reply_markup=get_back_keyboard()
        )
        return
    
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {product['name']}", 
            callback_data=f"delete_product_{product['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="manage_products")])
    
    await query.edit_message_text(
        "🗑️ **Выберите товар для удаления:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_projects_for_delete(query):
    """Show projects for deletion"""
    projects = await db.projects.find().to_list(1000)
    
    if not projects:
        await query.edit_message_text(
            "❌ Проекты не найдены",
            reply_markup=get_back_keyboard()
        )
        return
    
    keyboard = []
    for project in projects:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {project['title']}", 
            callback_data=f"delete_project_{project['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="manage_projects")])
    
    await query.edit_message_text(
        "🗑️ **Выберите проект для удаления:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_product(query, product_id: str):
    """Delete a product"""
    product = await db.products.find_one({"id": product_id})
    if not product:
        await query.answer("❌ Товар не найден", show_alert=True)
        return
    
    await db.products.delete_one({"id": product_id})
    await query.edit_message_text(
        f"✅ Товар '{product['name']}' успешно удален!",
        reply_markup=get_main_menu_keyboard()
    )


async def delete_project(query, project_id: str):
    """Delete a project"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        await query.answer("❌ Проект не найден", show_alert=True)
        return
    
    await db.projects.delete_one({"id": project_id})
    await query.edit_message_text(
        f"✅ Проект '{project['title']}' успешно удален!",
        reply_markup=get_main_menu_keyboard()
    )


async def show_statistics(query):
    """Show statistics"""
    products_count = await db.products.count_documents({})
    projects_count = await db.projects.count_documents({})
    orders_count = await db.orders.count_documents({})
    feedback_count = await db.feedback.count_documents({})
    
    text = f"""
📊 **Статистика**

📦 Товары: {products_count}
🏗️ Проекты: {projects_count}
🛒 Заказы: {orders_count}
💬 Обратная связь: {feedback_count}
    """
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_keyboard()
    )


async def finish_project_creation(query, user_id: int):
    """Finish creating a new project"""
    project_data = admin_state.get_state(user_id).get("new_project", {})
    
    if not project_data.get("images"):
        await query.edit_message_text(
            "❌ Проект должен содержать хотя бы одно изображение!",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Generate UUID for project
    import uuid
    project_data["id"] = str(uuid.uuid4())
    project_data["created_at"] = datetime.utcnow()
    
    # Save to database
    await db.projects.insert_one(project_data)
    
    admin_state.clear_state(user_id)
    await query.edit_message_text(
        f"✅ Проект '{project_data['title']}' успешно добавлен!",
        reply_markup=get_main_menu_keyboard()
    )


async def finish_project_images_edit(query, user_id: int):
    """Finish editing project images"""
    editing_project = admin_state.get_state(user_id).get("editing_project", {})
    new_images = admin_state.get_state(user_id).get("new_project_images", [])
    
    if not new_images:
        await query.edit_message_text(
            "❌ Не добавлено ни одного изображения!",
            reply_markup=get_back_keyboard()
        )
        return
    
    project_id = editing_project.get("id")
    if not project_id:
        await query.edit_message_text(
            "❌ Ошибка: проект не найден!",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Update project with new images
    await db.projects.update_one(
        {"id": project_id}, 
        {"$set": {"images": new_images}}
    )
    
    admin_state.clear_state(user_id)
    await query.edit_message_text(
        f"✅ Изображения проекта обновлены! Добавлено: {len(new_images)}",
        reply_markup=get_main_menu_keyboard()
    )


async def start_product_edit(query, product_id: str):
    """Start editing a product"""
    user_id = query.from_user.id
    product = await db.products.find_one({"id": product_id})
    
    if not product:
        await query.answer("❌ Товар не найден", show_alert=True)
        return
    
    admin_state.set_state(user_id, "editing_product", product)
    
    keyboard = [
        [InlineKeyboardButton("📝 Название", callback_data=f"edit_product_name_{product_id}")],
        [InlineKeyboardButton("📄 Краткое описание", callback_data=f"edit_product_short_desc_{product_id}")],
        [InlineKeyboardButton("📋 Подробное описание", callback_data=f"edit_product_desc_{product_id}")],
        [InlineKeyboardButton("💰 Цена", callback_data=f"edit_product_price_{product_id}")],
        [InlineKeyboardButton("⚙️ Характеристики", callback_data=f"edit_product_specs_{product_id}")],
        [InlineKeyboardButton("📷 Изображение", callback_data=f"edit_product_image_{product_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="edit_product")]
    ]
    
    text = f"""
📝 **Редактирование товара**

**Название:** {product['name']}
**Цена:** {product['price']:,.0f} ₽
**Краткое описание:** {product['short_description']}

Выберите, что хотите изменить:
    """
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_project_edit(query, project_id: str):
    """Start editing a project"""
    user_id = query.from_user.id
    project = await db.projects.find_one({"id": project_id})
    
    if not project:
        await query.answer("❌ Проект не найден", show_alert=True)
        return
    
    admin_state.set_state(user_id, "editing_project", project)
    
    keyboard = [
        [InlineKeyboardButton("📝 Название", callback_data=f"edit_project_title_{project_id}")],
        [InlineKeyboardButton("📋 Описание", callback_data=f"edit_project_desc_{project_id}")],
        [InlineKeyboardButton("📍 Адрес", callback_data=f"edit_project_address_{project_id}")],
        [InlineKeyboardButton("📷 Изображения", callback_data=f"edit_project_images_{project_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="edit_project")]
    ]
    
    text = f"""
📝 **Редактирование проекта**

**Название:** {project['title']}
**Адрес:** {project['address']}
**Изображений:** {len(project.get('images', []))}

Выберите, что хотите изменить:
    """
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
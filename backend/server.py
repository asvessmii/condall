from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import httpx
import asyncio
import json
from pathlib import Path

# Импорт класса для работы с резервными копиями
try:
    from backend.database_backup import DatabaseBackup
except ImportError:
    try:
        from .database_backup import DatabaseBackup
    except ImportError:
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from database_backup import DatabaseBackup
        except ImportError:
            DatabaseBackup = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Telegram configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OWNER_CHAT_ID = os.environ.get('OWNER_CHAT_ID')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    short_description: str
    price: float
    image_url: str
    specifications: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductCreate(BaseModel):
    name: str
    description: str
    short_description: str
    price: float
    image_url: str
    specifications: dict = Field(default_factory=dict)

class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Telegram user ID for cart isolation
    product_id: str
    product_name: str
    price: float
    quantity: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CartItemCreate(BaseModel):
    user_id: str  # Telegram user ID for cart isolation
    product_id: str
    quantity: int = 1

class FeedbackForm(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    message: str
    tg_user_id: Optional[str] = None
    tg_username: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeedbackFormCreate(BaseModel):
    name: str
    phone: str
    message: str
    tg_user_id: Optional[str] = None
    tg_username: Optional[str] = None

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    address: str
    images: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[CartItem]
    total_amount: float
    tg_user_id: Optional[str] = None
    tg_username: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"

class OrderCreate(BaseModel):
    items: List[CartItem]
    tg_user_id: Optional[str] = None
    tg_username: Optional[str] = None

# Telegram helper functions
async def send_telegram_message(message: str):
    """Send message to owner via Telegram bot"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    "chat_id": OWNER_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            return response.json()
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")
        return None

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Добро пожаловать в интернет-магазин кондиционеров!"}

# Products endpoints
@api_router.get("/products", response_model=List[Product])
async def get_products():
    products = await db.products.find().to_list(1000)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return Product(**product)

@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate):
    product = Product(**product_data.dict())
    await db.products.insert_one(product.dict())
    return product

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return {"message": "Товар успешно удален"}

# Cart endpoints
@api_router.post("/cart", response_model=CartItem)
async def add_to_cart(cart_item_data: CartItemCreate):
    # Validate user_id
    if not cart_item_data.user_id:
        raise HTTPException(status_code=400, detail="user_id обязателен для добавления в корзину")
    
    # Check if item already exists in user's cart
    existing_item = await db.cart_items.find_one({
        "user_id": cart_item_data.user_id,
        "product_id": cart_item_data.product_id
    })
    
    if existing_item:
        # Update quantity instead of creating duplicate
        new_quantity = existing_item["quantity"] + cart_item_data.quantity
        await db.cart_items.update_one(
            {"user_id": cart_item_data.user_id, "product_id": cart_item_data.product_id},
            {"$set": {"quantity": new_quantity}}
        )
        existing_item["quantity"] = new_quantity
        return CartItem(**existing_item)
    
    # Get product details
    product = await db.products.find_one({"id": cart_item_data.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    cart_item = CartItem(
        user_id=cart_item_data.user_id,
        product_id=cart_item_data.product_id,
        product_name=product["name"],
        price=product["price"],
        quantity=cart_item_data.quantity
    )
    await db.cart_items.insert_one(cart_item.dict())
    return cart_item

@api_router.get("/cart", response_model=List[CartItem])
async def get_cart(user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id обязателен для получения корзины")
    
    cart_items = await db.cart_items.find({"user_id": user_id}).to_list(1000)
    return [CartItem(**item) for item in cart_items]

@api_router.delete("/cart/{item_id}")
async def remove_from_cart(item_id: str, user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id обязателен для удаления из корзины")
    
    result = await db.cart_items.delete_one({"id": item_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Товар в корзине не найден или не принадлежит пользователю")
    return {"message": "Товар удален из корзины"}

@api_router.delete("/cart")
async def clear_cart(user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id обязателен для очистки корзины")
    
    result = await db.cart_items.delete_many({"user_id": user_id})
    return {"message": f"Корзина очищена. Удалено товаров: {result.deleted_count}"}

# Feedback endpoints
@api_router.post("/feedback")
async def submit_feedback(feedback_data: FeedbackFormCreate):
    feedback = FeedbackForm(**feedback_data.dict())
    await db.feedback.insert_one(feedback.dict())
    
    # Build user info for message
    user_info = ""
    if feedback.tg_user_id:
        user_info += f"\n🆔 <b>Telegram ID:</b> {feedback.tg_user_id}"
    if feedback.tg_username:
        user_info += f"\n👤 <b>Username:</b> @{feedback.tg_username}"
    
    # Send to Telegram
    message = f"""
🔔 <b>Новая заявка с сайта</b>

👤 <b>Имя:</b> {feedback.name}
📞 <b>Телефон:</b> {feedback.phone}
💬 <b>Сообщение:</b> {feedback.message}{user_info}

🕐 <b>Время:</b> {feedback.created_at.strftime('%d.%m.%Y %H:%M')}
"""
    
    await send_telegram_message(message)
    return {"message": "Ваша заявка отправлена. Мы свяжемся с вами в ближайшее время."}

# Orders endpoints  
@api_router.post("/orders")
async def create_order(order_data: OrderCreate):
    total_amount = sum(item.price * item.quantity for item in order_data.items)
    order = Order(
        items=order_data.items, 
        total_amount=total_amount,
        tg_user_id=order_data.tg_user_id,
        tg_username=order_data.tg_username
    )
    await db.orders.insert_one(order.dict())
    
    # Send order to Telegram
    items_text = "\n".join([
        f"• {item.product_name} - {item.quantity} шт. × {item.price:,.0f} ₽ = {item.price * item.quantity:,.0f} ₽"
        for item in order.items
    ])
    
    # Build user info for message
    user_info = ""
    if order.tg_user_id:
        user_info += f"\n🆔 <b>Telegram ID:</b> {order.tg_user_id}"
    if order.tg_username:
        user_info += f"\n👤 <b>Username:</b> @{order.tg_username}"
    
    message = f"""
🛒 <b>Новый заказ #{order.id[:8]}</b>

📦 <b>Товары:</b>
{items_text}

💰 <b>Общая сумма:</b> {total_amount:,.0f} ₽{user_info}

🕐 <b>Время заказа:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}
"""
    
    await send_telegram_message(message)
    
    # Clear cart after order - need user_id to clear specific user's cart
    if order.tg_user_id:
        await db.cart_items.delete_many({"user_id": order.tg_user_id})
    
    return {"message": "Спасибо за заказ! Мы свяжемся с вами для подтверждения."}

# Projects endpoints
@api_router.get("/projects", response_model=List[Project])
async def get_projects():
    projects = await db.projects.find().to_list(1000)
    return [Project(**project) for project in projects]

@api_router.post("/projects", response_model=Project)
async def create_project(project_data: Project):
    await db.projects.insert_one(project_data.dict())
    return project_data

# Initialize sample data
@api_router.post("/init-data") 
async def init_sample_data():
    # Check if data already exists
    existing_products = await db.products.count_documents({})
    if existing_products > 0:
        return {"message": "Данные уже инициализированы", "products_count": existing_products}
    
    # Попытка восстановления из резервной копии
    if DatabaseBackup:
        backup = DatabaseBackup()
        try:
            # Проверяем, есть ли резервная копия
            backup_dir = Path(__file__).parent / 'data'
            if (backup_dir / 'products.json').exists():
                logging.info("Найдена резервная копия, восстанавливаем данные...")
                success = await backup.restore_backup()
                if success:
                    products_count = await db.products.count_documents({})
                    projects_count = await db.projects.count_documents({})
                    return {
                        "message": "Данные успешно восстановлены из резервной копии", 
                        "products_count": products_count,
                        "projects_count": projects_count
                    }
        except Exception as e:
            logger.error(f"Ошибка при восстановлении из резервной копии: {e}")
        finally:
            await backup.close()
    
    # Check if this is a manual initialization (from admin)
    # For now, we disable automatic initialization completely
    return {"message": "Автоматическая инициализация отключена", "products_count": existing_products}
    
    # Sample products
    products = [
        {
            "name": "Mitsubishi Electric MSZ-AP35VG",
            "short_description": "Инверторная сплит-система с Wi-Fi управлением",
            "description": "Современная инверторная сплит-система с технологией 3D i-see Sensor для равномерного распределения воздуха. Энергоэффективный класс A+++, низкий уровень шума, режим обогрева до -25°C.",
            "price": 45000,
            "image_url": "https://images.pexels.com/photos/3964537/pexels-photo-3964537.jpeg",
            "specifications": {
                "Мощность охлаждения": "3.5 кВт",
                "Площадь помещения": "35 м²",
                "Энергопотребление": "1.2 кВт",
                "Уровень шума": "19 дБ",
                "Класс энергоэффективности": "A+++"
            }
        },
        {
            "name": "Daikin FTXM35R",
            "short_description": "Премиальная модель с системой очистки воздуха",
            "description": "Высокотехнологичная сплит-система с системой фильтрации Flash Streamer. Интеллектуальное управление, функция самоочистки, работа при низких температурах до -25°C.",
            "price": 52000,
            "image_url": "https://images.pexels.com/photos/3964341/pexels-photo-3964341.jpeg",
            "specifications": {
                "Мощность охлаждения": "3.5 кВт",
                "Площадь помещения": "35 м²",
                "Энергопотребление": "1.1 кВт",
                "Уровень шума": "20 дБ",
                "Класс энергоэффективности": "A+++"
            }
        },
        {
            "name": "LG Dual Cool AP09RT",
            "short_description": "Двойная система охлаждения с экономичным потреблением",
            "description": "Инновационная технология Dual Cool обеспечивает быстрое охлаждение и равномерное распределение воздуха. Инверторный компрессор, Wi-Fi модуль, режим энергосбережения.",
            "price": 38000,
            "image_url": "https://images.unsplash.com/photo-1709432767122-d3cb5326911a",
            "specifications": {
                "Мощность охлаждения": "2.6 кВт",
                "Площадь помещения": "26 м²",
                "Энергопотребление": "0.9 кВт",
                "Уровень шума": "18 дБ",
                "Класс энергоэффективности": "A+++"
            }
        },
        {
            "name": "Samsung AR12TXHZAWK",
            "short_description": "Smart кондиционер с голосовым управлением",
            "description": "Умный кондиционер с поддержкой голосовых команд и управления через смартфон. Технология WindFree для комфортного охлаждения без сквозняков, функция самодиагностики.",
            "price": 41000,
            "image_url": "https://images.pexels.com/photos/32588555/pexels-photo-32588555.jpeg",
            "specifications": {
                "Мощность охлаждения": "3.5 кВт",
                "Площадь помещения": "35 м²",
                "Энергопотребление": "1.15 кВт",
                "Уровень шума": "17 дБ",
                "Класс энергоэффективности": "A+++"
            }
        },
        {
            "name": "Panasonic CS-TZ25WKEW",
            "short_description": "Компактная модель для небольших помещений",
            "description": "Компактный и энергоэффективный кондиционер для небольших помещений. Быстрое охлаждение, тихая работа, режим осушения, экономичное энергопотребление.",
            "price": 32000,
            "image_url": "https://images.pexels.com/photos/7937300/pexels-photo-7937300.jpeg",
            "specifications": {
                "Мощность охлаждения": "2.5 кВт",
                "Площадь помещения": "25 м²",
                "Энергопотребление": "0.8 кВт", 
                "Уровень шума": "21 дБ",
                "Класс энергоэффективности": "A++"
            }
        },
        {
            "name": "Haier AS18NS4ERA",
            "short_description": "Настенная сплит-система с самоочисткой",
            "description": "Надежная сплит-система с функцией самоочистки и ионизации воздуха. Инверторный компрессор, режим 'Я дома/Меня нет', защита от перепадов напряжения.",
            "price": 29000,
            "image_url": "https://images.unsplash.com/photo-1727797208736-6efdc1088f81",
            "specifications": {
                "Мощность охлаждения": "5.0 кВт",
                "Площадь помещения": "50 м²",
                "Энергопотребление": "1.8 кВт",
                "Уровень шума": "24 дБ",
                "Класс энергоэффективности": "A++"
            }
        }
    ]
    
    for product_data in products:
        product = Product(**product_data)
        await db.products.insert_one(product.dict())
    
    # Sample projects
    projects = [
        {
            "title": "Монтаж системы кондиционирования в офисе",
            "description": "Установка мульти-зональной системы кондиционирования в современном офисном здании площадью 500 м². Включает 12 внутренних блоков и 3 наружных блока с централизованным управлением.",
            "address": "г. Москва, ул. Тверская, д. 15",
            "images": [
                "https://images.pexels.com/photos/32497161/pexels-photo-32497161.jpeg",
                "https://images.pexels.com/photos/8297856/pexels-photo-8297856.jpeg",
                "https://images.pexels.com/photos/31462219/pexels-photo-31462219.jpeg"
            ]
        },
        {
            "title": "Кондиционирование жилого дома",
            "description": "Комплексная установка сплит-систем в трехэтажном частном доме. Установлено 6 внутренних блоков различной мощности с учетом планировки и особенностей каждого помещения.",
            "address": "Московская область, г. Одинцово",
            "images": [
                "https://images.pexels.com/photos/16592625/pexels-photo-16592625.jpeg",
                "https://images.pexels.com/photos/3964341/pexels-photo-3964341.jpeg",
                "https://images.unsplash.com/photo-1729183672500-46c52a897de5"
            ]
        },
        {
            "title": "Промышленная система вентиляции",
            "description": "Монтаж промышленной системы вентиляции и кондиционирования на производственном предприятии. Включает приточно-вытяжную установку мощностью 10 кВт и систему воздуховодов.",
            "address": "г. Москва, Варшавское шоссе, д. 42",
            "images": [
                "https://images.pexels.com/photos/7937300/pexels-photo-7937300.jpeg",
                "https://images.unsplash.com/photo-1616185501655-b134ec9405f9",
                "https://images.pexels.com/photos/32588555/pexels-photo-32588555.jpeg"
            ]
        }
    ]
    
    for project_data in projects:
        project = Project(**project_data)
        await db.projects.insert_one(project.dict())
    
    return {"message": "Тестовые данные успешно загружены"}

# Manual data initialization for admin
@api_router.post("/admin/init-data")
async def manual_init_sample_data():
    # Clear existing data
    await db.products.delete_many({})
    await db.projects.delete_many({})
    
    # Sample products (copy from original init-data)
    products = [
        {
            "name": "Mitsubishi Electric MSZ-AP35VG",
            "short_description": "Инверторная сплит-система с Wi-Fi управлением",
            "description": "Современная инверторная сплит-система с технологией 3D i-see Sensor для равномерного распределения воздуха. Энергоэффективный класс A+++, низкий уровень шума, режим обогрева до -25°C.",
            "price": 45000,
            "image_url": "https://images.pexels.com/photos/3964537/pexels-photo-3964537.jpeg",
            "specifications": {
                "Мощность охлаждения": "3.5 кВт",
                "Площадь помещения": "35 м²",
                "Энергопотребление": "1.2 кВт",
                "Уровень шума": "19 дБ",
                "Класс энергоэффективности": "A+++"
            }
        },
        {
            "name": "Daikin FTXM35R",
            "short_description": "Премиальная модель с системой очистки воздуха",
            "description": "Высокотехнологичная сплит-система с системой фильтрации Flash Streamer. Интеллектуальное управление, функция самоочистки, работа при низких температурах до -25°C.",
            "price": 52000,
            "image_url": "https://images.pexels.com/photos/3964341/pexels-photo-3964341.jpeg",
            "specifications": {
                "Мощность охлаждения": "3.5 кВт",
                "Площадь помещения": "35 м²",
                "Энергопотребление": "1.1 кВт",
                "Уровень шума": "20 дБ",
                "Класс энергоэффективности": "A+++"
            }
        },
        {
            "name": "LG Dual Cool AP09RT",
            "short_description": "Двойная система охлаждения с экономичным потреблением",
            "description": "Инновационная технология Dual Cool обеспечивает быстрое охлаждение и равномерное распределение воздуха. Инверторный компрессор, Wi-Fi модуль, режим энергосбережения.",
            "price": 38000,
            "image_url": "https://images.unsplash.com/photo-1709432767122-d3cb5326911a",
            "specifications": {
                "Мощность охлаждения": "2.6 кВт",
                "Площадь помещения": "26 м²",
                "Энергопотребление": "0.9 кВт",
                "Уровень шума": "18 дБ",
                "Класс энергоэффективности": "A+++"
            }
        },
        {
            "name": "Samsung AR12TXHZAWK",
            "short_description": "Smart кондиционер с голосовым управлением",
            "description": "Умный кондиционер с поддержкой голосовых команд и управления через смартфон. Технология WindFree для комфортного охлаждения без сквозняков, функция самодиагностики.",
            "price": 41000,
            "image_url": "https://images.pexels.com/photos/32588555/pexels-photo-32588555.jpeg",
            "specifications": {
                "Мощность охлаждения": "3.5 кВт",
                "Площадь помещения": "35 м²",
                "Энергопотребление": "1.15 кВт",
                "Уровень шума": "17 дБ",
                "Класс энергоэффективности": "A+++"
            }
        },
        {
            "name": "Panasonic CS-TZ25WKEW",
            "short_description": "Компактная модель для небольших помещений",
            "description": "Компактный и энергоэффективный кондиционер для небольших помещений. Быстрое охлаждение, тихая работа, режим осушения, экономичное энергопотребление.",
            "price": 32000,
            "image_url": "https://images.pexels.com/photos/7937300/pexels-photo-7937300.jpeg",
            "specifications": {
                "Мощность охлаждения": "2.5 кВт",
                "Площадь помещения": "25 м²",
                "Энергопотребление": "0.8 кВт", 
                "Уровень шума": "21 дБ",
                "Класс энергоэффективности": "A++"
            }
        },
        {
            "name": "Haier AS18NS4ERA",
            "short_description": "Настенная сплит-система с самоочисткой",
            "description": "Надежная сплит-система с функцией самоочистки и ионизации воздуха. Инверторный компрессор, режим 'Я дома/Меня нет', защита от перепадов напряжения.",
            "price": 29000,
            "image_url": "https://images.unsplash.com/photo-1727797208736-6efdc1088f81",
            "specifications": {
                "Мощность охлаждения": "5.0 кВт",
                "Площадь помещения": "50 м²",
                "Энергопотребление": "1.8 кВт",
                "Уровень шума": "24 дБ",
                "Класс энергоэффективности": "A++"
            }
        }
    ]
    
    for product_data in products:
        product = Product(**product_data)
        await db.products.insert_one(product.dict())
    
    # Sample projects
    projects = [
        {
            "title": "Монтаж системы кондиционирования в офисе",
            "description": "Установка мульти-зональной системы кондиционирования в современном офисном здании площадью 500 м². Включает 12 внутренних блоков и 3 наружных блока с централизованным управлением.",
            "address": "г. Москва, ул. Тверская, д. 15",
            "images": [
                "https://images.pexels.com/photos/32497161/pexels-photo-32497161.jpeg",
                "https://images.pexels.com/photos/8297856/pexels-photo-8297856.jpeg",
                "https://images.pexels.com/photos/31462219/pexels-photo-31462219.jpeg"
            ]
        },
        {
            "title": "Кондиционирование жилого дома",
            "description": "Комплексная установка сплит-систем в трехэтажном частном доме. Установлено 6 внутренних блоков различной мощности с учетом планировки и особенностей каждого помещения.",
            "address": "Московская область, г. Одинцово",
            "images": [
                "https://images.pexels.com/photos/16592625/pexels-photo-16592625.jpeg",
                "https://images.pexels.com/photos/3964341/pexels-photo-3964341.jpeg",
                "https://images.unsplash.com/photo-1729183672500-46c52a897de5"
            ]
        },
        {
            "title": "Промышленная система вентиляции",
            "description": "Монтаж промышленной системы вентиляции и кондиционирования на производственном предприятии. Включает приточно-вытяжную установку мощностью 10 кВт и систему воздуховодов.",
            "address": "г. Москва, Варшавское шоссе, д. 42",
            "images": [
                "https://images.pexels.com/photos/7937300/pexels-photo-7937300.jpeg",
                "https://images.unsplash.com/photo-1616185501655-b134ec9405f9",
                "https://images.pexels.com/photos/32588555/pexels-photo-32588555.jpeg"
            ]
        }
    ]
    
    for project_data in projects:
        project = Project(**project_data)
        await db.projects.insert_one(project.dict())
    
    return {"message": "Данные успешно инициализированы администратором", "products_count": len(products), "projects_count": len(projects)}

# Backup management endpoints
@api_router.post("/backup/create")
async def create_database_backup():
    """Создать резервную копию базы данных"""
    if not DatabaseBackup:
        raise HTTPException(status_code=500, detail="Модуль резервного копирования не доступен")
    
    backup = DatabaseBackup()
    try:
        success = await backup.create_backup()
        if success:
            return {"message": "Резервная копия создана успешно", "timestamp": datetime.utcnow().isoformat()}
        else:
            raise HTTPException(status_code=500, detail="Ошибка при создании резервной копии")
    finally:
        await backup.close()

@api_router.post("/backup/restore")
async def restore_database_backup():
    """Восстановить данные из резервной копии"""
    if not DatabaseBackup:
        raise HTTPException(status_code=500, detail="Модуль резервного копирования не доступен")
    
    backup = DatabaseBackup()
    try:
        success = await backup.restore_backup()
        if success:
            products_count = await db.products.count_documents({})
            projects_count = await db.projects.count_documents({})
            return {
                "message": "Данные восстановлены успешно", 
                "products_count": products_count,
                "projects_count": projects_count
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка при восстановлении данных")
    finally:
        await backup.close()

@api_router.get("/backup/status")
async def get_backup_status():
    """Получить информацию о состоянии базы данных и резервных копий"""
    if not DatabaseBackup:
        raise HTTPException(status_code=500, detail="Модуль резервного копирования не доступен")
    
    backup = DatabaseBackup()
    try:
        status = await backup.get_database_status()
        
        # Проверяем наличие файлов резервных копий
        backup_dir = Path(__file__).parent / 'data'
        backup_files = {}
        for collection in ['products', 'projects', 'orders', 'feedback']:
            backup_file = backup_dir / f"{collection}.json"
            backup_files[collection] = backup_file.exists()
        
        # Информация о последней резервной копии
        info_file = backup_dir / "backup_info.json"
        last_backup = None
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
                last_backup = backup_info.get('timestamp')
        
        return {
            "database_status": status,
            "backup_files": backup_files,
            "last_backup": last_backup,
            "backup_available": any(backup_files.values())
        }
    finally:
        await backup.close()

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
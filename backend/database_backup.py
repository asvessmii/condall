#!/usr/bin/env python3
"""
Скрипт для работы с резервными копиями базы данных MongoDB
Позволяет экспортировать и импортировать данные в/из JSON файлов
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Настройки MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Папка для хранения резервных копий
BACKUP_DIR = ROOT_DIR / 'data'
BACKUP_DIR.mkdir(exist_ok=True)

# Коллекции для резервного копирования
COLLECTIONS = ['products', 'projects', 'orders', 'feedback']

class DatabaseBackup:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]

    async def close(self):
        """Закрыть соединение с БД"""
        self.client.close()

    async def export_collection(self, collection_name: str) -> list:
        """Экспорт данных из коллекции"""
        try:
            collection = self.db[collection_name]
            documents = await collection.find().to_list(None)
            
            # Конвертируем ObjectId и datetime в строки для JSON сериализации
            for doc in documents:
                if '_id' in doc:
                    del doc['_id']  # Удаляем ObjectId, используем наш uuid в поле id
                
                # Конвертируем datetime объекты в строки
                for key, value in doc.items():
                    if hasattr(value, 'isoformat'):
                        doc[key] = value.isoformat()
            
            logger.info(f"Экспортировано {len(documents)} документов из коллекции '{collection_name}'")
            return documents
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте коллекции '{collection_name}': {e}")
            return []

    async def import_collection(self, collection_name: str, documents: list) -> bool:
        """Импорт данных в коллекцию"""
        try:
            if not documents:
                logger.info(f"Нет данных для импорта в коллекцию '{collection_name}'")
                return True

            collection = self.db[collection_name]
            
            # Конвертируем строки datetime обратно в datetime объекты
            for doc in documents:
                if 'created_at' in doc and isinstance(doc['created_at'], str):
                    try:
                        doc['created_at'] = datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))
                    except:
                        doc['created_at'] = datetime.utcnow()
            
            # Очищаем коллекцию перед импортом
            await collection.delete_many({})
            
            # Вставляем документы
            if documents:
                await collection.insert_many(documents)
            
            logger.info(f"Импортировано {len(documents)} документов в коллекцию '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при импорте коллекции '{collection_name}': {e}")
            return False

    async def create_backup(self) -> bool:
        """Создать полный бэкап всех коллекций"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_info = {
                'timestamp': datetime.now().isoformat(),
                'collections': {}
            }

            logger.info("Начинаем создание резервной копии...")

            for collection_name in COLLECTIONS:
                documents = await self.export_collection(collection_name)
                
                # Сохраняем данные в отдельный файл для каждой коллекции
                backup_file = BACKUP_DIR / f"{collection_name}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(documents, f, ensure_ascii=False, indent=2)
                
                backup_info['collections'][collection_name] = len(documents)

            # Сохраняем информацию о бэкапе
            info_file = BACKUP_DIR / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)

            logger.info(f"Резервная копия создана успешно. Данные сохранены в папке: {BACKUP_DIR}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при создании резервной копии: {e}")
            return False

    async def restore_backup(self) -> bool:
        """Восстановить данные из резервной копии"""
        try:
            logger.info("Начинаем восстановление из резервной копии...")

            # Проверяем наличие файла с информацией о бэкапе
            info_file = BACKUP_DIR / "backup_info.json"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                logger.info(f"Найдена резервная копия от {backup_info['timestamp']}")

            success_count = 0
            for collection_name in COLLECTIONS:
                backup_file = BACKUP_DIR / f"{collection_name}.json"
                
                if backup_file.exists():
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        documents = json.load(f)
                    
                    if await self.import_collection(collection_name, documents):
                        success_count += 1
                else:
                    logger.warning(f"Файл резервной копии не найден: {backup_file}")

            if success_count == len(COLLECTIONS):
                logger.info("Все данные успешно восстановлены из резервной копии!")
                return True
            else:
                logger.warning(f"Восстановлено {success_count} из {len(COLLECTIONS)} коллекций")
                return False

        except Exception as e:
            logger.error(f"Ошибка при восстановлении: {e}")
            return False

    async def get_database_status(self) -> dict:
        """Получить информацию о состоянии базы данных"""
        try:
            status = {}
            total_documents = 0
            
            for collection_name in COLLECTIONS:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                status[collection_name] = count
                total_documents += count
            
            status['total'] = total_documents
            status['has_data'] = total_documents > 0
            
            return status
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса БД: {e}")
            return {}

async def main():
    """Главная функция для работы из командной строки"""
    if len(sys.argv) < 2:
        print("Usage: python database_backup.py [export|import|status]")
        print("  export - создать резервную копию")
        print("  import - восстановить из резервной копии")
        print("  status - показать состояние базы данных")
        return

    command = sys.argv[1].lower()
    backup = DatabaseBackup()

    try:
        if command == 'export':
            success = await backup.create_backup()
            if success:
                print("✅ Резервная копия создана успешно!")
            else:
                print("❌ Ошибка при создании резервной копии")
                
        elif command == 'import':
            success = await backup.restore_backup()
            if success:
                print("✅ Данные восстановлены успешно!")
            else:
                print("❌ Ошибка при восстановлении данных")
                
        elif command == 'status':
            status = await backup.get_database_status()
            print("\n📊 Состояние базы данных:")
            print("-" * 30)
            for collection, count in status.items():
                if collection != 'total' and collection != 'has_data':
                    print(f"{collection}: {count} документов")
            print("-" * 30)
            print(f"Всего документов: {status.get('total', 0)}")
            print(f"База данных {'заполнена' if status.get('has_data', False) else 'пуста'}")
            
        else:
            print(f"Неизвестная команда: {command}")

    finally:
        await backup.close()

if __name__ == "__main__":
    asyncio.run(main())
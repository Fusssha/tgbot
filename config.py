import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "8967972499:AAEf2Du0bKf45M7M0vgJiAP0GKHpeot5Zqs")
ADMIN_IDS = [5777965524, 8236488906, 1704639076]  # Добавь свой ID админа

# Database
DB_NAME = "shop.db"

# Payments (fake addresses for testing)
CRYPTO_ADDRESSES = {
    "bitcoin": "bc1qmdsx8xrudawknpqhkusszp76u5huf9hdj34q55",
    "tron": "TEj61yeQVsbyQ4Szu2i7U5nHScDFEF9bMh",
    "ton": "EQA_hJy0kO5wj-XWvA4WPyVfLMklxX_lP3Z6kA2tPpqV1vHq"
}

# Карты администратора (добавляются через админ панель)
# Формат: {card_id: {"number": "1234 5678 9012 3456", "name": "John Doe"}}
ADMIN_CARDS = {}

# Shop settings
SHOP_NAME = "magazin"
SUPPORT_CONTACT = "@krnms66"

# Комиссия при оплате картой (в процентах)
CARD_COMMISSION_PERCENT = 25

# Картинки бота (лежат в папке с проектом, рядом с main.py)
import os as _os
_BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
MAIN_MENU_IMAGE = _os.path.join(_BASE_DIR, "main.jpg")   # фото в главном меню
PRODUCT_IMAGE = _os.path.join(_BASE_DIR, "tovar.jpg")    # фото при выборе товара
CITY_IMAGE = _os.path.join(_BASE_DIR, "gorod.jpg")       # фото при выборе города
DISTRICT_IMAGE = _os.path.join(_BASE_DIR, "rayon.jpg")   # фото при выборе района
CATEGORY_IMAGE = _os.path.join(_BASE_DIR, "kategoriya.jpg")  # фото при выборе категории
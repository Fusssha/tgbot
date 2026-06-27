from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database, DEFAULT_CATEGORIES

# Сколько городов на одной странице (2 столбца x 10 строк)
CITIES_PER_PAGE = 20
CITIES_COLUMNS = 2


# ===== Main Menu =====
def get_main_inline_keyboard():
    """Главное меню - инлайн кнопки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Каталог", callback_data="catalog")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
             InlineKeyboardButton(text="📋 Заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="⭐ Отзывы", callback_data="reviews"),
             InlineKeyboardButton(text="💬 Поддержка", callback_data="support")]
        ]
    )
    return keyboard


def get_admin_inline_keyboard():
    """Главное меню для админа - инлайн кнопки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Каталог", callback_data="catalog")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
             InlineKeyboardButton(text="📋 Заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="⭐ Отзывы", callback_data="reviews"),
             InlineKeyboardButton(text="💬 Поддержка", callback_data="support")],
            [InlineKeyboardButton(text="⚙️ Админ панель", callback_data="admin_panel")]
        ]
    )
    return keyboard


# ===== Admin Panel =====
def get_admin_panel_keyboard():
    """Клавиатура админ панели"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🏙️ Управление городами", callback_data="admin_cities")],
            [InlineKeyboardButton(text="🏘️ Добавить район", callback_data="admin_add_district")],
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
            [InlineKeyboardButton(text="✏️ Управление товарами", callback_data="admin_products")],
            [InlineKeyboardButton(text="🏷️ Категории и кейворды", callback_data="admin_keywords")],
            [InlineKeyboardButton(text="💳 Настройка карты", callback_data="admin_cards")],
            [InlineKeyboardButton(text="⭐ Управление отзывами", callback_data="admin_reviews")],
            [InlineKeyboardButton(text="🔙 Вернуться", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_admin_cities_keyboard():
    """Меню управления городами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить город", callback_data="admin_add_city")],
            [InlineKeyboardButton(text="📋 Добавить города списком", callback_data="admin_add_cities_bulk")],
            [InlineKeyboardButton(text="✏️ Изменить / удалить город", callback_data="admin_edit_cities_0")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]
    )
    return keyboard


def get_admin_cards_keyboard():
    """Клавиатура управления картами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить карту", callback_data="admin_add_card")],
            [InlineKeyboardButton(text="📋 Список карт", callback_data="admin_list_cards")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]
    )
    return keyboard


def get_admin_reviews_keyboard():
    """Меню управления отзывами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить отзыв", callback_data="admin_add_review")],
            [InlineKeyboardButton(text="🗑️ Удалить отзыв", callback_data="admin_del_reviews")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ]
    )
    return keyboard


def get_reviews_list_keyboard(page: int = 0):
    """Список отзывов кнопками (для покупателя), 2 столбца х 10 строк, с пагинацией"""
    db = Database()
    reviews = db.get_all_reviews()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    total = len(reviews)
    total_pages = max(1, (total + CITIES_PER_PAGE - 1) // CITIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * CITIES_PER_PAGE
    page_reviews = reviews[start:start + CITIES_PER_PAGE]

    row = []
    for r in page_reviews:
        stars = "⭐" * int(r.get('rating', 5))
        row.append(InlineKeyboardButton(
            text=f"{r['author']} — {stars}",
            callback_data=f"review_{r['review_id']}"
        ))
        if len(row) == CITIES_COLUMNS:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"reviewpage_{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"reviewpage_{page+1}"))
    if nav:
        keyboard.inline_keyboard.append(nav)

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_main")
    ])
    return keyboard


def get_review_card_keyboard():
    """Кнопка возврата к списку отзывов"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К отзывам", callback_data="reviews")]
    ])


def get_stars_keyboard():
    """Выбор количества звёзд (для админа)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐", callback_data="stars_1"),
         InlineKeyboardButton(text="⭐⭐", callback_data="stars_2"),
         InlineKeyboardButton(text="⭐⭐⭐", callback_data="stars_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="stars_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="stars_5")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_reviews")]
    ])
    return keyboard


def get_review_city_keyboard(page: int = 0):
    """Выбор города для отзыва (2 столбца х 10 строк, с пагинацией)"""
    db = Database()
    cities = db.get_all_cities()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    total = len(cities)
    total_pages = max(1, (total + CITIES_PER_PAGE - 1) // CITIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * CITIES_PER_PAGE
    page_cities = cities[start:start + CITIES_PER_PAGE]

    row = []
    for city_id, city_name in page_cities:
        row.append(InlineKeyboardButton(text=city_name, callback_data=f"rvcity_{city_id}"))
        if len(row) == CITIES_COLUMNS:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"rvcitypage_{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"rvcitypage_{page+1}"))
    if nav:
        keyboard.inline_keyboard.append(nav)

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="⏭️ Без города", callback_data="rvcity_0")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_reviews")
    ])
    return keyboard


def get_review_product_keyboard():
    """Кнопки для шага товара в отзыве"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Без товара", callback_data="rvprod_skip")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_reviews")]
    ])


# ===== Пагинация городов (универсальная) =====
def _paginate_cities(cities, page, callback_prefix, back_callback, search_callback=None, search_text="🔍 Поиск города"):
    """
    Строит клавиатуру городов в 2 столбца по 10 строк (20 на страницу) с навигацией.
    cities: список (city_id, name)
    callback_prefix: например "city" -> city_{id}, "ecity" -> ecity_{id}
    search_text: подпись кнопки поиска (зависит от того, что выбираем - город/район/etc.)
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    total = len(cities)
    total_pages = max(1, (total + CITIES_PER_PAGE - 1) // CITIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    
    start = page * CITIES_PER_PAGE
    end = start + CITIES_PER_PAGE
    page_cities = cities[start:end]
    
    # Кнопка поиска (лупа)
    if search_callback:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=search_text, callback_data=search_callback)
        ])
    
    # Раскладываем по 2 в ряд
    row = []
    for city_id, city_name in page_cities:
        row.append(InlineKeyboardButton(text=city_name, callback_data=f"{callback_prefix}_{city_id}"))
        if len(row) == CITIES_COLUMNS:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    
    # Навигация по страницам
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{callback_prefix}page_{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{callback_prefix}page_{page+1}"))
    if nav:
        keyboard.inline_keyboard.append(nav)
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Вернуться", callback_data=back_callback)
    ])
    
    return keyboard


def get_cities_keyboard(page: int = 0):
    """Клавиатура выбора города (каталог) с пагинацией и поиском"""
    db = Database()
    cities = db.get_all_cities()
    return _paginate_cities(cities, page, "city", "back_main", search_callback="city_search")


def get_cities_search_results_keyboard(cities, page: int = 0):
    """Результаты поиска городов (каталог)"""
    return _paginate_cities(cities, page, "city", "catalog", search_callback="city_search")


def _paginate_admin(items, page, page_prefix, back_callback, back_text="❌ Отмена", top_buttons=None):
    """
    Универсальный пагинатор для админских списков (2 столбца, 20 на страницу).
    items: список (callback_data, label) — полный callback на каждую кнопку.
    page_prefix: префикс навигации с подчёркиванием в конце, напр. "apdpage_" -> apdpage_{n}.
    top_buttons: список (label, callback_data) — кнопки над списком (на всех страницах).
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if top_buttons:
        for label, cb in top_buttons:
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=label, callback_data=cb)])

    total = len(items)
    total_pages = max(1, (total + CITIES_PER_PAGE - 1) // CITIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * CITIES_PER_PAGE
    chunk = items[start:start + CITIES_PER_PAGE]

    row = []
    for cb, label in chunk:
        row.append(InlineKeyboardButton(text=label, callback_data=cb))
        if len(row) == CITIES_COLUMNS:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{page_prefix}{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{page_prefix}{page+1}"))
    if nav:
        keyboard.inline_keyboard.append(nav)

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text=back_text, callback_data=back_callback)
    ])
    return keyboard


def get_admin_product_cities_keyboard(page: int = 0):
    """Выбор города при добавлении товара (2 столбца + страницы)"""
    db = Database()
    items = [(f"admin_city_{cid}", name) for cid, name in db.get_all_cities()]
    return _paginate_admin(items, page, "apcpage_", "admin_back")


def get_admin_product_districts_keyboard(city_id: int, page: int = 0):
    """Выбор района при добавлении товара (2 столбца + страницы)"""
    db = Database()
    items = [(f"admin_dist_{did}", name) for did, name in db.get_districts_by_city(city_id)]
    return _paginate_admin(
        items, page, "apdpage_", "admin_back",
        top_buttons=[("🏙️ Без района (весь город)", "admin_dist_0")]
    )


def get_admin_district_cities_keyboard(page: int = 0):
    """Выбор города при добавлении района (2 столбца + страницы)"""
    db = Database()
    items = [(f"distcity_{cid}", name) for cid, name in db.get_all_cities()]
    return _paginate_admin(items, page, "adcpage_", "admin_back")


def get_admin_manage_cities_keyboard(page: int = 0):
    """Выбор города в управлении товарами (2 столбца + страницы)"""
    db = Database()
    items = [(f"pcity_{cid}", name) for cid, name in db.get_all_cities()]
    return _paginate_admin(items, page, "pcpage_", "admin_panel", back_text="🔙 Назад")


def get_admin_products_list_keyboard(city_id: int, page: int = 0):
    """Список товаров города в управлении (2 столбца + страницы)"""
    db = Database()
    products = db.get_products_by_city(city_id)
    items = [(f"eprod_{p['product_id']}", f"{p['name']} • {p['price']}₽") for p in products]
    return _paginate_admin(items, page, f"eppage_{city_id}_", "admin_products", back_text="🔙 Назад")


def get_admin_edit_cities_keyboard(page: int = 0):
    """Клавиатура городов для редактирования (админ) с пагинацией"""
    db = Database()
    cities = db.get_all_cities()
    return _paginate_cities(cities, page, "ecity", "admin_cities")


def get_city_edit_keyboard(city_id: int):
    """Меню действий с конкретным городом"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"rename_city_{city_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить город", callback_data=f"delcity_{city_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_cities_0")]
        ]
    )
    return keyboard


def get_city_delete_confirm_keyboard(city_id: int):
    """Подтверждение удаления города"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delcity_yes_{city_id}")],
            [InlineKeyboardButton(text="❌ Нет", callback_data=f"ecity_{city_id}")]
        ]
    )
    return keyboard


# ===== Districts =====
def get_districts_keyboard(city_id: int, page: int = 0):
    """Клавиатура выбора района с пагинацией (2 столбца x 10 строк) и поиском"""
    db = Database()
    districts = db.get_districts_by_city(city_id)
    return _paginate_cities(districts, page, "district", "back_cities", search_callback="district_search", search_text="🔍 Поиск района")


def get_districts_search_results_keyboard(districts, page: int = 0):
    """Результаты поиска районов"""
    return _paginate_cities(districts, page, "district", "back_districts", search_callback="district_search", search_text="🔍 Поиск района")


# ===== Categories =====
def get_categories_keyboard(district_id: int):
    """Клавиатура выбора категории (для покупателя)"""
    db = Database()
    cats = db.get_categories_by_district(district_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for cat_id, cat_name in cats:
        row.append(InlineKeyboardButton(text=cat_name, callback_data=f"category_{cat_id}"))
        if len(row) == 2:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Вернуться", callback_data="back_districts")
    ])
    return keyboard


def get_admin_categories_keyboard(district_id: int):
    """Клавиатура выбора категории (для админа при добавлении товара)"""
    db = Database()
    cats = db.get_categories_by_district(district_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for cat_id, cat_name in cats:
        row.append(InlineKeyboardButton(text=cat_name, callback_data=f"admin_cat_{cat_id}"))
        if len(row) == 2:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
    ])
    return keyboard


# ===== Имена категорий (общие для всех районов) =====
def get_all_category_names():
    """Стабильный упорядоченный список имён категорий: стандартные + кастомные"""
    db = Database()
    return db.get_all_category_names()


def get_add_product_mode_keyboard():
    """Меню выбора способа добавления товара"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏙️ В конкретный город", callback_data="addprod_single")],
            [InlineKeyboardButton(text="🌍 Во все города и районы", callback_data="addprod_all")],
            [InlineKeyboardButton(text="🤖 Авто по кейвордам (во все)", callback_data="addprod_auto")],
            [InlineKeyboardButton(text="📋 Списком (настроить по очереди)", callback_data="addprod_list")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_category_names_keyboard(callback_prefix: str, back_callback: str = "admin_back"):
    """Клавиатура выбора ИМЕНИ категории (индекс в стабильном списке имён).
    callback_prefix: например 'apcat' -> apcat_{idx}"""
    names = get_all_category_names()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for idx, name in enumerate(names):
        row.append(InlineKeyboardButton(text=name, callback_data=f"{callback_prefix}_{idx}"))
        if len(row) == 2:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data=back_callback)
    ])
    return keyboard


# ===== Управление кейвордами категорий =====
def get_keywords_categories_keyboard():
    """Список категорий с количеством кейвордов"""
    db = Database()
    names = db.get_all_category_names()
    counts = db.get_keyword_counts()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for idx, name in enumerate(names):
        cnt = counts.get(name, 0)
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"{name} • кейвордов: {cnt}", callback_data=f"kwcat_{idx}")
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    ])
    return keyboard


def get_keyword_category_keyboard(idx: int):
    """Действия с кейвордами конкретной категории"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить кейворды", callback_data=f"kwadd_{idx}")],
            [InlineKeyboardButton(text="✏️ Переименовать категорию", callback_data=f"kwrename_{idx}")],
            [InlineKeyboardButton(text="🗑️ Очистить все", callback_data=f"kwclear_{idx}")],
            [InlineKeyboardButton(text="🔙 К категориям", callback_data="admin_keywords")]
        ]
    )
    return keyboard


# ===== Products =====
def get_products_keyboard(city_id: int, district_id: int = None):
    """Клавиатура товаров города/района"""
    db = Database()
    products = db.get_products_by_city(city_id, district_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for product in products:
        qty = product.get('quantity', 1)
        qty_str = str(int(qty)) if qty == int(qty) else str(qty)
        units = product.get('units', 'шт')
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} • {qty_str} {units} • {product['price']}₽",
                callback_data=f"product_{product['product_id']}"
            )
        ])
    
    back_cb = "back_districts" if district_id is not None else "back_cities"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Вернуться", callback_data=back_cb)
    ])
    
    return keyboard


def get_products_by_category_keyboard(category_id: int):
    """Клавиатура товаров категории"""
    db = Database()
    products = db.get_products_by_category(category_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for product in products:
        qty = product.get('quantity', 1)
        qty_str = str(int(qty)) if qty == int(qty) else str(qty)
        units = product.get('units', 'шт')
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} • {qty_str} {units} • {product['price']}₽",
                callback_data=f"product_{product['product_id']}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Вернуться", callback_data="back_categories")
    ])
    return keyboard


# ===== Типы доставки (покупатель) =====
def get_delivery_types_keyboard(category_id: int):
    """Кнопки типов доставки для товаров категории"""
    db = Database()
    types = db.get_delivery_types_by_category(category_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for idx, t in enumerate(types):
        label = t if t else "Стандарт"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"🚚 {label}", callback_data=f"dtype_{category_id}_{idx}")
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Вернуться", callback_data="back_categories")
    ])
    return keyboard


def get_products_by_delivery_keyboard(category_id: int, products):
    """Товары конкретного типа доставки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for product in products:
        qty = product.get('quantity', 1)
        qty_str = str(int(qty)) if qty == int(qty) else str(qty)
        units = product.get('units', 'шт')
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} • {qty_str} {units} • {product['price']}₽",
                callback_data=f"product_{product['product_id']}"
            )
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Вернуться", callback_data=f"backdelivery_{category_id}")
    ])
    return keyboard


# ===== Мультивыбор (добавление товара списком) =====
def _paginate_multiselect(items, selected_keys, page, item_prefix, page_prefix,
                          done_callback, back_callback, done_text="✅ Готово", extra_rows=None):
    """items: список (key, label). selected_keys: множество отмеченных key.
    2 столбца + страницы + кнопки 'Готово' и 'Отмена'.
    extra_rows: список дополнительных рядов кнопок (например, "выбрать все"),
    вставляется после пагинации и перед кнопкой 'Готово'."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    total = len(items)
    total_pages = max(1, (total + CITIES_PER_PAGE - 1) // CITIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    chunk = items[page * CITIES_PER_PAGE:page * CITIES_PER_PAGE + CITIES_PER_PAGE]
    row = []
    for key, label in chunk:
        mark = "✅ " if key in selected_keys else ""
        row.append(InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"{item_prefix}{key}"))
        if len(row) == CITIES_COLUMNS:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"{page_prefix}{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"{page_prefix}{page+1}"))
    if nav:
        keyboard.inline_keyboard.append(nav)
    if extra_rows:
        for row in extra_rows:
            keyboard.inline_keyboard.append(row)
    keyboard.inline_keyboard.append([InlineKeyboardButton(text=done_text, callback_data=done_callback)])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data=back_callback)])
    return keyboard


def get_bulk_cities_keyboard(selected_ids, page: int = 0):
    """Мультивыбор городов для добавления товара списком"""
    db = Database()
    items = [(str(cid), name) for cid, name in db.get_all_cities()]
    sel = {str(i) for i in selected_ids}
    total_pages = max(1, (len(items) + CITIES_PER_PAGE - 1) // CITIES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    extra_rows = [
        [InlineKeyboardButton(text="📄 Выбрать города на этой странице", callback_data=f"bcity_selpage_{page}")],
        [InlineKeyboardButton(text="🌍 Выбрать все города", callback_data="bcity_selall")],
    ]
    return _paginate_multiselect(items, sel, page, "bcity_", "bcitypage_", "bcity_done", "admin_back",
                                  extra_rows=extra_rows)


def get_bulk_districts_keyboard(city_ids, selected_keys, page: int = 0):
    """Мультивыбор районов (по выбранным городам). Ключ: 'cityid:districtid'."""
    db = Database()
    names = {cid: name for cid, name in db.get_all_cities()}
    items = []
    for cid in city_ids:
        cname = names.get(cid, str(cid))
        for did, dname in db.get_districts_by_city(cid):
            items.append((f"{cid}:{did}", f"{cname} · {dname}"))
    extra_rows = [
        [InlineKeyboardButton(text="🏘️ Выбрать все районы", callback_data="bdist_selall")],
    ]
    return _paginate_multiselect(items, set(selected_keys), page, "bdist_", "bdistpage_", "bdist_done", "admin_back",
                                  extra_rows=extra_rows)


def get_payment_keyboard(order_id: int):
    """Клавиатура выбора способа оплаты"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Карта", callback_data=f"pay_card_{order_id}")],
            [InlineKeyboardButton(text="₿ Bitcoin", callback_data=f"pay_bitcoin_{order_id}")],
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_order")]
        ]
    )
    return keyboard


def get_confirm_order_keyboard(order_id: int):
    """Клавиатура подтверждения заказа"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{order_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
        ]
    )
    return keyboard


def get_profile_keyboard():
    """Клавиатура профиля"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться", callback_data="back_main")]
        ]
    )
    return keyboard


def get_check_payment_keyboard(order_id: int):
    """Клавиатура проверки платежа"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить платеж", callback_data=f"check_payment_{order_id}")],
            [InlineKeyboardButton(text="🔙 Вернуться", callback_data="back_main")]
        ]
    )
    return keyboard


# ===== Product photos during creation =====
def get_product_photos_keyboard():
    """Кнопки при добавлении фото товара"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Готово (сохранить товар)", callback_data="finish_product")],
            [InlineKeyboardButton(text="⏭️ Без фото", callback_data="finish_product")]
        ]
    )
    return keyboard
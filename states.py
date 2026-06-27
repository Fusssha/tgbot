from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Состояния админ панели"""
    in_admin_panel = State()
    adding_city = State()
    adding_cities_bulk = State()
    adding_district = State()
    selecting_city_for_district = State()
    adding_product = State()
    selecting_city_for_product = State()
    selecting_district_for_product = State()
    selecting_category_for_product = State()
    entering_product_name = State()
    entering_product_price = State()
    entering_product_quantity = State()
    entering_product_units = State()
    entering_product_description = State()
    entering_product_photos = State()
    adding_card = State()
    entering_card_number = State()
    entering_card_holder = State()
    approving_payment = State()
    # Кейворды категорий
    entering_keywords = State()
    renaming_category = State()
    # Добавление товара списком
    bulk_entering_names = State()
    bulk_selecting_cities = State()
    bulk_selecting_districts = State()
    bulk_selecting_category = State()
    bulk_entering_price = State()
    bulk_entering_quantity = State()
    bulk_entering_units = State()
    bulk_entering_description = State()
    bulk_entering_photos = State()
    bulk_entering_delivery = State()
    # Управление городами
    editing_city_name = State()
    searching_city = State()
    # Управление товарами
    editing_product_price = State()
    # Отзывы
    adding_review_author = State()
    adding_review_rating = State()
    adding_review_city = State()
    adding_review_product = State()
    adding_review_text = State()


class CatalogStates(StatesGroup):
    """Состояния каталога"""
    selecting_city = State()
    selecting_product = State()
    searching_city = State()
    searching_district = State()


class ShoppingStates(StatesGroup):
    """Состояния покупок"""
    confirming_order = State()
    selecting_payment = State()
    selecting_quantity = State()
    entering_quantity = State()


class ProfileStates(StatesGroup):
    """Состояния профиля"""
    editing_profile = State()
    entering_phone = State()
    entering_address = State()
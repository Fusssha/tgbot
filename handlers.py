import os
import html
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from database import Database, DEFAULT_CATEGORIES
from keyboards import *
from states import AdminStates, CatalogStates, ShoppingStates, ProfileStates
from config import ADMIN_IDS, SUPPORT_CONTACT, SHOP_NAME, CRYPTO_ADDRESSES, MAIN_MENU_IMAGE, PRODUCT_IMAGE, CITY_IMAGE, DISTRICT_IMAGE, CATEGORY_IMAGE, CARD_COMMISSION_PERCENT

router = Router()
db = Database()


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None, parse_mode=None):
    """Безопасно показать текст: если сообщение с фото/без текста — удалить и прислать новое."""
    msg = callback.message
    # Сообщение с фото или подписью нельзя редактировать как текст
    if getattr(msg, "photo", None) or getattr(msg, "caption", None) is not None:
        try:
            await msg.delete()
        except Exception:
            pass
        await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    try:
        await msg.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            await msg.delete()
        except Exception:
            pass
        await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


def get_main_keyboard_for(user_id: int):
    """Клавиатура главного меню в зависимости от роли"""
    if user_id in ADMIN_IDS:
        return get_admin_inline_keyboard()
    return get_main_inline_keyboard()


def category_name_by_index(idx: int):
    """Имя категории по индексу из стабильного списка имён (или None)"""
    names = db.get_all_category_names()
    if 0 <= idx < len(names):
        return names[idx]
    return None


async def send_main_menu(message: Message, text: str, keyboard):
    """Отправить главное меню с фото main.jpg, если оно есть"""
    if os.path.exists(MAIN_MENU_IMAGE):
        try:
            await message.answer_photo(
                FSInputFile(MAIN_MENU_IMAGE),
                caption=text,
                reply_markup=keyboard
            )
            return
        except Exception as e:
            print(f"Error sending main menu photo: {e}")
    await message.answer(text, reply_markup=keyboard)


async def show_main_menu_callback(callback: CallbackQuery, text: str, keyboard):
    """Показать главное меню (из callback) с фото main.jpg"""
    if os.path.exists(MAIN_MENU_IMAGE):
        try:
            await callback.message.delete()
        except Exception:
            pass
        try:
            await callback.message.answer_photo(
                FSInputFile(MAIN_MENU_IMAGE),
                caption=text,
                reply_markup=keyboard
            )
            return
        except Exception as e:
            print(f"Error sending main menu photo: {e}")
    try:
        await safe_edit(callback, text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


async def show_with_product_image(callback: CallbackQuery, text: str, keyboard):
    """Показать сообщение с прикреплённым фото tovar.jpg (для списка товаров)."""
    # Удаляем предыдущее сообщение и шлём новое с фото
    try:
        await callback.message.delete()
    except Exception:
        pass
    if os.path.exists(PRODUCT_IMAGE):
        try:
            await callback.message.answer_photo(
                FSInputFile(PRODUCT_IMAGE),
                caption=text,
                reply_markup=keyboard
            )
            return
        except Exception as e:
            print(f"Error sending product image: {e}")
    # Фото нет - просто текст
    await callback.message.answer(text, reply_markup=keyboard)


async def show_with_city_image(callback: CallbackQuery, text: str, keyboard):
    """Показать экран выбора города с картинкой gorod.jpg (из callback)."""
    try:
        await callback.message.delete()
    except Exception:
        pass
    if os.path.exists(CITY_IMAGE):
        try:
            await callback.message.answer_photo(
                FSInputFile(CITY_IMAGE),
                caption=text,
                reply_markup=keyboard
            )
            return
        except Exception as e:
            print(f"Error sending city image: {e}")
    await callback.message.answer(text, reply_markup=keyboard)


async def send_city_image_message(message: Message, text: str, keyboard):
    """Показать экран выбора города с картинкой gorod.jpg (из message)."""
    if os.path.exists(CITY_IMAGE):
        try:
            await message.answer_photo(
                FSInputFile(CITY_IMAGE),
                caption=text,
                reply_markup=keyboard
            )
            return
        except Exception as e:
            print(f"Error sending city image: {e}")
    await message.answer(text, reply_markup=keyboard)


async def show_with_image_callback(callback: CallbackQuery, image_path: str, text: str, keyboard):
    """Удалить предыдущее сообщение и показать новое с картинкой image_path."""
    try:
        await callback.message.delete()
    except Exception:
        pass
    if os.path.exists(image_path):
        try:
            await callback.message.answer_photo(
                FSInputFile(image_path),
                caption=text,
                reply_markup=keyboard
            )
            return
        except Exception as e:
            print(f"Error sending image {image_path}: {e}")
    await callback.message.answer(text, reply_markup=keyboard)


async def show_with_district_image(callback: CallbackQuery, text: str, keyboard):
    """Экран выбора района с картинкой rayon.jpg"""
    await show_with_image_callback(callback, DISTRICT_IMAGE, text, keyboard)


async def show_with_category_image(callback: CallbackQuery, text: str, keyboard):
    """Экран выбора категории с картинкой kategoriya.jpg"""
    await show_with_image_callback(callback, CATEGORY_IMAGE, text, keyboard)


async def send_image_message(message: Message, image_path: str, text: str, keyboard):
    """Отправить новое сообщение с картинкой image_path (из message)."""
    if os.path.exists(image_path):
        try:
            await message.answer_photo(
                FSInputFile(image_path),
                caption=text,
                reply_markup=keyboard
            )
            return
        except Exception as e:
            print(f"Error sending image {image_path}: {e}")
    await message.answer(text, reply_markup=keyboard)


# ===== START COMMAND =====
@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Команда старта"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Добавляем пользователя в БД
    db.add_user(user_id, username, first_name)
    
    # Очищаем состояние
    await state.clear()
    
    welcome_text = f"🔸Добро пожаловать в KRAKEN🔸\n\nКрупнейший Darknet магазин для покупки ПАВ представляет упрощенную версию для телеграмма, где вы можете купить товар от проверенных площадкой поставщиков напрямую.\n\nДля удобства приобретения ПАВ представлен бот в виде упрощенной версии маркетплейса на случай затруднений в работе сайта из-за DDOS атак со стороны сторонних маркетплейсов.\n\nИнклюзивные условия для сотрудничества с нами дали возможность предоставить вам ассортимент от лучших продавцов. Каждый магазин, который сотрудничает с нами, имеет страховой депозит. В случае спорной ситуации ваша покупка или ее не наход оплачиваются из этого депозита.\n\nСамой главной целью этого бота является сделать процесс покупки анонимным, безопасным и приятным для всех сторон.\n\n🐙KRAKEN : 2km.es \n\nЕсли бот не отвечает, перезапустите командой /start"    
    keyboard = get_main_keyboard_for(user_id)
    await send_main_menu(message, welcome_text, keyboard)


# ===== CATALOG =====
@router.callback_query(F.data == "catalog")
async def catalog_command(callback: CallbackQuery, state: FSMContext):
    """Открыть каталог"""
    await state.clear()
    cities = db.get_all_cities()
    
    if not cities:
        await safe_edit(callback, "Города еще не добавлены. Вернитесь позже", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]]))
        return
    
    await show_with_city_image(callback, "🏙️ Выберите город:", get_cities_keyboard(0))


@router.message(F.text == "📦 Каталог")
async def catalog_command_text(message: Message, state: FSMContext):
    """Открыть каталог (текстовая команда - для совместимости)"""
    cities = db.get_all_cities()
    
    if not cities:
        await message.answer("Города еще не добавлены. Вернитесь позже", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]]))
        return
    
    await send_city_image_message(message, "🏙️ Выберите город:", get_cities_keyboard(0))


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Пустая кнопка (номер страницы)"""
    await callback.answer()


@router.callback_query(F.data.startswith("citypage_"))
async def cities_pagination(callback: CallbackQuery):
    """Перелистывание страниц городов в каталоге"""
    page = int(callback.data.split("_")[1])
    # Меняем только клавиатуру, чтобы не терять картинку города
    try:
        await callback.message.edit_reply_markup(reply_markup=get_cities_keyboard(page))
    except Exception:
        await show_with_city_image(callback, "🏙️ Выберите город:", get_cities_keyboard(page))


@router.callback_query(F.data == "city_search")
async def city_search_start(callback: CallbackQuery, state: FSMContext):
    """Начать поиск города"""
    await state.set_state(CatalogStates.searching_city)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="catalog")]])
    await safe_edit(callback, "🔍 Введите название города или его часть:", reply_markup=keyboard)


@router.message(CatalogStates.searching_city)
async def city_search_results(message: Message, state: FSMContext):
    """Показать результаты поиска города"""
    query = message.text.strip()
    cities = db.search_cities(query)
    await state.clear()
    
    if not cities:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Искать снова", callback_data="city_search")],
            [InlineKeyboardButton(text="🔙 К каталогу", callback_data="catalog")]
        ])
        await message.answer(f"❌ По запросу «{query}» городов не найдено", reply_markup=keyboard)
        return
    
    await send_city_image_message(
        message,
        f"🔍 Найдено городов: {len(cities)}",
        get_cities_search_results_keyboard(cities, 0)
    )


@router.callback_query(F.data.startswith("city_"))
async def select_city(callback: CallbackQuery, state: FSMContext):
    """Выбрать город. Если есть районы - показать их, иначе товары"""
    # Защита от пересечения с city_search (он обрабатывается выше, но на всякий)
    if callback.data == "city_search":
        return
    
    city_id = int(callback.data.split("_")[1])
    
    # Сохраняем выбранный город в состояние
    await state.update_data(selected_city_id=city_id, selected_district_id=None)
    
    # Проверяем есть ли районы у города
    districts = db.get_districts_by_city(city_id)
    
    if districts:
        await show_with_district_image(callback, "🏘️ Выберите район:", get_districts_keyboard(city_id))
        return
    
    # Районов нет - показываем товары города
    products = db.get_products_by_city(city_id)
    if not products:
        await callback.answer("Товаров в этом городе нет", show_alert=True)
        return
    
    await show_with_product_image(callback, "👕 Выберите товар:", get_products_keyboard(city_id))


@router.callback_query(F.data.startswith("districtpage_"))
async def districts_pagination(callback: CallbackQuery, state: FSMContext):
    """Перелистывание страниц районов"""
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    city_id = data.get("selected_city_id")
    if not city_id:
        await show_with_city_image(callback, "🏙️ Выберите город:", get_cities_keyboard(0))
        return
    # Меняем только клавиатуру, чтобы не терять картинку района
    try:
        await callback.message.edit_reply_markup(reply_markup=get_districts_keyboard(city_id, page))
    except Exception:
        await show_with_district_image(callback, "🏘️ Выберите район:", get_districts_keyboard(city_id, page))


@router.callback_query(F.data == "district_search")
async def district_search_start(callback: CallbackQuery, state: FSMContext):
    """Начать поиск района (в рамках выбранного города)"""
    data = await state.get_data()
    city_id = data.get("selected_city_id")
    if not city_id:
        await show_with_city_image(callback, "🏙️ Выберите город:", get_cities_keyboard(0))
        return
    await state.set_state(CatalogStates.searching_district)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="back_districts")]])
    await safe_edit(callback, "🔍 Введите название района или его часть:", reply_markup=keyboard)


@router.message(CatalogStates.searching_district)
async def district_search_results(message: Message, state: FSMContext):
    """Показать результаты поиска района"""
    query = message.text.strip()
    data = await state.get_data()
    city_id = data.get("selected_city_id")
    # Выходим из режима ввода, но сохраняем выбранный город
    await state.set_state(None)

    if not city_id:
        await send_city_image_message(message, "🏙️ Выберите город:", get_cities_keyboard(0))
        return

    districts = db.search_districts(city_id, query)

    if not districts:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Искать снова", callback_data="district_search")],
            [InlineKeyboardButton(text="🔙 К районам", callback_data="back_districts")]
        ])
        await message.answer(f"❌ По запросу «{query}» районов не найдено", reply_markup=keyboard)
        return

    await send_image_message(
        message,
        DISTRICT_IMAGE,
        f"🔍 Найдено районов: {len(districts)}",
        get_districts_search_results_keyboard(districts, 0)
    )


@router.callback_query(F.data.startswith("district_"))
async def select_district(callback: CallbackQuery, state: FSMContext):
    """Выбрать район и показать категории"""
    # Защита от пересечения с district_search (он обрабатывается выше)
    if callback.data == "district_search":
        return

    district_id = int(callback.data.split("_")[1])
    district = db.get_district(district_id)
    
    if not district:
        await callback.answer("Район не найден", show_alert=True)
        return
    
    city_id = district['city_id']
    await state.update_data(selected_city_id=city_id, selected_district_id=district_id)
    
    # Показываем категории района
    cats = db.get_categories_by_district(district_id)
    if not cats:
        await callback.answer("В этом районе нет категорий", show_alert=True)
        return
    
    await show_with_category_image(callback, "🗂️ Выберите категорию:", get_categories_keyboard(district_id))


@router.callback_query(F.data.startswith("category_"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    """Выбрать категорию. Если у товаров есть типы доставки — показать их, иначе товары."""
    category_id = int(callback.data.split("_")[1])
    category = db.get_category(category_id)
    
    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    
    await state.update_data(selected_category_id=category_id)
    
    products = db.get_products_by_category(category_id)
    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    
    # Есть ли у товаров типы доставки?
    has_delivery = any((p.get('delivery_type') or '').strip() for p in products)
    if has_delivery:
        await show_with_product_image(
            callback,
            f"🚚 {category['name']} — выберите тип клада:",
            get_delivery_types_keyboard(category_id)
        )
    else:
        await show_with_product_image(
            callback,
            f"👕 {category['name']} — выберите товар:",
            get_products_by_category_keyboard(category_id)
        )


@router.callback_query(F.data.startswith("dtype_"))
async def select_delivery_type(callback: CallbackQuery, state: FSMContext):
    """Выбрать тип доставки -> показать товар(ы) этого типа"""
    parts = callback.data.split("_")  # dtype_{category_id}_{idx}
    category_id = int(parts[1])
    idx = int(parts[2])
    types = db.get_delivery_types_by_category(category_id)
    if idx < 0 or idx >= len(types):
        await callback.answer("Тип клада не найден", show_alert=True)
        return
    delivery_type = types[idx]
    products = db.get_products_by_category_and_delivery(category_id, delivery_type)
    if not products:
        await callback.answer("Товаров нет", show_alert=True)
        return
    if len(products) == 1:
        await show_product_order(callback, state, products[0]['product_id'])
        return
    label = delivery_type if delivery_type else "Стандарт"
    await show_with_product_image(
        callback,
        f"🚚 {label} — выберите товар:",
        get_products_by_delivery_keyboard(category_id, products)
    )


@router.callback_query(F.data.startswith("backdelivery_"))
async def back_to_delivery_types(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору типа доставки"""
    category_id = int(callback.data.split("_")[1])
    category = db.get_category(category_id)
    name = category['name'] if category else ""
    await show_with_product_image(
        callback,
        f"🚚 {name} — выберите тип клада:",
        get_delivery_types_keyboard(category_id)
    )


async def show_product_order(callback: CallbackQuery, state: FSMContext, product_id: int):
    """Показать карточку товара и подтверждение заказа"""
    product = db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    await state.update_data(selected_product_id=product_id)
    await state.set_state(ShoppingStates.confirming_order)
    
    qty = product.get('quantity', 1)
    qty_str = str(int(qty)) if qty == int(qty) else str(qty)
    units = product.get('units', 'шт')
    delivery = (product.get('delivery_type') or '').strip()
    delivery_line = f"\n🚚 Клад: {delivery}" if delivery else ""
    
    order_info = f"""✅ ВАШ ЗАКАЗ

🔸 {product['name']}
🔸 Количество: {qty_str} {units}
🔸 {product['description'] or 'Описания нет'}
🔸 Цена: {product['price']}₽{delivery_line}

☑️ Подтвердите заказ:"""
    
    from aiogram.types import InputMediaPhoto
    photos = db.get_product_photos(product_id)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    if photos:
        if len(photos) == 1:
            await callback.message.answer_photo(photos[0], caption=order_info, reply_markup=get_confirm_order_keyboard(0))
        else:
            media = [InputMediaPhoto(media=fid) for fid in photos[:10]]
            await callback.message.answer_media_group(media)
            await callback.message.answer(order_info, reply_markup=get_confirm_order_keyboard(0))
    else:
        await callback.message.answer(order_info, reply_markup=get_confirm_order_keyboard(0))


@router.callback_query(F.data.startswith("product_"))
async def select_product(callback: CallbackQuery, state: FSMContext):
    """Выбрать товар и сразу показать заказ"""
    product_id = int(callback.data.split("_")[1])
    await show_product_order(callback, state, product_id)



@router.callback_query(F.data.startswith("confirm_"))
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтвердить заказ и перейти к оплате"""
    data = await state.get_data()
    user_id = callback.from_user.id
    product_id = data.get('selected_product_id')
    
    product = db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Количество = 1 заказ товара (товар уже содержит свое количество)
    total_price = product['price']
    
    # Создаем заказ со статусом pending
    order_id = db.create_order(user_id, product_id, 1)
    
    if not order_id:
        await callback.answer("Ошибка при создании заказа", show_alert=True)
        return
    
    # Сохраняем order_id в состояние
    await state.update_data(order_id=order_id)
    
    payment_text = f"""💳 ОПЛАТА ЗАКАЗА

🔢 Заказ: #{order_id}
💰 Сумма: {total_price}₽

⬇️ Выберите способ оплаты:"""
    
    # Если сообщение с фото - edit_text не сработает, отправляем новое
    try:
        await safe_edit(callback, 
            payment_text,
            reply_markup=get_payment_keyboard(order_id)
        )
    except Exception:
        await callback.message.answer(
            payment_text,
            reply_markup=get_payment_keyboard(order_id)
        )


# ===== PAYMENT METHODS =====
@router.callback_query(F.data.startswith("pay_card_"))
async def pay_card(callback: CallbackQuery, state: FSMContext):
    """Оплата картой - ручной режим"""
    order_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    username = callback.from_user.username or "без username"
    
    order = db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    # Получаем карту админа
    cards = db.get_all_admin_cards()
    if not cards:
        await callback.answer("Карты для оплаты не настроены. Выберите другой способ", show_alert=True)
        return
    
    card = cards[0]  # Берем первую карту
    
    # Считаем комиссию за оплату картой
    base_amount = order['total_price']
    commission = round(base_amount * CARD_COMMISSION_PERCENT / 100, 2)
    total_with_commission = round(base_amount + commission, 2)
    
    # Создаем платеж по карте (сумма уже с комиссией)
    payment_id = db.create_card_payment(order_id, user_id, username, total_with_commission)
    
    if not payment_id:
        await callback.answer("Ошибка при создании платежа", show_alert=True)
        return
    
    # Сохраняем payment_id в состояние
    await state.update_data(payment_id=payment_id)
    
    payment_text = f"""💳 ОПЛАТА ПО КАРТЕ

🔢 Заказ: #{order_id}
🧾 Сумма заказа: {base_amount}₽
💼 Комиссия ({CARD_COMMISSION_PERCENT}%): {commission}₽
━━━━━━━━━━━━━━━━━
💰 Итого к оплате: {total_with_commission}₽

📋 Переведите на карту:
<code>{card['card_number']}</code>
👤 Получатель: {card['holder_name']}

После перевода нажмите кнопку ниже 👇"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"card_paid_{payment_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])
    await safe_edit(callback, payment_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("card_paid_"))
async def card_paid(callback: CallbackQuery, state: FSMContext):
    """Пользователь подтвердил оплату картой"""
    payment_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    username = callback.from_user.username or "без username"
    
    payment = db.get_card_payment(payment_id)
    if not payment:
        await callback.answer("Платеж не найден", show_alert=True)
        return
    
    payment_text = f"""⏳ ПЛАТЕЖ НА ПРОВЕРКЕ

🔢 Заказ: #{payment['order_id']}
💰 Сумма: {payment['amount']}₽

Ваш платеж отправлен администратору на подтверждение.
Пожалуйста, дождитесь ответа."""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]])
    await safe_edit(callback, payment_text, reply_markup=keyboard)
    
    # Отправляем уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            admin_notification = f"""🔔 НОВАЯ ОПЛАТА ПО КАРТЕ

📱 ID пользователя: {user_id}
👤 Username: @{username}
🔢 Заказ: #{payment['order_id']}
💰 Сумма: {payment['amount']}₽
🆔 ID платежа: {payment_id}

Подтвердить или отклонить оплату?"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_payment_{payment_id}"), 
                 InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_payment_{payment_id}")]
            ])
            
            await callback.bot.send_message(admin_id, admin_notification, reply_markup=keyboard)
        except Exception as e:
            print(f"Error sending admin notification: {e}")


@router.callback_query(F.data.startswith("pay_bitcoin_") | F.data.startswith("pay_tron_") | F.data.startswith("pay_ton_"))
async def select_payment_method(callback: CallbackQuery, state: FSMContext):
    """Выбрать метод оплаты - крипто"""
    parts = callback.data.split("_")
    payment_method = parts[1]
    order_id = int(parts[2])
    
    order = db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    # Получаем адрес из конфига
    address = CRYPTO_ADDRESSES.get(payment_method, "Адрес не найден")
    
    # Красивые названия криптовалют
    crypto_names = {
        "bitcoin": "₿ Bitcoin",
        "tron": "⬡ Tron (USDT)",
        "ton": "💎 TON"
    }
    
    payment_info = f"""📍 РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ

🔐 Способ: {crypto_names.get(payment_method, payment_method.upper())}
💰 Сумма: {order['total_price']}₽
🔢 Заказ: #{order_id}

📋 Адрес для отправки:
<code>{address}</code>

⏳ После отправки нажмите "Проверить":"""
    
    await safe_edit(callback, 
        payment_info,
        reply_markup=get_check_payment_keyboard(order_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("approve_payment_"))
async def approve_payment(callback: CallbackQuery):
    """Одобрить платеж по карте"""
    payment_id = int(callback.data.split("_")[2])
    
    if db.approve_card_payment(payment_id):
        payment = db.get_card_payment(payment_id)
        order = db.get_order(payment['order_id'])
        
        # Помечаем заказ как оплаченный
        db.mark_order_paid(payment['order_id'])
        
        # Отправляем уведомление пользователю
        try:
            user_notification = f"""✅ ПЛАТЕЖ ПРИНЯТ

🔢 Заказ: #{payment['order_id']}
💰 Сумма: {payment['amount']}₽

Ваш платеж одобрен! Спасибо за покупку! 🎉

Товар будет отправлен в течение 24-48 часов."""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]])
            await callback.bot.send_message(payment['user_id'], user_notification, reply_markup=keyboard)
        except Exception as e:
            print(f"Error sending user notification: {e}")
        
        await callback.answer("✅ Платеж одобрен", show_alert=True)
        await safe_edit(callback, f"✅ Платеж #{payment_id} одобрен\nПользователь уведомлен")
    else:
        await callback.answer("❌ Ошибка при одобрении платежа", show_alert=True)


@router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: CallbackQuery):
    """Отклонить платеж по карте"""
    payment_id = int(callback.data.split("_")[2])
    
    if db.reject_card_payment(payment_id):
        payment = db.get_card_payment(payment_id)
        
        # Отменяем заказ
        db.cancel_order_by_id(payment['order_id'])
        
        # Отправляем уведомление пользователю
        try:
            user_notification = f"""❌ ПЛАТЕЖ ОТКЛОНЕН

🔢 Заказ: #{payment['order_id']}
💰 Сумма: {payment['amount']}₽

К сожалению, ваш платеж был отклонен администратором.

Пожалуйста, попробуйте другой способ оплаты или свяжитесь с поддержкой."""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Поддержка", callback_data="support")]])
            await callback.bot.send_message(payment['user_id'], user_notification, reply_markup=keyboard)
        except Exception as e:
            print(f"Error sending user notification: {e}")
        
        await callback.answer("❌ Платеж отклонен", show_alert=True)
        await safe_edit(callback, f"❌ Платеж #{payment_id} отклонен\nПользователь уведомлен")
    else:
        await callback.answer("❌ Ошибка при отклонении платежа", show_alert=True)


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: CallbackQuery, state: FSMContext):
    """Проверить платеж (заглушка)"""
    order_id = int(callback.data.split("_")[2])
    
    check_text = f"""🔍 ПРОВЕРКА ПЛАТЕЖА

❌ Платеж не найден

🔢 Заказ: #{order_id}
⏱️ Время на оплату: 24 часа

💡 Пожалуйста, отправьте платеж на указанный адрес"""
    
    await safe_edit(callback, 
        check_text,
        reply_markup=get_check_payment_keyboard(order_id)
    )


@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отменить заказ"""
    user_id = callback.from_user.id
    await state.clear()
    
    if user_id in ADMIN_IDS:
        keyboard = get_admin_inline_keyboard()
    else:
        keyboard = get_main_inline_keyboard()
    
    await safe_edit(callback, "❌ Заказ отменен\n\n🏠 ГЛАВНОЕ МЕНЮ", reply_markup=keyboard)


# ===== PROFILE =====
def _format_reg_date(created_at: str) -> str:
    """Дата регистрации в виде ДД.ММ.ГГГГ"""
    if not created_at:
        return "—"
    try:
        dt = datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return created_at[:10]


def _make_uid(user_id: int) -> str:
    """Уникальный код пользователя, производный от Telegram ID (взаимно-однозначный)"""
    return f"FS-{user_id:X}"


def build_profile_text(profile: dict) -> str:
    """Красиво оформленный профиль (HTML)"""
    name = html.escape(profile.get('first_name') or "—")
    username = profile.get('username')
    username_str = f"@{html.escape(username)}" if username else "не указан"
    user_id = profile['user_id']
    uid = _make_uid(user_id)
    reg_date = _format_reg_date(profile.get('created_at'))

    return (
        "👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "<blockquote>"
        f"👤 <b>Имя:</b> {name}\n"
        f"🌐 <b>Username:</b> {username_str}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🪪 <b>UID:</b> <code>{uid}</code>\n"
        f"📅 <b>Дата регистрации:</b> {reg_date}"
        "</blockquote>\n\n"
        "<i>Нажмите на ID или UID, чтобы скопировать.</i>"
    )


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery, state: FSMContext):
    """Показать профиль (инлайн кнопка)"""
    user_id = callback.from_user.id
    profile = db.get_user_profile(user_id)

    if not profile:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    await safe_edit(callback, build_profile_text(profile), reply_markup=get_profile_keyboard(), parse_mode="HTML")


@router.message(F.text == "👤 Профиль")
async def profile_command(message: Message, state: FSMContext):
    """Показать профиль (текстовая команда)"""
    user_id = message.from_user.id
    profile = db.get_user_profile(user_id)

    if not profile:
        await message.answer("Профиль не найден", reply_markup=get_main_inline_keyboard())
        return

    await message.answer(build_profile_text(profile), reply_markup=get_profile_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "edit_phone")
async def edit_phone(callback: CallbackQuery, state: FSMContext):
    """Редактировать телефон"""
    await state.set_state(ProfileStates.entering_phone)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="profile")]])
    await safe_edit(callback, "📞 Введите ваш номер телефона:", reply_markup=keyboard)


@router.message(ProfileStates.entering_phone)
async def save_phone(message: Message, state: FSMContext):
    """Сохранить телефон"""
    user_id = message.from_user.id
    phone = message.text
    
    db.update_user_profile(user_id, phone=phone)
    await state.clear()
    
    if user_id in ADMIN_IDS:
        keyboard = get_admin_inline_keyboard()
    else:
        keyboard = get_main_inline_keyboard()
    
    await message.answer("✅ Телефон сохранен", reply_markup=keyboard)


@router.callback_query(F.data == "edit_address")
async def edit_address(callback: CallbackQuery, state: FSMContext):
    """Редактировать адрес"""
    await state.set_state(ProfileStates.entering_address)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="profile")]])
    await safe_edit(callback, "📍 Введите ваш адрес:", reply_markup=keyboard)


@router.message(ProfileStates.entering_address)
async def save_address(message: Message, state: FSMContext):
    """Сохранить адрес"""
    user_id = message.from_user.id
    address = message.text
    
    db.update_user_profile(user_id, address=address)
    await state.clear()
    
    if user_id in ADMIN_IDS:
        keyboard = get_admin_inline_keyboard()
    else:
        keyboard = get_main_inline_keyboard()
    
    await message.answer("✅ Адрес сохранен", reply_markup=keyboard)


# ===== MY ORDERS =====
def format_orders_text(orders: list) -> str:
    """Форматирует заказы по категориям статусов"""
    # Категории:
    # ожидают внимания = pending (создан, не оплачен, ещё не просрочен)
    # оплаченные = paid
    # отменённые = cancelled (не оплачен и просрочен 30 мин, либо отклонён)
    awaiting = [o for o in orders if o['status'] == 'pending']
    paid = [o for o in orders if o['status'] == 'paid']
    cancelled = [o for o in orders if o['status'] == 'cancelled']
    
    text = "📋 МОИ ЗАКАЗЫ\n"
    
    text += "\n⏳ ОЖИДАЮТ ВНИМАНИЯ (не оплачены):\n"
    if awaiting:
        for o in awaiting:
            text += f"• #{o['order_id']} — {o['product_name']} — {o['total_price']}₽\n"
    else:
        text += "—\n"
    
    text += "\n✅ ОПЛАЧЕННЫЕ:\n"
    if paid:
        for o in paid:
            text += f"• #{o['order_id']} — {o['product_name']} — {o['total_price']}₽\n"
    else:
        text += "—\n"
    
    text += "\n❌ ОТМЕНЁННЫЕ (не оплачены вовремя):\n"
    if cancelled:
        for o in cancelled:
            text += f"• #{o['order_id']} — {o['product_name']} — {o['total_price']}₽\n"
    else:
        text += "—\n"
    
    return text


@router.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery):
    """Показать мои заказы (инлайн)"""
    user_id = callback.from_user.id
    orders = db.get_user_orders(user_id)
    
    if not orders:
        await safe_edit(callback, "📭 У вас еще нет заказов", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]]))
        return
    
    back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]])
    await safe_edit(callback, format_orders_text(orders), reply_markup=back_btn)


@router.message(F.text == "📋 Мои заказы")
async def my_orders(message: Message):
    """Показать мои заказы (текстовая команда)"""
    user_id = message.from_user.id
    orders = db.get_user_orders(user_id)
    
    if not orders:
        await message.answer("📭 У вас еще нет заказов", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]]))
        return
    
    back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]])
    await message.answer(format_orders_text(orders), reply_markup=back_btn)


# ===== SUPPORT =====
@router.callback_query(F.data == "support")
async def support_callback(callback: CallbackQuery):
    """Техническая поддержка (инлайн)"""
    support_text = f"""💬 ТЕХНИЧЕСКАЯ ПОДДЕРЖКА

📞 Контакт: {SUPPORT_CONTACT}
⏱️ Время ответа: 24 часа
🕐 Доступно: Пн-Вс, 9:00-21:00
"""
    
    back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]])
    await safe_edit(callback, support_text, reply_markup=back_btn)


@router.message(F.text == "💬 Поддержка")
async def support_command(message: Message):
    """Техническая поддержка (текстовая команда)"""
    support_text = f"""💬 ТЕХНИЧЕСКАЯ ПОДДЕРЖКА

📞 Контакт: {SUPPORT_CONTACT}
⏱️ Время ответа: 24 часа
🕐 Доступно: Пн-Вс, 9:00-21:00
"""
    
    back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]])
    await message.answer(support_text, reply_markup=back_btn)


# ===== ADMIN PANEL =====
@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    """Админ панель (инлайн)"""
    user_id = callback.from_user.id
    
    if user_id not in ADMIN_IDS:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    await state.set_state(AdminStates.in_admin_panel)
    await safe_edit(callback, "Админ панель:", reply_markup=get_admin_panel_keyboard())


@router.message(F.text == "⚙️ Админ панель")
async def admin_panel(message: Message, state: FSMContext):
    """Админ панель (текстовая команда)"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.answer("Доступ запрещен")
        return
    
    await state.set_state(AdminStates.in_admin_panel)
    
    await message.answer("Админ панель:", reply_markup=get_admin_panel_keyboard())


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Статистика"""
    user_count = db.get_user_count()
    orders_stats = db.get_orders_stats()
    
    stats_text = f"""📊 СТАТИСТИКА МАГАЗИНА

👥 Пользователей: {user_count}
📦 Всего заказов: {orders_stats['total_orders']}
💰 Общий доход: {orders_stats['total_revenue']:.2f}₽
📈 Средний заказ: {orders_stats['total_revenue']/max(orders_stats['total_orders'], 1):.2f}₽"""
    
    await safe_edit(callback, stats_text, reply_markup=get_admin_panel_keyboard())


# ===== ADMIN CARDS MANAGEMENT =====
@router.callback_query(F.data == "admin_cards")
async def admin_cards_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления картами"""
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    cards = db.get_all_admin_cards()
    cards_text = f"💳 УПРАВЛЕНИЕ КАРТАМИ\n\nВсего карт: {len(cards)}"
    
    await safe_edit(callback, cards_text, reply_markup=get_admin_cards_keyboard())


@router.callback_query(F.data == "admin_add_card")
async def admin_add_card(callback: CallbackQuery, state: FSMContext):
    """Добавить карту - ввод номера"""
    await state.set_state(AdminStates.entering_card_number)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cards")]])
    await safe_edit(callback, "💳 Введите номер карты (например: 1234 5678 9012 3456):", reply_markup=keyboard)


@router.message(AdminStates.entering_card_number)
async def admin_enter_card_number(message: Message, state: FSMContext):
    """Ввести номер карты"""
    card_number = message.text.strip()
    await state.update_data(card_number=card_number)
    await state.set_state(AdminStates.entering_card_holder)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cards")]])
    await message.answer("👤 Введите имя держателя карты:", reply_markup=keyboard)


@router.message(AdminStates.entering_card_holder)
async def admin_enter_card_holder(message: Message, state: FSMContext):
    """Ввести имя держателя и сохранить карту"""
    holder_name = message.text.strip()
    data = await state.get_data()
    card_number = data['card_number']
    
    if db.add_admin_card(card_number, holder_name):
        await message.answer(f"✅ Карта добавлена!\n💳 {card_number}\n👤 {holder_name}")
        await state.clear()
        await message.answer("💳 Управление картами:", reply_markup=get_admin_cards_keyboard())
    else:
        await message.answer("❌ Ошибка. Возможно, такая карта уже существует", reply_markup=get_admin_cards_keyboard())
        await state.clear()


@router.callback_query(F.data == "admin_list_cards")
async def admin_list_cards(callback: CallbackQuery):
    """Список всех карт"""
    cards = db.get_all_admin_cards()
    
    if not cards:
        await safe_edit(callback, "📭 Карт пока нет", reply_markup=get_admin_cards_keyboard())
        return
    
    cards_text = "📋 СПИСОК КАРТ:\n\n"
    for card in cards:
        cards_text += f"💳 {card['card_number']}\n👤 {card['holder_name']}\n\n"
    
    await safe_edit(callback, cards_text, reply_markup=get_admin_cards_keyboard())


@router.callback_query(F.data == "skip_description")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Пропустить описание товара - перейти к фото"""
    await state.update_data(product_description=None, product_photos=[])
    await state.set_state(AdminStates.entering_product_photos)
    
    await safe_edit(callback, 
        "📸 Прикрепите фотографии товара (можно несколько, по одной).\n\nКогда закончите — нажмите «Готово».",
        reply_markup=get_product_photos_keyboard()
    )


@router.callback_query(F.data == "admin_add_city")
async def admin_add_city(callback: CallbackQuery, state: FSMContext):
    """Добавить город"""
    await state.set_state(AdminStates.adding_city)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback, "🏙️ Введите название города:", reply_markup=keyboard)


@router.message(AdminStates.adding_city)
async def save_city(message: Message, state: FSMContext):
    """Сохранить город"""
    city_name = message.text.strip()
    
    if db.city_exists(city_name):
        await message.answer(f"⚠️ Город '{city_name}' уже существует", reply_markup=get_admin_panel_keyboard())
        return
    
    if db.add_city(city_name):
        # Возвращаемся в админ панель
        cities = db.get_all_cities()
        cities_text = "✅ Город добавлен!\n\n🏙️ Все города:\n"
        for city_id, name in cities:
            cities_text += f"• {name}\n"
        
        await message.answer(cities_text, reply_markup=get_admin_panel_keyboard())
        await state.clear()
    else:
        await message.answer("❌ Ошибка при добавлении города", reply_markup=get_admin_panel_keyboard())


# ===== МАССОВОЕ ДОБАВЛЕНИЕ ГОРОДОВ =====
@router.callback_query(F.data == "admin_add_cities_bulk")
async def admin_add_cities_bulk(callback: CallbackQuery, state: FSMContext):
    """Добавить города списком"""
    await state.set_state(AdminStates.adding_cities_bulk)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback, 
        "📋 Отправьте список городов.\n\nКаждый город с новой строки или через запятую. Например:\n\nМосква\nСанкт-Петербург\nКазань\nНовосибирск\n\nИли: Москва, Казань, Уфа",
        reply_markup=keyboard
    )


@router.message(AdminStates.adding_cities_bulk)
async def save_cities_bulk(message: Message, state: FSMContext):
    """Сохранить города списком"""
    text = message.text.strip()
    
    # Разбиваем по переносам строк или запятым
    if "," in text:
        names = [n.strip() for n in text.split(",")]
    else:
        names = [n.strip() for n in text.split("\n")]
    
    names = [n for n in names if n]
    
    if not names:
        await message.answer("❌ Список пуст. Попробуйте снова", reply_markup=get_admin_panel_keyboard())
        await state.clear()
        return
    
    result = db.add_cities_bulk(names)
    
    result_text = f"✅ Добавление завершено!\n\n➕ Добавлено: {result['added']}\n⏭️ Пропущено (уже были): {result['skipped']}\n📊 Всего в списке: {len(names)}"
    
    await message.answer(result_text, reply_markup=get_admin_panel_keyboard())
    await state.clear()


# ===== ДОБАВЛЕНИЕ РАЙОНА =====
@router.callback_query(F.data == "admin_add_district")
async def admin_add_district(callback: CallbackQuery, state: FSMContext):
    """Выбрать город для добавления района"""
    cities = db.get_all_cities()
    
    if not cities:
        await callback.answer("Сначала добавьте город!", show_alert=True)
        return
    
    await state.set_state(AdminStates.selecting_city_for_district)
    await safe_edit(callback, "🏙️ Выберите город для добавления района:", reply_markup=get_admin_district_cities_keyboard(0))


@router.callback_query(F.data.startswith("distcity_"), AdminStates.selecting_city_for_district)
async def admin_select_city_for_district(callback: CallbackQuery, state: FSMContext):
    """Город выбран - просим ввести районы"""
    city_id = int(callback.data.split("_")[1])
    await state.update_data(district_city_id=city_id)
    await state.set_state(AdminStates.adding_district)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback, 
        "🏘️ Отправьте район или список районов.\n\nКаждый с новой строки или через запятую. Например:\n\nЦентральный\nСеверный\nЮжный",
        reply_markup=keyboard
    )


@router.message(AdminStates.adding_district)
async def save_districts(message: Message, state: FSMContext):
    """Сохранить районы"""
    text = message.text.strip()
    data = await state.get_data()
    city_id = data.get('district_city_id')
    
    if "," in text:
        names = [n.strip() for n in text.split(",")]
    else:
        names = [n.strip() for n in text.split("\n")]
    
    names = [n for n in names if n]
    
    if not names:
        await message.answer("❌ Список пуст. Попробуйте снова", reply_markup=get_admin_panel_keyboard())
        await state.clear()
        return
    
    result = db.add_districts_bulk(city_id, names)
    
    result_text = f"✅ Районы добавлены!\n\n➕ Добавлено: {result['added']}\n⏭️ Пропущено (уже были): {result['skipped']}"
    
    await message.answer(result_text, reply_markup=get_admin_panel_keyboard())
    await state.clear()


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_menu(callback: CallbackQuery, state: FSMContext):
    """Меню выбора способа добавления товара"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    await state.clear()
    menu_text = """➕ <b>ДОБАВЛЕНИЕ ТОВАРА</b>

Выберите способ добавления:

🏙️ <b>В конкретный город</b> — обычный режим (город → район → категория).

🌍 <b>Во все города и районы</b> — товар добавится сразу во все районы всех городов. Категорию нужно выбрать вручную.

🤖 <b>Авто по кейвордам</b> — категория определится автоматически по кейвордам из названия товара, и товар добавится во все районы."""
    await safe_edit(callback, menu_text, reply_markup=get_add_product_mode_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "addprod_single")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Режим «в конкретный город» — выбор города"""
    cities = db.get_all_cities()
    
    if not cities:
        await callback.answer("Сначала добавьте город!", show_alert=True)
        return
    
    await state.update_data(product_mode="single", category_name=None)
    await state.set_state(AdminStates.selecting_city_for_product)
    await safe_edit(callback, "🏙️ Выберите город для товара:", reply_markup=get_admin_product_cities_keyboard(0))


@router.callback_query(F.data == "addprod_all")
async def admin_add_product_all(callback: CallbackQuery, state: FSMContext):
    """Режим «во все города и районы» — выбор имени категории"""
    if db.count_districts() == 0:
        await callback.answer("Сначала добавьте хотя бы один район — категории живут в районах", show_alert=True)
        return
    
    await state.clear()
    await state.update_data(product_mode="all_manual", city_id=None, district_id=None, category_id=None)
    await safe_edit(callback,
        "🗂️ Выберите категорию, в которую добавить товар <b>во всех районах</b>:",
        reply_markup=get_category_names_keyboard("apcat"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("apcat_"))
async def admin_add_product_all_category(callback: CallbackQuery, state: FSMContext):
    """Выбрана категория для режима «во все» — переходим к названию"""
    idx = int(callback.data.split("_")[1])
    cat_name = category_name_by_index(idx)
    if not cat_name:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    
    await state.update_data(product_mode="all_manual", category_name=cat_name)
    await state.set_state(AdminStates.entering_product_name)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback,
        f"🗂️ Категория: <b>{html.escape(cat_name)}</b> (во всех районах)\n\n📝 Введите название товара:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "addprod_auto")
async def admin_add_product_auto(callback: CallbackQuery, state: FSMContext):
    """Режим «авто по кейвордам» — сразу к названию, категория определится позже"""
    if db.count_districts() == 0:
        await callback.answer("Сначала добавьте хотя бы один район — категории живут в районах", show_alert=True)
        return
    
    await state.clear()
    await state.update_data(product_mode="all_auto", city_id=None, district_id=None, category_id=None, category_name=None)
    await state.set_state(AdminStates.entering_product_name)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback,
        "🤖 <b>Авто-категория по кейвордам</b>\n\nКатегория определится по названию товара. 📝 Введите название товара:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ===== ДОБАВЛЕНИЕ ТОВАРА СПИСКОМ =====
def _bulk_header(data: dict) -> str:
    names = data.get('bulk_names', [])
    i = data.get('bulk_index', 0)
    total = len(names)
    cur = names[i] if i < total else ''
    return f"📋 Товар {i+1}/{total}: <b>{html.escape(cur)}</b>\n\n"


@router.callback_query(F.data == "addprod_list")
async def admin_add_product_list(callback: CallbackQuery, state: FSMContext):
    """Старт режима «списком»"""
    if db.count_districts() == 0:
        await callback.answer("Сначала добавьте район — категории живут в районах", show_alert=True)
        return
    await state.clear()
    await state.set_state(AdminStates.bulk_entering_names)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback,
        "📋 <b>Добавление товаров списком</b>\n\n"
        "Отправьте названия товаров — по одному в строке:\n"
        "<blockquote>товар1\nтовар2\nтовар3</blockquote>\n\n"
        "Потом для каждого по очереди спрошу город, район, категорию, цену, описание, фото и тип клада.",
        reply_markup=kb, parse_mode="HTML")


@router.message(AdminStates.bulk_entering_names)
async def bulk_enter_names(message: Message, state: FSMContext):
    names = [l.strip() for l in message.text.split("\n") if l.strip()]
    if not names:
        await message.answer("❌ Пусто. Отправьте названия — по одному в строке.")
        return
    await state.update_data(bulk_names=names, bulk_index=0, bulk_cities=[], bulk_districts=[],
                            bulk_city_page=0, bulk_dist_page=0, bulk_photos=[])
    await state.set_state(AdminStates.bulk_selecting_cities)
    data = await state.get_data()
    await message.answer(
        _bulk_header(data) + f"Всего товаров: {len(names)}\n\n🏙️ Отметьте города (можно несколько) и нажмите «Готово»:",
        reply_markup=get_bulk_cities_keyboard([], 0), parse_mode="HTML"
    )


# --- Мультивыбор городов ---
@router.callback_query(F.data == "bcity_done", AdminStates.bulk_selecting_cities)
async def bulk_cities_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sel = data.get('bulk_cities', [])
    if not sel:
        await callback.answer("Отметьте хотя бы один город", show_alert=True)
        return
    if not any(db.get_districts_by_city(c) for c in sel):
        await callback.answer("В выбранных городах нет районов. Добавьте районы.", show_alert=True)
        return
    await state.update_data(bulk_districts=[], bulk_dist_page=0)
    await state.set_state(AdminStates.bulk_selecting_districts)
    await safe_edit(callback,
        _bulk_header(data) + "🏘️ Отметьте районы (можно несколько) и нажмите «Готово»:",
        reply_markup=get_bulk_districts_keyboard(sel, [], 0), parse_mode="HTML")


@router.callback_query(F.data.startswith("bcitypage_"), AdminStates.bulk_selecting_cities)
async def bulk_cities_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    await state.update_data(bulk_city_page=page)
    data = await state.get_data()
    try:
        await callback.message.edit_reply_markup(reply_markup=get_bulk_cities_keyboard(data.get('bulk_cities', []), page))
    except Exception:
        pass


@router.callback_query(F.data.startswith("bcity_selpage_"), AdminStates.bulk_selecting_cities)
async def bulk_select_cities_page(callback: CallbackQuery, state: FSMContext):
    """Отметить все города на текущей странице"""
    page = int(callback.data.split("_", 2)[2])
    data = await state.get_data()
    sel = list(data.get('bulk_cities', []))
    all_cities = db.get_all_cities()
    chunk = all_cities[page * CITIES_PER_PAGE: page * CITIES_PER_PAGE + CITIES_PER_PAGE]
    for cid, _name in chunk:
        if cid not in sel:
            sel.append(cid)
    await state.update_data(bulk_cities=sel)
    try:
        await callback.message.edit_reply_markup(reply_markup=get_bulk_cities_keyboard(sel, page))
    except Exception:
        pass
    await callback.answer(f"Отмечено городов на странице: {len(chunk)}")


@router.callback_query(F.data == "bcity_selall", AdminStates.bulk_selecting_cities)
async def bulk_select_cities_all(callback: CallbackQuery, state: FSMContext):
    """Отметить все города"""
    data = await state.get_data()
    all_cities = db.get_all_cities()
    sel = [cid for cid, _name in all_cities]
    page = data.get('bulk_city_page', 0)
    await state.update_data(bulk_cities=sel)
    try:
        await callback.message.edit_reply_markup(reply_markup=get_bulk_cities_keyboard(sel, page))
    except Exception:
        pass
    await callback.answer(f"Отмечено городов: {len(sel)}")


@router.callback_query(F.data.startswith("bcity_"), AdminStates.bulk_selecting_cities)
async def bulk_toggle_city(callback: CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[1])
    data = await state.get_data()
    sel = list(data.get('bulk_cities', []))
    if cid in sel:
        sel.remove(cid)
    else:
        sel.append(cid)
    await state.update_data(bulk_cities=sel)
    page = data.get('bulk_city_page', 0)
    try:
        await callback.message.edit_reply_markup(reply_markup=get_bulk_cities_keyboard(sel, page))
    except Exception:
        pass


# --- Мультивыбор районов ---
@router.callback_query(F.data == "bdist_done", AdminStates.bulk_selecting_districts)
async def bulk_districts_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sel = data.get('bulk_districts', [])
    if not sel:
        await callback.answer("Отметьте хотя бы один район", show_alert=True)
        return
    await state.set_state(AdminStates.bulk_selecting_category)
    await safe_edit(callback,
        _bulk_header(data) + "🗂️ Выберите категорию (для всех выбранных точек):",
        reply_markup=get_category_names_keyboard("bcat", "admin_back"), parse_mode="HTML")


@router.callback_query(F.data.startswith("bdistpage_"), AdminStates.bulk_selecting_districts)
async def bulk_districts_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    await state.update_data(bulk_dist_page=page)
    data = await state.get_data()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_bulk_districts_keyboard(data.get('bulk_cities', []), data.get('bulk_districts', []), page))
    except Exception:
        pass


@router.callback_query(F.data == "bdist_selall", AdminStates.bulk_selecting_districts)
async def bulk_select_districts_all(callback: CallbackQuery, state: FSMContext):
    """Отметить все районы выбранных городов"""
    data = await state.get_data()
    city_ids = data.get('bulk_cities', [])
    sel = []
    for cid in city_ids:
        for did, _dname in db.get_districts_by_city(cid):
            sel.append(f"{cid}:{did}")
    page = data.get('bulk_dist_page', 0)
    await state.update_data(bulk_districts=sel)
    try:
        await callback.message.edit_reply_markup(reply_markup=get_bulk_districts_keyboard(city_ids, sel, page))
    except Exception:
        pass
    await callback.answer(f"Отмечено районов: {len(sel)}")


@router.callback_query(F.data.startswith("bdist_"), AdminStates.bulk_selecting_districts)
async def bulk_toggle_district(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split("_", 1)[1]
    data = await state.get_data()
    sel = list(data.get('bulk_districts', []))
    if key in sel:
        sel.remove(key)
    else:
        sel.append(key)
    await state.update_data(bulk_districts=sel)
    page = data.get('bulk_dist_page', 0)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_bulk_districts_keyboard(data.get('bulk_cities', []), sel, page))
    except Exception:
        pass


# --- Категория / цена / описание / фото / доставка ---
@router.callback_query(F.data.startswith("bcat_"), AdminStates.bulk_selecting_category)
async def bulk_select_category(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    cat_name = category_name_by_index(idx)
    if not cat_name:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    await state.update_data(bulk_category_name=cat_name)
    await state.set_state(AdminStates.bulk_entering_price)
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback,
        _bulk_header(data) + f"🗂️ Категория: <b>{html.escape(cat_name)}</b>\n\n💰 Введите цену:",
        reply_markup=kb, parse_mode="HTML")


@router.message(AdminStates.bulk_entering_price)
async def bulk_enter_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число, например 1500")
        return
    await state.update_data(bulk_price=price)
    await state.set_state(AdminStates.bulk_entering_quantity)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await message.answer("🔢 Введите количество (например: 1, 5, 100):", reply_markup=kb)


@router.message(AdminStates.bulk_entering_quantity)
async def bulk_enter_quantity(message: Message, state: FSMContext):
    try:
        quantity = float(message.text.replace(",", "."))
        if quantity <= 0:
            await message.answer("❌ Введите положительное число:")
            return
    except ValueError:
        await message.answer("❌ Введите корректное число (например: 1, 5, 100):")
        return
    await state.update_data(bulk_quantity=quantity)
    await state.set_state(AdminStates.bulk_entering_units)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await message.answer("📏 Введите единицу измерения (например: шт, гр, мл, л, кг):", reply_markup=kb)


@router.message(AdminStates.bulk_entering_units)
async def bulk_enter_units(message: Message, state: FSMContext):
    units = message.text.strip() or "шт"
    await state.update_data(bulk_units=units)
    await state.set_state(AdminStates.bulk_entering_description)
    await message.answer("📝 Введите описание (или «-» чтобы пропустить):")


@router.message(AdminStates.bulk_entering_description)
async def bulk_enter_description(message: Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = None
    await state.update_data(bulk_description=desc, bulk_photos=[])
    await state.set_state(AdminStates.bulk_entering_photos)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Готово / без фото", callback_data="bphotos_done")]])
    await message.answer(
        "📸 Пришлите фото товара (можно несколько). Когда закончите — нажмите кнопку.\n"
        "Или нажмите её сразу, чтобы без фото:",
        reply_markup=kb)


@router.message(AdminStates.bulk_entering_photos, F.photo)
async def bulk_add_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = list(data.get('bulk_photos', []))
    photos.append(message.photo[-1].file_id)
    await state.update_data(bulk_photos=photos)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"✅ Готово ({len(photos)} фото)", callback_data="bphotos_done")]])
    await message.answer(f"📸 Добавлено фото: {len(photos)}. Ещё или нажмите «Готово».", reply_markup=kb)


@router.callback_query(F.data == "bphotos_done", AdminStates.bulk_entering_photos)
async def bulk_photos_done(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.bulk_entering_delivery)
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback,
        _bulk_header(data) + "🚚 Введите тип клада (например: <i>тайник</i>).\nИли «-» для стандартной:",
        reply_markup=kb, parse_mode="HTML")


async def _bulk_next_or_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    i = data.get('bulk_index', 0)
    names = data.get('bulk_names', [])
    if i + 1 < len(names):
        await state.update_data(bulk_index=i + 1, bulk_cities=[], bulk_districts=[],
                                bulk_city_page=0, bulk_dist_page=0, bulk_category_name=None,
                                bulk_price=None, bulk_quantity=None, bulk_units=None,
                                bulk_description=None, bulk_photos=[], bulk_delivery=None)
        await state.set_state(AdminStates.bulk_selecting_cities)
        d2 = await state.get_data()
        await message.answer(
            _bulk_header(d2) + "🏙️ Отметьте города (можно несколько) и нажмите «Готово»:",
            reply_markup=get_bulk_cities_keyboard([], 0), parse_mode="HTML")
    else:
        await state.clear()
        await message.answer("✅ Список обработан! Все товары добавлены.", reply_markup=get_admin_panel_keyboard())


@router.message(AdminStates.bulk_entering_delivery)
async def bulk_enter_delivery(message: Message, state: FSMContext):
    delivery = message.text.strip()
    if delivery == "-" or delivery.lower() in ("нет", "стандарт", "стандартная"):
        delivery = None
    data = await state.get_data()
    name = data['bulk_names'][data['bulk_index']]
    price = data['bulk_price']
    description = data.get('bulk_description')
    photos = data.get('bulk_photos', [])
    category_name = data['bulk_category_name']
    targets = data.get('bulk_districts', [])
    quantity = data.get('bulk_quantity', 1)
    units = data.get('bulk_units', 'шт')
    created = 0
    for key in targets:
        try:
            cid_s, did_s = key.split(":")
            city_id = int(cid_s)
            district_id = int(did_s)
        except ValueError:
            continue
        category_id = db.get_category_id_by_district_and_name(district_id, category_name)
        if not category_id:
            continue
        pid = db.add_product(city_id, name, price, description, units=units, quantity=quantity,
                             district_id=district_id, category_id=category_id, delivery_type=delivery)
        if pid:
            created += 1
            for fid in photos:
                db.add_product_photo(pid, fid)
    qty_str = str(int(quantity)) if quantity == int(quantity) else str(quantity)
    await message.answer(
        f"✅ «{name}» добавлен в точек: {created}.\n"
        f"📊 {qty_str} {units} • 🚚 {delivery or 'Стандарт'}"
    )
    await _bulk_next_or_finish(message, state)


@router.callback_query(F.data.startswith("admin_city_"), AdminStates.selecting_city_for_product)
async def admin_select_city_for_product(callback: CallbackQuery, state: FSMContext):
    """Выбрать город для товара. Если есть районы - предложить выбор района"""
    city_id = int(callback.data.split("_")[2])
    await state.update_data(city_id=city_id, district_id=None)
    
    # Проверяем есть ли районы
    districts = db.get_districts_by_city(city_id)
    
    if districts:
        await state.set_state(AdminStates.selecting_district_for_product)
        await safe_edit(callback, "🏘️ Выберите район для товара:", reply_markup=get_admin_product_districts_keyboard(city_id, 0))
        return
    
    # Районов нет - сразу к названию
    await state.set_state(AdminStates.entering_product_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback, "📝 Введите название товара:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("admin_dist_"), AdminStates.selecting_district_for_product)
async def admin_select_district_for_product(callback: CallbackQuery, state: FSMContext):
    """Выбрать район для товара. Если район реальный - показать категории"""
    district_id = int(callback.data.split("_")[2])
    
    if district_id == 0:
        # Без района - категорий нет, сразу к названию
        await state.update_data(district_id=None, category_id=None)
        await state.set_state(AdminStates.entering_product_name)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
        await safe_edit(callback, "📝 Введите название товара:", reply_markup=keyboard)
        return
    
    # Реальный район - показываем категории
    await state.update_data(district_id=district_id)
    await state.set_state(AdminStates.selecting_category_for_product)
    await safe_edit(callback, "🗂️ Выберите категорию для товара:", reply_markup=get_admin_categories_keyboard(district_id))


# ===== Пагинация админских списков =====
@router.callback_query(F.data.startswith("apcpage_"))
async def admin_product_cities_page(callback: CallbackQuery):
    """Страницы городов при добавлении товара"""
    page = int(callback.data.split("_")[1])
    try:
        await callback.message.edit_reply_markup(reply_markup=get_admin_product_cities_keyboard(page))
    except Exception:
        await safe_edit(callback, "🏙️ Выберите город для товара:", reply_markup=get_admin_product_cities_keyboard(page))


@router.callback_query(F.data.startswith("apdpage_"))
async def admin_product_districts_page(callback: CallbackQuery, state: FSMContext):
    """Страницы районов при добавлении товара"""
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    city_id = data.get("city_id")
    if not city_id:
        await callback.answer("Сначала выберите город", show_alert=True)
        return
    try:
        await callback.message.edit_reply_markup(reply_markup=get_admin_product_districts_keyboard(city_id, page))
    except Exception:
        await safe_edit(callback, "🏘️ Выберите район для товара:", reply_markup=get_admin_product_districts_keyboard(city_id, page))


@router.callback_query(F.data.startswith("adcpage_"))
async def admin_district_cities_page(callback: CallbackQuery):
    """Страницы городов при добавлении района"""
    page = int(callback.data.split("_")[1])
    try:
        await callback.message.edit_reply_markup(reply_markup=get_admin_district_cities_keyboard(page))
    except Exception:
        await safe_edit(callback, "🏙️ Выберите город для добавления района:", reply_markup=get_admin_district_cities_keyboard(page))


@router.callback_query(F.data.startswith("pcpage_"))
async def admin_manage_cities_page(callback: CallbackQuery):
    """Страницы городов в управлении товарами"""
    page = int(callback.data.split("_")[1])
    try:
        await callback.message.edit_reply_markup(reply_markup=get_admin_manage_cities_keyboard(page))
    except Exception:
        await safe_edit(callback, "✏️ Выберите город:", reply_markup=get_admin_manage_cities_keyboard(page))


@router.callback_query(F.data.startswith("eppage_"))
async def admin_products_list_page(callback: CallbackQuery):
    """Страницы товаров в управлении"""
    parts = callback.data.split("_")  # eppage_{city_id}_{page}
    city_id = int(parts[1])
    page = int(parts[2])
    try:
        await callback.message.edit_reply_markup(reply_markup=get_admin_products_list_keyboard(city_id, page))
    except Exception:
        await safe_edit(callback, "✏️ Выберите товар:", reply_markup=get_admin_products_list_keyboard(city_id, page))


@router.callback_query(F.data.startswith("admin_cat_"), AdminStates.selecting_category_for_product)
async def admin_select_category_for_product(callback: CallbackQuery, state: FSMContext):
    """Выбрать категорию для товара"""
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminStates.entering_product_name)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await safe_edit(callback, "📝 Введите название товара:", reply_markup=keyboard)


@router.message(AdminStates.entering_product_name)
async def admin_enter_product_name(message: Message, state: FSMContext):
    """Ввести название товара"""
    product_name = message.text
    await state.update_data(product_name=product_name)
    
    data = await state.get_data()
    mode = data.get("product_mode", "single")
    
    note = ""
    # Авто-режим: определяем категорию по кейвордам прямо сейчас
    if mode == "all_auto":
        matched = db.match_category_name(product_name)
        if matched:
            await state.update_data(category_name=matched)
            note = f"🤖 Определена категория по кейвордам: <b>{html.escape(matched)}</b>\n\n"
        else:
            await state.update_data(category_name="Другое")
            note = ("🤖 Подходящих кейвордов не нашлось — товар уйдёт в категорию <b>Другое</b>.\n"
                    "💡 Добавьте кейворды в «🏷️ Категории и кейворды».\n\n")
    
    await state.set_state(AdminStates.entering_product_price)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await message.answer(note + "💰 Введите цену товара (например: 25.99):", reply_markup=keyboard, parse_mode="HTML")


@router.message(AdminStates.entering_product_price)
async def admin_enter_product_price(message: Message, state: FSMContext):
    """Ввести цену товара"""
    try:
        price = float(message.text)
        await state.update_data(product_price=price)
        await state.set_state(AdminStates.entering_product_quantity)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
        await message.answer("🔢 Введите количество товара (например: 1, 5, 100):", reply_markup=keyboard)
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
        await message.answer("❌ Введите корректную цену (например: 25.99):", reply_markup=keyboard)


@router.message(AdminStates.entering_product_quantity)
async def admin_enter_product_quantity(message: Message, state: FSMContext):
    """Ввести количество товара"""
    try:
        quantity = float(message.text)
        if quantity <= 0:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
            await message.answer("❌ Введите положительное число:", reply_markup=keyboard)
            return
        await state.update_data(product_quantity=quantity)
        await state.set_state(AdminStates.entering_product_units)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
        await message.answer("📏 Введите единицу измерения (например: шт, гр, мл, л, кг):", reply_markup=keyboard)
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
        await message.answer("❌ Введите корректное число (например: 1, 5, 100):", reply_markup=keyboard)


@router.message(AdminStates.entering_product_units)
async def admin_enter_product_units(message: Message, state: FSMContext):
    """Ввести единицы измерения"""
    units = message.text.strip()
    await state.update_data(product_units=units)
    await state.set_state(AdminStates.entering_product_description)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description")], [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]])
    await message.answer("📄 Введите описание товара или /skip:", reply_markup=keyboard)


@router.message(AdminStates.entering_product_description)
async def admin_enter_product_description(message: Message, state: FSMContext):
    """Ввести описание товара и перейти к фото"""
    description = None if message.text == "/skip" else message.text
    await state.update_data(product_description=description, product_photos=[])
    await state.set_state(AdminStates.entering_product_photos)
    
    await message.answer(
        "📸 Прикрепите фотографии товара (можно несколько, по одной).\n\nКогда закончите — нажмите «Готово».",
        reply_markup=get_product_photos_keyboard()
    )


@router.message(AdminStates.entering_product_photos, F.photo)
async def admin_add_product_photo(message: Message, state: FSMContext):
    """Принять фото товара"""
    data = await state.get_data()
    photos = data.get('product_photos', [])
    # Берём file_id самого большого размера
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(product_photos=photos)
    
    await message.answer(
        f"✅ Фото добавлено (всего: {len(photos)}). Можно ещё или нажмите «Готово».",
        reply_markup=get_product_photos_keyboard()
    )


@router.callback_query(F.data == "finish_product", AdminStates.entering_product_photos)
async def finish_product(callback: CallbackQuery, state: FSMContext):
    """Завершить создание товара - сохранить с фото"""
    data = await state.get_data()
    mode = data.get("product_mode", "single")
    city_id = data.get('city_id')
    district_id = data.get('district_id')
    category_id = data.get('category_id')
    category_name = data.get('category_name')
    product_name = data['product_name']
    product_price = data['product_price']
    product_units = data.get('product_units', 'шт')
    product_quantity = data.get('product_quantity', 1)
    description = data.get('product_description')
    photos = data.get('product_photos', [])
    
    qty_str = str(int(product_quantity)) if product_quantity == int(product_quantity) else str(product_quantity)
    
    # ===== Режим «во все районы» (вручную или авто по кейвордам) =====
    if mode in ("all_manual", "all_auto"):
        created_ids = db.add_product_everywhere(
            product_name, product_price, description,
            units=product_units, quantity=product_quantity,
            category_name=category_name
        )
        
        if created_ids:
            # Привязываем фото к каждой копии товара
            for pid in created_ids:
                for file_id in photos:
                    db.add_product_photo(pid, file_id)
            
            photo_info = f"\n📸 Фото: {len(photos)} на каждую копию" if photos else "\n📸 Без фото"
            mode_label = "🤖 авто по кейвордам" if mode == "all_auto" else "🌍 вручную"
            result_text = (
                f"✅ <b>Товар добавлен во все районы!</b>\n\n"
                f"📦 {html.escape(product_name)}\n"
                f"🗂️ Категория: <b>{html.escape(category_name or '—')}</b> ({mode_label})\n"
                f"📊 Количество: {qty_str} {product_units}\n"
                f"💰 Цена: {product_price}₽\n"
                f"🏘️ Добавлено в районов: <b>{len(created_ids)}</b>"
                f"{photo_info}"
            )
            await safe_edit(callback, result_text, parse_mode="HTML")
        else:
            await safe_edit(callback,
                f"⚠️ Не удалось добавить товар: в категории «{html.escape(category_name or '—')}» "
                f"нет ни одного района. Проверьте районы и категории."
            )
        
        await state.clear()
        await callback.message.answer("⚙️ Админ панель:", reply_markup=get_admin_panel_keyboard())
        return
    
    # ===== Обычный режим: один город / район / категория =====
    product_id = db.add_product(city_id, product_name, product_price, description, units=product_units, quantity=product_quantity, district_id=district_id, category_id=category_id)
    
    if product_id:
        # Сохраняем фото
        for file_id in photos:
            db.add_product_photo(product_id, file_id)
        
        photo_info = f"\n📸 Фото: {len(photos)}" if photos else "\n📸 Без фото"
        await safe_edit(callback, 
            f"✅ Товар '{product_name}' добавлен!\n📊 Количество: {qty_str} {product_units}\n💰 Цена: {product_price}₽{photo_info}"
        )
        await state.clear()
        await callback.message.answer("⚙️ Админ панель:", reply_markup=get_admin_panel_keyboard())
    else:
        await safe_edit(callback, "❌ Ошибка при добавлении товара", reply_markup=get_admin_panel_keyboard())
        await state.clear()


# ===== КЕЙВОРДЫ КАТЕГОРИЙ (админ) =====
@router.callback_query(F.data == "admin_keywords")
async def admin_keywords_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления кейвордами категорий"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    await state.clear()
    
    counts = db.get_keyword_counts()
    total = sum(counts.values())
    
    text = (
        "🏷️ <b>КАТЕГОРИИ И КЕЙВОРДЫ</b>\n\n"
        "Кейворды нужны для режима <b>🤖 Авто по кейвордам</b> при добавлении товара.\n\n"
        "<blockquote>Если в названии товара встречается кейворд категории — "
        "товар автоматически попадёт в эту категорию.</blockquote>\n\n"
        f"📊 Всего кейвордов: <b>{total}</b>\n\n"
        "Выберите категорию, чтобы посмотреть или изменить её кейворды:"
    )
    await safe_edit(callback, text, reply_markup=get_keywords_categories_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("kwcat_"))
async def admin_keyword_category(callback: CallbackQuery, state: FSMContext):
    """Показать кейворды конкретной категории"""
    idx = int(callback.data.split("_")[1])
    cat_name = category_name_by_index(idx)
    if not cat_name:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    
    keywords = db.get_category_keywords(cat_name)
    
    text = f"🗂️ <b>{html.escape(cat_name)}</b>\n\n"
    if keywords:
        kw_lines = "\n".join(f"• {html.escape(kw)}" for _, kw in keywords)
        text += f"🏷️ Кейворды ({len(keywords)}):\n<blockquote>{kw_lines}</blockquote>\n\n"
        text += "<i>Товар с этими словами в названии попадёт в эту категорию.</i>"
    else:
        text += "<blockquote>Кейвордов пока нет.</blockquote>\n\nДобавьте слова, по которым товары будут попадать в эту категорию."
    
    await safe_edit(callback, text, reply_markup=get_keyword_category_keyboard(idx), parse_mode="HTML")


@router.callback_query(F.data.startswith("kwadd_"))
async def admin_keyword_add_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление кейвордов"""
    idx = int(callback.data.split("_")[1])
    cat_name = category_name_by_index(idx)
    if not cat_name:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    
    await state.update_data(kw_category_name=cat_name, kw_idx=idx)
    await state.set_state(AdminStates.entering_keywords)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=f"kwcat_{idx}")]])
    text = (
        f"🗂️ Категория: <b>{html.escape(cat_name)}</b>\n\n"
        "✍️ Отправьте кейворды.\n\n"
        "<blockquote>Каждый с новой строки или через запятую. Например:\n"
        "футболка, джинсы, куртка\n"
        "худи\n"
        "кроссовки</blockquote>\n\n"
        "<i>Регистр не важен.</i>"
    )
    await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")


@router.message(AdminStates.entering_keywords)
async def admin_keyword_add_save(message: Message, state: FSMContext):
    """Сохранить кейворды"""
    data = await state.get_data()
    cat_name = data.get("kw_category_name")
    idx = data.get("kw_idx", 0)
    text = message.text.strip()
    
    if "," in text:
        kws = [k.strip() for k in text.split(",")]
    else:
        kws = [k.strip() for k in text.split("\n")]
    kws = [k for k in kws if k]
    
    if not kws:
        await message.answer("❌ Список пуст. Попробуйте снова.", reply_markup=get_keyword_category_keyboard(idx))
        await state.clear()
        return
    
    result = db.add_category_keywords(cat_name, kws)
    await state.clear()
    
    # Показываем обновлённый список
    keywords = db.get_category_keywords(cat_name)
    kw_lines = "\n".join(f"• {html.escape(kw)}" for _, kw in keywords) if keywords else "—"
    
    result_text = (
        f"✅ <b>Кейворды добавлены!</b>\n\n"
        f"🗂️ Категория: <b>{html.escape(cat_name)}</b>\n"
        f"➕ Добавлено: {result['added']}\n"
        f"⏭️ Пропущено (уже были): {result['skipped']}\n\n"
        f"🏷️ Все кейворды категории ({len(keywords)}):\n<blockquote>{kw_lines}</blockquote>"
    )
    await message.answer(result_text, reply_markup=get_keyword_category_keyboard(idx), parse_mode="HTML")


@router.callback_query(F.data.startswith("kwclear_"))
async def admin_keyword_clear(callback: CallbackQuery, state: FSMContext):
    """Очистить все кейворды категории"""
    idx = int(callback.data.split("_")[1])
    cat_name = category_name_by_index(idx)
    if not cat_name:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    
    count = db.clear_category_keywords(cat_name)
    await callback.answer(f"🗑️ Удалено кейвордов: {count}", show_alert=True)
    
    text = (
        f"🗂️ <b>{html.escape(cat_name)}</b>\n\n"
        "<blockquote>Кейвордов пока нет.</blockquote>\n\n"
        "Добавьте слова, по которым товары будут попадать в эту категорию."
    )
    await safe_edit(callback, text, reply_markup=get_keyword_category_keyboard(idx), parse_mode="HTML")


@router.callback_query(F.data.startswith("kwrename_"))
async def admin_category_rename_start(callback: CallbackQuery, state: FSMContext):
    """Начать переименование категории (во всех районах сразу)"""
    idx = int(callback.data.split("_")[1])
    cat_name = category_name_by_index(idx)
    if not cat_name:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    
    await state.update_data(rename_cat_old=cat_name, rename_cat_idx=idx)
    await state.set_state(AdminStates.renaming_category)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=f"kwcat_{idx}")]])
    text = (
        f"✏️ <b>Переименование категории</b>\n\n"
        f"Текущее имя: <b>{html.escape(cat_name)}</b>\n\n"
        "Введите новое название. Оно применится <b>сразу во всех районах</b>.\n\n"
        "<blockquote>Товары сохранятся, кейворды перенесутся. Если в каком-то районе уже есть "
        "категория с новым именем — товары объединятся в неё.</blockquote>"
    )
    await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")


@router.message(AdminStates.renaming_category)
async def admin_category_rename_save(message: Message, state: FSMContext):
    """Сохранить новое имя категории во всех районах"""
    data = await state.get_data()
    old_name = data.get("rename_cat_old")
    new_name = message.text.strip()
    await state.clear()
    
    if not new_name:
        await message.answer("❌ Пустое название. Попробуйте снова.", reply_markup=get_keywords_categories_keyboard())
        return
    
    if new_name == old_name:
        await message.answer("ℹ️ Имя не изменилось.", reply_markup=get_keywords_categories_keyboard())
        return
    
    result = db.rename_category(old_name, new_name)
    
    text = (
        f"✅ <b>Категория переименована</b>\n\n"
        f"<b>{html.escape(old_name)}</b> → <b>{html.escape(new_name)}</b>\n\n"
        f"🔁 Переименовано районов: {result['renamed']}\n"
        f"🔗 Объединено (где имя уже было): {result['merged']}\n"
        f"📦 Перенесено товаров при объединении: {result['products_moved']}"
    )
    await message.answer(text, reply_markup=get_keywords_categories_keyboard(), parse_mode="HTML")


# ===== ОТЗЫВЫ (пользователь) =====
@router.callback_query(F.data == "reviews")
async def show_reviews(callback: CallbackQuery):
    """Показать отзывы списком кнопок"""
    reviews = db.get_all_reviews()
    
    if not reviews:
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")]])
        await safe_edit(callback, "⭐ ОТЗЫВЫ\n\nПока нет отзывов.", reply_markup=back_btn)
        return
    
    await safe_edit(callback,
        "⭐ ОТЗЫВЫ НАШИХ КЛИЕНТОВ\n\nНажмите на отзыв, чтобы прочитать:",
        reply_markup=get_reviews_list_keyboard()
    )


@router.callback_query(F.data.startswith("reviewpage_"))
async def reviews_pagination(callback: CallbackQuery):
    """Перелистывание страниц списка отзывов"""
    page = int(callback.data.split("_")[1])
    try:
        await callback.message.edit_reply_markup(reply_markup=get_reviews_list_keyboard(page))
    except Exception:
        await safe_edit(callback,
            "⭐ ОТЗЫВЫ НАШИХ КЛИЕНТОВ\n\nНажмите на отзыв, чтобы прочитать:",
            reply_markup=get_reviews_list_keyboard(page)
        )


@router.callback_query(F.data.startswith("review_"))
async def show_review_card(callback: CallbackQuery):
    """Показать карточку конкретного отзыва"""
    review_id = int(callback.data.split("_")[1])
    r = db.get_review(review_id)
    
    if not r:
        await callback.answer("Отзыв не найден", show_alert=True)
        return
    
    stars = "⭐" * int(r.get('rating', 5))
    card = f"{stars}\n\n👤 {r['author']}\n"
    if r.get('city'):
        card += f"🏙️ Город: {r['city']}\n"
    if r.get('product_name'):
        card += f"📦 Товар: {r['product_name']}\n"
    card += f"\n💬 {r['text']}"
    
    await safe_edit(callback, card, reply_markup=get_review_card_keyboard())


# ===== ОТЗЫВЫ (админ) =====
@router.callback_query(F.data == "admin_reviews")
async def admin_reviews_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления отзывами"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    await state.clear()
    reviews = db.get_all_reviews()
    await safe_edit(callback, 
        f"⭐ УПРАВЛЕНИЕ ОТЗЫВАМИ\n\nВсего отзывов: {len(reviews)}",
        reply_markup=get_admin_reviews_keyboard()
    )


@router.callback_query(F.data == "admin_add_review")
async def admin_add_review_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление отзыва - имя автора"""
    await state.set_state(AdminStates.adding_review_author)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_reviews")]])
    await safe_edit(callback, "✍️ Введите имя автора отзыва:", reply_markup=keyboard)


@router.message(AdminStates.adding_review_author)
async def admin_review_author(message: Message, state: FSMContext):
    """Сохранить автора, спросить количество звёзд"""
    await state.update_data(review_author=message.text.strip())
    await state.set_state(AdminStates.adding_review_rating)
    await message.answer("⭐ Выберите оценку (количество звёзд):", reply_markup=get_stars_keyboard())


@router.callback_query(F.data.startswith("stars_"), AdminStates.adding_review_rating)
async def admin_review_rating(callback: CallbackQuery, state: FSMContext):
    """Сохранить оценку, спросить город"""
    rating = int(callback.data.split("_")[1])
    await state.update_data(review_rating=rating)
    
    cities = db.get_all_cities()
    if cities:
        await state.set_state(AdminStates.adding_review_city)
        await safe_edit(callback, "🏙️ Выберите город автора отзыва:", reply_markup=get_review_city_keyboard())
    else:
        # Городов нет - пропускаем
        await state.update_data(review_city=None)
        await state.set_state(AdminStates.adding_review_product)
        await safe_edit(callback, "📦 Введите название товара (или «Без товара»):", reply_markup=get_review_product_keyboard())


@router.callback_query(F.data.startswith("rvcity_"), AdminStates.adding_review_city)
async def admin_review_city(callback: CallbackQuery, state: FSMContext):
    """Сохранить город, спросить товар"""
    city_id = int(callback.data.split("_")[1])
    if city_id == 0:
        city_name = None
    else:
        city = db.get_city(city_id)
        city_name = city['name'] if city else None
    
    await state.update_data(review_city=city_name)
    await state.set_state(AdminStates.adding_review_product)
    await safe_edit(callback, "📦 Введите название товара или нажмите «Без товара»:", reply_markup=get_review_product_keyboard())


@router.callback_query(F.data.startswith("rvcitypage_"), AdminStates.adding_review_city)
async def admin_review_city_page(callback: CallbackQuery):
    """Перелистывание страниц городов при выборе города для отзыва"""
    page = int(callback.data.split("_")[1])
    try:
        await callback.message.edit_reply_markup(reply_markup=get_review_city_keyboard(page))
    except Exception:
        await safe_edit(callback, "🏙️ Выберите город автора отзыва:", reply_markup=get_review_city_keyboard(page))


@router.callback_query(F.data == "rvprod_skip", AdminStates.adding_review_product)
async def admin_review_product_skip(callback: CallbackQuery, state: FSMContext):
    """Пропустить товар, спросить текст"""
    await state.update_data(review_product=None)
    await state.set_state(AdminStates.adding_review_text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_reviews")]])
    await safe_edit(callback, "✍️ Введите текст отзыва:", reply_markup=keyboard)


@router.message(AdminStates.adding_review_product)
async def admin_review_product(message: Message, state: FSMContext):
    """Сохранить товар (ввод текстом), спросить текст отзыва"""
    await state.update_data(review_product=message.text.strip())
    await state.set_state(AdminStates.adding_review_text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_reviews")]])
    await message.answer("✍️ Введите текст отзыва:", reply_markup=keyboard)


@router.message(AdminStates.adding_review_text)
async def admin_review_text(message: Message, state: FSMContext):
    """Сохранить отзыв"""
    data = await state.get_data()
    author = data.get('review_author', 'Аноним')
    rating = data.get('review_rating', 5)
    city = data.get('review_city')
    product = data.get('review_product')
    text = message.text.strip()
    
    if db.add_review(author, text, rating, city, product):
        await message.answer("✅ Отзыв добавлен!", reply_markup=get_admin_reviews_keyboard())
    else:
        await message.answer("❌ Ошибка при добавлении отзыва", reply_markup=get_admin_reviews_keyboard())
    await state.clear()


@router.callback_query(F.data == "admin_del_reviews")
async def admin_del_reviews_list(callback: CallbackQuery):
    """Список отзывов для удаления"""
    reviews = db.get_all_reviews()
    
    if not reviews:
        await safe_edit(callback, "Отзывов нет", reply_markup=get_admin_reviews_keyboard())
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for r in reviews:
        stars = "⭐" * int(r.get('rating', 5))
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"🗑️ {r['author']} — {stars}", callback_data=f"delreview_{r['review_id']}")
        ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_reviews")])
    
    await safe_edit(callback, "🗑️ Выберите отзыв для удаления:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("delreview_"))
async def admin_delete_review(callback: CallbackQuery):
    """Удалить отзыв"""
    review_id = int(callback.data.split("_")[1])
    if db.delete_review(review_id):
        await callback.answer("✅ Отзыв удален", show_alert=True)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)
    # Обновляем список
    await admin_del_reviews_list(callback)


# ===== УПРАВЛЕНИЕ ГОРОДАМИ (админ) =====
@router.callback_query(F.data == "admin_cities")
async def admin_cities_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления городами"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    await state.clear()
    cities = db.get_all_cities()
    await safe_edit(callback, 
        f"🏙️ УПРАВЛЕНИЕ ГОРОДАМИ\n\nВсего городов: {len(cities)}",
        reply_markup=get_admin_cities_keyboard()
    )


@router.callback_query(F.data.startswith("admin_edit_cities_"))
async def admin_edit_cities_list(callback: CallbackQuery):
    """Список городов для редактирования с пагинацией"""
    page = int(callback.data.split("_")[-1])
    cities = db.get_all_cities()
    if not cities:
        await safe_edit(callback, "Городов нет", reply_markup=get_admin_cities_keyboard())
        return
    await safe_edit(callback, 
        "✏️ Выберите город для изменения/удаления:",
        reply_markup=get_admin_edit_cities_keyboard(page)
    )


@router.callback_query(F.data.startswith("ecitypage_"))
async def admin_edit_cities_pagination(callback: CallbackQuery):
    """Пагинация городов в админке"""
    page = int(callback.data.split("_")[1])
    await safe_edit(callback, 
        "✏️ Выберите город для изменения/удаления:",
        reply_markup=get_admin_edit_cities_keyboard(page)
    )


@router.callback_query(F.data.startswith("ecity_"))
async def admin_city_actions(callback: CallbackQuery):
    """Меню действий с городом"""
    city_id = int(callback.data.split("_")[1])
    city = db.get_city(city_id)
    if not city:
        await callback.answer("Город не найден", show_alert=True)
        return
    districts = db.get_districts_by_city(city_id)
    products = db.get_products_by_city(city_id)
    await safe_edit(callback, 
        f"🏙️ Город: {city['name']}\n🏘️ Районов: {len(districts)}\n📦 Товаров: {len(products)}\n\nВыберите действие:",
        reply_markup=get_city_edit_keyboard(city_id)
    )


@router.callback_query(F.data.startswith("rename_city_"))
async def admin_rename_city_start(callback: CallbackQuery, state: FSMContext):
    """Начать переименование города"""
    city_id = int(callback.data.split("_")[2])
    await state.update_data(edit_city_id=city_id)
    await state.set_state(AdminStates.editing_city_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=f"ecity_{city_id}")]])
    await safe_edit(callback, "✏️ Введите новое название города:", reply_markup=keyboard)


@router.message(AdminStates.editing_city_name)
async def admin_rename_city_save(message: Message, state: FSMContext):
    """Сохранить новое название города"""
    data = await state.get_data()
    city_id = data.get('edit_city_id')
    new_name = message.text.strip()
    
    if db.update_city(city_id, new_name):
        await message.answer(f"✅ Город переименован в «{new_name}»", reply_markup=get_admin_cities_keyboard())
    else:
        await message.answer("❌ Ошибка (возможно, такое название уже есть)", reply_markup=get_admin_cities_keyboard())
    await state.clear()


@router.callback_query(F.data.startswith("delcity_yes_"))
async def admin_delete_city_confirmed(callback: CallbackQuery):
    """Удалить город подтверждено"""
    city_id = int(callback.data.split("_")[2])
    if db.delete_city(city_id):
        await callback.answer("✅ Город удален", show_alert=True)
        cities = db.get_all_cities()
        await safe_edit(callback, 
            f"🏙️ УПРАВЛЕНИЕ ГОРОДАМИ\n\nВсего городов: {len(cities)}",
            reply_markup=get_admin_cities_keyboard()
        )
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


@router.callback_query(F.data.startswith("delcity_"))
async def admin_delete_city_confirm(callback: CallbackQuery):
    """Подтверждение удаления города"""
    # Защита: delcity_yes_ обрабатывается выше
    if callback.data.startswith("delcity_yes_"):
        return
    city_id = int(callback.data.split("_")[1])
    city = db.get_city(city_id)
    if not city:
        await callback.answer("Город не найден", show_alert=True)
        return
    await safe_edit(callback, 
        f"⚠️ Удалить город «{city['name']}»?\n\nВместе с ним удалятся все его районы и товары!",
        reply_markup=get_city_delete_confirm_keyboard(city_id)
    )


# ===== УПРАВЛЕНИЕ ТОВАРАМИ (админ) =====
@router.callback_query(F.data == "admin_products")
async def admin_products_menu(callback: CallbackQuery, state: FSMContext):
    """Выбор города для управления товарами"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    await state.clear()
    cities = db.get_all_cities()
    if not cities:
        await callback.answer("Сначала добавьте город", show_alert=True)
        return
    
    await safe_edit(callback, "✏️ Выберите город:", reply_markup=get_admin_manage_cities_keyboard(0))


@router.callback_query(F.data.startswith("pcity_"))
async def admin_products_by_city(callback: CallbackQuery):
    """Список товаров города для управления"""
    city_id = int(callback.data.split("_")[1])
    products = db.get_products_by_city(city_id)
    
    if not products:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_products")]])
        await safe_edit(callback, "В этом городе нет товаров", reply_markup=keyboard)
        return
    
    await safe_edit(callback, "✏️ Выберите товар:", reply_markup=get_admin_products_list_keyboard(city_id, 0))


@router.callback_query(F.data.startswith("eprod_"))
async def admin_product_actions(callback: CallbackQuery):
    """Меню действий с товаром"""
    product_id = int(callback.data.split("_")[1])
    product = db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    qty = product.get('quantity', 1)
    qty_str = str(int(qty)) if qty == int(qty) else str(qty)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"editprice_{product_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить товар", callback_data=f"delprod_{product_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_products")]
    ])
    await safe_edit(callback, 
        f"📦 {product['name']}\n📊 {qty_str} {product.get('units','шт')}\n💰 Цена: {product['price']}₽\n\nВыберите действие:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("editprice_"))
async def admin_edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Начать изменение цены"""
    product_id = int(callback.data.split("_")[1])
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminStates.editing_product_price)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=f"eprod_{product_id}")]])
    await safe_edit(callback, "💰 Введите новую цену (например: 1500):", reply_markup=keyboard)


@router.message(AdminStates.editing_product_price)
async def admin_edit_price_save(message: Message, state: FSMContext):
    """Сохранить новую цену"""
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    try:
        new_price = float(message.text)
        if db.update_product_price(product_id, new_price):
            await message.answer(f"✅ Цена изменена на {new_price}₽", reply_markup=get_admin_panel_keyboard())
        else:
            await message.answer("❌ Ошибка при изменении цены", reply_markup=get_admin_panel_keyboard())
        await state.clear()
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=f"eprod_{product_id}")]])
        await message.answer("❌ Введите корректную цену (например: 1500):", reply_markup=keyboard)


@router.callback_query(F.data.startswith("delprod_"))
async def admin_delete_product(callback: CallbackQuery):
    """Удалить товар"""
    product_id = int(callback.data.split("_")[1])
    if db.delete_product(product_id):
        await callback.answer("✅ Товар удален", show_alert=True)
        await safe_edit(callback, "✅ Товар удален", reply_markup=get_admin_panel_keyboard())
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    user_id = callback.from_user.id
    await state.clear()
    keyboard = get_main_keyboard_for(user_id)
    await show_main_menu_callback(callback, "🏠 ГЛАВНОЕ МЕНЮ", keyboard)


# ===== BACK BUTTONS =====
@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    user_id = callback.from_user.id
    await state.clear()
    keyboard = get_main_keyboard_for(user_id)
    await show_main_menu_callback(callback, "🏠 ГЛАВНОЕ МЕНЮ", keyboard)


@router.callback_query(F.data == "back_cities")
async def back_to_cities(callback: CallbackQuery):
    """Вернуться к выбору городов"""
    await show_with_city_image(callback, "🏙️ Выберите город:", get_cities_keyboard(0))


@router.callback_query(F.data == "back_districts")
async def back_to_districts(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору района"""
    # Выходим из возможного режима поиска района, данные сохраняем
    await state.set_state(None)
    data = await state.get_data()
    city_id = data.get('selected_city_id')
    
    if not city_id:
        await show_with_city_image(callback, "🏙️ Выберите город:", get_cities_keyboard(0))
        return
    
    await show_with_district_image(callback, "🏘️ Выберите район:", get_districts_keyboard(city_id))


@router.callback_query(F.data == "back_products")
async def back_to_products(callback: CallbackQuery, state: FSMContext):
    """Вернуться к товарам"""
    data = await state.get_data()
    city_id = data.get('selected_city_id')
    district_id = data.get('selected_district_id')
    category_id = data.get('selected_category_id')
    
    # Если был выбор по категории - возвращаем к товарам категории
    if category_id:
        category = db.get_category(category_id)
        if category:
            await show_with_product_image(
                callback,
                f"👕 {category['name']} — выберите товар:",
                get_products_by_category_keyboard(category_id)
            )
            return
    
    if not city_id:
        await show_with_city_image(callback, "🏙️ Выберите город:", get_cities_keyboard(0))
        return
    
    await safe_edit(callback,
        "👕 Выберите товар:",
        reply_markup=get_products_keyboard(city_id, district_id)
    )


@router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору категории"""
    data = await state.get_data()
    district_id = data.get('selected_district_id')
    
    if not district_id:
        city_id = data.get('selected_city_id')
        if city_id:
            await show_with_district_image(callback, "🏘️ Выберите район:", get_districts_keyboard(city_id))
        else:
            await show_with_city_image(callback, "🏙️ Выберите город:", get_cities_keyboard(0))
        return
    
    await show_with_category_image(callback, "🗂️ Выберите категорию:", get_categories_keyboard(district_id))
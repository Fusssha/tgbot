"""
Утилиты и примеры для работы с Fashion Shop Bot
"""

from database import Database
import sqlite3

db = Database()


# ===== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ БАЗЫ ДАННЫХ =====

def init_demo_data():
    """
    Инициализировать демо данные для тестирования
    Раскомментируй и запусти один раз для заполнения БД примерами
    """
    
    print("📝 Добавляем демо города...")
    cities = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург"]
    for city in cities:
        if not db.city_exists(city):
            db.add_city(city)
            print(f"✅ Город {city} добавлен")
    
    print("\n📦 Добавляем демо товары...")
    
    # Товары для Москвы
    moscow_products = [
        ("Черная футболка", 25.99, "Комфортная футболка из хлопка"),
        ("Синие джинсы", 49.99, "Классические джинсы с отличной посадкой"),
        ("Красная куртка", 89.99, "Теплая куртка для холодной погоды"),
        ("Белый топ", 19.99, "Элегантный топ для летнего образа"),
    ]
    
    # Товары для СПб
    spb_products = [
        ("Серое худи", 45.99, "Уютное худи на все случаи"),
        ("Белые кроссовки", 79.99, "Удобные спортивные кроссовки"),
        ("Черные леггинсы", 29.99, "Облегающие леггинсы для фитнеса"),
    ]
    
    # Добавляем товары Москвы
    moscow_id = 1
    for name, price, desc in moscow_products:
        db.add_product(moscow_id, name, price, desc)
        print(f"✅ Товар '{name}' добавлен в Москву")
    
    # Добавляем товары СПб
    spb_id = 2
    for name, price, desc in spb_products:
        db.add_product(spb_id, name, price, desc)
        print(f"✅ Товар '{name}' добавлен в СПб")
    
    print("\n✨ Демо данные успешно добавлены!")


# ===== SQL ЗАПРОСЫ ДЛЯ АДМИНИСТРАТОРА =====

def get_all_users():
    """Получить всех пользователей"""
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, first_name, username, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    
    print("\n👥 ВСЕ ПОЛЬЗОВАТЕЛИ:")
    print(f"{'ID':<15} {'Имя':<15} {'Username':<15} {'Дата':<15}")
    print("-" * 60)
    for user in users:
        print(f"{user[0]:<15} {user[1]:<15} {@user[2] if user[2] else '-':<15} {user[3]:<15}")
    print(f"\n✅ Всего пользователей: {len(users)}")


def get_detailed_orders():
    """Получить подробную информацию о заказах"""
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            o.order_id,
            u.first_name,
            p.name,
            o.quantity,
            o.total_price,
            o.status,
            o.payment_method,
            o.created_at
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN products p ON o.product_id = p.product_id
        ORDER BY o.created_at DESC
    """)
    orders = cursor.fetchall()
    conn.close()
    
    print("\n📋 ВСЕ ЗАКАЗЫ:")
    print(f"{'ID':<6} {'User':<15} {'Product':<20} {'Qty':<4} {'$':<10} {'Status':<10} {'Payment':<10}")
    print("-" * 90)
    for order in orders:
        print(f"{order[0]:<6} {order[1]:<15} {order[2]:<20} {order[3]:<4} ${order[4]:<9.2f} {order[5]:<10} {order[6] or '-':<10}")
    print(f"\n✅ Всего заказов: {len(orders)}")


def get_revenue_by_city():
    """Получить доход по городам"""
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.name as city,
            COUNT(o.order_id) as orders,
            SUM(o.total_price) as revenue
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        JOIN cities c ON p.city_id = c.city_id
        GROUP BY c.name
        ORDER BY revenue DESC
    """)
    results = cursor.fetchall()
    conn.close()
    
    print("\n💰 ДОХОД ПО ГОРОДАМ:")
    print(f"{'Город':<20} {'Заказов':<10} {'Доход':<15}")
    print("-" * 45)
    total = 0
    for city, orders, revenue in results:
        print(f"{city:<20} {orders:<10} ${revenue:<14.2f}")
        total += revenue if revenue else 0
    print("-" * 45)
    print(f"{'ВСЕГО':<20} {'':<10} ${total:<14.2f}")


def get_top_products():
    """Получить самые популярные товары"""
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.name,
            c.name as city,
            COUNT(o.order_id) as sales,
            SUM(o.quantity) as items_sold,
            p.price
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        JOIN cities c ON p.city_id = c.city_id
        GROUP BY p.product_id
        ORDER BY sales DESC
        LIMIT 10
    """)
    products = cursor.fetchall()
    conn.close()
    
    print("\n⭐ ТОП 10 ТОВАРОВ:")
    print(f"{'Товар':<25} {'Город':<15} {'Продаж':<8} {'Шт':<8} {'Цена':<8}")
    print("-" * 70)
    for product in products:
        print(f"{product[0]:<25} {product[1]:<15} {product[2]:<8} {product[3]:<8} ${product[4]:<7.2f}")


def export_users_csv():
    """Экспортировать пользователей в CSV"""
    import csv
    
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.user_id, u.first_name, u.username, u.created_at,
               p.phone, p.address
        FROM users u
        LEFT JOIN user_profiles p ON u.user_id = p.user_id
        ORDER BY u.created_at DESC
    """)
    users = cursor.fetchall()
    conn.close()
    
    with open("users_export.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Name", "Username", "Created At", "Phone", "Address"])
        writer.writerows(users)
    
    print(f"✅ Экспортировано {len(users)} пользователей в users_export.csv")


def export_orders_csv():
    """Экспортировать заказы в CSV"""
    import csv
    
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            o.order_id,
            u.first_name,
            u.user_id,
            p.name,
            o.quantity,
            o.total_price,
            o.status,
            o.payment_method,
            o.created_at
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN products p ON o.product_id = p.product_id
        ORDER BY o.created_at DESC
    """)
    orders = cursor.fetchall()
    conn.close()
    
    with open("orders_export.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Order ID", "User Name", "User ID", "Product", "Qty", "Total Price", "Status", "Payment", "Date"])
        writer.writerows(orders)
    
    print(f"✅ Экспортировано {len(orders)} заказов в orders_export.csv")


# ===== УТИЛИТЫ =====

def clear_test_data():
    """⚠️ ОЧИСТИТЬ ВСЕ ДАННЫЕ (только для тестирования!)"""
    confirm = input("⚠️ Вы уверены? Это удалит ВСЕ данные из БД! (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Операция отменена")
        return
    
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM user_profiles")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM cities")
    
    conn.commit()
    conn.close()
    
    print("✅ Все данные очищены")


def get_database_stats():
    """Получить общую статистику БД"""
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    
    # Считаем записи в каждой таблице
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cities")
    cities_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    products_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_price) FROM orders")
    total_revenue = cursor.fetchone()[0] or 0
    
    conn.close()
    
    print("\n📊 СТАТИСТИКА БД:")
    print(f"├─ Пользователей: {users_count}")
    print(f"├─ Городов: {cities_count}")
    print(f"├─ Товаров: {products_count}")
    print(f"├─ Заказов: {orders_count}")
    print(f"└─ Общий доход: ${total_revenue:.2f}")


# ===== ГЛАВНОЕ МЕНЮ =====

def admin_menu():
    """Интерактивное меню администратора"""
    
    while True:
        print("\n" + "="*50)
        print("⚙️ МЕНЮ АДМИНИСТРАТОРА")
        print("="*50)
        print("1. 📊 Получить статистику БД")
        print("2. 👥 Показать всех пользователей")
        print("3. 📋 Показать все заказы")
        print("4. 💰 Доход по городам")
        print("5. ⭐ Топ 10 товаров")
        print("6. 📤 Экспортировать пользователей (CSV)")
        print("7. 📤 Экспортировать заказы (CSV)")
        print("8. 🌱 Инициализировать демо данные")
        print("9. 🗑️ Очистить все данные (ОПАСНО!)")
        print("0. 🚪 Выход")
        print("="*50)
        
        choice = input("Выбери действие: ").strip()
        
        if choice == "1":
            get_database_stats()
        elif choice == "2":
            get_all_users()
        elif choice == "3":
            get_detailed_orders()
        elif choice == "4":
            get_revenue_by_city()
        elif choice == "5":
            get_top_products()
        elif choice == "6":
            export_users_csv()
        elif choice == "7":
            export_orders_csv()
        elif choice == "8":
            init_demo_data()
        elif choice == "9":
            clear_test_data()
        elif choice == "0":
            print("👋 До встречи!")
            break
        else:
            print("❌ Неправильный выбор")


if __name__ == "__main__":
    # Раскомментируй для использования:
    # init_demo_data()
    # get_database_stats()
    # admin_menu()
    
    print("Это файл утилит. Импортируй функции или раскомментируй последние строки.")

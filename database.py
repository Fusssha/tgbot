import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
from config import DB_NAME

# 6 категорий, которые автоматически создаются в каждом районе
DEFAULT_CATEGORIES = ["Еда", "Одежда", "Электроника", "Техника", "Телефоны", "Другое"]


class Database:
    _initialized = set()

    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        # init_db выполняем один раз за процесс на каждую БД.
        # Database() создаётся часто (в т.ч. при каждом рендере клавиатур),
        # повторная тяжёлая инициализация не нужна и вредна.
        if db_name not in Database._initialized:
            self.init_db()
            Database._initialized.add(db_name)

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица городов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cities (
                city_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Таблица районов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS districts (
                district_id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (city_id) REFERENCES cities(city_id),
                UNIQUE(city_id, name)
            )
        """)

        # Таблица товаров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_id INTEGER NOT NULL,
                district_id INTEGER,
                category_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                quantity REAL DEFAULT 1,
                units TEXT DEFAULT 'шт',
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (city_id) REFERENCES cities(city_id),
                FOREIGN KEY (district_id) REFERENCES districts(district_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        """)

        # Миграция: тип доставки у товара
        cursor.execute("PRAGMA table_info(products)")
        _pcols = [r[1] for r in cursor.fetchall()]
        if "delivery_type" not in _pcols:
            cursor.execute("ALTER TABLE products ADD COLUMN delivery_type TEXT")

        # Таблица заказов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                payment_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)

        # Таблица профилей пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                phone TEXT,
                address TEXT,
                bio TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Таблица карт администратора
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_cards (
                card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_number TEXT UNIQUE NOT NULL,
                holder_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица платежей по картам
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                admin_approved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Таблица фотографий товаров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_photos (
                photo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)

        # Таблица отзывов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                text TEXT NOT NULL,
                rating INTEGER DEFAULT 5,
                city TEXT,
                product_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица категорий (привязаны к району)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                district_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (district_id) REFERENCES districts(district_id),
                UNIQUE(district_id, name)
            )
        """)

        # Таблица кейвордов категорий (привязаны к ИМЕНИ категории, а не к району,
        # т.к. одни и те же категории повторяются во всех районах)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_keywords (
                keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL,
                keyword TEXT NOT NULL,
                UNIQUE(category_name, keyword)
            )
        """)

        conn.commit()

        # === Самолечение: убираем накопившиеся дубли и жёстко включаем уникальность ===
        # На старых базах ограничение UNIQUE(district_id, name) могло не действовать
        # (таблица создавалась раньше без него), поэтому дубли категорий могли копиться сотнями.
        # 0) Нормализуем названия: убираем лишние пробелы по краям, чтобы "Еда" и "Еда "
        #    считались одной категорией.
        cursor.execute("UPDATE categories SET name = TRIM(name) WHERE name <> TRIM(name)")
        cursor.execute("UPDATE category_keywords SET category_name = TRIM(category_name) WHERE category_name <> TRIM(category_name)")

        # 1) Схлопываем дубликаты (district_id, name): оставляем минимальный category_id,
        #    переносим на него товары, остальные строки удаляем.
        cursor.execute("""
            SELECT district_id, name, MIN(category_id), COUNT(*)
            FROM categories
            GROUP BY district_id, name
            HAVING COUNT(*) > 1
        """)
        dup_groups = cursor.fetchall()
        for district_id, name, keep_id, _cnt in dup_groups:
            cursor.execute(
                "SELECT category_id FROM categories WHERE district_id=? AND name=? AND category_id<>?",
                (district_id, name, keep_id)
            )
            dup_ids = [r[0] for r in cursor.fetchall()]
            for dup_id in dup_ids:
                cursor.execute("UPDATE products SET category_id=? WHERE category_id=?", (keep_id, dup_id))
                cursor.execute("DELETE FROM categories WHERE category_id=?", (dup_id,))

        # 2) Уникальный индекс работает и на уже существующих таблицах,
        #    в отличие от UNIQUE в CREATE TABLE IF NOT EXISTS.
        try:
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_district_name ON categories(district_id, name)"
            )
        except sqlite3.IntegrityError:
            pass

        # То же для кейвордов категорий
        cursor.execute("""
            DELETE FROM category_keywords
            WHERE keyword_id NOT IN (
                SELECT MIN(keyword_id) FROM category_keywords GROUP BY category_name, keyword
            )
        """)
        try:
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_keywords_name_kw ON category_keywords(category_name, keyword)"
            )
        except sqlite3.IntegrityError:
            pass

        conn.commit()

        # Бэкфилл: создаём категории для районов, у которых их ещё нет.
        # Набор имён берём из БАЗЫ (а не из константы), чтобы не плодить старые названия.
        cursor.execute("SELECT DISTINCT name FROM categories")
        existing_names = [r[0] for r in cursor.fetchall()]
        seed_names = existing_names if existing_names else list(DEFAULT_CATEGORIES)

        cursor.execute("SELECT district_id FROM districts")
        all_districts = [r[0] for r in cursor.fetchall()]
        for did in all_districts:
            cursor.execute("SELECT COUNT(*) FROM categories WHERE district_id = ?", (did,))
            if cursor.fetchone()[0] == 0:
                for cat_name in seed_names:
                    try:
                        cursor.execute("INSERT INTO categories (district_id, name) VALUES (?, ?)", (did, cat_name))
                    except sqlite3.IntegrityError:
                        pass
        conn.commit()
        conn.close()

    # ===== Users =====
    def add_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        """Добавить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username, first_name)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
        finally:
            conn.close()

    def get_user_count(self) -> int:
        """Получить количество пользователей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def user_exists(self, user_id: int) -> bool:
        """Проверить существует ли пользователь"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_user_profile(self, user_id: int) -> dict:
        """Получить профиль пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, u.created_at,
                   COALESCE(p.phone, '-') as phone, COALESCE(p.address, '-') as address
            FROM users u
            LEFT JOIN user_profiles p ON u.user_id = p.user_id
            WHERE u.user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "user_id": result[0],
                "username": result[1],
                "first_name": result[2],
                "created_at": result[3],
                "phone": result[4],
                "address": result[5]
            }
        return None

    def update_user_profile(self, user_id: int, phone: str = None, address: str = None) -> bool:
        """Обновить профиль пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)",
                (user_id,)
            )
            if phone:
                cursor.execute("UPDATE user_profiles SET phone = ? WHERE user_id = ?", (phone, user_id))
            if address:
                cursor.execute("UPDATE user_profiles SET address = ? WHERE user_id = ?", (address, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False
        finally:
            conn.close()

    # ===== Cities =====
    def add_city(self, city_name: str) -> bool:
        """Добавить город"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO cities (name) VALUES (?)", (city_name,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding city: {e}")
            return False
        finally:
            conn.close()

    def get_all_cities(self) -> List[Tuple[int, str]]:
        """Получить все города"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT city_id, name FROM cities ORDER BY name")
        cities = cursor.fetchall()
        conn.close()
        return cities

    def get_city(self, city_id: int) -> dict:
        """Получить город по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT city_id, name FROM cities WHERE city_id = ?", (city_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {"city_id": result[0], "name": result[1]}
        return None

    def search_cities(self, query: str) -> List[Tuple[int, str]]:
        """Поиск городов по названию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT city_id, name FROM cities WHERE name LIKE ? ORDER BY name", (f"%{query}%",))
        cities = cursor.fetchall()
        conn.close()
        return cities

    def update_city(self, city_id: int, new_name: str) -> bool:
        """Изменить название города"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE cities SET name = ? WHERE city_id = ?", (new_name, city_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating city: {e}")
            return False
        finally:
            conn.close()

    def delete_city(self, city_id: int) -> bool:
        """Удалить город вместе с районами, категориями и товарами"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Удаляем категории всех районов города
            cursor.execute("""
                DELETE FROM categories WHERE district_id IN (
                    SELECT district_id FROM districts WHERE city_id = ?
                )
            """, (city_id,))
            cursor.execute("DELETE FROM products WHERE city_id = ?", (city_id,))
            cursor.execute("DELETE FROM districts WHERE city_id = ?", (city_id,))
            cursor.execute("DELETE FROM cities WHERE city_id = ?", (city_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting city: {e}")
            return False
        finally:
            conn.close()

    def city_exists(self, city_name: str) -> bool:
        """Проверить существует ли город"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM cities WHERE name = ?", (city_name,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def add_cities_bulk(self, city_names: List[str]) -> dict:
        """Добавить несколько городов списком. Возвращает статистику"""
        conn = self.get_connection()
        cursor = conn.cursor()
        added = 0
        skipped = 0
        try:
            for name in city_names:
                name = name.strip()
                if not name:
                    continue
                try:
                    cursor.execute("INSERT INTO cities (name) VALUES (?)", (name,))
                    added += 1
                except sqlite3.IntegrityError:
                    skipped += 1
            conn.commit()
        except Exception as e:
            print(f"Error bulk adding cities: {e}")
        finally:
            conn.close()
        return {"added": added, "skipped": skipped}

    # ===== Districts =====
    def _create_default_categories(self, cursor, district_id: int):
        """Создать категории для нового района.
        Имена берём ИЗ БАЗЫ (текущий набор, уже с учётом переименований),
        а к константе обращаемся только если категорий нет вообще (первый район в системе)."""
        cursor.execute("SELECT DISTINCT name FROM categories ORDER BY name")
        names = [r[0] for r in cursor.fetchall()]
        if not names:
            names = list(DEFAULT_CATEGORIES)
        seen = set()
        for cat_name in names:
            cat_name = (cat_name or "").strip()
            if not cat_name or cat_name in seen:
                continue
            seen.add(cat_name)
            try:
                cursor.execute("INSERT INTO categories (district_id, name) VALUES (?, ?)", (district_id, cat_name))
            except sqlite3.IntegrityError:
                pass

    def add_district(self, city_id: int, district_name: str) -> bool:
        """Добавить район к городу (+ 6 категорий)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO districts (city_id, name) VALUES (?, ?)", (city_id, district_name))
            district_id = cursor.lastrowid
            self._create_default_categories(cursor, district_id)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding district: {e}")
            return False
        finally:
            conn.close()

    def add_districts_bulk(self, city_id: int, district_names: List[str]) -> dict:
        """Добавить несколько районов списком (каждому - 6 категорий)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        added = 0
        skipped = 0
        try:
            for name in district_names:
                name = name.strip()
                if not name:
                    continue
                try:
                    cursor.execute("INSERT INTO districts (city_id, name) VALUES (?, ?)", (city_id, name))
                    district_id = cursor.lastrowid
                    self._create_default_categories(cursor, district_id)
                    added += 1
                except sqlite3.IntegrityError:
                    skipped += 1
            conn.commit()
        except Exception as e:
            print(f"Error bulk adding districts: {e}")
        finally:
            conn.close()
        return {"added": added, "skipped": skipped}

    def get_districts_by_city(self, city_id: int) -> List[Tuple[int, str]]:
        """Получить все районы города"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT district_id, name FROM districts WHERE city_id = ? ORDER BY name", (city_id,))
        districts = cursor.fetchall()
        conn.close()
        return districts

    def search_districts(self, city_id: int, query: str) -> List[Tuple[int, str]]:
        """Поиск районов города по названию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT district_id, name FROM districts WHERE city_id = ? AND name LIKE ? ORDER BY name",
            (city_id, f"%{query}%")
        )
        districts = cursor.fetchall()
        conn.close()
        return districts

    def get_district(self, district_id: int) -> dict:
        """Получить информацию о районе"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT district_id, city_id, name FROM districts WHERE district_id = ?", (district_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {"district_id": result[0], "city_id": result[1], "name": result[2]}
        return None

    # ===== Categories =====
    def get_categories_by_district(self, district_id: int) -> List[Tuple[int, str]]:
        """Получить категории района. Если их нет — создать из текущего набора БД (самолечение)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories WHERE district_id = ?", (district_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT DISTINCT name FROM categories ORDER BY name")
            names = [r[0] for r in cursor.fetchall()] or list(DEFAULT_CATEGORIES)
            for n in names:
                try:
                    cursor.execute("INSERT INTO categories (district_id, name) VALUES (?, ?)", (district_id, n.strip()))
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
        cursor.execute("SELECT category_id, name FROM categories WHERE district_id = ? ORDER BY category_id", (district_id,))
        cats = cursor.fetchall()
        conn.close()
        return cats

    def get_category(self, category_id: int) -> dict:
        """Получить категорию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, district_id, name FROM categories WHERE category_id = ?", (category_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {"category_id": result[0], "district_id": result[1], "name": result[2]}
        return None

    def get_products_by_category(self, category_id: int) -> List[dict]:
        """Получить товары в категории"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, name, price, description, quantity, units, delivery_type
            FROM products
            WHERE category_id = ?
            ORDER BY created_at DESC
        """, (category_id,))
        products = cursor.fetchall()
        conn.close()
        return [
            {
                "product_id": p[0],
                "name": p[1],
                "price": p[2],
                "description": p[3],
                "quantity": p[4],
                "units": p[5],
                "delivery_type": p[6]
            }
            for p in products
        ]

    def get_delivery_types_by_category(self, category_id: int) -> List[str]:
        """Уникальные типы доставки товаров в категории.
        Пустые/NULL приводятся к None (стандартная доставка)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT delivery_type FROM products WHERE category_id = ? ORDER BY delivery_type", (category_id,))
        rows = cursor.fetchall()
        conn.close()
        types = []
        for (dt,) in rows:
            norm = (dt or "").strip() or None
            if norm not in types:
                types.append(norm)
        return types

    def get_products_by_category_and_delivery(self, category_id: int, delivery_type) -> List[dict]:
        """Товары категории с конкретным типом доставки (None = стандартная)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if delivery_type is None:
            cursor.execute("""
                SELECT product_id, name, price, description, quantity, units, delivery_type
                FROM products
                WHERE category_id = ? AND (delivery_type IS NULL OR TRIM(delivery_type) = '')
                ORDER BY created_at DESC
            """, (category_id,))
        else:
            cursor.execute("""
                SELECT product_id, name, price, description, quantity, units, delivery_type
                FROM products
                WHERE category_id = ? AND TRIM(delivery_type) = ?
                ORDER BY created_at DESC
            """, (category_id, delivery_type.strip()))
        products = cursor.fetchall()
        conn.close()
        return [
            {
                "product_id": p[0], "name": p[1], "price": p[2], "description": p[3],
                "quantity": p[4], "units": p[5], "delivery_type": p[6]
            }
            for p in products
        ]

    def get_category_id_by_district_and_name(self, district_id: int, name: str):
        """category_id категории с данным именем в районе (или None)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category_id FROM categories WHERE district_id = ? AND name = ?", (district_id, name))
        r = cursor.fetchone()
        conn.close()
        return r[0] if r else None

    def get_distinct_category_names(self) -> List[str]:
        """Уникальные имена категорий, реально существующих в районах"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM categories ORDER BY name")
        names = [r[0] for r in cursor.fetchall()]
        conn.close()
        return names

    def get_all_category_names(self) -> List[str]:
        """Имена категорий из БАЗЫ (реально существующие во всех районах).
        Константа DEFAULT_CATEGORIES используется только как подсказка,
        когда категорий в базе ещё нет вообще (нет районов)."""
        names = self.get_distinct_category_names()
        if names:
            return names
        return list(DEFAULT_CATEGORIES)

    def count_districts(self) -> int:
        """Сколько всего районов во всех городах"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM districts")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    # ===== Category keywords (привязаны к ИМЕНИ категории) =====
    def add_category_keywords(self, category_name: str, keywords: List[str]) -> dict:
        """Добавить кейворды к категории (нормализуем в нижний регистр). Возвращает статистику"""
        conn = self.get_connection()
        cursor = conn.cursor()
        added = 0
        skipped = 0
        try:
            for kw in keywords:
                kw = kw.strip().lower()
                if not kw:
                    continue
                try:
                    cursor.execute(
                        "INSERT INTO category_keywords (category_name, keyword) VALUES (?, ?)",
                        (category_name, kw)
                    )
                    added += 1
                except sqlite3.IntegrityError:
                    skipped += 1
            conn.commit()
        except Exception as e:
            print(f"Error adding keywords: {e}")
        finally:
            conn.close()
        return {"added": added, "skipped": skipped}

    def get_category_keywords(self, category_name: str) -> List[Tuple[int, str]]:
        """Получить кейворды категории: список (keyword_id, keyword)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT keyword_id, keyword FROM category_keywords WHERE category_name = ? ORDER BY keyword",
            (category_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_keyword_counts(self) -> dict:
        """Словарь {имя_категории: количество_кейвордов}"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category_name, COUNT(*) FROM category_keywords GROUP BY category_name")
        rows = cursor.fetchall()
        conn.close()
        return {name: cnt for name, cnt in rows}

    def delete_category_keyword(self, keyword_id: int) -> bool:
        """Удалить один кейворд"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM category_keywords WHERE keyword_id = ?", (keyword_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting keyword: {e}")
            return False
        finally:
            conn.close()

    def clear_category_keywords(self, category_name: str) -> int:
        """Удалить все кейворды категории. Возвращает кол-во удалённых"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM category_keywords WHERE category_name = ?", (category_name,))
            count = cursor.rowcount
            conn.commit()
            return count
        except Exception as e:
            print(f"Error clearing keywords: {e}")
            return 0
        finally:
            conn.close()

    def rename_category(self, old_name: str, new_name: str) -> dict:
        """Переименовать категорию во ВСЕХ районах сразу (безопасно к слияниям).
        Товары сохраняются (ссылаются на category_id). Кейворды мигрируют.
        Возвращает статистику {renamed, merged, products_moved}."""
        old_name = (old_name or "").strip()
        new_name = (new_name or "").strip()
        if not old_name or not new_name or old_name == new_name:
            return {"renamed": 0, "merged": 0, "products_moved": 0}

        conn = self.get_connection()
        cursor = conn.cursor()
        renamed = 0
        merged = 0
        products_moved = 0
        try:
            # Все районы, где есть категория со старым именем
            cursor.execute("SELECT district_id, category_id FROM categories WHERE name = ?", (old_name,))
            old_rows = cursor.fetchall()

            for district_id, old_cat_id in old_rows:
                # Есть ли уже в этом районе категория с новым именем?
                cursor.execute(
                    "SELECT category_id FROM categories WHERE district_id = ? AND name = ?",
                    (district_id, new_name)
                )
                existing = cursor.fetchone()

                if existing:
                    # Слияние: переносим товары на существующую категорию и удаляем старую
                    new_cat_id = existing[0]
                    cursor.execute(
                        "UPDATE products SET category_id = ? WHERE category_id = ?",
                        (new_cat_id, old_cat_id)
                    )
                    products_moved += cursor.rowcount
                    cursor.execute("DELETE FROM categories WHERE category_id = ?", (old_cat_id,))
                    merged += 1
                else:
                    # Простое переименование
                    cursor.execute(
                        "UPDATE categories SET name = ? WHERE category_id = ?",
                        (new_name, old_cat_id)
                    )
                    renamed += 1

            # Мигрируем кейворды: old_name -> new_name (дубли пропускаем, остатки удаляем)
            cursor.execute(
                "UPDATE OR IGNORE category_keywords SET category_name = ? WHERE category_name = ?",
                (new_name, old_name)
            )
            cursor.execute("DELETE FROM category_keywords WHERE category_name = ?", (old_name,))

            conn.commit()
        except Exception as e:
            print(f"Error renaming category: {e}")
        finally:
            conn.close()
        return {"renamed": renamed, "merged": merged, "products_moved": products_moved}

    def match_category_name(self, text: str) -> Optional[str]:
        """Определить категорию по кейвордам, встречающимся в тексте.
        Возвращает имя категории с наибольшим числом совпадений или None"""
        if not text:
            return None
        text_low = text.lower()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category_name, keyword FROM category_keywords")
        rows = cursor.fetchall()
        conn.close()

        scores = {}
        for cat_name, kw in rows:
            kw = (kw or "").strip().lower()
            if kw and kw in text_low:
                scores[cat_name] = scores.get(cat_name, 0) + 1
        if not scores:
            return None
        # Категория с максимальным числом совпадений
        return max(scores, key=scores.get)

    def add_product_everywhere(self, name: str, price: float, description: str = None,
                               units: str = "шт", quantity: float = 1,
                               category_name: str = None) -> List[int]:
        """Добавить товар во ВСЕ районы всех городов под категорию с данным именем.
        Возвращает список созданных product_id."""
        conn = self.get_connection()
        cursor = conn.cursor()
        created = []
        try:
            cursor.execute("""
                SELECT d.district_id, d.city_id, c.category_id
                FROM districts d
                JOIN categories c ON c.district_id = d.district_id AND c.name = ?
            """, (category_name,))
            rows = cursor.fetchall()
            for district_id, city_id, category_id in rows:
                cursor.execute("""
                    INSERT INTO products (city_id, district_id, category_id, name, price, description, units, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (city_id, district_id, category_id, name, price, description, units, quantity))
                created.append(cursor.lastrowid)
            conn.commit()
        except Exception as e:
            print(f"Error add_product_everywhere: {e}")
        finally:
            conn.close()
        return created

    # ===== Products =====
    def add_product(self, city_id: int, name: str, price: float, description: str = None, image_url: str = None, units: str = "шт", quantity: float = 1, district_id: int = None, category_id: int = None, delivery_type: str = None) -> int:
        """Добавить товар. Возвращает product_id или 0 при ошибке"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO products (city_id, district_id, category_id, name, price, description, image_url, units, quantity, delivery_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (city_id, district_id, category_id, name, price, description, image_url, units, quantity, delivery_type))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding product: {e}")
            return 0
        finally:
            conn.close()

    def update_product_price(self, product_id: int, new_price: float) -> bool:
        """Изменить цену товара"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE products SET price = ? WHERE product_id = ?", (new_price, product_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating price: {e}")
            return False
        finally:
            conn.close()

    def delete_product(self, product_id: int) -> bool:
        """Удалить товар вместе с фото"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM product_photos WHERE product_id = ?", (product_id,))
            cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False
        finally:
            conn.close()

    def add_product_photo(self, product_id: int, file_id: str) -> bool:
        """Добавить фото к товару"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO product_photos (product_id, file_id) VALUES (?, ?)", (product_id, file_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding photo: {e}")
            return False
        finally:
            conn.close()

    def get_product_photos(self, product_id: int) -> List[str]:
        """Получить все file_id фото товара"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT file_id FROM product_photos WHERE product_id = ? ORDER BY created_at", (product_id,))
        photos = cursor.fetchall()
        conn.close()
        return [p[0] for p in photos]

    def get_products_by_city(self, city_id: int, district_id: int = None) -> List[dict]:
        """Получить товары по городу (и району, если указан)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if district_id is not None:
            cursor.execute("""
                SELECT product_id, name, price, description, quantity, units
                FROM products
                WHERE city_id = ? AND district_id = ?
                ORDER BY created_at DESC
            """, (city_id, district_id))
        else:
            cursor.execute("""
                SELECT product_id, name, price, description, quantity, units
                FROM products
                WHERE city_id = ?
                ORDER BY created_at DESC
            """, (city_id,))
        products = cursor.fetchall()
        conn.close()
        
        return [
            {
                "product_id": p[0],
                "name": p[1],
                "price": p[2],
                "description": p[3],
                "quantity": p[4],
                "units": p[5]
            }
            for p in products
        ]

    def get_product(self, product_id: int) -> dict:
        """Получить информацию о товаре"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, name, price, description, quantity, units, delivery_type
            FROM products
            WHERE product_id = ?
        """, (product_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "product_id": result[0],
                "name": result[1],
                "price": result[2],
                "description": result[3],
                "quantity": result[4],
                "units": result[5],
                "delivery_type": result[6]
            }
        return None

    # ===== Orders =====
    def create_order(self, user_id: int, product_id: int, quantity: int = 1, 
                     payment_method: str = None, payment_address: str = None) -> int:
        """Создать заказ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            product = self.get_product(product_id)
            if not product:
                return 0
            
            total_price = product["price"] * quantity
            
            cursor.execute("""
                INSERT INTO orders (user_id, product_id, quantity, total_price, payment_method, payment_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, product_id, quantity, total_price, payment_method, payment_address))
            conn.commit()
            order_id = cursor.lastrowid
            return order_id
        except Exception as e:
            print(f"Error creating order: {e}")
            return 0
        finally:
            conn.close()

    def get_user_orders(self, user_id: int) -> List[dict]:
        """Получить заказы пользователя (с автоотменой просроченных)"""
        # Сначала отменяем просроченные
        self.cancel_expired_orders()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.order_id, p.name, o.quantity, o.total_price, o.status, o.created_at
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        """, (user_id,))
        orders = cursor.fetchall()
        conn.close()
        
        return [
            {
                "order_id": o[0],
                "product_name": o[1],
                "quantity": o[2],
                "total_price": o[3],
                "status": o[4],
                "created_at": o[5]
            }
            for o in orders
        ]

    def cancel_expired_orders(self) -> int:
        """Отменить неоплаченные заказы старше 30 минут. Возвращает кол-во отмененных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # SQLite: created_at в UTC, сравниваем с now - 30 минут
            cursor.execute("""
                UPDATE orders
                SET status = 'cancelled'
                WHERE status = 'pending'
                AND datetime(created_at) <= datetime('now', '-30 minutes')
            """)
            count = cursor.rowcount
            conn.commit()
            return count
        except Exception as e:
            print(f"Error cancelling expired orders: {e}")
            return 0
        finally:
            conn.close()

    def mark_order_paid(self, order_id: int) -> bool:
        """Пометить заказ как оплаченный (подтвержден)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE orders SET status = 'paid' WHERE order_id = ?", (order_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error marking order paid: {e}")
            return False
        finally:
            conn.close()

    def cancel_order_by_id(self, order_id: int) -> bool:
        """Отменить конкретный заказ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE orders SET status = 'cancelled' WHERE order_id = ?", (order_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False
        finally:
            conn.close()

    def get_order(self, order_id: int) -> dict:
        """Получить информацию о заказе"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT order_id, user_id, product_id, quantity, total_price, status, payment_method, payment_address, created_at
            FROM orders
            WHERE order_id = ?
        """, (order_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "order_id": result[0],
                "user_id": result[1],
                "product_id": result[2],
                "quantity": result[3],
                "total_price": result[4],
                "status": result[5],
                "payment_method": result[6],
                "payment_address": result[7],
                "created_at": result[8]
            }
        return None

    def get_all_orders_count(self) -> int:
        """Получить общее количество заказов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_orders_stats(self) -> dict:
        """Получить статистику по заказам"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*), SUM(total_price)
            FROM orders
        """)
        result = cursor.fetchone()
        conn.close()
        
        return {
            "total_orders": result[0] or 0,
            "total_revenue": result[1] or 0
        }

    # ===== ADMIN CARDS =====
    def add_admin_card(self, card_number: str, holder_name: str) -> bool:
        """Добавить карту администратора"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO admin_cards (card_number, holder_name)
                VALUES (?, ?)
            """, (card_number, holder_name))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding card: {e}")
            return False
        finally:
            conn.close()

    def get_all_admin_cards(self) -> List[dict]:
        """Получить все карты администратора"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT card_id, card_number, holder_name FROM admin_cards ORDER BY created_at DESC")
        cards = cursor.fetchall()
        conn.close()
        
        return [
            {
                "card_id": c[0],
                "card_number": c[1],
                "holder_name": c[2]
            }
            for c in cards
        ]

    # ===== CARD PAYMENTS =====
    def create_card_payment(self, order_id: int, user_id: int, username: str, amount: float) -> int:
        """Создать платеж по карте"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO card_payments (order_id, user_id, username, amount, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (order_id, user_id, username, amount))
            conn.commit()
            payment_id = cursor.lastrowid
            return payment_id
        except Exception as e:
            print(f"Error creating card payment: {e}")
            return 0
        finally:
            conn.close()

    def get_pending_card_payments(self) -> List[dict]:
        """Получить все ожидающие платежи по карте"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT payment_id, order_id, user_id, username, amount, created_at
            FROM card_payments
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        payments = cursor.fetchall()
        conn.close()
        
        return [
            {
                "payment_id": p[0],
                "order_id": p[1],
                "user_id": p[2],
                "username": p[3],
                "amount": p[4],
                "created_at": p[5]
            }
            for p in payments
        ]

    def get_card_payment(self, payment_id: int) -> dict:
        """Получить платеж по карте"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT payment_id, order_id, user_id, username, amount, status, admin_approved
            FROM card_payments
            WHERE payment_id = ?
        """, (payment_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "payment_id": result[0],
                "order_id": result[1],
                "user_id": result[2],
                "username": result[3],
                "amount": result[4],
                "status": result[5],
                "admin_approved": result[6]
            }
        return None

    def approve_card_payment(self, payment_id: int) -> bool:
        """Одобрить платеж по карте"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE card_payments
                SET status = 'approved', admin_approved = 1
                WHERE payment_id = ?
            """, (payment_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error approving payment: {e}")
            return False
        finally:
            conn.close()

    def reject_card_payment(self, payment_id: int) -> bool:
        """Отклонить платеж по карте"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE card_payments
                SET status = 'rejected', admin_approved = 0
                WHERE payment_id = ?
            """, (payment_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error rejecting payment: {e}")
            return False
        finally:
            conn.close()

    # ===== Reviews =====
    def add_review(self, author: str, text: str, rating: int = 5, city: str = None, product_name: str = None) -> bool:
        """Добавить отзыв"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO reviews (author, text, rating, city, product_name) VALUES (?, ?, ?, ?, ?)",
                (author, text, rating, city, product_name)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding review: {e}")
            return False
        finally:
            conn.close()

    def get_all_reviews(self) -> List[dict]:
        """Получить все отзывы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT review_id, author, text, rating, city, product_name, created_at FROM reviews ORDER BY created_at DESC")
        reviews = cursor.fetchall()
        conn.close()
        return [
            {
                "review_id": r[0],
                "author": r[1],
                "text": r[2],
                "rating": r[3],
                "city": r[4],
                "product_name": r[5],
                "created_at": r[6]
            }
            for r in reviews
        ]

    def get_review(self, review_id: int) -> dict:
        """Получить один отзыв"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT review_id, author, text, rating, city, product_name, created_at FROM reviews WHERE review_id = ?", (review_id,))
        r = cursor.fetchone()
        conn.close()
        if r:
            return {
                "review_id": r[0],
                "author": r[1],
                "text": r[2],
                "rating": r[3],
                "city": r[4],
                "product_name": r[5],
                "created_at": r[6]
            }
        return None

    def delete_review(self, review_id: int) -> bool:
        """Удалить отзыв"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM reviews WHERE review_id = ?", (review_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting review: {e}")
            return False
        finally:
            conn.close()
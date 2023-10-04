import telebot
import sqlite3
from telebot import types
import threading
import requests
from io import BytesIO

# Замените 'YOUR_API_KEY' на ваш ключ API Telegram Bot Father
bot = telebot.TeleBot('6340345708:AAHv5M58voClrGGL0HBJtfw81Z2AeUA_714')

# Создание и настройка базы данных SQLite
conn = sqlite3.connect('store.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы для товаров
cursor.execute('''CREATE TABLE IF NOT EXISTS products
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, name TEXT, description TEXT, photo_url TEXT, price DECIMAL)''')
conn.commit()

# Создание таблицы для администраторов
cursor.execute('''CREATE TABLE IF NOT EXISTS admins
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER)''')
conn.commit()



# Клавиатура для выбора категорий
category_keyboard = types.ReplyKeyboardMarkup(row_width=1)  # Установим ширину клавиатуры в 4 кнопки
category_keyboard.add(
    types.KeyboardButton("Товари для блекауту 🕯️"),
    types.KeyboardButton("Автотовари 🚗"),
    types.KeyboardButton("Електроніка 📱"),
    types.KeyboardButton("Товари для кухні 🍳"),
    types.KeyboardButton("Товари для дому 🏡"),
    types.KeyboardButton("Гаджети та аксесуари 🎮"),
    types.KeyboardButton("Військові товари ⚔️"),
    types.KeyboardButton("Зарядні станції, генератори, сонячні панелі ☀️")
)


# Словарь для хранения товаров в категориях
categories = {
    'Товари для блекауту 🕯️': [],
    'Зарядні станції, генератори, сонячні панелі ☀️': [],
    'Автотовари 🚗': [],
    'Електроніка 📱': [],
    'Товари для кухні 🍳': [],
    'Товари для дому 🏡': [],
    'Гаджети та аксесуари 🎮': [],
    'Військові товари ⚔️': []
}

# Блокировка для доступа к базе данных из разных потоков
db_lock = threading.Lock()

# Обработчик команды /admin для входа в админ-панель
@bot.message_handler(commands=['admin'])
def admin_login(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        bot.send_message(user_id, "Ласкаво просимо, адміністратор!")
        show_admin_panel(user_id)
    else:
        bot.send_message(user_id, "Ця команда доступна тільки адміністраторам.")


# Отправка сообщения администратору о новом заказе
def send_order_to_manager(user_id, order_text):
    manager_user_id = 1878470364, 5928940080, 1135187857  # Замените на ID аккаунта менеджера
    bot.send_message(manager_user_id, f"Нове замовлення від користувача {user_id}:\n{order_text}")

# Проверка, является ли пользователь администратором
def is_admin(user_id):
    admin_ids = [1878470364, 5928940080, 1135187857]  # Замените на список ID администраторов
    return user_id in admin_ids

# Функция для отображения админ-панели
def show_admin_panel(user_id):
    admin_panel_keyboard = types.ReplyKeyboardMarkup(row_width=1)
    admin_panel_keyboard.add('Додати товар', 'Видалити товар',)
    bot.send_message(user_id, "Ви увійшли в адмін-панель.", reply_markup=admin_panel_keyboard)

# Функция для отображения категорий товаров
def show_categories(user_id):
    bot.send_message(user_id, "Виберіть категорію:", reply_markup=category_keyboard)

image_path = '123.jpg'  # Замените на путь к вашему изображению


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        bot.send_message(user_id, "Ласкаво просимо, адміністратор!")
        show_admin_panel(user_id)
    else:
        bot.send_message(user_id, "Ласкаво просимо до магазину!")
        show_categories(user_id)

# Функция для отображения товаров в выбранной категории
# Обработчик для отображения товаров в выбранной категории
def show_items_in_category(user_id, category):
    with db_lock:
        cursor.execute("SELECT name, description, photo_url, price FROM products WHERE category=?", (category,))
        items = cursor.fetchall()

    if not items:
        bot.send_message(user_id, "У цій категорії поки що немає товарів.")
    else:
        for item in items:
            name, description, photo_url, price = item
            markup = types.InlineKeyboardMarkup()
            buy_button = types.InlineKeyboardButton("Купити", url="https://t.me/prime_market_manager")
            markup.add(buy_button)
            message_text = f"<b>{name}</b>\n\n{description}\n\nЦіна: {price} грн"
            
            # Отправка фотографии как фото
            try:
                image_data = requests.get(photo_url).content
                bot.send_photo(user_id, BytesIO(image_data), caption=message_text, parse_mode='HTML', reply_markup=markup)
            except Exception as e:
                bot.send_message(user_id, f"Помилка при завантаженні фотографії товару: {str(e)}")

# Обработчик выбора категории
@bot.message_handler(func=lambda message: message.text in categories.keys())
def handle_category(message):
    category = message.text
    user_id = message.from_user.id
    bot.send_message(user_id, f"Вибрана категорія: {category}")
    show_items_in_category(user_id, category)

# Обработчик команды "Додати товар"
@bot.message_handler(func=lambda message: message.text == 'Додати товар')
def add_product(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        bot.send_message(user_id, "Введіть назву товару:")
        bot.register_next_step_handler(message, add_product_name)
    else:
        bot.send_message(user_id, "Ця функція доступна тільки адміністраторам.")

# Обработчик для ввода назвы товара
def add_product_name(message):
    user_id = message.from_user.id
    product_name = message.text.strip()
    
    if product_name:
        bot.send_message(user_id, "Виберіть категорію товару:", reply_markup=category_keyboard)
        bot.register_next_step_handler(message, add_product_category, product_name)
    else:
        bot.send_message(user_id, "Назва товару не може бути порожньою. Спробуйте ще раз.")

# Обработчик для выбора категории товара
def add_product_category(message, product_name):
    user_id = message.from_user.id
    category = message.text
    
    bot.send_message(user_id, "Введіть опис товару:")
    bot.register_next_step_handler(message, add_product_description, product_name, category)

# Обработчик для ввода описания товара
def add_product_description(message, product_name, category):
    user_id = message.from_user.id
    description = message.text.strip()
    
    bot.send_message(user_id, "Введіть посилання на фото товару:")
    bot.register_next_step_handler(message, add_product_photo, product_name, category, description)

# Обработчик для ввода фото товара
def add_product_photo(message, product_name, category, description):
    user_id = message.from_user.id
    photo_url = message.text.strip()
    
    bot.send_message(user_id, "Введіть ціну товару (грн):")
    bot.register_next_step_handler(message, add_product_price, product_name, category, description, photo_url)

# Обработчик для ввода цены товара и добавления товара в базу данных
def add_product_price(message, product_name, category, description, photo_url):
    user_id = message.from_user.id
    price_text = message.text.strip()
    
    try:
        price = float(price_text)
    except ValueError:
        bot.send_message(user_id, "Некоректна ціна. Спробуйте ще раз.")
        return
    
    with db_lock:
        cursor.execute("INSERT INTO products (category, name, description, photo_url, price) VALUES (?, ?, ?, ?, ?)", (category, product_name, description, photo_url, price))
        conn.commit()
    
    # Отправляем изображение как фото, а не как документ
    try:
        image_data = requests.get(photo_url).content
        bot.send_photo(user_id, BytesIO(image_data), caption=f"Товар '{product_name}' додано в категорію '{category}'.\n\nЦіна: {price} грн", parse_mode='HTML')
    except Exception as e:
        bot.send_message(user_id, f"Помилка при завантаженні фотографії товару: {str(e)}")

# Обработчик команды "Видалити товар"
@bot.message_handler(func=lambda message: message.text == 'Видалити товар')
def delete_product(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        bot.send_message(user_id, "Введіть назву товару, який ви хочете видалити:")
        bot.register_next_step_handler(message, delete_product_confirm)
    else:
        bot.send_message(user_id, "Ця функція доступна тільки адміністраторам.")

# Обработчик для подтверждения удаления товара
def delete_product_confirm(message):
    user_id = message.from_user.id
    product_name = message.text.strip()
    
    with db_lock:
        cursor.execute("DELETE FROM products WHERE name=?", (product_name,))
        conn.commit()
    
    bot.send_message(user_id, f"Товар '{product_name}' видалено.")

# Обработчик команды "Переглянути замовлення"
@bot.message_handler(func=lambda message: message.text == 'Переглянути замовлення')
def view_orders(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        # Здесь можно добавить код для просмотра заказов
        bot.send_message(user_id, "Вибачте, ця функція ще не реалізована.")
    else:
        bot.send_message(user_id, "Ця функція доступна тільки адміністраторам.")

# Обработчик команды "Корзина"
@bot.message_handler(func=lambda message: message.text == 'Корзина')
def show_cart(message):
    user_id = message.from_user.id
    if user_id in user_cart:
        cart_items = user_cart[user_id]
        if cart_items:
            cart = "\n".join(cart_items)
            bot.send_message(user_id, f"Ваша корзина:\n{cart}")
        else:
            bot.send_message(user_id, "Ваша корзина пуста.")
    else:
        bot.send_message(user_id, "Ваша корзина пуста.")

# Обработчик команды "Додати в корзину"
@bot.callback_query_handler(lambda query: query.data.startswith('add_to_cart_'))
def add_to_cart_callback(query):
    user_id = query.from_user.id
    product_name = query.data.replace('add_to_cart_', '').strip()
    
    if user_id not in user_cart:
        user_cart[user_id] = []
    
    user_cart[user_id].append(product_name)
    bot.answer_callback_query(query.id, text=f"{product_name} додано в корзину.")

# Обработчик команды "Додати в корзину"
@bot.callback_query_handler(lambda query: query.data.startswith('add_to_cart_'))
def add_to_cart_callback(query):
    user_id = query.from_user.id
    product_name = query.data.replace('add_to_cart_', '').strip()
    
    if user_id not in user_cart:
        user_cart[user_id] = []
    
    user_cart[user_id].append(product_name)
    
    # Создаем инлайн-кнопку "Купити" и отправляем ее пользователю
    buy_button = types.InlineKeyboardButton("Купити", url="https://t.me/prime_market_manager")
    markup = types.InlineKeyboardMarkup().add(buy_button)
    bot.send_message(user_id, f"Ви додали товар '{product_name}' в корзину.", reply_markup=markup)
    bot.answer_callback_query(query.id, text=f"Ви додали товар '{product_name}' в корзину.")

# Обработчик команды для удаления всех товаров
@bot.message_handler(commands=['delete_all_products'])
def delete_all_products(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        with db_lock:
            cursor.execute("DELETE FROM products")
            conn.commit()
        bot.send_message(user_id, "Всі товари було видалено з магазину.")
    else:
        bot.send_message(user_id, "Ця команда доступна тільки адміністраторам.")


# Удалите обработчик команды "Купити"
# @bot.callback_query_handler(lambda query: query.data.startswith('buy_'))
# def buy_callback(query):
#     user_id = query.from_user.id
#     product_name = query.data.replace('buy_', '').strip()
    
#     if user_id in user_cart:
#         cart_items = user_cart[user_id]
#         if product_name in cart_items:
#             cart_items.remove(product_name)
#             bot.answer_callback_query(query.id, text=f"Ви купили товар: {product_name}")
#         else:
#             bot.answer_callback_query(query.id, text=f"Товар {product_name} вже було куплено.")
#     else:
#         bot.answer_callback_query(query.id, text=f"Ваша корзина пуста. Додайте товари перед покупкою.")


# Функция для отображения админ-панели
def show_admin_panel(user_id):
    admin_panel_keyboard = types.ReplyKeyboardMarkup(row_width=1)
    admin_panel_keyboard.add('Додати товар', 'Видалити товар', 'Вийти з адмін-панелі')
    bot.send_message(user_id, "Ви увійшли в адмін-панель.", reply_markup=admin_panel_keyboard)

# Обработчик команды "Вийти з адмін-панелі"
@bot.message_handler(func=lambda message: message.text == 'Вийти з адмін-панелі')
def exit_admin_panel(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Ви вийшли з адмін-панелі.")
    show_categories(user_id)


# Запуск бота
if __name__ == "__main__":
    user_cart = {}  # Словарь для хранения корзин пользователей
    bot.polling(none_stop=True)





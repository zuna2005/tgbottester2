import os
import telebot
from telebot import types
import logging
import psycopg2
from config import *
from flask import Flask, request

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

db_connection = psycopg2.connect(DB_URI, sslmode='require')
db_object = db_connection.cursor()


def update_messages_count(user_id):
    db_object.execute(f"UPDATE users SET messages = messages + 1 WHERE id = {user_id}")
    db_connection.commit()


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    bot.reply_to(message, f'''Здравствуйте, {username}
Вас привествует бот для заказа компрессионого белья от Medex Solution''')
    main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    item_catalogue = types.KeyboardButton('Каталог')
    item_bag = types.KeyboardButton('Корзина')
    item_info = types.KeyboardButton('О нас')
    main_markup.add(item_catalogue)
    main_markup.add(item_bag, item_info)

    bot.send_message(message.chat.id, 'C чего начнем?', reply_markup=main_markup)

    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, messages) VALUES (%s, %s, %s)", (user_id, username, 0))
        db_connection.commit()

    update_messages_count(user_id)


@bot.message_handler(commands=["stats"])
def get_stats(message):
    db_object.execute("SELECT * FROM users ORDER BY messages DESC LIMIT 10")
    result = db_object.fetchall()

    if not result:
        bot.reply_to(message, "No data...")
    else:
        reply_message = "- Top flooders:\n"
        for i, item in enumerate(result):
            reply_message += f"[{i + 1}] {item[1].strip()} ({item[0]}) : {item[2]} messages.\n"
        bot.reply_to(message, reply_message)

    update_messages_count(message.from_user.id)


@bot.message_handler(func=lambda message: True, content_types=["text"])
def message_from_user(message):
    user_id = message.from_user.id
    update_messages_count(user_id)
    if message.text == 'Каталог':
        catalogue_markup = types.InlineKeyboardMarkup(row_width=3)
        item_category1 = types.InlineKeyboardButton(text='Категория 1', callback_data='category1')
        item_category2 = types.InlineKeyboardButton(text='Категория 2', callback_data='category2')
        catalogue_markup.add(item_category1, item_category2)
        bot.send_message(message.chat.id, 'Что вас интересует?', reply_markup=catalogue_markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    size_markup = types.InlineKeyboardMarkup(row_width=3)
    item_xs = types.InlineKeyboardButton(text='XS', callback_data='xs')
    item_s = types.InlineKeyboardButton(text='S', callback_data='s')
    item_m = types.InlineKeyboardButton(text='M', callback_data='m')
    item_l = types.InlineKeyboardButton(text='L', callback_data='l')
    item_xl = types.InlineKeyboardButton(text='XL', callback_data='xl')
    size_markup.add(item_xs, item_s, item_m, item_l, item_xl)
    if call.data == 'category1':
        category1_markup = types.InlineKeyboardMarkup(row_width=3)
        item_cat1_product1 = types.InlineKeyboardButton(text='Товар 1', callback_data='category1_product1')
        item_cat1_product2 = types.InlineKeyboardButton(text='Товар 2', callback_data='category1_product2')
        category1_markup.add(item_cat1_product1, item_cat1_product2)
        bot.send_message(call.message.chat.id, 'Выберите товар', reply_markup=category1_markup)
    elif call.data == 'category2':
        category2_markup = types.InlineKeyboardMarkup(row_width=3)
        item_cat2_product1 = types.InlineKeyboardButton(text='Товар 1', callback_data='category2_product1')
        item_cat2_product2 = types.InlineKeyboardButton(text='Товар 2', callback_data='category2_product2')
        category2_markup.add(item_cat2_product1, item_cat2_product2)
        bot.send_message(call.message.chat.id, 'Выберите товар', reply_markup=category2_markup)
    elif call.data == 'category1_product1':
        bot.send_message(call.message.chat.id, 'Выберите размер', reply_markup=size_markup)
    elif call.data == 'category1_product2':
        bot.send_message(call.message.chat.id, 'Выберите размер', reply_markup=size_markup)
    elif call.data == 'category2_product1':
        bot.send_message(call.message.chat.id, 'Выберите размер', reply_markup=size_markup)
    elif call.data == 'category2_product2':
        bot.send_message(call.message.chat.id, 'Выберите размер', reply_markup=size_markup)


@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
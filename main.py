from bcode import CreatePluBarcode
from pathlib import Path
from configparser import ConfigParser
from statistics import mode
from model import Model, Code, User
from loguru import logger
from math import floor

import telebot
import sqlite3


config_file = Path('config.ini')
log_file = Path('bot.log')
logger.add(log_file.absolute(), rotation='10 KB', compression='zip')
if not config_file.exists():
    logger.error('Немаж файлу конфігурації!!!')

conf = ConfigParser()
conf.read(config_file.absolute())

bot = telebot.TeleBot(conf['Telegram']['bot_token'])
model = Model(conf['Database']['name'])
default_profile = 'search'
profile = default_profile
chat_id = ''


@bot.message_handler(commands=['start'])
def com_start(message):
    user = User(message)
    logger.debug(user.username)
    if not model.is_exists_user(user):
        model.add_new_user(user)
    
    bot.reply_to(message, 'Привіт')


@bot.message_handler(commands=['add'])
def com_add(message):
    global profile
    profile = 'add'
    bot.send_message(message.chat.id, 'Вкажіть назву товару, код та код Н в форматі назва, код, код Н')
    logger.debug('Додавання нового коду')


@bot.message_handler(commands=['all'])
def com_all(message):
    res = model.all_codes()
    msg = 'Всі коди: ' + str(len(res)) + '\n'
    for c in res:
        msg += str(c)
    bot.send_message(message.chat.id, msg)
    logger.debug('Всі коди')


@bot.message_handler(commands=['search_code'])
def com_search_code(message):
    global profile, chat_id
    profile = 'search_code'
    chat_id = message.chat.id
    bot.send_message(message.chat.id, 'Вкажіть PLU-код товару для його пошуку.')
    logger.debug('Пошук по PLU-коду')


@bot.message_handler(commands=['create_bcode'])
def com_create_bcode(message):
    global profile, chat_id
    profile = 'create_bcode'
    logger.debug('Створення нового штрихкоду')
    chat_id = message.chat.id
    bot.send_message(message.chat.id, 'Створення штрихкоду для вагового товару.\nВкажіть PLU-код товару та його вагу через кому, наприклад 82,1.213')
    logger.debug('Пошук по PLU-коду')



@bot.message_handler(content_types=["text"])
def handler_text(message):
    global profile
    match profile:
        case 'create_bcode':
            m = message.text
            m = m.split(',')
            bc = CreatePluBarcode()
            bc.gen_data_plu_bcode(int(m[0]), float(m[1]))
            res = model.search_product_for_code(int(m[0]))
            if len(res) == 1:
                pr = floor( float(res[0].price) * float(m[1]) )
                cp = f"{res[0].name}\n\nКод: {m[0]}\nЦіна: {res[0].price}грн\nВага: {m[1]}\nОрінтовна ціна: {pr} грн."
                bot.send_photo(message.chat.id, bc.get_file_ean13(), caption=cp)
            else:
                cp = "Невдалося знайти товар в базі! Потрібно оновити базу, скиньте Богдану файл PLUData.xls"
                bot.send_message(message.chat.id, cp)
            profile = default_profile
        case 'search_code':
            cod = int( message.text)
            res = model.search_product_for_code(cod)
            msg = f'Пошук по коду {cod}.\n'
            msg += 'Всі коди: ' + str(len(res)) + '\n'
            for c in res:
                msg += str(c)
            bot.send_message(message.chat.id, msg)
            profile = default_profile
        case 'search':
            res = model.search_code(message.text)
            logger.debug(res)
            msg = 'Знайдено: ' + str(len(res)) + ':\n'
            for c in res:
                msg += str(c)
            if len(res) == 0:
                msg = f'Нічого не вдалося знайти за запитом \'{message.text}\', спробуйте вказати назву товару поішому.'
            bot.send_message(message.chat.id, msg)
        case 'add':
            
            bot.send_message(message.chat.id, 'Ця функція недоступна!')
            profile = default_profile
        case _:
            logger.error('Щось пішло не так...')
            bot.send_message(message.chat.id, 'Щось пішло не так... Спробуйте знову')
            

logger.info('Бот звпущений...')
try:
    bot.infinity_polling()
except:
    logger.error('Помилка в пулінгу Telegram...')

import telebot
from telebot import types
import messages
from threading import Thread
import time
import random
from models import BitcoinBot
from db import db_session
from multiprocessing.dummy import Pool as ThreadPool
from sqlalchemy import or_
from random_choose import get_result
from blockchain import block_io
import blockchain

token = '1093331195:AAG_GW8OVIG2FOEnWFbLMyV40Y3RmUnmx_M'
bot = telebot.TeleBot(token)
decision = None
print ("started work", flush=True)

time.sleep(5)
from db import init_db
init_db()

def extract_refferal(text):
    return text.split()[1] if len(text.split()) > 1 else None

@bot.message_handler(commands=['start'])
def start(message):
    refferal = extract_refferal(message.text)
    if refferal:
        if len(BitcoinBot.query.filter_by(user_id=message.from_user.id).all()) == 0:
            new_user = BitcoinBot(message.from_user.id, 1000, None, message.chat.id, refferal)
            db_session.add(new_user)
            db_session.flush()
            print("added new user", flush=True)
    else:
        if len(BitcoinBot.query.filter_by(user_id=message.from_user.id).all()) == 0:
            new_user = BitcoinBot(message.from_user.id, 1000, None, message.chat.id)
            db_session.add(new_user)
            refferal_user = BitcoinBot.query.filter_by(user_id=refferal).first()
            refferal_user.user_balance += 50
            db_session.flush()
            print("added new user", flush=True)
    markup = types.ReplyKeyboardMarkup()
    markup.row("Начать игру")
    markup.row("Пополнить баланс", "Проверить баланс" ,"Вывести баланс")
    markup.row("Информация")
    bot.send_message(message.chat.id, messages.hello_message, reply_markup=markup)
    print("Started", flush=True)


@bot.message_handler(content_types=["text"])
def choose_bet_field(message):
    if message.text == "Начать игру":
        markup = types.InlineKeyboardMarkup()
        button_1 = types.InlineKeyboardButton(text="🔴 1", callback_data="1")
        button_2 = types.InlineKeyboardButton(text="⚫️ 2", callback_data="2")
        button_3 = types.InlineKeyboardButton(text="🔴 3", callback_data="3")
        button_4 = types.InlineKeyboardButton(text="⚫️ 4", callback_data="4")
        button_5 = types.InlineKeyboardButton(text="🔴 5", callback_data="5")
        button_6 = types.InlineKeyboardButton(text="⚫️ 6", callback_data="6")
        button_7 = types.InlineKeyboardButton(text="⚫️ 7", callback_data="7")
        button_8 = types.InlineKeyboardButton(text="🔴 8", callback_data="8")
        button_9 = types.InlineKeyboardButton(text="⚫️ 9", callback_data="9")
        button_10 = types.InlineKeyboardButton(text="🔴 10", callback_data="10")
        button_11 = types.InlineKeyboardButton(text="️️⚫️ 11", callback_data="11")
        button_12 = types.InlineKeyboardButton(text="🔴 12", callback_data="12")
        button_1_6 = types.InlineKeyboardButton(text="1-6", callback_data="1-6")
        button_4_9 = types.InlineKeyboardButton(text="4-9", callback_data="4-9")
        button_7_12 = types.InlineKeyboardButton(text="7-12", callback_data="7-12")
        button_even = types.InlineKeyboardButton(text="EVEN", callback_data="EVEN")
        button_red = types.InlineKeyboardButton(text="🔴", callback_data="red")
        button_black = types.InlineKeyboardButton(text="⚫️", callback_data="black")
        button_odd = types.InlineKeyboardButton(text="ODD", callback_data="ODD")
        markup.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_10, button_11, button_12, button_1_6, button_4_9, button_7_12, button_even, button_red, button_black, button_odd)
        bot.send_message(message.chat.id, "Выберите поля для ставки:", reply_markup=markup)
        print ("started game", flush=True)
    elif message.text == "Пополнить баланс":
        address = blockchain.generate_for_user(message.from_user.id)
        bot.send_message(message.chat.id, messages.balance_plus % address)
        print ("got money", flush=True)
    elif message.text == "Проверить баланс":
        user = BitcoinBot.query.filter_by(user_id=message.from_user.id).first()
        bot.send_message(message.chat.id, messages.balance_message % (user.user_balance, "t.me/bitcoin_roulette_bot?start=%s" % user.user_id))
        print ("Checked", flush=True)
    elif message.text == "Вывести баланс":
        bot.send_message(message.chat.id, messages.out_balance_message)
        print ("Went", flush=True)
    elif message.text == "Информация":
        bot.send_message(message.chat.id, messages.bet_message)
        print ("Info", flush=True)
    elif message.text.isdigit():
        save_bet_size(message.text, message.from_user.id)
        print ("Choose bet", flush=True)
    elif len(message.text.split()[1]) == 35:
        if int(message.text.split()[0]) >= 1000:
            user = BitcoinBot.query.filter_by(user_id=message.from_user.id).first()
            if user.user_balance >= int(message.text.split()[0]):
                blockchain.out_balance(message.text.split()[1], int(message.text.split()[0])*0.000001, message.from_user.id)
                bot.send_message(message.chat.id, messages.sent_money)
            else:
                bot.send_message(message.chat.id, messages.not_enough_money)
        else:
            bot.send_message(message.chat.id, messages.too_little_out_amount)


@bot.callback_query_handler(func = lambda call:True)
def save_bet(call):
    user = BitcoinBot.query.filter_by(user_id=call.from_user.id).first()
    if call.data.isdigit():
        user.user_bet = int(call.data)
    else:
        user.user_bet = call.data
    print (user.user_bet, flush=True)
    db_session.flush()
    bot.send_message(user.user_chat_id, messages.bet_size_message)

def save_bet_size(bet_size, user_id):
    user = BitcoinBot.query.filter_by(user_id=user_id).first()
    if int(bet_size) >= 50:
        if user.user_balance >= int(bet_size):
            user.user_bet_size = int(bet_size)
            user.user_balance -= int(bet_size)
            db_session.flush()
            print(user.user_bet_size)
            bot.send_message(user.user_chat_id, messages.finished_message)
        else:
            bot.send_message(user.user_chat_id, messages.not_enough)
    else:
        bot.send_message(user.user_chat_id, messages.too_little_bet_size)

def grate_winner(user):
    if user.user_bet == "ODD" or user.user_bet == "EVEN" or user.user_bet == "1-6" or user.user_bet == "4-9" or user.user_bet == "7-12" or user.user_bet == "️black" or user.user_bet == "️red":
        user.user_balance += int(user.user_bet_size)*2
        winning = int(user.user_bet_size)*2
        print ("multiplied by 2", flush = True)
    else:
        user.user_balance += int(user.user_bet_size)*12
        winning = int(user.user_bet_size)*12
        print ("multiplied by 12", flush = True)
    bot.send_message(user.user_chat_id, messages.end_game % (decision, user.user_bet_size, user.user_bet, winning))
    user.user_bet = None

def send_loser(user):
    bot.send_message(user.user_chat_id, messages.end_game % (decision, user.user_bet_size, user.user_bet, 0))
    user.user_bet = None

def play_game():
    while (True):
        print ("Started game", flush=True)
        global decision
        decision, win_range, color, oddity = get_result()
        print ("Got result", flush=True)
        list_of_winners = db_session.query(BitcoinBot).filter(or_((BitcoinBot.user_bet==decision) | (BitcoinBot.user_bet==color) | (BitcoinBot.user_bet==oddity) | (BitcoinBot.user_bet==win_range)))
        print ("Got winners", flush=True)
        for win in list_of_winners:
            print (win.user_id)
            print (win.user_bet)
            grate_winner(win)
        db_session.flush()
        list_of_losers = db_session.query(BitcoinBot).filter(BitcoinBot.user_bet != None)
        for lose in list_of_losers:
            send_loser(lose)
        print("gone_to_sleep", flush=True)
        print ("Got balance", flush=True)
        result = block_io.get_my_addresses()
        print(result, flush=True)
        for address in result["data"]["addresses"]:
            if address["user_id"] == 0:
                continue
            print (address, flush=True)
            user_label = address["label"]
            print(user_label, flush=True)
            try:
                amount = address["available_balance"]
            except Exception as e:
                print(e, flush=True)
            if float(amount) == 0.0:
                continue
            print(str(round(float(amount)-float(amount)/100*10, 8)), flush=True)
            print(amount, flush=True)
            try:
                temp = block_io.get_network_fee_estimate(amounts=str(round(float(amount)-float(amount)/100*10, 8)), to_labels="default")
                print (temp, flush=True)
            except Exception as e:
                print(e, flush=True)
                continue
            fee = float(temp["data"]["estimated_network_fee"])
            print(fee, flush=True)
            print(float(amount)-fee, flush=True)
            try:
                temp = block_io.withdraw_from_labels(amounts=float(amount)-fee, from_labels=user_label, to_labels="default")
            except Exception as e:
                print(e, flush=True)
            print (temp, flush=True)
            try:
                user = BitcoinBot.query.filter_by(user_id=user_label).first()
                refferal_user = BitcoinBot.query.filter_by(user_id=user.user_refferal_address).first()
                print (user, flush=True)
            except Exception as e:
                print (e, flush=True)
            try:
                user.user_balance += float(amount)/0.001*1000
                refferal_user.user_balance += (float(amount)/0.001*1000)/100*30
                print (user.user_balance)
                db_session.flush()
            except Exception as e:
                print (e, flush=True)
        time.sleep(60)

thread = Thread(target=play_game, args=())
thread.setDaemon(True)
thread.start()

#balance_thread = Thread(target=blockchain.update_balance, args=())
#balance_thread.setDaemon(True)
#balance_thread.start()

if __name__ == '__main__':
    bot.polling(none_stop=True)

#!/usr/bin/env python3.7

import subprocess
from subprocess import Popen, PIPE
import sys, os
import asyncio
import telepot
import telepot.aio
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, select
from sqlalchemy import create_engine


# chat_allow1=123456789

chat_allow1 = *******

file_read_temp = '/home/pi/si7021_temp.py'
file_read_relay = '/home/pi/relay_state.py'
file_relay_on = '/home/pi/relay_on.py'
file_relay_off = '/home/pi/relay_off.py'

motion_id = "/home/pi/alert_state/m_on"
temper_id = "/home/pi/alert_state/t_on"

# Файл со значением минимального температурного порога срабатывания температурной сигналки
critical_temp = "/home/pi/alert_state/critical_temp"

engine = create_engine('postgresql://baza:1@localhost:5433/info')
metadata = MetaData()
user_table = Table('info_to_telega', metadata)
conn = engine.connect()


# считывание температуры из скрипта для si7021
def temp_read():
    proc = Popen(['%s' % file_read_temp], shell=True, stdout=PIPE, stderr=PIPE)
    proc.wait()
    t = proc.stdout.read()
    t = float(t)
    return t



# считывание состояния пина на котором висит реле
def relay_read():
    proc = Popen(['%s' % file_read_relay], shell=True, stdout=PIPE, stderr=PIPE)
    proc.wait()
    r = proc.communicate()[0]
    r = int(r)
    if r == 1:
        r = 'Реле включено'
    elif r == 0:
        r = 'Реле обесточено'
    else:
        r = 'Ошибка!'
    return r


# включение/выключение реле в зависимости от входящего параметра
def relay_execute(state):
    if state == 'on' and relay_read() == 'Реле обесточено':
        subprocess.call("%s" % file_relay_on, shell=True)
        text = "включаю реле"
    elif state == 'on' and relay_read() == 'Реле включено':
        text = "реле уже под напряжением"
    elif state == 'off' and relay_read() == 'Реле включено':
        subprocess.call("%s" % file_relay_off, shell=True)
        text = "отключаю реле"
    elif state == 'off' and relay_read() == 'Реле обесточено':
        text = "реле уже обесточено"
    else:
        print("Ошибка!")
    return text


# управление сигнализациями alarm: on/off. file_id - айдишник сигнализации (см выше)
def alert_f(alarm, file_id):
    # сигнализация уже включена
    if alarm == 'on' and os.path.exists(file_id):
        text = "Сигнализация уже была включена"
    # была включена, теперь отключаем
    elif alarm == 'off' and os.path.exists(file_id):
        text = "Отключаю сигнализацию"
        if file_id == '/home/pi/alert_state/m_on':
            subprocess.call("pkill motion", shell=True)
        subprocess.call("rm -f %s" % file_id, shell=True)
    # уже была выключена, выключать не надо
    elif alarm == 'off' and os.path.exists(file_id) == False:
        text = "Сигнализация уже была отключена"
    # выла выключена, теперь включаем
    elif alarm == 'on' and os.path.exists(file_id) == False:
        text = "Активирую сигнализацию"
        if file_id == '/home/pi/alert_state/m_on':
            subprocess.call("motion &", shell=True)
        subprocess.call("touch %s" % file_id, shell=True)
    else:
        text = "err"
    return text


# текущее сотояние сигнализации. file_id - айдишник сигнализации (см выше)
def alert_info_f(file_id):
    if os.path.exists(file_id):
        text = "Сигнализация сейчас активна"
    else:
        text = "Сигнализация сейчас отключена"
    return text


# Текущее минимальное значение температуры
# считывание значения с датчика воды
def c_t_read():
    proc = Popen(['cat %s' % critical_temp], shell=True, stdout=PIPE, stderr=PIPE)
    proc.wait()
    c_t = proc.communicate()[0]
    c_t = c_t.decode(encoding='utf-8')
    c_t = "\nПорог срабатывания установлен на " + c_t + " градусов"
    return c_t


message_with_inline_keyboard = None
id_write_critical_temper = 0


# эта функция отвечает за текстовые сообщения и "клавиатуру"
async def on_chat_message(msg):
    global id_write_critical_temper
    content_type, chat_type, chat_id = telepot.glance(msg)
    print('Chat:', content_type, chat_type)
    print("id отправителя сообщения: " + str(chat_id))
    if chat_id == chat_allow1:
        if content_type != 'text':
            return
        else:
            ok = 1
        command = msg['text'].lower()
        print(command)

        if command == '/start':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='инфо')],
                [dict(text='управление')],
                [dict(text='сигнализация')],
            ])
            await bot.sendMessage(chat_id, 'чем воспользуешься?', reply_markup=markup)

        elif command == 'главное меню':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='инфо')],
                [dict(text='управление')],
                [dict(text='сигнализация')],
                [dict(text='база данных')],
            ])
            await bot.sendMessage(chat_id, 'выбери раздел', reply_markup=markup)

        elif command == u'инфо':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='температура'), dict(text='розетка')],
                [dict(text='главное меню')],
            ])
            await bot.sendMessage(chat_id, 'выбери объект', reply_markup=markup)

        elif command == u'база данных':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='инфо всей базы'), dict(text='ифно первого ур')],
                [dict(text='инфо второго ур'), dict(text='инфо не серкетное')],
                [dict(text='главное меню')],
            ])
            await bot.sendMessage(chat_id, 'выбери объект', reply_markup=markup)


        elif command == u'управление':
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [dict(text='включить', callback_data='relay_on'), dict(text='отключить', callback_data='relay_off')],
                [dict(text='текущее состояние', callback_data='relay_info')],
            ])
            global message_with_inline_keyboard
            message_with_inline_keyboard = await bot.sendMessage(chat_id, 'Что сделать с розеткой?',
                                                                 reply_markup=markup)

        elif command == u'сигнализация':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='контроль движения')],
                [dict(text='контроль температуры')],
                [dict(text='главное меню')],
            ])
            await bot.sendMessage(chat_id, 'какой раздел необходим?', reply_markup=markup)

        elif command == u'температура':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='температура'), dict(text='розетка')],
                [dict(text='главное меню')]
            ])
            # считываем значение с датчика температуры
            t = str(temp_read()) + 'C°'
            await bot.sendMessage(chat_id, 'Текущая температура: %s' % t, reply_markup=markup)


        elif command == u'розетка':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='вода'), dict(text='розетка')],
                [dict(text='температура'), dict(text='влажность')],
                [dict(text='главное меню')]
            ])
            # считываем значение с пина, на который подключено реле
            R = str(relay_read())
            await bot.sendMessage(chat_id, 'Состояние розетки (реле): %s' % R, reply_markup=markup)

        elif command == u'инфо всей базы':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='инфо всей базы'), dict(text='ифно первого ур')],
                [dict(text='инфо второго ур'), dict(text='инфо не серкетное')],
                [dict(text='главное меню')],
            ])
            # считываем значение с пина, на который подключено реле
            # считываем всю базу
            #all_result = ""
            select_stmt = select([user_table])
            result = conn.execute(select_stmt).fetchall()
            #all_result = result.fetchone()
            print(result)
            # for row in result:
            #     all_result += "lvl: " + row[user_table.c.lvl] + "text: " + row[user_table.c.text]
            #     all_result += "\n"
            # R = str(relay_read())
            await bot.sendMessage(chat_id, 'Информация базы: %s' % result, reply_markup=markup)

        elif command == u'база данных':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='инфо всей базы'), dict(text='ифно первого ур')],
                [dict(text='инфо второго ур'), dict(text='инфо не серкетное')],
                [dict(text='главное меню')],
            ])
            await bot.sendMessage(chat_id, 'выбери объект', reply_markup=markup)



        elif command == u'контроль воды':
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [dict(text='включить', callback_data='water_on'), dict(text='отключить', callback_data='water_off')],
                [dict(text='текущее состояние', callback_data='water_alert_info')],
            ])
            message_with_inline_keyboard = await bot.sendMessage(chat_id, 'Опции сигнализации воды:',
                                                                 reply_markup=markup)

        elif command == u'контроль движения':
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [dict(text='включить', callback_data='motion_on'), dict(text='отключить', callback_data='motion_off')],
                [dict(text='текущее состояние', callback_data='motion_alert_info')],
            ])
            message_with_inline_keyboard = await bot.sendMessage(chat_id, 'Опции сигнализации движения:',
                                                                 reply_markup=markup)

        elif command == u'контроль температуры':
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [dict(text='включить', callback_data='temp_on'), dict(text='отключить', callback_data='temp_off')],
                [dict(text='порог срабатывания', callback_data='temp_alert_min')],
                [dict(text='текущее состояние', callback_data='temp_alert_info')],
            ])
            message_with_inline_keyboard = await bot.sendMessage(chat_id, 'Опции сигнализации температуры:',
                                                                 reply_markup=markup)

        else:
            if id_write_critical_temper == 1:
                # если происходит установка температуры срабатывания
                if command.isdigit():
                    subprocess.call("echo %s > %s" % (command, critical_temp), shell=True)
                    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='главное меню')]])
                    await bot.sendMessage(chat_id, str(
                        "Температурный минимум установлен в %s градусов. Ниже этой температуры будут приходить алерты") % command,
                                          reply_markup=markup)
                    id_write_critical_temper = 0
                else:
                    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='главное меню')]])
                    await bot.sendMessage(chat_id, str(
                        "%s - это не целое число. При необходимости пройдите настройку заново. Значение не установлено!") % command,
                                          reply_markup=markup)
                    id_write_critical_temper = 0
            else:
                # если ввели текст, не соответствующий команде
                await bot.sendMessage(chat_id, str("начните чат с команды /start"))

    else:
        # если чат айди не соответствует разрешенному
        markup_protect = ReplyKeyboardMarkup(keyboard=[[dict(text='я очень тугой, еще раз можно?')]])
        await bot.sendMessage(chat_id, 'Вы не имеете доступа к этому боту!',
                              reply_markup=markup_protect)
        return


# эта функция отвечает кнопки
async def on_callback_query(msg):
    global id_write_critical_temper
    query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
    print('Callback query:', query_id, data)
    id_owner_callback = msg['from']['id']
    print("id отправителя запроса: " + str(id_owner_callback))
    if id_owner_callback == chat_allow1 or id_owner_callback == chat_allow2:
        # управление реле (розеткой)
        if data == 'relay_on':
            R_inf = str(relay_execute('on'))
            await bot.answerCallbackQuery(query_id, text='%s' % R_inf, show_alert=True)
        elif data == 'relay_off':
            R_inf = str(relay_execute('off'))
            await bot.answerCallbackQuery(query_id, text='%s' % R_inf, show_alert=True)
        elif data == 'relay_info':
            R = str(relay_read())
            await bot.answerCallbackQuery(query_id, text='%s' % R, show_alert=True)

        # управление сигнализацией движения
        elif data == 'motion_on':
            inf = str(alert_f('on', motion_id))
            await bot.answerCallbackQuery(query_id, text='%s' % inf, show_alert=True)
        elif data == 'motion_off':
            inf = str(alert_f('off', motion_id))
            await bot.answerCallbackQuery(query_id, text='%s' % inf, show_alert=True)
        elif data == 'motion_alert_info':
            inf = str(alert_info_f(motion_id))
            await bot.answerCallbackQuery(query_id, text='%s' % inf, show_alert=True)

        # управление сигнализацией температуры
        elif data == 'temp_on':
            inf = str(alert_f('on', temper_id))
            await bot.answerCallbackQuery(query_id, text='%s' % inf, show_alert=True)
        elif data == 'temp_off':
            inf = str(alert_f('off', temper_id))
            await bot.answerCallbackQuery(query_id, text='%s' % inf, show_alert=True)
        elif data == 'temp_alert_min':
            id_write_critical_temper = 1
            await bot.answerCallbackQuery(query_id,
                                          text='Установите min порог срабатывания температурной сигнализации. Введите целое число.',
                                          show_alert=True)
        else:
            next = 1
    else:
        await bot.answerCallbackQuery(query_id, text='У вас нет доступа', show_alert=True)


# В TOKEN должен находиться токен бота
TOKEN = "********"

bot = telepot.aio.Bot(TOKEN)
loop = asyncio.get_event_loop()

loop.create_task(bot.message_loop({'chat': on_chat_message,
                                   'callback_query': on_callback_query}))

print('Listening ...')
try:
    loop.run_forever()
finally:
    loop.close()

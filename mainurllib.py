import telebot
from telebot import types
# import requests ; doesn't work on free version of PA
import urllib.request, urllib.error, urllib.parse
import json
import re
# import investpy
import difflib

bot = telebot.TeleBot('5374314269:AAFpPKX1XFauQmij_OYltpubqM89o4U3qnw')  # bot token api

nearest = [['None', 0.0, 'NONE', 'NA']]

def stock_data_out(sec_id, mainboard, long_name=''):
    print(sec_id, end='\t\t')
    # r = requests.get(f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/'
    #                  f'{sec_id}.json')

    r = urllib.request.urlopen(f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/'
                      f'{sec_id}.json')
    htmltext = json.loads(r.read())
    print(htmltext)
    if len(htmltext['marketdata']['data']) == 0:
        return f'🛑 Эмитент "{long_name}" прекратил свою работу на Мосбирже'
    index = -1
    for i, board in enumerate(htmltext['marketdata']['data']):
        if board[1] == mainboard:
            index = i
            break
    if index == -1:
        return f'🛑 Режим торгов данного эмитента ({mainboard}) не найден '

    current_price = htmltext['marketdata']['data'][index][12]  # 5350
    prev_price = htmltext['securities']['data'][index][3]  # 5270
    if long_name == '':
        name = htmltext['securities']['data'][index][2]
    else:
        name = long_name  # Магнит ао
    sec_id = htmltext['securities']['data'][index][0]  # MGNT
    time_date = str(htmltext['marketdata']['data'][index][48])  # 2022-08-18 19:05:00 [32]


    output_text = '<b>' + name + ' • #' + sec_id.replace('-', '_') + '</b>\n'
    if htmltext['marketdata']['data'][index][49] is None:
        output_text += 'Цена: <b>' + str(current_price) + '₽</b>\n'
    else:
        output_text += 'Цена: <b>' + str(htmltext['marketdata']['data'][index][49]) + '₽</b>\n'
    print(current_price, prev_price, name, sec_id, time_date)

    if current_price is None or prev_price is None:
        output_text += '🔚 <i>Торги сегодня не проводились</i>\n'
    else:
        if prev_price <= current_price:
            output_text += '🔼 +'
        else:
            output_text += '🔽 '

        correlation = current_price - prev_price
        # if correlation is float:
        #     correlation = "{0:.4f}".format(correlation)
        output_text += '<b>' + str("{0:.4f}".format(correlation)) + ' ₽</b>  ' + \
                       str("{0:.2f}".format(100.0 - prev_price / (current_price * 0.01))) + "%\n\n"

    output_text += '<i>⌚️' + time_date.replace('-', '.')[:-3] + ' МСК</i>'
    return output_text


@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.send_message(message.chat.id, f'<b>Привет, {message.from_user.first_name}!</b>\n¤ Чтобы узнать сегодняшний '
                                      f'курс ЦБ РФ, напишите <a>/currency</a>\n¤ Чтобы узнать котировки определённой '
                                      f'акции, напишите <pre>/stocks [индекс или название эмитента]</pre> ',
                     parse_mode='html')


@bot.message_handler(commands=['currency', 'валюты'])
def currency(message):
    r = urllib.request.urlopen('http://iss.moex.com/iss/statistics/engines/currency/markets/selt/rates.json')
    if r.getcode() != 200:
        bot.send_message(message.chat.id, 'Какие-то проблемы с сервером! Я не могу связаться с Мосбиржей!')
        return
    data = json.loads(r.read())
    output_text = '<b>'
    for i in range(len(data['wap_rates']['data'])):
        output_text += '1 ' + str(data['wap_rates']['data'][i][3])[:-7] + ' равен ' + \
                       str(data['wap_rates']['data'][i][4]) + ' ' + str(data['wap_rates']['data'][i][3])[3:-4] + '\n'
    output_text += '</b>\n⚡️Данные предоставлены ЦБ РФ на ' + str(data['wap_rates']['data'][0][0]).replace('-', '.')

    bot.send_message(message.chat.id, output_text, parse_mode='html')


@bot.message_handler(commands=['stocks', 'акции'])
def stocks(message):

    global nearest
    r = urllib.request.urlopen('http://iss.moex.com/iss/statistics/engines/stock/quotedsecurities.json')
    input_text = message.text[message.text.find(" ") + 1:]
    if not re.match(r'^[А-Яа-яa-zA-Z-.() —–,\'\"\\]*$', input_text):
        bot.send_message(message.chat.id, 'Введите <pre>/stocks [название или индекс эмитента]</pre>\nНапример: <pre>/'
                                          'stocks SBER</pre> или <pre>/stocks магнит</pre>', parse_mode='html')
        return
    print('>>', message.text, ':', input_text, ':', sep='')
    if r.getcode() != 200:
        bot.send_message(message.chat.id, '<b>🥶 Какие-то проблемы с сервером! Я не могу связаться с Мосбиржей!</b>',
                         parse_mode='html')
        return
    data = json.loads(r.read())['quotedsecurities']['data']
    output_text = '<b>'
    if len(input_text) < 4:
        if input_text == 'мяу':
            bot.send_sticker(message.chat.id,
                             'CAACAgIAAxkBAAEFmh1i_p-SOvwNGpR1XUPPj24DS2ATZwACVBoAAnRZuUgkKEBcwEsn3CkE')
        bot.send_message(message.chat.id, '🤨 Введённый индекс или название эмитента слишком короткий!')
        return
    nearest = [['None', 0.0, 'NONE', 'NA']]
    if re.match(r'^[a-zA-Z-]*$', input_text) and (len(input_text) <= 5 or input_text.find('-') > -1):
        for line in data:
            if line[1] == input_text.upper():
                nearest[0][0], nearest[0][1], nearest[0][2], nearest[0][3] = line[2], 1.0, line[1], line[5]
                break
        if nearest[0][2] == 'NONE':
            bot.send_message(message.chat.id,
                             '😟 Вы ввели индекс эмитента, который не был найден на Московской Бирже!')
            return

        bot.send_message(message.chat.id, stock_data_out(nearest[0][2], nearest[0][3], long_name=nearest[0][0]),
                         parse_mode='html')

    else:
        nearest = [['None', 0.0, 'NONE', 'NA']]
        for line in data:
            line[2].replace('\\"', '')  # Если компания имеет вид АО \"Кселл\" ao в БД
            # if line.find('\\'):
            #     line = line[line.find('\\')+2:line.rfind('"')] #Если компания имеет вид АО \"Кселл\" ao в БД
            if re.search(input_text.lower(), line[2].lower()):
                if nearest[0][1] != 1.0:
                    nearest[0][0], nearest[0][1], nearest[0][2], nearest[0][3] = line[2], 1.0, line[1], line[5]
                else:
                    nearest.append([line[2], 1.0, line[1], line[5]])
            if (difflib.SequenceMatcher(a=line[2].lower(), b=input_text.lower())).ratio() > nearest[0][1]:
                if nearest[0][1] > 0.71:
                    nearest.append([line[2], (difflib.SequenceMatcher(
                        a=line[2].lower(), b=input_text.lower())).ratio(), line[1], line[5]])
                else:
                    nearest[0][0], nearest[0][1], nearest[0][2], nearest[0][3] = line[2], (difflib.SequenceMatcher(
                        a=line[2].lower(), b=input_text.lower())).ratio(), line[1], line[5]
            if len(nearest) > 9:
                output_text += '❗️Эмитентов со схожим названием слишком много, будут предложены ' \
                               'первые 10 вариантов\n '
                break

        nearest = sorted(nearest, reverse=True, key=lambda x: x[1])

        if len(nearest) == 1:
            if nearest[0][1] < 0.46:
                bot.send_message(message.chat.id, '😞 К сожалению, по данному запросу нет ничего похожего')
                return
            output_text += f'🔘 {nearest[0][0]}</b>'
            bot.send_message(message.chat.id, stock_data_out(nearest[0][2], nearest[0][3], long_name=nearest[0][0]),
                             parse_mode='html')
        else:
            output_text += '🔘 Возможно, вы имели ввиду одного из следующих эмитентов:</b>\n'
            markup = types.ReplyKeyboardMarkup(row_width=1)
            answer = []
            for line in nearest:
                output_text += f'▫️ <a>{line[0]}</a>\n'
                answer.append(line[0])

            markup.add(*answer)

            bot.send_message(message.chat.id, output_text, parse_mode='html', reply_markup=markup)

            @bot.message_handler(func=lambda message: message.text in [i[0] for i in nearest])
            def answer_hook(message):
                global nearest
                output_text = ''
                print('>>>>', message.text)
                if len(nearest) > 1:
                    print(nearest)
                    for line in nearest:
                        if message.text == line[0]:
                            nearest[0][0] = line[0]
                            nearest[0][2] = line[2]
                            nearest[0][3] = line[3]
                            output_text = 'a'
                            break
                            # output_text = '<b>' + line[0] + ' • ' + line[2] + '</b>\n'
                    if output_text == '':
                        bot.send_message(message.chat.id, '😓 Попробуйте ещё раз',
                                         reply_markup=types.ReplyKeyboardRemove())
                        return

                bot.send_message(message.chat.id, stock_data_out(nearest[0][2], nearest[0][3], long_name=nearest[0][0]),
                                 parse_mode='html', reply_markup=types.ReplyKeyboardRemove())
                nearest = [['None', 0.0, 'NONE', 'NA']]


@bot.message_handler(regexp="я писька?")
def piska(message):
    if message.text.lower() == 'я писька?':
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEFmh9i_p_c2qaR1Ceq5NV8_JTyI49YjwACZhgAAgS18EsT-zFayC5AkikE')
        bot.send_message(message.chat.id, '<b><i>🫶 Ну конечно! 🫶</i></b>', parse_mode='html')


bot.polling(none_stop=True)

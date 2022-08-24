import requests
import json
import re
import difflib
import investpy

def currency(message):
    r = requests.get(f'http://iss.moex.com/iss/statistics/engines/stock/quotedsecurities.json')
    input_text = message
    if r.status_code != 200:
        print( '<b>Какие-то проблемы с сервером! Я не могу связаться с Мосбиржей!</b>')
        return
    data = json.loads(r.text)['quotedsecurities']['data']
    output_text = '<b>'
    if len(input_text) < 4:
        print( 'Введённый индекс или название акции/облигации слишком короткий!')
        return
    nearest = ['None', 0.0, 'None']
    if re.match(r'^[A-Z-]*$', input_text):
        print('о! индекс!')
        for line in data:
            if line[1] == line:
                nearest[0][0], nearest[0][1], nearest[0][2] = line[2], 1.0, line[1]
                break
        if nearest[0] == 'None':
            print( 'Вы ввели индекс облигации/акции, который не был найден на Московской Бирже!')
            return

    else:
        nearest = [['None', 0.0, 'NONE']]
        for line in data:
            line[2].replace('\\"', '')  # Если компания имеет вид АО \"Кселл\" ao в БД
            # if line[2].find('\\'):
            #     line[2] = (line[2])[line[2].find('\\')+2:line[2].rfind('"')]  #Если компания имеет вид АО \"Кселл\" ao в БД
            if re.search(input_text, line[2]):
                if nearest[0][1] != 1.0:
                    nearest[0][0], nearest[0][1], nearest[0][2] = line[2], 1.0, line[1]
                else:
                    nearest.append([line[2], 1.0, line[1]])
            if (difflib.SequenceMatcher(a=line[2].lower(), b=input_text.lower())).ratio() > nearest[0][1]:
                if nearest[0][1] > 0.46:
                    nearest.append([line[2], (difflib.SequenceMatcher(
                        a=line[2].lower(), b=input_text.lower())).ratio(), line[1]])
                else:
                    nearest[0][0], nearest[0][1], nearest[0][2] = line[2], (difflib.SequenceMatcher(
                        a=line[2].lower(), b=input_text.lower())).ratio(), line[1]
            if len(nearest) > 9:
                output_text += f'Компаний, со схожим с "{input_text}" названием слишком много, будут предложены ' \
                               f'первые 10 вариантов\n '
                break

    nearest = sorted(nearest, reverse=True, key=lambda x: x[1])

    if len(nearest) == 1:
        output_text += f'{nearest[0][0]} – Вы ищите эту компанию?'
        positive = 'Да'
        negative = 'Нет'

        print(positive, negative)
    else:
        output_text += 'Возможно, вы имели ввиду одну из следующих компаний:\n'
        answer = []
        for line in nearest:
            output_text += f'<a>{line[0]}</a>\n'
            answer.append(line[0])

        print([i for i in answer])

    print(output_text, '\n', nearest)


# df = investpy.get_stock_company_profile(stock='AAPL', country='United States', language='english')
# df = investpy.get_stock_information(stock='MGNT',
#                                     country='Russia')
# print(df)
import urllib3
print(urllib3.PoolManager().request('GET', 'http://webcode.me').status)

# currency(input())
# r = requests.get(f'http://iss.moex.com/iss/statistics/engines/stock/quotedsecurities.json')
# data = json.loads(r.text)['quotedsecurities']['data']
# for line in data:
#     if re.search(r'.*', line[2]):
#         print(line[2])
#         print(re.sub(r'.*?\\\"(.*)\\\".*', r'\1', line[2]), end='\n\n')
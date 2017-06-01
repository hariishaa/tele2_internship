"""Задание №1: 
Изучите курс казахского тенге к российскому рублю за 2016 год. Проверьте статистическую гипотезу о 
зависимости курса от фаз лунного цикла """

import xml.etree.ElementTree as ET
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

if __name__ == '__main__':
    # получение данных о динамике курса тенге к рублю за 2016 год с сайта ЦБ РФ
    url = 'http://www.cbr.ru/scripts/XML_dynamic.asp'
    params = {
        'date_req1': '01/01/2016',
        'date_req2': '31/12/2016',
        'VAL_NM_RQ': 'R01335'
    }
    response = requests.get(url, params)
    # парсинг полученного xml, получение значений курса по каждой дате
    date = []
    values = []
    root = ET.fromstring(response.content)
    for child in root.findall('Record'):
        dt = datetime.strptime(child.get('Date'), '%d.%m.%Y')
        date.append(dt)
        values.append(child.find('Value').text.replace(',', '.'))
    # построение графика динамики курса тенге к рублю
    x_axis = mdates.date2num(date)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis_date()
    plt.plot(x_axis, values, 'b-')
    plt.gcf().autofmt_xdate()
    plt.title('Динамика курса тенге к рублю за 2016 год')
    plt.grid()
    plt.show()

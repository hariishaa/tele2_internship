"""Задание №3:
Получите из открытых источников корпус стихотворений А.С. Пушкина. Постройте классификатор, разделяющий документы 
на классы, соответствующие стихотворному размеру: «ямб», «хорей», «прочее». Постройте график долей классов по годам 
творчества поэта. """

import re
import requests
import time
from lxml import html
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# списки с гласными буквами
VOWELS_LOWER = ('а', 'у', 'о', 'ы', 'и', 'э', 'я', 'ю', 'ё', 'е')
VOWELS_UPPER = ('А', 'У', 'О', 'Ы', 'И', 'Э', 'Я', 'Ю', 'Ё', 'Е')
VOWELS = VOWELS_LOWER + VOWELS_UPPER


# разделение текста на слоги
def divide_on_syllables(text):
    syllables = []
    syllable = ''
    for char in text:
        syllable += char
        if char in VOWELS:
            syllables.append(syllable)
            syllable = ''
    if len(syllables) > 0:
        syllables[-1] += syllable
    else:
        syllables.append(syllable)
    return syllables


# определение стихотворного размера по массиву слогов с проставленными ударениями
def check_poem_size(syllables):
    accented_syllables_indexes = []
    # определение номеров ударных слогов
    for i, syllable in enumerate(syllables, start=1):
        for char in syllable:
            if char in VOWELS_UPPER:
                accented_syllables_indexes.append(i)
                break
    # определение размера стихотворения
    for i, idx in enumerate(accented_syllables_indexes[1:], start=1):
        if (idx - accented_syllables_indexes[i - 1]) % 4 not in {0, 2}:
            return 'other'
    else:
        if accented_syllables_indexes[0] % 2 == 0:
            return 'iamb'
        return 'trochee'


# является ли слово односложным
def is_monosyllabic_word(word):
    if len(word) > 1 and len(divide_on_syllables(word)) > 1:
        return False
    return True


# поставить ударение в слове
def make_accent(word):
    word = word.lower()
    # если слово односложное, поставить ударение без обращения к серверу с ударениями
    if is_monosyllabic_word(word):
        for c in word:
            if c in VOWELS_LOWER:
                return word.replace(c, c.upper())
    # формирование запроса к сайту с ударениями
    url = 'http://udarenieru.ru/index.php'
    params = {
        'doc': word
    }
    headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 '
            'Safari/537.36 '
    }
    response = requests.get(url, params, headers=headers)
    # если искомое слово существует в бд на сайте, парсим его ударение
    if response.status_code == 200:
        html_tree = html.fromstring(response.text)
        red = html_tree.xpath('//div[@id="search_result"]//span[@class="red"]')  # тег red, в котором находится ударная гласная
        if red:
            red_parent = red[0].xpath('..')[0]  # предок тега red для определения количества букв перед ударной гласной
            chars = list(word)
            # если предок тега red непустой, находим и изменяем ударную гласную по индексу, иначе изменяем первую букву
            if red_parent.text:
                chars[len(red_parent.text)] = chars[len(red_parent.text)].upper()
            # является ли содержимое тега red гласной буквой (из-за особенностей верстки сайта)
            elif red.text[0] in VOWELS:
                chars[0] = chars[0].upper()
            return ''.join(chars)
    return word


# построение графика долей классов по годам
def draw_plot(year_size_list):
    # преобразование списка годов и размеров в словарь типа {год: {кол-во ямбов, кол-во хореев, кол-во остальных}}
    year_size_dict = {}
    for year, size in year_size_list:
        if not year_size_dict.get(year):
            year_size_dict[year] = {'all': 0}
        if not year_size_dict[year].get(size):
            year_size_dict[year][size] = 0
        year_size_dict[year][size] += 1
        year_size_dict[year]['all'] += 1
    year_size_dict = sorted(year_size_dict.items(), key=lambda x: x[0])  # сортировка словаря по возрастанию годов
    # создание списков годов и долей каждого из классов для последующей отрисовки
    years = [value[0] for value in year_size_dict]
    iamb_share = [value[1].get('iamb', 0) / value[1]['all'] for value in year_size_dict]
    trochee_share = [value[1].get('trochee', 0) / value[1]['all'] for value in year_size_dict]
    other_share = [value[1].get('other', 0) / value[1]['all'] for value in year_size_dict]
    # построение графика
    x_axis = mdates.date2num([datetime.strptime(year, '%Y') for year in years])
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.gca().xaxis_date()
    plt.gcf().autofmt_xdate()
    plt.plot(x_axis, iamb_share, 'bD:')
    plt.plot(x_axis, trochee_share, 'r^:')
    plt.plot(x_axis, other_share, 'go:')
    plt.title('График долей классов стихотворных размеров\nпо годам творчества А.С.Пушкина')
    plt.legend(('Ямб', 'Хорей', 'Остальное'), loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.grid()
    plt.show()


if __name__ == '__main__':
    year_size_list = []  # список вида (год, стихотворный размер)
    # парсинг списка ссылок на стихотворения
    response = requests.get('http://pushkin.299.ru')
    html_tree = html.fromstring(response.text)
    table = html_tree.xpath('//table')[3]
    td = table.xpath('.//tr')[1][1]
    a_list = td.xpath('.//a')  # список тегов a
    for a in a_list[:1]:  # todo: delete
        # парсинг первой строки каждого стихотворения из списка
        response = requests.get('http://pushkin.299.ru/%s' % a.attrib['href'])
        html_tree = html.fromstring(response.text)
        table = html_tree.xpath('//table')[3]
        tr = table.xpath('.//tr')[1]
        td = tr[1]
        # из-за особенностей верстки сайта первая строка может находиться в разных тегах
        if td.text.strip():
            poem_first_line = td.text.strip()
        else:
            p = tr.xpath('.//p')[0]
            poem_first_line = p.text.strip()
        # разделение первой строки на слова и проставление ударения в каждом слове
        poem_first_line_words = re.sub(r'[^а-яА-Я\s]', '', poem_first_line.lower()).split()
        if len(poem_first_line_words) > 0:
            accented_poem_first_line_words = []
            for word in poem_first_line_words:
                # проверка слова на многосложность
                # односложные слова остаются безударными из-за особенностей определения стихотворного размера
                if not is_monosyllabic_word(word):
                    accented_poem_first_line_words.append(make_accent(word))
                    time.sleep(1)  # задержка для того чтобы не получить бан на сайте с проверкой ударений
            # разбиение слов с проставленными ударениями на слоги
            syllables = divide_on_syllables(' '.join(accented_poem_first_line_words))
            poem_size = check_poem_size(syllables)  # определение стихотворного размера
            year = table.xpath('.//i')[0].text  # парсинг года создания стихотворения
            year_size_list.append((year, poem_size))
    draw_plot(year_size_list)  # построение графика долей классов по годам

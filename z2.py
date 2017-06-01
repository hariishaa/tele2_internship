"""Задание №2: 
Получите из открытых источников список GPS координат станций московского метрополитена. Для каждой из 
пар пересекающихся линий метрополитена постройте полигон минимального размера, покрывающий все станции этих линий. 
Проранжируйте полигоны по площади (км^2) и выдайте топ 3 сочетания линий, где площадь этого полигона максимальна. """

import matplotlib.pyplot as plt
import requests
from shapely.geometry import LineString, Polygon, Point, MultiPoint
from descartes.patch import PolygonPatch


def get_all_subway_lines():
    all_lines = requests.get('https://api.hh.ru/metro/1').json()['lines']  # обращение к HeadHunter API
    # разделение Калининской линии на Калининскую и Солнцевскую
    kalininskaya_line = all_lines[0]
    solncevskaya_line = dict(kalininskaya_line)
    kalininskaya_line['stations'] = kalininskaya_line['stations'][:8]
    solncevskaya_line['stations'] = solncevskaya_line['stations'][8:]
    all_lines.append(solncevskaya_line)
    # смена местами станций Курская и Площадь Революции из-за ошибки в API
    arbatsko_pokrovskaya_line = all_lines[4]
    arbatsko_pokrovskaya_line['stations'][7], arbatsko_pokrovskaya_line['stations'][8] = \
        arbatsko_pokrovskaya_line['stations'][8], arbatsko_pokrovskaya_line['stations'][7]
    # замыкание кольцевой линии
    kolcevaya_line = all_lines[8]
    kolcevaya_line['stations'].append(kolcevaya_line['stations'][0])
    # удаление из списка линий метро Монорельса и МЦК
    for line in all_lines[:]:
        if line['name'] == 'Монорельс' or line['name'] == 'Московское центральное кольцо':
            all_lines.remove(line)
            continue
    return all_lines


def get_top_min_polygons(subway_lines):
    all_min_polygons = []
    # для каждой пары линий метро проверяем наличие пересечения и строим полигон минимальной площади
    for i, line1 in enumerate(subway_lines):
        print(line1['name'])  # todo: remove all prints
        # создание объекта LineString со списком координат каждой станции для определение пересечения двух веток метро
        # широту и долготу переводим в км, чтобы потом посчитать площадь в км^2
        line1_coordinates = [(station['lng'] * 104, station['lat'] * 111) for station in line1['stations']]
        line1_linestring = LineString(line1_coordinates)
        # нанесение точек-станций метро на график
        # x, y = line1_linestring.xy
        # ax.plot(x, y, '-o', color='#{}'.format(line1['hex_color']))
        # проходим по тем станциям, с которыми еще не проверяли пересечение
        for line2 in subway_lines[i + 1:]:
            # аналогично первой ветке создаем объект LineString и проверяем пересечение двух линий метро
            line2_coordinates = [(station['lng'] * 104, station['lat'] * 111) for station in line2['stations']]
            line2_linestring = LineString(line2_coordinates)
            intersection = line1_linestring.intersection(line2_linestring)
            # если линии метро пересекаются в одной или несколкьих точках, находим полигон минимальной площади
            if isinstance(intersection, (Point, MultiPoint)):
                print(line1['name'] + ' пересекается с ' + line2['name'])
                polygon1 = Polygon(line1_coordinates + line2_coordinates)
                polygon2 = Polygon(line1_coordinates + line2_coordinates[::-1])
                if polygon1.area < polygon2.area:
                    polygon = polygon1
                else:
                    polygon = polygon2
                # добавляем найденный полигон в список всех минимальных полигонов вместе со сведениями о ветках метро
                all_min_polygons.append({
                    'line1_name': line1['name'],
                    'line1_hex_color': line1['hex_color'],
                    'line1_coordinates': line1_coordinates,
                    'line2_name': line2['name'],
                    'line2_hex_color': line2['hex_color'],
                    'line2_coordinates': line2_coordinates,
                    'polygon': polygon,
                    'polygon_area': polygon.area,
                })
    # сортируем список полигонов по убыванию площади
    top_min_polygons = sorted(all_min_polygons, key=lambda polygon_info: polygon_info['polygon_area'], reverse=True)
    return top_min_polygons


# построение графика трех минимальных полигонов с наибольшими площадями
def draw_plot(top_min_polygons):
    fig = plt.figure()
    for i, polygon_info in enumerate(top_min_polygons[:3], start=1):
        ax = fig.add_subplot(3, 1, i)
        ax.set_title('{} - {}, {} км^2'.format(polygon_info['line1_name'], polygon_info['line2_name'],
                                               round(polygon_info['polygon_area'], 2)))
        line1_linestring = LineString(polygon_info['line1_coordinates'])
        x, y = line1_linestring.xy
        ax.plot(x, y, '-o', color='#{}'.format(polygon_info['line1_hex_color']))
        line2_linestring = LineString(polygon_info['line2_coordinates'])
        x, y = line2_linestring.xy
        ax.plot(x, y, '-o', color='#{}'.format(polygon_info['line2_hex_color']))
        patch = PolygonPatch(polygon_info['polygon'], facecolor='#{}'.format(polygon_info['line1_hex_color']),
                             edgecolor='#{}'.format(polygon_info['line1_hex_color']), alpha=0.5)
        ax.add_patch(patch)
        ax.plot()
    fig.subplots_adjust(hspace=0.5)
    plt.grid()
    plt.show()


if __name__ == '__main__':
    # todo: delete
    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    subway_lines = get_all_subway_lines()
    top_min_polygons = get_top_min_polygons(subway_lines)
    draw_plot(top_min_polygons)

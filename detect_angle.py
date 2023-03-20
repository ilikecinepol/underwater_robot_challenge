# Пример выделения контуров объектов по заданным цветам.

import math
import numpy as np
from pid import keep_yaw_pix
import cv2
import pymurapi as mur
cnt = 0

auv = mur.mur_init()

# Для начала, создадим словарь, который хранит
# диапазоны цветов и их наименования.

colors = {
    'green':    (( 45, 50,  50), ( 75, 255, 255)),
    'blue':     ((130, 50,  50), (140, 255, 255)),
    'cyan':     (( 80, 50,  50), (100, 255, 255)),
    'magenta':  ((140, 50,  50), (160, 255, 255)),
    'yellow':   (( 20, 50,  50), ( 30, 255, 255)),
    'orange':   ((  0, 50,  50), ( 20, 255, 255)),
}

def get_cnt_xy(contour):
    moments = cv2.moments(contour)

    try:
        x = int(moments['m10'] / moments['m00'])
        y = int(moments['m01'] / moments['m00'])
        return x, y
    except ZeroDivisionError:
        return None, None

# Выделим поиск контуров в отдельную функцию.

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours

# Напишем функцию для отрисовки контуров, которая включает
# отсеивание слишком маленьких контуров, вычисление координат
# центра контура, а также отрисовку как самого контура, так и
# его центра с подписью соответствующего цвета.

def draw_object_contour(drawing, contour, name):
    global cnt
    if cv2.contourArea(contour) < 200:
        return

    line_color = (0,0,255)
    cv2.drawContours(drawing, [contour], 0, line_color, 2)

    moments = cv2.moments(contour)

    x, y = get_cnt_xy(cnt)

    if x != None and y != None:
        cv2.circle(drawing, (x,y), 4, line_color, -1)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(drawing, name, (x-30, y+30), font, 0.75, (0,0,0), 1)

def process_biggest_cnt(drawing, contour):
    cv2.drawContours(drawing, [contour], 0, (0, 255, 255), 3)

def calc_angle(drawing, cnt):
    try:
        rectangle = cv2.minAreaRect(cnt)

        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        cv2.drawContours(drawing, [box], 0, (0,255,0), 3)

        # К сожалению, мы не можем использовать тот угол,
        # который входит в вывод функции minAreaRect,
        # т.к. нам необходимо ориентироваться именно по
        # длинной стороне полоски. Находим длинную сторону.

        edge_first = np.int0((box[1][0] - box[0][0], box[1][1] - box[0][1]))
        edge_second = np.int0((box[2][0] - box[1][0], box[2][1] - box[1][1]))

        edge = edge_first
        if cv2.norm(edge_second) > cv2.norm(edge_first):
            edge = edge_second

        # Вычисляем угол по длинной стороне.
        angle = -((180.0 / math.pi * math.acos(edge[0] / (cv2.norm((1, 0)) * cv2.norm(edge)))) - 90)

        return angle if not math.isnan(angle) else 0
    except:
        return 0

if __name__ == '__main__':
    while True:
        img = auv.get_image_bottom()
        drawing = img.copy()

        biggest_orange_cnt = None
        biggest_orange_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if not contours:
                continue

            for cnt in contours:
                draw_object_contour(drawing, cnt, name)

                if name == 'orange' or name == 'yellow':
                    area = cv2.contourArea(cnt)
                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt




        if biggest_orange_area > 200:
            angle = calc_angle(drawing, biggest_orange_cnt)
            print(angle)
            keep_yaw_pix(angle, auv.get_yaw())


        cv2.imshow('drawing', drawing)
        cv2.waitKey(20)
# Пример выделения контуров объектов по заданным цветам.

import cv2
import pymurapi as mur
from auv_moving import *

auv = mur.mur_init()

# Для начала, создадим словарь, который хранит
# диапазоны цветов и их наименования.

colors = {
    'red': ((141, 51, 77), (180, 255, 255)),
    'orange': ((1, 59, 69), (84, 255, 255)),
    'black': ((126, 0, 0), (150, 255, 255)),
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
    if cv2.contourArea(contour) < 500:
        return

    line_color = (0, 0, 255)
    cv2.drawContours(drawing, [contour], 0, line_color, 2)

    moments = cv2.moments(contour)

    x, y = get_cnt_xy(contour)

    if x != None and y != None:
        cv2.circle(drawing, (x, y), 4, line_color, -1)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(drawing, name, (x - 30, y + 30), font, 0.75, (0, 0, 0), 1)
        # go_to_goal(x, y)


# Теперь опишем основной алгоритм работы.

def process_biggest_cnt(drawing, contour):
    cv2.drawContours(drawing, [contour], 0, (0, 255, 0), 3)
    x, y = get_cnt_xy(contour)
    try:
        cv2.line(drawing, (160, y), (x, y), (0, 0, 0), 2)
        cv2.line(drawing, (x, y), (x, 120), (0, 0, 0), 2)
        diff1 = abs(x - 160)
        diff2 = abs(y - 120)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(drawing, str(diff1), (160, y), font, 0.5, (0, 0, 0), 2)
        cv2.putText(drawing, str(diff2), (x, 120), font, 0.5, (0, 0, 0), 2)
        return x, y
    except:
        pass


def pict():
    img = auv.get_image_bottom()
    drawing = img.copy()

    cv2.line(drawing, (160, 0), (160, 240), (0, 0, 255), 2)
    cv2.line(drawing, (0, 120), (320, 120), (0, 0, 255), 2)

    biggest_orange_cnt = None
    biggest_orange_area = 0
    x, y = 0, 0
    for name in colors:
        contours = find_contours(img, colors[name])

        if not contours:
            continue

        for cnt in contours:
            draw_object_contour(drawing, cnt, name)
            if name == 'orange':
                area = cv2.contourArea(cnt)

                if area > biggest_orange_area:
                    biggest_orange_area = area
                    biggest_orange_cnt = cnt

    if biggest_orange_area > 50:
        process_biggest_cnt(drawing, biggest_orange_cnt)

    cv2.imshow('drawing', drawing)
    cv2.waitKey(1)


def calc_angle(drawing, cnt):
    try:
        rectangle = cv2.minAreaRect(cnt)

        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        cv2.drawContours(drawing, [box], 0, (0, 255, 0), 3)

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

        cv2.line(drawing, (160, 0), (160, 240), (0, 0, 255), 2)
        cv2.line(drawing, (0, 120), (320, 120), (0, 0, 255), 2)

        biggest_orange_cnt = None
        biggest_orange_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if not contours:
                continue

            for cnt in contours:
                draw_object_contour(drawing, cnt, name)
                if name == 'orange':
                    area = cv2.contourArea(cnt)

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

        if biggest_orange_area > 100:
            process_biggest_cnt(drawing, biggest_orange_cnt)

        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)

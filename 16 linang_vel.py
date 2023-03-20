import time

import cv2
import numpy as np
import math
import pymurapi as mur
import auv_moving

auv = mur.mur_init()

# Для начала, создадим словарь, который хранит
# диапазоны цветов и их наименования.
ellipce_area = 0
colors = {
    'green': ((45, 50, 50), (75, 255, 255)),
    'blue': ((130, 50, 50), (140, 255, 255)),
    'cyan': ((80, 50, 50), (100, 255, 255)),
    'magenta': ((140, 50, 50), (160, 255, 255)),
    'yellow': ((20, 50, 50), (30, 255, 255)),
    'orange': ((0, 50, 50), (20, 255, 255)),
}

# Рассчитаем координаты центра изображения
img = auv.get_image_bottom()
drawing = img.copy()
h, w = img.shape[0], img.shape[1]
x_goal, y_goal = int(w/2), int(h/2)
print(x_goal, y_goal)

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours


def process_cnt(cnt):
    global drawing, ellipce_area, x_goal, y_goal
    area = cv2.contourArea(cnt)

    if abs(area) < 500:
        return 0

    # Описанный прямоугольник (с вращением)
    rectangle = cv2.minAreaRect(cnt)
    # print('rectangle = ', rectangle)

    # Получим контур описанного прямоугольника
    box = cv2.boxPoints(rectangle)
    box = np.int0(box)

    # Вычислим площадь и соотношение сторон прямоугольника.
    rectangle_area = cv2.contourArea(box)
    rect_w, rect_h = rectangle[1][0], rectangle[1][1]
    try:
        aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)
    except ZeroDivisionError:
        pass
    # Описанная окружность.
    (circle_x, circle_y), circle_radius = cv2.minEnclosingCircle(cnt)
    circle_area = circle_radius ** 2 * math.pi
    circle = cv2.minAreaRect(cnt)
    circ_w, circ_h = circle[1][0], circle[1][1]
    try:
        aspect_ratio = max(circ_w, circ_h) / min(circ_w, circ_h)
    except ZeroDivisionError:
        pass

    # Описанный треугольник
    try:
        triangle = cv2.minEnclosingTriangle(cnt)[1]
        triangle = np.int0(triangle)
        triangle_area = cv2.contourArea(triangle)
    except:
        triangle_area = 0

    # Описанный элипс
    try:
        ellipce = cv2.fitEllipse(cnt)
        (ellipce_x, ellipce_y), (ellipce_h, elllipce_w), ellipce_angle = ellipce
        ellipce_area = math.pi * (ellipce_h / 2) * (elllipce_w / 2)
        cv2.ellipse(drawing, ellipce, (255, 0, 0), 2)
    except:
        pass

    # Заполним словарь, который будет содержать площади каждой из описанных фигур
    shapes_areas = {
        'ellipse': ellipce_area,
        'rectangle': rectangle_area,
        'triangle': triangle_area,
    }

    # Заполним словарь, который будет содержать площади каждой из описанных фигур
    try:
        shapes_areas = {
            'ellipse' if aspect_ratio > 1.25 else 'circle': ellipce_area,
            'rectangle' if aspect_ratio > 1.25 else 'square': rectangle_area,
            'triangle': triangle_area,
            'circle': circle_area,
        }
    except:
        pass
    # Теперь заполним аналогичный словарь, который будет содержать
    # разницу между площадью контора и площадью каждой из фигур.
    diffs = {
        name: abs(area - shapes_areas[name]) for name in shapes_areas
    }

    # вычислим центр, нарисуем в центре окружность и ниже подпишем
    # текст с именем фигуры, которая наиболее похожа на исследуемый контур.

    moments = cv2.moments(cnt)

    # Получаем имя фигуры с наименьшей разницой площади.
    shape_name = min(diffs, key=diffs.get)

    line_color = (125, 0, 125)

    # Нарисуем соответствующую описанную фигуру вокруг контура

    if shape_name == 'circle':
        cv2.circle(drawing, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)

    if shape_name == 'rectangle':
        cv2.drawContours(drawing, [box], 0, line_color, 2, cv2.LINE_AA)

    if shape_name == 'triangle':
        cv2.drawContours(drawing, [triangle], 0, line_color, 2, cv2.LINE_AA)

    if shape_name == 'ellipce':
        cv2.drawContours(drawing, ellipce, 0, line_color, 2, cv2.LINE_AA)

    cv2.line(drawing, (160, 0), (160, 240), (0, 0, 255), 2)
    cv2.line(drawing, (0, 120), (320, 120), (0, 0, 255), 2)

    try:
        x = int(moments['m10'] / moments['m00'])
        y = int(moments['m01'] / moments['m00'])
        cv2.circle(drawing, (x, y), 4, line_color, -1, cv2.LINE_AA)

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(drawing, shape_name, (x - 40, y + 31), font, 1, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(drawing, shape_name, (x - 41, y + 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Отрисовка линий удалённости от центра по каждой из осей и подпись значения удалённости
        cv2.line(drawing, (160, y), (x, y), (0, 0, 0), 2)
        cv2.line(drawing, (x, y), (x, 120), (0, 0, 0), 2)
        diff1 = abs(x - 160)
        diff2 = abs(y - 120)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(drawing, str(diff1), (160, y), font, 0.5, (0, 0, 0), 2)
        cv2.putText(drawing, str(diff2), (x, 120), font, 0.5, (0, 0, 0), 2)

        auv_moving.go_to_goal(x, y, k_lin=0.5, k_ang=-0.2)

    except ZeroDivisionError:
        pass


if __name__ == '__main__':
    while True:
        img = auv.get_image_bottom()
        drawing = img.copy()
        c_d = auv.get_depth()
        if abs(c_d - 3) > 0.05:
            auv_moving.keep_depth(3)

        # Переменные для определения самого большого контура и его площади
        biggest_cnt = None
        biggest_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if contours:
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > biggest_area:
                        biggest_area = area
                        biggest_cnt = cnt
            if biggest_area > 50:
                process_cnt(cnt)

        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)

import cv2
import numpy as np
import math
import pymurapi as mur

auv = mur.mur_init()
vid = cv2.VideoCapture(0)

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours


def process_cnt(cnt):
    global drawing
    area = cv2.contourArea(cnt)

    if abs(area) < 500:
        pass
    hull = cv2.convexHull(cnt)
    approx = cv2.approxPolyDP(hull, cv2.arcLength(cnt, True) * 0.02, True)
    if len(approx) == 4:
        cv2.drawContours(drawing, cnt, -1, (0,0,255), 3)

    # Описанная окружность.
    (circle_x, circle_y), circle_radius = cv2.minEnclosingCircle(cnt)
    circle_area = circle_radius ** 2 * math.pi
    circle = cv2.minAreaRect(cnt)
    circ_w, circ_h = circle[1][0], circle[1][1]
    aspect_ratio = max(circ_w, circ_h) / min(circ_w, circ_h)

    # Описанный прямоугольник (с вращением)
    rectangle = cv2.minAreaRect(cnt)
    # print('rectangle = ', rectangle)

    # Получим контур описанного прямоугольника
    box = cv2.boxPoints(rectangle)
    box = np.int0(box)

    # Вычислим площадь и соотношение сторон прямоугольника.
    rectangle_area = cv2.contourArea(box)
    rect_w, rect_h = rectangle[1][0], rectangle[1][1]
    aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)

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
        'ellipse' if aspect_ratio > 1.25 else 'circle': ellipce_area,
        'rectangle' if aspect_ratio > 1.25 else 'square': rectangle_area,
        'triangle': triangle_area,
        'circle': circle_area,
    }

    # Теперь заполним аналогичный словарь, который будет содержать
    # разницу между площадью контора и площадью каждой из фигур.
    diffs = {
        name: abs(area - shapes_areas[name]) for name in shapes_areas
    }

    # Получаем имя фигуры с наименьшей разницой площади.
    shape_name = min(diffs, key=diffs.get)

    line_color = (0, 100, 255)

    # Нарисуем соответствующую описанную фигуру вокруг контура

    if shape_name == 'circle':
        cv2.circle(drawing, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)

    if shape_name == 'rectangle' or shape_name == 'square':
        cv2.drawContours(drawing, [box], 0, line_color, 2, cv2.LINE_AA)

    if shape_name == 'triangle':
        cv2.drawContours(drawing, [triangle], 0, line_color, 2, cv2.LINE_AA)

    if shape_name == 'ellipce':
        cv2.drawContours(drawing, ellipce, 0, line_color, 2, cv2.LINE_AA)

    # вычислим центр, нарисуем в центре окружность и ниже подпишем
    # текст с именем фигуры, которая наиболее похожа на исследуемый контур.

    moments = cv2.moments(cnt)

    try:
        x = int(moments['m10'] / moments['m00'])
        y = int(moments['m01'] / moments['m00'])
        cv2.circle(drawing, (x, y), 4, line_color, -1, cv2.LINE_AA)

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(drawing, shape_name, (x - 40, y + 31), font, 1, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(drawing, shape_name, (x - 41, y + 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    except ZeroDivisionError:
        pass


if __name__ == '__main__':
    while True:
        img = auv.get_image_bottom()
        drawing = img.copy()

        color = ((0, 50,  50), ( 20, 255, 255))

        contours = find_contours(img, color)

        if contours:
            for cnt in contours:
                process_cnt(cnt)

        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)

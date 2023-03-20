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
x_goal, y_goal = int(w / 2), int(h / 2)


# print(x_goal, y_goal)


def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours


def calc_angle(drawing, cnt):
    try:
        rectangle = cv2.minAreaRect(cnt)

        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        cv2.drawContours(drawing, [box], 0, (0, 255, 0), 3)

        edge_first = np.int0((box[1][0] - box[0][0], box[1][1] - box[0][1]))
        edge_second = np.int0((box[2][0] - box[1][0], box[2][1] - box[1][1]))
        edge = edge_first if cv2.norm(edge_second) < cv2.norm(edge_first) else edge_second
        angle = -(180 / math.pi * (math.acos(edge[0] / (cv2.norm((1, 0)) * cv2.norm(edge)))))
        angle = auv_moving.to_360(angle) - 47
        print('angle: ', angle)
        return angle if not math.isnan(angle) else 0
    except:
        return 0


def calc_triangle_course(drawing, cnt):
    # Описанный треугольник
    try:
        triangle = cv2.minEnclosingTriangle(cnt)[1]
        triangle = np.int0(triangle)
        x2, y2 = get_contour_xy(cnt)
        coords = {abs(math.sqrt(((triangle[i][0][0] - x2) ** 2) + ((triangle[i][0][1] - y2) ** 2))): (
            triangle[i][0][0], triangle[i][0][1]) for i in range(3)}
        coords = sorted(coords.items())
        top = coords[0][1]
        x1, y1 = top
        cv2.line(drawing, (x1, y1), (x2, y2), (0, 0, 255), 2)
        angle_a = 180 / math.pi * (math.atan2(y1 - y2, x1 - x2)) +90
        print('angle_a', angle_a)
        return angle_a if not math.isnan(angle_a) else 0
    except:
        return 0


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
        x, y = get_contour_xy(cnt)
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


    except ZeroDivisionError:
        pass


def get_contour_xy(cnt):
    try:
        moments = cv2.moments(cnt)
        line_color = (125, 0, 125)
        x = int(moments['m10'] / moments['m00'])
        y = int(moments['m01'] / moments['m00'])
        cv2.circle(drawing, (x, y), 4, line_color, -1, cv2.LINE_AA)
        return x, y
    except:
        return 0


if __name__ == '__main__':
    while True:
        img = auv.get_image_bottom()
        drawing = img.copy()
        c_d = auv.get_depth()
        if abs(c_d - 3) > 0.05:
            # auv_moving.keep_depth(3)
            pass
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
                ang_z = calc_triangle_course(drawing, cnt)
                # ang_z = auv_moving.keep_angle(angle-90, auv_moving.to_360(auv.get_yaw()))
                try:
                    x, y = get_contour_xy(cnt)
                    lin_v, ang_v = auv_moving.go_to_goal(x, y, 160, 120)
                    depth_vel = auv_moving.keep_depth(3.5)
                    auv_moving.moving(linear_y=0, angular_z=ang_z, linear_z=depth_vel)
                except:
                    pass
        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)

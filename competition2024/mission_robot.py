# Пример выделения контуров объектов по заданным цветам.

import cv2
import pymurapi as mur
import numpy as np
import math
import time

auv = mur.mur_init()
# vid = auv.get_image_bottom()
vid = cv2.VideoCapture(0)
ok, frame0 = vid.read()
img = frame0
mur_view = auv.get_videoserver()
ang_z =0 
course_motor1 = 2
course_motor2 = 1
depth_motor_1 = 3
depth_motor_2 = 0
stepper_motor = 4

#course_motor1 = 0
#course_motor2 = 1
#depth_motor_1 = 2
#depth_motor_2 = 3
#stepper_motor = 4

ellipce_area = 0
i_component = 0
last_error = 0

auv = mur.mur_init()

# координаты центра изображения
# img = auv.get_image_bottom()
# h, w = img.shape[0], img.shape[1]
# x_goal, y_goal = int(w / 2), int(h / 2)
depth = 0.50


def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours


def get_cnt_xy(contour):
    moments = cv2.moments(contour)
    x = int(moments['m10'] / moments['m00'])
    y = int(moments['m01'] / moments['m00'])
    return x, y


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


def limiter(value, min=-100, max=100):
    return min if value < min else max if value > max else value


def moving(linear_x=0, linear_y=0, linear_z=0, angular_x=0, angular_y=0, angular_z=0):
    global course_motor1, course_motor2, depth_motor1, depth_motor2, stepper_motor
    auv.set_motor_power(course_motor1, limiter(linear_x) + angular_z)
    auv.set_motor_power(course_motor2, limiter(linear_x) - angular_z)
    auv.set_motor_power(depth_motor_1, limiter(linear_z))
    auv.set_motor_power(depth_motor_2, limiter(linear_z))
    auv.set_motor_power(stepper_motor, limiter(linear_x))


def pid_controller(value, setpoint, p=0, i=0, d=0, delta_error=0.05):
    global last_error, i_component
    eror = setpoint - value
    if abs(eror) > delta_error:
        i_component += i_component * eror
    else:
        i_component = 0
    p_component = eror * p
    d_component = d * (eror - last_error)
    i_component = i_component * i
    last_error = eror
    time.sleep(0.0005)
    return p_component + d_component + i_component


def to_360(angle):
    return angle if angle > 0.0 else angle + 360.0


def keep_angle(goal_angle, p=0.05, i=0, d=0.01):
    current_angle = to_360(auv.get_yaw())
    print('current_angle:', current_angle)
    goal_angle = to_360(goal_angle)
    print('goal_angle:', goal_angle)
    power = pid_controller(to_360(current_angle), to_360(goal_angle), p=p, i=i, d=d)
    return power


def keep_depth(goal_depth=0, p=-50, i=-5, d=0.1):
    current_depth = auv.get_depth()
    print('current_depth', current_depth)
    power = pid_controller(current_depth, goal_depth, p=p, i=i, d=d)
    return limiter(power)


def rad_to_deg(rad):
    return pi / 180 * rad


def go_to_goal(x_goal, y_goal, x=160, y=120, k_lin=0.3, k_ang=-0.2):
    yaw = auv.get_yaw()
    distance = abs(math.sqrt(((x_goal - x) * 2) + ((y_goal - y) * 2)))
    k_lin = -k_lin if y_goal - y > 0 else k_lin
    k_ang = -k_ang if x_goal - x > 0 else k_ang
    linear_speed = limiter(distance * k_lin)
    if distance > 1:
        desired_angle_goal = 180 / math.pi * (math.atan2(y_goal - y, x_goal - x))
        angular_speed = limiter((desired_angle_goal - to_360(yaw)) * k_ang)
    else:
        angular_speed = 0
    print('linear = ', linear_speed, 'angular = ', angular_speed)
    return linear_speed, angular_speed


def get_picture():
    # img = auv.get_image_bottom()
    # cv2.line(img, (160, 0), (160, 240), (0, 0, 255), 2)
    # cv2.line(img, (0, 120), (320, 120), (0, 0, 255), 2)
    ok, frame0 = vid.read()

    img = frame0
    # cv2.imshow('drawing', img)
    # cv2.waitKey(1)
    
    return img


def get_biggest_cnt(img, cnt_color):
    biggest_cnt = None
    biggest_area = 0
    for name in colors:
        contours = find_contours(img, colors[name])

        if not contours:
            continue

        for cnt in contours:
            draw_object_contour(img, cnt, name)
            if name == cnt_color:
                area = cv2.contourArea(cnt)
                color_status = True

                if area > biggest_area:
                    biggest_area = area
                    biggest_cnt = cnt
    return biggest_cnt, biggest_area


def diving_orange_circle(img, cnt_color):
    global depth
    count = 0
    while count < 200:
        img = get_picture()
        biggest_cnt, biggest_area = get_biggest_cnt(img, cnt_color)

        if biggest_area > 100:
            x, y = get_cnt_xy(biggest_cnt)
            lin_y, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=0.1, k_ang=0.1)
            lin_z = keep_depth(depth, p=-40)
            moving(linear_y=lin_y, angular_z=ang_z, linear_z=lin_z)
            if abs(y - 120) < 5:
                count += 1
            else:
                count = 0

    # cv2.imshow('drawing', img)
    # cv2.waitKey(1)


def move_line(img, cnt_color):
    global depth
    count = 0
    while count < 200:
        img = get_picture()
        biggest_cnt, biggest_area = get_biggest_cnt(img, cnt_color)
        ang_z=5
        if biggest_area > 100:

            rect = cv2.minAreaRect(biggest_cnt) 
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(img, [box], 0, (0,0,255), 2)

            # Определяем координаты вершин верхнего ребра
            top_left_vertex = box[1]
            top_right_vertex = box[0]

            # Вычисляем координаты середины верхнего ребра
            midpoint_x = (top_left_vertex[0] + top_right_vertex[0]) // 2
            midpoint_y = (top_left_vertex[1] + top_right_vertex[1]) // 2

            # lin_y, ang_z = go_to_goal(x_goal=midpoint_x, y_goal=midpoint_y, k_lin=0, k_ang=0.1)
            angle = calc_angle(img, biggest_cnt)
            ang_z = keep_angle(angle)
        lin_z = keep_depth(depth, p=-40)
        moving(linear_x=-10, angular_z=ang_z, linear_z=lin_z)    
        mur_view.show(img, 0)
            # if abs(y - 120) < 5:
            #     count += 1
            # else:
            #     count = 0

    # cv2.imshow('drawing', img)
    # cv2.waitKey(1)

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
        angle = -((180.0 / math.pi * math.acos(edge[0] / (cv2.norm((1, 0)) * cv2.norm(edge))))- 90)

        return angle if not math.isnan(angle) else 0
    except:
        return 0

colors = {
#    'red': ((0, 0, 0), (76, 255, 255)),
#   'orange': ((8, 0, 0), (13, 255, 255)),
    'yellow': ((14, 43, 65), (99, 146, 171)),
#    'yellow': ((18, 48, 58), (65, 255, 203)),                                                      
#    'black': ((0, 0, 0), (0, 0, 20))
}

if _name_ == '_main_':
    while True:
        # img = auv.get_image_bottom()
        # cv2.line(img, (160, 0), (160, 240), (0, 0, 255), 2)
        # cv2.line(img, (0, 120), (320, 120), (0, 0, 255), 2)
        #diving_orange_circle(img, 'orange')
        move_line(img, 'yellow')
        
        # cv2.imshow('drawing', img)
        # cv2.waitKey(1)

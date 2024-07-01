import cv2
import numpy as np
import pymurapi as mur
import time
import math

auv = mur.mur_init()

robot = 'simulator'
if robot != 'simulator':
    mur_view = auv.get_videoserver()

cap0 = cv2.VideoCapture(1)
cap1 = cv2.VideoCapture(0)
if robot == 68:
    course_motor1 = 2
    course_motor2 = 1
    depth_motor_1 = 3
    depth_motor_2 = 0
    stepper_motor = 4
    colors = {
        'red': ((110, 31, 0), (178, 255, 255)),
        'orange': ((14, 83, 83), (52, 199, 194)),
        'black': ((94, 99, 30), (106, 195, 59)),
    }
elif robot == 70:
    course_motor1 = 1
    course_motor2 = 2
    depth_motor_1 = 3
    depth_motor_2 = 0
    stepper_motor = 4
    colors = {
        'red': ((110, 31, 0), (178, 255, 255)),
        'orange': ((14, 83, 83), (52, 199, 194)),
        'black': ((94, 99, 30), (106, 195, 59)),
    }
elif robot == 'simulator':
    course_motor1 = 0
    course_motor2 = 1
    depth_motor_1 = 2
    depth_motor_2 = 3
    stepper_motor = 4
    img = auv.get_image_bottom()
    colors = {
        'red': ((146, 14, 0), (180, 255, 241)),
        'orange': ((8, 0, 0), (13, 255, 255)),
        'yellow': ((18, 75, 92), (93, 255, 255)),
        'black': ((0, 0, 1), (180, 255, 86))
    }

ellipce_area = 0
i_component = 0
last_error = 0
max_area = 50
depth = 3.3
max_depth = depth + 0.5


def limiter(value, min=-100, max=100):
    return min if value < min else max if value > max else value


def moving(linear_x=0, linear_y=0, linear_z=0, angular_x=0, angular_y=0, angular_z=0):
    global course_motor1, course_motor2, depth_motor1, depth_motor2, stepper_motor
    auv.set_motor_power(course_motor1, limiter(linear_x) + angular_z)
    auv.set_motor_power(course_motor2, limiter(linear_x) - angular_z)
    auv.set_motor_power(depth_motor_1, limiter(linear_z) + angular_x)
    auv.set_motor_power(depth_motor_2, limiter(linear_z) - angular_x)
    auv.set_motor_power(stepper_motor, limiter(linear_y))


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


def keep_depth(goal_depth=0, p=-50, i=-5, d=0.1):
    current_depth = auv.get_depth()
    # print('current_depth', current_depth)
    power = pid_controller(current_depth, goal_depth, p=p, i=i, d=d)
    return limiter(power)


def keep_pitch(goal_pitch=0, p=-50, i=-5, d=0.1):
    current_pitch = auv.get_pitch()
    # print('current_pitch:', current_pitch)
    power = pid_controller(current_pitch, goal_pitch, p=p, i=i, d=d)
    return limiter(power)


def rad_to_deg(rad):
    return pi / 180 * rad


def go_to_goal(x_goal, y_goal, x=160, y=120, k_lin=0.3, k_ang=-0.2):
    yaw = auv.get_yaw()
    distance = abs(math.sqrt(((x_goal - x) ** 2) + ((y_goal - y) ** 2)))
    k_lin = -1.5 * k_lin if y_goal - y > 0 else k_lin
    k_ang = -k_ang if x_goal - x > 0 else k_ang
    linear_speed = limiter(distance * k_lin)
    if distance > 1:
        desired_angle_goal = 180 / math.pi * (math.atan2(y_goal - y, x_goal - x))
        angular_speed = limiter((desired_angle_goal - to_360(yaw)) * k_ang)
    else:
        angular_speed = 0
    # print('linear = ', linear_speed, 'angular = ', angular_speed)
    return linear_speed, angular_speed


def keep_angle(goal_angle, p=0.2, i=0.5, d=0.01):
    current_angle = to_360(auv.get_yaw())
    # print('current_angle:', current_angle)
    goal_angle = to_360(goal_angle)
    # print('goal_angle:', goal_angle)
    power = pid_controller(to_360(current_angle), to_360(goal_angle), p=p, i=i, d=d)
    return power


def get_img(camera, mask_bottom=True):
    if robot == 'simulator':
        img = auv.get_image_bottom()
    else:
        if camera == 'front':
            ok, frame0 = cap1.read()
        else:
            ok, frame0 = cap0.read()
        frame0 = cv2.resize(frame0, (320, 240))
        img = frame0

    if mask_bottom:
        # Закрываем нижние 20% изображения маской
        height, width, _ = img.shape
        mask_height = int(height * 0.2)  # Измените значение по необходимости
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[:height - mask_height, :] = 255
        img = cv2.bitwise_and(img, img, mask=mask)

    return img


def get_cnt_xy(contour):
    moments = cv2.moments(contour)
    x = int(moments['m10'] / moments['m00'])
    y = int(moments['m01'] / moments['m00'])
    return x, y


def find_contours(image, color, approx=cv2.CHAIN_APPROX_SIMPLE):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_image, color[0], color[1])
    contours, _ = cv2.findContours(mask, cv2.RETR_CCOMP, approx)

    return contours


def img_process(img, cnt, color):
    global colors, ellipce_area
    font = cv2.FONT_HERSHEY_PLAIN

    if cnt is None or len(cnt) == 0:
        return img, color, None

    area = cv2.contourArea(cnt)
    drawing = np.zeros_like(img)

    if abs(area) < 500:
        pass
    hull = cv2.convexHull(cnt)
    approx = cv2.approxPolyDP(hull, cv2.arcLength(cnt, True) * 0.02, True)
    if len(approx) == 4:
        cv2.drawContours(drawing, cnt, -1, (0, 0, 255), 3)

    # Описанная окружность.
    (circle_x, circle_y), circle_radius = cv2.minEnclosingCircle(cnt)
    circle_area = circle_radius ** 2 * math.pi
    circle = cv2.minAreaRect(cnt)
    circ_w, circ_h = circle[1][0], circle[1][1]

    # Описанный прямоугольник (с вращением)
    rectangle = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rectangle)
    box = np.int0(box)

    # Вычислим площадь и соотношение сторон прямоугольника.
    rectangle_area = cv2.contourArea(box)
    rect_w, rect_h = rectangle[1][0], rectangle[1][1]
    try:
        aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)
    except:
        aspect_ratio = 1

    # Описанный треугольник
    try:
        triangle = cv2.minEnclosingTriangle(cnt)[1]
        triangle = np.int0(triangle)
        triangle_area = cv2.contourArea(triangle)
    except:
        triangle_area = 0

    # Описанный эллипс
    # try:
    #     ellipce = cv2.fitEllipse(cnt)
    #     (ellipce_x, ellipce_y), (ellipce_h, elllipce_w), ellipce_angle = ellipce
    #     ellipce_area = math.pi * (ellipce_h / 2) * (elllipce_w / 2)
    #     cv2.ellipse(drawing, ellipce, (255, 0, 0), 2)
    # except:
    #     pass

    # Заполним словарь, который будет содержать площади каждой из описанных фигур
    shapes_areas = {
        # 'ellipse' if aspect_ratio > 1.25 else 'circle': ellipce_area,
        'rectangle' if aspect_ratio > 1.25 else 'square': rectangle_area,
        'triangle': triangle_area,
        'circle': circle_area,
    }

    # Теперь заполним аналогичный словарь, который будет содержать
    # разницу между площадью контура и площадью каждой из фигур.
    diffs = {
        name: abs(area - shapes_areas[name]) for name in shapes_areas
    }

    # Получаем имя фигуры с наименьшей разницей площади.
    shape_name = min(diffs, key=diffs.get)

    line_color = (0, 100, 255)

    # Нарисуем соответствующую описанную фигуру вокруг контура

    # вычислим центр, нарисуем в центре окружность и ниже подпишем
    # текст с именем фигуры, которая наиболее похожа на исследуемый контур.

    if cnt is not None and len(cnt) > 0:
        cnt = cnt  # Убираем извлечение первого элемента, так как он уже есть
        try:
            area = cv2.contourArea(cnt)

            if area > 10:
                x, y = get_cnt_xy(cnt)
                cv2.circle(img, (x, y), 4, (0, 0, 250), -1)
                line_color = (0, 100, 255)

                # Нарисуем соответствующую описанную фигуру вокруг контура

                if shape_name == 'circle':
                    cv2.circle(img, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)

                if shape_name == 'rectangle' or shape_name == 'square':
                    cv2.drawContours(img, [box], 0, line_color, 2, cv2.LINE_AA)

                if shape_name == 'triangle':
                    cv2.drawContours(img, [triangle], 0, line_color, 2, cv2.LINE_AA)

                # if shape_name == 'ellipce':
                #     cv2.drawContours(img, ellipce, 0, line_color, 2, cv2.LINE_AA)
                cv2.putText(img, '{}'.format(color), (x, y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(img, '{}'.format(shape_name), (x, y + 20), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        except:
            pass
    return color, cnt, shape_name


def get_single_cnt(img, cnt_color, max_area=50):
    biggest_cnt = None
    biggest_area = 0
    biggest_color = None

    contours = find_contours(img, colors[cnt_color])

    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area > biggest_area:
            biggest_area = area
            biggest_cnt = cnt
            biggest_color = cnt_color

    return biggest_cnt, biggest_area, biggest_color


def get_second_largest_cnt(img, cnt_color, max_area=50):
    largest_cnt = None
    largest_area = 0
    second_largest_cnt = None
    second_largest_area = 0

    contours = find_contours(img, colors[cnt_color])

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > largest_area:
            # Обновляем второй по величине контур, когда находим новый самый большой контур
            second_largest_area = largest_area
            second_largest_cnt = largest_cnt
            # Обновляем самый большой контур
            largest_area = area
            largest_cnt = cnt
        elif area > second_largest_area:
            # Обновляем второй по величине контур, если найденная площадь больше текущего второго
            second_largest_area = area
            second_largest_cnt = cnt

    return second_largest_cnt, second_largest_area, cnt_color


def get_biggest_cnt(img):
    global max_area, colors
    biggest_cnt = None
    biggest_area = 0
    biggest_color = None

    for color in colors:
        contours = find_contours(img, colors[color])

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > biggest_area:
                biggest_area = area
                biggest_cnt = cnt
                biggest_color = color

    # print('biggest_color is', biggest_color)
    return biggest_cnt, biggest_area, biggest_color


def go_to_figure(color, p_ang=0.05, p_depth=-30, error_position=30):
    global depth, colors
    count = 0
    t1 = time.time()
    while count < 100:
        img = get_img(camera='front', mask_bottom=True)
        if color == 'red':

            biggest_cnt, biggest_area, biggest_color = get_single_cnt(img, color)
            second_largest_cnt, second_largest_area, cnt_color = get_second_largest_cnt(img, color)
            x1, y1 = get_cnt_xy(biggest_cnt)
            try:
                x2, y2 = get_cnt_xy(second_largest_cnt)
                if y2 < y1 and abs(y2 - y1) > 100 and y2 < 120:
                    biggest_cnt, biggest_area, biggest_color = second_largest_cnt, second_largest_area, cnt_color
                    cv2.circle(img, (x2, y2), 4, (0, 0, 250), -1)
            except:
                pass
        else:
            biggest_cnt, biggest_area, biggest_color = get_single_cnt(img, color)
        if biggest_cnt is not None:
            col, contour, shape = img_process(img, biggest_cnt, biggest_color)
            x, y = get_cnt_xy(biggest_cnt)
            lin_x, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=0.1, k_ang=p_ang)
            lin_z = keep_depth(depth, p=p_depth)
            if time.time() - t1 < 1:
                lin_x = 0
            moving(linear_x=lin_x, angular_z=ang_z, linear_z=lin_z)
            if abs(y - 120) < error_position and abs(x - 160) < error_position and abs(lin_z) < 10:
                count += 1
                # print('count = ', count)
            else:
                count = 0
            img_out(img)
    return shape, color


def img_out(img):
    if robot == 'simulator':
        cv2.imshow('Out', img)
        cv2.waitKey(1)
    else:
        mur_view.show(img, 0)


def move_line(target_counto, p_lin=0.1, p_ang=0.05, stop_color1='orange', stop_color2='black'):
    print('move line {}'.format(target_counto))
    global depth, robot
    if robot != 'simulator':
        auv.set_on_delay(0.5)
        auv.set_off_delay(0)
        auv.set_rgb_color(255, 255, 255)
    counto = 0


    while True:
        img = get_img(camera='front')
        # ('wait {} color'.format(stop_color1))
        biggest_cnt, biggest_area, biggest_color = get_biggest_cnt(img)
        # print(dt, dt_max)
        current_yaw = to_360(auv.get_yaw())
        print('counto {}'.format(counto))
        if biggest_cnt is not None and biggest_color == 'red':
            color, contour, shape = img_process(img, biggest_cnt, biggest_color)

            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(img, [box], 0, (0, 0, 255), 2)

            # Определяем координаты вершин верхнего ребра

            # Сортируем вершины по координате y
            sorted_vertices = box[np.argsort(box[:, 1])]
            # Из первых двух вершин выбираем те, которые имеют меньшую y координату
            bottom_width_points = sorted_vertices[:2]
            # print(bottom_width_points)

            top_left_vertex = bottom_width_points[0]
            top_right_vertex = bottom_width_points[1]

            # Вычисляем координаты середины верхнего ребра
            midpoint_x = (top_left_vertex[0] + top_right_vertex[0]) // 2
            midpoint_y = (top_left_vertex[1] + top_right_vertex[1]) // 2
            cv2.circle(img, (midpoint_x, midpoint_y), 4, (0, 255, 250), -1)

            lin_y, ang_z = go_to_goal(x_goal=midpoint_x, y_goal=midpoint_y, k_lin=p_lin, k_ang=p_ang)
            lin_z = keep_depth(depth, p=-30)
            ang_x = keep_pitch(0, p=0.5)
            lin_x = 10
            moving(linear_x=lin_x, angular_z=ang_z, linear_z=lin_z, angular_x=ang_x)
            counto += 1

        elif counto > target_counto and (biggest_color == stop_color2 or biggest_color == stop_color1):
            return biggest_color, current_yaw
            # print('stop')


        img_out(img)


# def go_to_figure(color, p_ang=0.05, p_depth=-30, error_position=30):
#     global depth, colors
#     count = 0
#     t1 = time.time()
#
#     while count < 100:
#         img = get_img(camera='front', mask_bottom=True)
#         if color == 'red':
#
#             biggest_cnt, biggest_area, biggest_color = get_single_cnt(img, color)
#             second_largest_cnt, second_largest_area, cnt_color = get_second_largest_cnt(img, color)
#             x1, y1 = get_cnt_xy(biggest_cnt)
#             try:
#                 x2, y2 = get_cnt_xy(second_largest_cnt)
#                 if y2 < y1 and abs(y2 - y1) > 100 and y2 < 120:
#                     biggest_cnt, biggest_area, biggest_color = second_largest_cnt, second_largest_area, cnt_color
#                     cv2.circle(img, (x2, y2), 4, (0, 0, 250), -1)
#             except:
#                 pass
#         else:
#             biggest_cnt, biggest_area, biggest_color = get_single_cnt(img, color)
#         if biggest_cnt is not None:
#             col, contour, shape = img_process(img, biggest_cnt, biggest_color)
#             x, y = get_cnt_xy(biggest_cnt)
#             lin_x, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=0.1, k_ang=p_ang)
#             lin_z = keep_depth(depth, p=p_depth)
#             if time.time() - t1 < 1:
#                 lin_x = 0
#             moving(linear_x=lin_x, angular_z=ang_z, linear_z=lin_z)
#             if abs(y - 120) < error_position and abs(x - 160) < error_position and abs(lin_z) < 10:
#                 count += 1
#                 # print('count = ', count)
#             else:
#                 count = 0
#             img_out(img)
#     return shape, color


def go_to_figure(color,p_lin=0.1, p_ang=0.05, p_depth=-30, error_position=30):
    print('go_to_figure  {}'.format(color))
    global depth, colors
    count = 0
    t1 = time.time()

    while count < 100:
        img = get_img(camera='front', mask_bottom=True)
        biggest_cnt, biggest_area, biggest_color = get_single_cnt(img, color)
        if biggest_cnt is not None:
            col, contour, shape = img_process(img, biggest_cnt, biggest_color)
            x, y = get_cnt_xy(biggest_cnt)
            lin_x, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=p_lin, k_ang=p_ang)
            lin_z = keep_depth(depth, p=p_depth)
            if time.time() - t1 < 1:
                lin_x = 0
            moving(linear_x=lin_x, angular_z=ang_z, linear_z=lin_z)
            if abs(y - 120) < error_position and abs(x - 160) < error_position and abs(lin_z) < 10:
                count += 1
                # print('count = ', count)
            else:
                count = 0
        img_out(img)
    return shape, color


def action(color, shape, target_yaw):
    print('action {}'.format(shape))
    global robot
    # print(shape, color)
    if robot != 'simulator':
        if color == 'black':
            auv.set_on_delay(0.5)
            auv.set_off_delay(0)
            auv.set_rgb_color(255, 0, 0)
        elif color == 'orange' or color == 'yellow' and shape == 'square':
            auv.set_on_delay(0.5)
            auv.set_off_delay(0)
            auv.set_rgb_color(0, 255, 0)
            t1 = time.time()
            if (time.time() - t1) < 10:
                auv.set_on_delay(0)
                auv.set_off_delay(0.5)

    if shape == 'square' and color != 'black':
        t1 = time.time()
        while time.time() - t1 < 5:
            lin_z = keep_depth(max_depth)
            moving(linear_z=lin_z)
        while time.time() - t1 < 12:
            lin_z = keep_depth(depth)
            moving(linear_z=lin_z)
    elif color == 'orange' or color == 'yellow' and shape == 'triangle':
        t1 = time.time()
        while time.time() - t1 < 10:
            moving(angular_z=20)
        count = 0
        while count < 200:
            current_yaw = to_360(auv.get_yaw())
            ang_z = keep_angle(target_yaw, p=0.1)
            moving(angular_z=ang_z)
            if abs(current_yaw - to_360(target_yaw)) < 15:
                count += 1
            else:
                count = 0


def last_funk(target_yaw):
    count = 0
    while count < 200:
        current_yaw = to_360(auv.get_yaw())
        lin_z = keep_depth(depth)
        ang_z = keep_angle(target_yaw)
        moving(linear_z=lin_z, angular_z=ang_z)
        if abs(current_yaw - target_yaw) < 5:
            count += 1
        else:
            count = 0
        t1 = time.time()
    # while time.time() - t1 < 3:
    #     moving(linear_x=15)
    #     print('m')


if __name__ == '__main__':
    go_to_figure('orange', p_ang=0.03, p_depth=-20, error_position=30)
    for sensor in range(6):
        go_to_figure('red', p_ang=0.03,p_lin=0.05, p_depth=-20, error_position=50)

        col, c_yaw = move_line(target_counto=100, p_ang=0.08,p_lin=0.2, stop_color1='yellow', stop_color2='black')

        shape, color = go_to_figure(col, p_ang=0.03, p_depth=-20, error_position=30)
        action(color, shape, c_yaw)
        # shape, color = go_to_figure(col, p_ang=0.03, p_depth=-20, error_position=30)
        last_funk(c_yaw)

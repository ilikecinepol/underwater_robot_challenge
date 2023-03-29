# Пример выделения контуров объектов по заданным цветам.

import cv2
import pymurapi as mur
import numpy as np
import math
import time

goal_depth = 3.3  # Поменять на нужную глубину
sleep_time = 1.5

auv = mur.mur_init()
vid = cv2.VideoCapture(0)
mur_view = auv.get_videoserver()
auv.set_on_delay(0)
ok, frame0 = vid.read()
img = frame0

course_motor1 = 2
course_motor2 = 1
depth_motor_1 = 3
depth_motor_2 = 0
stepper_motor = 4

last_error = 0
i_component = 0

# Для начала, создадим словарь, который хранит
# диапазоны цветов и их наименования.
print('размер экрана', img.shape)
h, w = img.shape[0], img.shape[1]
colors = {
    'red': ((141, 51, 77), (180, 255, 255)),
    'orange': ((1, 59, 69), (84, 255, 255)),
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
    global h, w
    cv2.drawContours(drawing, [contour], 0, (0, 255, 0), 3)
    x, y = get_cnt_xy(contour)
    try:
        cv2.line(drawing, ((int(w/2)), y), (x, y), (0, 0, 0), 2)
        cv2.line(drawing, (x, y), (x, (int(h/2))), (0, 0, 0), 2)
        diff1 = abs(x - (int(w/2)))
        diff2 = abs(y - (int(h/2)))
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(drawing, str(diff1), (160, y), font, 0.5, (0, 0, 0), 2)
        cv2.putText(drawing, str(diff2), (x, 120), font, 0.5, (0, 0, 0), 2)
        return x, y
    except:
        pass


def pict():
    img = auv.get_image_bottom()
    drawing = img.copy()

   # h, w = img.shape[0], img.shape[1]
    #x_goal, y_goal = int(w / 2), int(h / 2)

    #cv2.line(drawing, (x_goal, 0), (x_goal, h), (0, 0, 255), 2)
    #cv2.line(drawing, (0, x_goal, y_goal), (w, x_goal, y_goal), (0, 0, 255), 2)

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

    mur_view.show(img, 0)


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








def limiter(value, min=-100, max=100):
    return min if value < min else max if value > max else value


def moving(linear_x=0, linear_y=0, linear_z=0, angular_x=0, angular_y=0, angular_z=0):
    global course_motor1, course_motor2, depth_motor2, depth_motor1, stepper_motor
    linear_y = -linear_y
    auv.set_motor_power(course_motor1, limiter(linear_y) - angular_z)
    auv.set_motor_power(course_motor2, limiter(linear_y) + angular_z)
    auv.set_motor_power(depth_motor_1, limiter(linear_z) + angular_y)
    auv.set_motor_power(depth_motor_2, limiter(linear_z) - angular_y)
    auv.set_motor_power(stepper_motor, limiter(linear_x))


def relay_controller(value, setpoint):
    power = 20 if value > setpoint else -20
    moving(linear_z=power)


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


def keep_angle(goal_angle, p=0.2, i=0.5, d=0.01):
    current_angle = to_360(auv.get_yaw())
    print('current_angle:', current_angle)
    goal_angle = to_360(goal_angle)
    print('goal_angle:', goal_angle)
    power = pid_controller(to_360(current_angle), to_360(goal_angle), p=p, i=i, d=d)
    return power


def keep_depth(goal_depth=0, p=-40, i=-5, d=0.1):
    current_depth = auv.get_depth()
    # print('current_depth', current_depth)
    power = pid_controller(current_depth, goal_depth, p=p, i=i, d=d)
    return power




def go_to_goal_xy(goal_x, goal_y, x=160, y=120, k_x=-0.2, k_y=-0.2):
    power_x = (goal_x - x) * k_x
    power_y = (goal_y - y) * k_y
    # print(power_x)
    moving(linear_x=power_x, linear_y=power_y)


def go_to_goal(x_goal, y_goal, x=160, y=120, k_lin=0.3, k_ang=-0.2):
    yaw = auv.get_yaw()
    distance = abs(math.sqrt(((x_goal - x) ** 2) + ((y_goal - y) ** 2)))
    k_lin = -k_lin if y_goal - y > 0 else k_lin
    k_ang = -k_ang if x_goal - x > 0 else k_ang
    linear_speed = distance * k_lin
    if distance > 1:
        desired_angle_goal = 180 / math.pi * (math.atan2(y_goal - y, x_goal - x))
        angular_speed = (desired_angle_goal - to_360(yaw)) * k_ang
    else:
        angular_speed = 0
    return linear_speed, angular_speed


###################



def deeping():
    auv.set_rgb_color(148, 87, 235) 
    auv.set_on_delay(10)
    count = 0
    global goal_depth, mur_view, h, w
    # mur_view = auv.get_videoserver()
    auv.set_on_delay(0)

    while count < 100:

        ok, frame0 = vid.read()

        img = frame0
        h, w = img.shape[0], img.shape[1]
        x_1, y_1 = int(w / 2), int(h / 2)

        cv2.line(img, (x_1, 0), (x_1, h), (0, 0, 255), 2)
        cv2.line(img, (0, y_1), (w, y_1), (0, 0, 255), 2)

        biggest_orange_cnt = None
        biggest_orange_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if not contours:
                continue

            for cnt in contours:
                draw_object_contour(img, cnt, name)
                if name == 'red':
                    area = cv2.contourArea(cnt)

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

        if biggest_orange_area > 100:
            x, y = process_biggest_cnt(img, biggest_orange_cnt)
            lin_y, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=0.1, k_ang=0.0)
            lin_z = keep_depth(goal_depth)
            moving(linear_y=lin_y, linear_z=lin_z, angular_z=ang_z)
            if abs(y - int(h/2)) < 10:
                count += 1
            else:
                count = 0
        mur_view.show(img, 0)


def set_angle_0():
    print('Устанавливаю угол 0 градусов')
    goal_angle = 0
    global goal_depth
    counter = 0
    while counter < 75:
        keep_angle(goal_angle=goal_angle, goal_depth=goal_depth)
        if abs(auv.get_yaw() - goal_angle) > 1:
            counter += 1
            time.sleep(0.1)
        else:
            counter = 0


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


def calc_triangle_course(drawing, cnt):
    # Описанный треугольник

    try:
        triangle = cv2.minEnclosingTriangle(cnt)[1]
        triangle = np.int0(triangle)

        moments = cv2.moments(cnt)
        line_color = (125, 0, 125)
        x2 = int(moments['m10'] / moments['m00'])
        y2 = int(moments['m01'] / moments['m00'])
        cv2.circle(drawing, (x2, y2), 4, line_color, -1, cv2.LINE_AA)

        coords = {abs(math.sqrt(((triangle[i][0][0] - x2) ** 2) + ((triangle[i][0][1] - y2) ** 2))): (
            triangle[i][0][0], triangle[i][0][1]) for i in range(3)}
        coords = sorted(coords.items())
        top = coords[0][1]
        x1, y1 = top
        cv2.line(drawing, (x1, y1), (x2, y2), (0, 0, 255), 2)
        angle_a = 180 / math.pi * (math.atan2(y1 - y2, x1 - x2)) + 90
        # print('angle_a', angle_a)
        return angle_a if not math.isnan(angle_a) else 0
    except:
        pass


def move_to_red():
    auv.set_rgb_color(255, 0, 0)
    auv.set_on_delay(10) 
    global goal_depth, sleep_time, h, w
    lin_z = keep_depth(goal_depth=goal_depth)
    moving(linear_z=lin_z, linear_y=25)
    time.sleep(sleep_time)
    moving()
    count = 0
    orange = False
    while count < 200:
        ok, frame0 = vid.read()

        img = frame0

      #  cv2.line(drawing, (160, 0), (160, 240), (0, 0, 255), 2)
      #  cv2.line(drawing, (0, 120), (320, 120), (0, 0, 255), 2)

        biggest_orange_cnt = None
        biggest_orange_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if not contours:
                continue

            for cnt in contours:
                draw_object_contour(img, cnt, name)
                if name == 'red':
                    area = cv2.contourArea(cnt)
                    orange = True

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

        if biggest_orange_area > 100:
            x, y = get_cnt_xy(biggest_orange_cnt)
            lin_y, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=0.05, k_ang=0.02)
            lin_z = keep_depth(goal_depth)
            moving(linear_y=lin_y, angular_z=ang_z, linear_z=lin_z)
            if abs(y - int(h/2)) < 5:
                count += 1
            else:
                count = 0
        else:
            moving(linear_z=lin_z, linear_y=25)
        mur_view.show(img, 0)


def move_to_orange():
    auv.set_on_delay(10)
    auv.set_rgb_color(240, 116, 39) 
    global goal_depth, sleep_time, h, w
    lin_z = keep_depth(goal_depth=goal_depth)
    moving(linear_z=lin_z, linear_y=25)
    time.sleep(sleep_time)
    moving()
    count = 0
    while count < 200:
        ok, frame0 = vid.read()

        img = frame0
        #h, w = img.shape[0], img.shape[1]
        #x_1, y_1 = int(w / 2), int(h / 2)

        #cv2.line(img, (x_1, 0), (x_1, h), (0, 0, 255), 2)
        #cv2.line(img, (0, y_1), (w, y_1), (0, 0, 255), 2)

        biggest_orange_cnt = None
        biggest_orange_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if not contours:
                continue

            for cnt in contours:
                draw_object_contour(img, cnt, name)
                if name == 'orange':
                    area = cv2.contourArea(cnt)
                    orange = True

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

        if biggest_orange_area > 100:
            x, y = get_cnt_xy(biggest_orange_cnt)
            lin_y, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=0.05, k_ang=0.015)
            lin_z = keep_depth(goal_depth)
            moving(linear_y=lin_y, angular_z=ang_z, linear_z=lin_z)
            if abs(y - int(h/2)) < 5:
                count += 1
            else:
                count = 0
        else:
            moving(linear_z=lin_z, linear_y=25)
        mur_view.show(img, 0)


# Функция выравнивания по оранжевой стрелке
def orange_aligment():
    auv.set_rgb_color(244, 202, 22)
    auv.set_on_delay(10) 
    global goal_depth, h, w
    count = 0
    while count < 200:

        ok, frame0 = vid.read()

        img = frame0
       # h, w = img.shape[0], img.shape[1]
       # x_1, y_1 = int(w / 2), int(h / 2)

       # cv2.line(img, (x_1, 0), (x_1, h), (0, 0, 255), 2)
       # cv2.line(img, (0, y_1), (w, y_1), (0, 0, 255), 2)

        biggest_orange_cnt = None
        biggest_orange_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if not contours:
                continue

            for cnt in contours:
                draw_object_contour(img, cnt, name)
                if name == 'orange':
                    area = cv2.contourArea(cnt)

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

            if biggest_orange_area > 100:

                angle = calc_triangle_course(img, biggest_orange_cnt)
                power = int(angle * 0.25)
                print(power)
                k = 0.1
                # power = int(angle*k + last_ang*(k-1))
                lin_z = -power

                moving(angular_z=int(power), linear_z=lin_z)
                last_ang = angle
                if abs(angle) < 3:
                    count += 1
                else:
                    count = 0
                last_ang = angle

        mur_view.show(img, 0)


def finish():
    print('Финиш')
    keep_depth(goal_depth=goal_depth)


def set_angle_90():
    print('Устанавливаю угол 90 градусов')
    goal_angle = 90
    global goal_depth
    counter = 0
    while counter < 100:
        keep_angle(goal_angle=goal_angle, goal_depth=goal_depth)
        if abs(auv.get_yaw() - goal_angle) > 1:
            counter += 1
            time.sleep(0.1)
        else:
            counter = 0


def keep_goal_depth():
    global goal_depth
    count = 0
    lin_z = keep_depth(goal_depth)
    while count < 50:
        moving(linear_z=lin_z)
        if abs(auv.get_depth() - goal_depth) < 0.05:
            count += 1
        else:
            count = 0


def ascent():
    while auv.get_depth() > 0:
        auv.set_rgb_color(255, 255, 255)  
        auv.set_on_delay(1)
        moving(linear_z=75)
def viid():
    ok, frame0 = vid.read()

    img = frame0

    mur_view.show(img, 0)

if __name__ == '__main__':

    mission = [deeping, move_to_orange, orange_aligment, move_to_orange,
               orange_aligment, move_to_orange, orange_aligment,
               move_to_orange, orange_aligment, move_to_orange,
               orange_aligment, move_to_red, ascent]
    #for mis in mission:
     #    print(mis.__name__)
      #   mis()


    #deeping()
while 1:
    deeping()
       
    
    
    
    
    
    
    
    
    

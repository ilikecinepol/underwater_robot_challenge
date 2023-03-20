import pymurapi as mur
import cv2
import time
import math

auv = mur.mur_init()
last_time = 0
last_error = 0.0

status = False

x = 0
y = 0
yaw = 0


# Перевод угла из -180 <=> 180 в 0 <=> 360
def to_360(angle):
    if angle > 0.0:
        return angle
    if angle <= 0.0:
        return 360.0 + angle


# Перевод угла >< 360 в 0 <=> 360
def clamp_to_360(angle):
    if angle < 0.0:
        return angle + 360.0
    if angle > 360.0:
        return angle - 360.0
    return angle


# Перевод угла из 0 <=> 360 в -180 <=> 180
def to_180(angle):
    if angle > 180.0:
        return angle - 360.0
    return angle


# Преобразовать v в промежуток между min max
def clamp(v, min, max):
    if v < min:
        return min
    if v > max:
        return max
    return v


# Функция удержания курса
def keep_yaw_meter(yaw_to_set, power):
    current_yaw = to_360(auv.get_yaw())
    er = clamp_to_360(yaw_to_set - current_yaw)
    er = to_180(er)
    res = er * 0.7
    auv.set_motor_power(1, clamp(int(power - res), -100, 100))
    auv.set_motor_power(2, clamp(int(power + res), -100, 100))


def stop():
    for i in range(5):
        auv.set_motor_power(i, 0)


# Функция пересчёта значений переменной в рамках указанного диапазона
def map(value, max, min):
    return max if value > max else min if value < min else value


# Функция пересчёта значений угла в рамках указанного диапазона
def angle_map(angle):
    return angle - 360 if angle > 180 else angle + 360 if angle < -180 else angle


def rotate(speed_degree, relative_angle_degree, clockwise):
    angilar_speed = math.radians(abs(speed_degree))


# Перевод угла из -180 <=> 180 в 0 <=> 360
def to_360(angle):
    if angle > 0.0:
        return angle
    if angle <= 0.0:
        return 360.0 + angle


def go_forwrd(t):
    power = 50
    auv.set_motor_power(0, power)
    auv.set_motor_power(1, power)
    time.sleep(t)
    auv.set_motor_power(0, 0)
    auv.set_motor_power(1, 0)


# Перевод угла >< 360 в 0 <=> 360
def clamp_to_360(angle):
    if angle < 0.0:
        return angle + 360.0
    if angle > 360.0:
        return angle - 360.0
    return angle


def keep_depth_pix(goal_depth, current_depth):
    # acurrent_depth = auv.get_depth()
    delta = goal_depth - current_depth
    power = 0.4 * delta

    auv.set_motor_power(2, power)
    auv.set_motor_power(3, power)
    # print(power)


# Установить направление
def keep_yaw_pix(goal_angle, current_angle):
    power = 15
    current_yaw = to_360(auv.get_yaw())
    er = clamp_to_360(- - current_angle)
    er = to_180(er)
    res = -er * 0.1
    auv.set_motor_power(0, clamp(int(power - res), -100, 100))
    auv.set_motor_power(1, clamp(int(power + res), -100, 100))


# Установить глубину аппарата в метрах
def keep_detpth_meters(goal_depth):
    current_depth = auv.get_depth()
    print(current_depth)
    error = current_depth - goal_depth
    power = 40 * error
    auv.set_motor_power(2, power)
    auv.set_motor_power(3, power)
    # print(power)


# Установить направление
def keep_yaw_meters(goal_angle):
    global last_time, last_error
    while True:
        current_time = time.time()
        current_yaw = auv.get_yaw()
        error = current_yaw - goal_angle
        diff_value = 0.5 / (current_time - last_time) * (current_yaw - goal_angle - last_error)

        if abs(error) > 3:
            power = angle_map(error + diff_value) * 0.8
        else:
            power = 0
            break
        auv.set_motor_power(0, -power)
        auv.set_motor_power(1, power)

        last_time = current_time
        last_error = error

        time.sleep(0.3)


def side_moving(power):
    # power = 60
    auv.set_motor_power(4, power)


def keep_x_pix(goal_x, current_x):
    delta = goal_x - current_x
    power = 0.4 * delta

    side_moving(power)


def pid_forward(power):
    auv.set_motor_power(0, power)
    auv.set_motor_power(1, power)


def keep_y_pix(goal_y, current_y):
    delta = goal_y - current_y
    power = 0.4 * delta

    # pid_forward(power)


def go_to_goal_pix(goal_x, goal_y):
    global x
    global y, yaw
    distance = abs(math.sqrt(((goal_x - x) ** 2) + ((goal_y - y) ** 2)))
    kp = 0.1
    linear_speed = distance * kp
    k_angular = 0.00000001
    if distance > 1:
        desired_angle_goal = math.atan2(goal_y - y, goal_x - x)
        angular_speed = (desired_angle_goal - yaw) * k_angular
    else:
        angular_speed = 0

    return linear_speed, angular_speed


def driving(data, goal_angle):
    global status
    linear = data[0]
    angular = data[1]

    if linear > 0 and angular == 0:
        auv.set_motor_power(0, linear)
        auv.set_motor_power(1, linear)
    elif linear < 0 and angular == 0:
        auv.set_motor_power(0, -linear)
        auv.set_motor_power(1, -linear)
    # keep_yaw_pix(angle, auv.get_yaw())
    else:
        ang_er = (auv.get_yaw() - goal_angle) * -0.2
        if angular > 0:

            auv.set_motor_power(0, ang_er)
            auv.set_motor_power(1, -ang_er)
        else:
            auv.set_motor_power(0, -ang_er)
            auv.set_motor_power(1, ang_er)
    if abs(linear) < 1:
        status = True


def driving_2d(data):
    global status
    linear = data[0]
    angular = data[1]
    yaw = auv.get_yaw()
    if linear > 0 and angular == 0:
        auv.set_motor_power(0, linear)
        auv.set_motor_power(1, linear)
    elif linear < 0 and angular == 0:
        auv.set_motor_power(0, -linear)
        auv.set_motor_power(1, -linear)
    # keep_yaw_pix(yaw, auv.get_yaw())


def round_360_deg(angle):
    keep_yaw_meters(angle)
    stop()
    time.sleep(1)
    print('готовимся')
    count = 0
    print('начать поворот')
    while count < 500000:
        auv.set_motor_power(0, 50)
        auv.set_motor_power(1, -50)
        count += 1
        print(count)

    stop()
    keep_yaw_meters(angle)


if __name__ == '__main__':
    while True:
        keep_detpth_meters(2)

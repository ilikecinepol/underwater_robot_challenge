import time

import pymurapi as mur
import numpy as np
import auv_moving
from center_detect import *
from auv_moving import *
import math

goal_depth = 3.3    # Поменять на нужную глубину
sleep_time = 1.5
auv = mur.mur_init()


def deeping():
    count = 0
    global goal_depth
    while count < 100:
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
                if name == 'red':
                    area = cv2.contourArea(cnt)

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

        if biggest_orange_area > 100:
            x, y = process_biggest_cnt(drawing, biggest_orange_cnt)
            lin_y, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=0.1, k_ang=0.0)
            lin_z = keep_depth(goal_depth)
            moving(linear_y=lin_y, linear_z=lin_z, angular_z=ang_z)
            if abs(y - 120) < 10:
                count += 1
            else:
                count = 0
        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)


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
    global goal_depth, sleep_time
    lin_z = keep_depth(goal_depth=goal_depth)
    moving(linear_z=lin_z, linear_y=25)
    time.sleep(sleep_time)
    moving()
    count = 0
    orange = False
    while count < 200:
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
            if abs(y - 120) < 5:
                count += 1
            else:
                count = 0
        else:
            moving(linear_z=lin_z, linear_y=25)
        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)

def move_to_orange():
    global goal_depth, sleep_time
    lin_z = keep_depth(goal_depth=goal_depth)
    moving(linear_z=lin_z, linear_y=25)
    time.sleep(sleep_time)
    moving()
    count = 0
    while count < 200:
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
                    orange = True

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

        if biggest_orange_area > 100:
            x, y = get_cnt_xy(biggest_orange_cnt)
            lin_y, ang_z = go_to_goal(x_goal=x, y_goal=y, k_lin=0.05, k_ang=0.015)
            lin_z = keep_depth(goal_depth)
            moving(linear_y=lin_y, angular_z=ang_z, linear_z=lin_z)
            if abs(y - 120) < 5:
                count += 1
            else:
                count = 0
        else:
            moving(linear_z=lin_z, linear_y=25)
        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)


# Функция выравнивания по оранжевой стрелке
def orange_aligment():
    global goal_depth
    count = 0
    while count < 200:
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

                angle = calc_triangle_course(drawing, biggest_orange_cnt)
                power = int(angle* 0.25)
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

        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)


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
        moving(linear_z=75)

if __name__ == '__main__':

    mission = [deeping, move_to_orange, orange_aligment, move_to_orange,
               orange_aligment, move_to_orange, orange_aligment,
               move_to_orange, orange_aligment, move_to_orange,
               orange_aligment, move_to_red, ascent]
    for mis in mission:
        print(mis.__name__)
        mis()

    # orange_aligment()
    

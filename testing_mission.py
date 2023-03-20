import time

import pymurapi as mur
from center_detect import *
from auv_moving import *

goal_depth = 3.4
auv = mur.mur_init()


def deeping():
    count = 0
    global goal_depth
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

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

        if biggest_orange_area > 100:
            x, y = process_biggest_cnt(drawing, biggest_orange_cnt)
            go_to_goal(x_goal=x, y_goal=y, goal_depth=goal_depth)
            if abs(y - 120) < 5:
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


def move_to_orange():
    global goal_depth
    keep_depth(linear_vel=5, goal_depth=goal_depth)
    time.sleep(2)
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

                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

        if biggest_orange_area > 100:
            x, y = process_biggest_cnt(drawing, biggest_orange_cnt)
            go_to_goal(x_goal=x, y_goal=y, goal_depth=goal_depth, k_lin=0.05, k_ang=0.001)
            if abs(y - 120) < 5:
                count += 1
            else:
                count = 0
        cv2.imshow('drawing', drawing)
        cv2.waitKey(1)


# Функция выравнивания по оранжевой стрелке
def orange_aligment():
    pass


def finish():
    print('Финиш')


def set_angle_90():
    print('Устанавливаю угол 90 градусов')
    goal_angle = 90
    global goal_depth
    counter = 0
    while counter < 75:
        keep_angle(goal_angle=goal_angle, goal_depth=goal_depth)
        if abs(auv.get_yaw() - goal_angle) > 1:
            counter += 1
            time.sleep(0.1)
        else:
            counter = 0


if __name__ == '__main__':
    mission = [deeping, set_angle_0, move_to_orange, set_angle_90, finish]
    for mis in mission:
        print(mis.__name__)
        mis()

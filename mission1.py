import time

import pymurapi as mur
from auv_moving import *

auv = mur.mur_init()


def set_depth_2():
    print('Устанавливаю глубину 2 м')
    goal_depth = 2
    counter = 0
    while counter < 85:
        keep_depth(goal_depth)
        if abs(auv.get_depth() - goal_depth) > 0.03:
            counter += 1
            time.sleep(0.1)
        else:
            counter = 0


def set_angle_180():
    print('Устанавливаю угол 180 градусов')
    goal_angle = 180
    counter = 0
    while counter < 75:
        keep_angle(goal_angle)
        if abs(auv.get_yaw() - goal_angle) > 1:
            counter += 1
            time.sleep(0.1)
        else:
            counter = 0


def drop():
    print('Сбрасываю мину')
    auv.drop()
    time.sleep(2)


def shot():
    print('Стреляю')
    auv.shoot()
    time.sleep(2)


def finish():
    print('Пора всплывать')
    goal_depth = 0
    counter = 0
    while counter < 50:
        keep_depth(goal_depth)
        if abs(auv.get_depth() - goal_depth) > 0.03:
            counter += 1
            time.sleep(0.1)
        else:
            counter = 0


def go_frwd_5sec():
    print('Плыву вперёд')
    moving(linear_x=20)
    time.sleep(5)
    moving()


def stop():
    print('Остановка')
    moving()


def depth():
    keep_depth(2)
    time.sleep(2)


mission = [set_depth_2, depth, shot, depth, set_angle_180, depth, go_frwd_5sec, depth, stop, depth, drop, depth, finish]

if __name__ == '__main__':
    for mis in mission:
        print('Выполняется', mis.__name__)

        mis()

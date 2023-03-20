import cv2
import pymurapi as mur

from pid import *
import time
from detect_angle import *

x = 0
y = 0
x_er = 0
y_er = 0
cnt = 0
area = 0

color = 'yellow'
auv = mur.mur_init()
colors = {
    'orange': ((0, 50, 50), (20, 255, 255)),
    'yellow': ((20, 50, 50), (30, 255, 255)),
    'purple': ((98, 124, 144), (180, 255, 255)),
    'green': ((31, 113, 116), (81, 255, 255)),
}


def get_image(color, camera='front'):
    if camera == 'front':
        img = auv.get_image_front()
    else:
        img = auv.get_image_bottom()
    h, w = img.shape[0], img.shape[1]
    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    goal_x = int(w / 2)
    goal_y = int(h / 2)
    cv2.imshow('camera' + camera, img)
    img_mask = cv2.inRange(hsv_image, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return img, w, h, goal_x, goal_y


# функция поиска контуров
def find_colors(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    font = cv2.FONT_HERSHEY_SIMPLEX
    # print(color)
    # cv2.putText(img, name, (0, 0), font, 1, (255, 255, 0), 2)
    return contours


# Функция отрисовки контура
def draw_object_contour(drawing, contour, name):
    if cv2.contourArea(contour) < 100:
        return

    line_color = (0, 0, 255)
    cv2.drawContours(drawing, [contour], 0, line_color, 2)


def draw_object_contour(drawing, contour, name):
    if cv2.contourArea(contour) < 100:
        return

    line_color = (0, 0, 255)
    cv2.drawContours(drawing, [contour], 0, line_color, 2)
    moments = cv2.moments(cnt)

    try:
        x = int(moments['m10'] / moments['m00'])
        y = int(moments['m01'] / moments['m00'])
        cv2.circle(drawing, (x, y), 4, (0, 255, 255), -1)
        # print(name)
        text = str(name)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(drawing, text, (x - 100, y), font, 0.75, (0, 0, 0), 2)

    except ZeroDivisionError:
        print('Упс, деление на ноль')


def process_biggest_cnt(drawing, contour):
    cv2.drawContours(drawing, [contour], 0, (0, 255, 0), 3)


def cam_pid(color, status):
    t1 = time.time()
    t2 = 0

    global x, y, x_er, y_er, cnt, area, count
    current_time = 0
    while current_time < 10:
        t2 = time.time()
        current_time = t2 - t1
        # print(current_time)
        keep_detpth_meters(2)

        img = auv.get_image_bottom()

        h, w = img.shape[0], img.shape[1]
        hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        goal_x = int(w / 2)
        goal_y = int(h / 2)
        drawing = img.copy()

        biggest_orange_cnt = None
        biggest_orange_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if not contours:
                continue

            for cnt in contours:
                draw_object_contour(drawing, cnt, name)

                if name == 'orange' or name == 'yellow':
                    area = cv2.contourArea(cnt)
                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

                        moments = cv2.moments(cnt)

                        try:
                            x = int(moments['m10'] / moments['m00'])
                            y = int(moments['m01'] / moments['m00'])
                            cv2.circle(drawing, (x, y), 4, (0, 255, 255), -1)
                            # print(x, y)s
                            x_er = keep_x_pix(goal_x, x)
                            y_er = keep_y_pix(goal_y, y)
                        except ZeroDivisionError:
                            pass

        if biggest_orange_area > 200:
            angle = calc_angle(drawing, biggest_orange_cnt)
            # print('angle = ', angle)
            # keep_yaw_pix(angle, auv.get_yaw())

            keep_detpth_meters(3)
            speeds = go_to_goal_pix(goal_x, goal_y)

            driving(speeds, angle + 45)
        # print(current_time)
        if current_time > 9:

            return 'go'


if __name__ == '__main__':

    while True:
        keep_detpth_meters(2)

        img = auv.get_image_bottom()

        h, w = img.shape[0], img.shape[1]
        hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        goal_x = int(w / 2)
        goal_y = int(h / 2)
        drawing = img.copy()

        biggest_orange_cnt = None
        biggest_orange_area = 0

        for name in colors:
            contours = find_contours(img, colors[name])

            if not contours:
                continue

            for cnt in contours:
                draw_object_contour(drawing, cnt, name)

                if name == 'orange' or name == 'yellow':
                    area = cv2.contourArea(cnt)
                    if area > biggest_orange_area:
                        biggest_orange_area = area
                        biggest_orange_cnt = cnt

                        moments = cv2.moments(cnt)

                        try:
                            x = int(moments['m10'] / moments['m00'])
                            y = int(moments['m01'] / moments['m00'])
                            cv2.circle(drawing, (x, y), 4, (0, 255, 255), -1)
                            # print(x, y)s
                            x_er = keep_x_pix(goal_x, x)
                            y_er = keep_y_pix(goal_y, y)
                            if area > 15000:
                                stop()
                        except ZeroDivisionError:
                            pass
                        cv2.line(drawing, (int(w / 2), 0), (int(w / 2), h), (0, 0, 255), 3)
                        cv2.line(drawing, (0, int(h / 2)), (w, int(h / 2)), (0, 0, 255), 3)
                        cv2.line(drawing, (goal_x, y), (x, y), (255, 255, 255), 3)
                        cv2.line(drawing, (x, goal_y), (x, y), (255, 255, 255), 3)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(drawing, str(x_er), (goal_x, y), font, 0.5, (255, 255, 255), 2)
                        cv2.putText(drawing, str(y_er), (x, goal_y), font, 0.5, (255, 255, 255), 2)
                        cv2.imshow('contour', drawing)

        if biggest_orange_area > 200:
            angle = calc_angle(drawing, biggest_orange_cnt)
            # print('angle = ', angle)
            # keep_yaw_pix(angle, auv.get_yaw())

            keep_detpth_meters(3)
            speeds = go_to_goal_pix(goal_x, goal_y)

            driving(speeds, angle + 45)

        # print(area)

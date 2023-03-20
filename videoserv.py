import cv2
import numpy as np
import math
import pymurapi as mur
from time import sleep


auv = mur.mur_init()
mur_view = auv.get_videoserver()
auv.set_on_delay(0)
cap0 = cv2.VideoCapture(0)


def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    _, contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours
   


if __name__ == '__main__':
    while True:
        ok, frame0 = cap0.read()

        img = frame0
        
        mur_view.show(img, 0)





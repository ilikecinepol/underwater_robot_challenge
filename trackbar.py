import pymurapi as mur
import cv2

auv = mur.mur_init()
img = auv.get_image_bottom()



img = cv2.imread('Screenshot_2.png')
# ok, img = vid.read()
def process_img(img, name, color):
    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    img_mask = cv2.inRange(hsv_image, color[0], color[1])
    cv2.imshow('mask' + name, img_mask)

    img_mixed = cv2.bitwise_and(img, img, mask=img_mask)
    cv2.imshow(name, img_mixed)


def update(value=0):
    color_low = (
        cv2.getTrackbarPos('h_min', 'ui'),
        cv2.getTrackbarPos('s_min', 'ui'),
        cv2.getTrackbarPos('v_min', 'ui')
    )
    color_high = (
        cv2.getTrackbarPos('h_max', 'ui'),
        cv2.getTrackbarPos('s_max', 'ui'),
        cv2.getTrackbarPos('v_max', 'ui')
    )
    color = (color_low, color_high)
    cv2.imshow('ui', img)
    process_img(img, 'img', color)


if __name__ == '__main__':
    cv2.namedWindow('ui')

    cv2.createTrackbar('h_min', 'ui', 0, 180, update)
    cv2.createTrackbar('s_min', 'ui', 0, 255, update)
    cv2.createTrackbar('v_min', 'ui', 0, 255, update)
    cv2.createTrackbar('h_max', 'ui', 180, 180, update)
    cv2.createTrackbar('s_max', 'ui', 255, 255, update)
    cv2.createTrackbar('v_max', 'ui', 255, 255, update)
    while True:
        img = cv2.imread('1112.png')
        update()
        pressed_key = cv2.waitKey(1)

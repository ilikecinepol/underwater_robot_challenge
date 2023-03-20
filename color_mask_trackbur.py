import cv2
import pymurapi as mur

auv = mur.mur_init()


# Функция обработки изображения
def process_img(img, name, color):
    # Конвертируем в HSV
    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Создаём маску, используя показатели toolbars и Выводим изображение маски
    img_mask = cv2.inRange(hsv_image, color[0], color[1])
    cv2.imshow('mask' + name, img_mask)
    # Создаём изображение, умножая маску на оригинал.
    # Всё что умножается на черный в маске, обнуляется, что на белый, остается.
    # Получается выводим вырезанное изображение с оригинало, подошедшее под маску
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
    # Выводим окно с оригинальным изображением
    cv2.imshow('ui', img)
    # Вызываем функцию обработки озображения, используя показатели toolbars
    process_img(img, 'img', color)


if __name__ == '__main__':
    # Создаём окно под названием ui. В нём будем регулировать цвет HSV
    cv2.namedWindow('ui')
    # Создаём регуляторы
    cv2.createTrackbar('h_min', 'ui', 0, 180, update)
    cv2.createTrackbar('s_min', 'ui', 0, 255, update)
    cv2.createTrackbar('v_min', 'ui', 0, 255, update)
    cv2.createTrackbar('h_max', 'ui', 180, 180, update)
    cv2.createTrackbar('s_max', 'ui', 255, 255, update)
    cv2.createTrackbar('v_max', 'ui', 255, 255, update)

    while True:
        img = auv.get_image_bottom()
        update()
        pressed_key = cv2.waitKey(1)








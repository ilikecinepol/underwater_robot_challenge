# Код для создания бинарной маски по заданному цвету из видеоролика.
# Сначала на подводном аппарате проплываем трассу и делаем запись экрана.
# Потом в коде указываем путь к видеофайлу и, двигая ползунки, добиваемся эффекта.
# Для замедления/ускорения видео нажать -/+
# Для пазуы нажать "Р" (английский)


import pymurapi as mur
import cv2
import numpy as np

auv = mur.mur_init()
img = auv.get_image_bottom()

# Функция для обработки изображения
def process_img(img, name, color):
    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(hsv_image, color[0], color[1])
    cv2.imshow('mask_' + name, img_mask)
    img_mixed = cv2.bitwise_and(img, img, mask=img_mask)
    cv2.imshow(name, img_mixed)

# Функция для обновления изображения с трекбаром
def update(value=0):
    h_min = cv2.getTrackbarPos('h_min', 'ui')
    s_min = cv2.getTrackbarPos('s_min', 'ui')
    v_min = cv2.getTrackbarPos('v_min', 'ui')
    h_max = cv2.getTrackbarPos('h_max', 'ui')
    s_max = cv2.getTrackbarPos('s_max', 'ui')
    v_max = cv2.getTrackbarPos('v_max', 'ui')

    color_low = (h_min, s_min, v_min)
    color_high = (h_max, s_max, v_max)
    color = (color_low, color_high)

    process_img(img, 'img', color)

if __name__ == '__main__':
    cv2.namedWindow('ui')
    cv2.createTrackbar('h_min', 'ui', 0, 180, update)
    cv2.createTrackbar('s_min', 'ui', 0, 255, update)
    cv2.createTrackbar('v_min', 'ui', 0, 255, update)
    cv2.createTrackbar('h_max', 'ui', 180, 180, update)
    cv2.createTrackbar('s_max', 'ui', 255, 255, update)
    cv2.createTrackbar('v_max', 'ui', 255, 255, update)

    # Использование видеоролика
    video_path = 'pool.mkv'  # Укажите путь к вашему видеофайлу
    cap = cv2.VideoCapture(video_path)

    paused = False
    delay = 30  # Начальная задержка между кадрами (в миллисекундах)

    while True:
        if not paused:
            ret, img = cap.read()
            if not ret:
                break

        cv2.imshow('ui', img)  # Показать оригинальное видео
        update()

        key = cv2.waitKey(delay) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            paused = not paused
        elif key == ord('+'):
            delay = max(1, delay - 10)  # Уменьшение задержки для ускорения видео
        elif key == ord('-'):
            delay += 10  # Увеличение задержки для замедления видео

    cap.release()
    cv2.destroyAllWindows()

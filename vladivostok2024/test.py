import cv2
import pytesseract
import pymurapi as mur  # Импорт библиотеки mur для инициализации AUV

# Инициализация AUV
auv = mur.mur_init()

# Настройки pytesseract, путь к исполняемому файлу tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Проверьте правильность пути

# Функция для распознавания черных цифр с изображения, полученного от AUV
def recognize_black_digits_from_auv():
    while True:
        # Получение изображения с передней камеры AUV
        frame = auv.get_image_front()

        if frame is None:
            print("Не удалось получить изображение с камеры AUV")
            continue  # Попробуем снова вместо выхода

        # Преобразование изображения в оттенки серого
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Применение размытия для уменьшения шума
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Применение пороговой обработки для улучшения качества распознавания
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Морфологическая обработка для улучшения качества цифр
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Инверсия изображения, чтобы черные цифры стали белыми
        inverted_thresh = cv2.bitwise_not(morphed)

        # Сохранение промежуточного изображения для отладки
        cv2.imwrite('frame.jpg', frame)
        cv2.imwrite('gray.jpg', gray)
        cv2.imwrite('blurred.jpg', blurred)
        cv2.imwrite('thresh.jpg', thresh)
        cv2.imwrite('morphed.jpg', morphed)
        cv2.imwrite('inverted_thresh.jpg', inverted_thresh)

        # Использование pytesseract для распознавания текста
        custom_config = r'--oem 3 --psm 6 outputbase digits'
        try:
            digits = pytesseract.image_to_string(inverted_thresh, config=custom_config)
        except pytesseract.TesseractError as e:
            print(f"Ошибка Tesseract: {e}")
            continue  # Попробуем снова вместо выхода

        # Вывод распознанных цифр
        print("Распознанные цифры:", digits.strip())

        # Отображение текущего кадра
        cv2.imshow('Frame', frame)
        cv2.imshow('Thresh', inverted_thresh)

        # Завершение работы по нажатию клавиши 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Освобождение ресурсов
    cv2.destroyAllWindows()

# Запуск функции распознавания черных цифр с камеры AUV
recognize_black_digits_from_auv()

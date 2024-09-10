import cv2
import numpy as np


def detect_red_light(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    potential_lights = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 100 < area < 1000:
            (x, y, w, h) = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if 0.8 < aspect_ratio < 1.2:
                potential_lights.append((x, y, w, h))

    return potential_lights


def draw_lights(frame, lights, confirmed=False):
    for i, (x, y, w, h) in enumerate(lights):
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        label = f"Light {i + 1}" if not confirmed else f"Confirmed {i + 1}"
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


def main():
    cap = cv2.VideoCapture(0)
    confirmed_lights = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        potential_lights = detect_red_light(frame)

        # 绘制已确认的红灯
        draw_lights(frame, confirmed_lights, confirmed=True)

        # 如果没有已确认的红灯，绘制潜在的红灯
        if not confirmed_lights:
            draw_lights(frame, potential_lights)

        cv2.putText(frame, f"Detected: {len(potential_lights)}, Confirmed: {len(confirmed_lights)}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow('Red Light Detection', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c') and potential_lights and not confirmed_lights:
            # 创建一个新窗口来显示潜在的红灯区域
            for i, (x, y, w, h) in enumerate(potential_lights):
                light_region = frame[y:y + h, x:x + w]
                cv2.imshow(f'Confirm Light {i + 1}', light_region)

            # 等待用户确认
            while True:
                confirm_key = cv2.waitKey(0) & 0xFF
                if confirm_key == ord('y'):
                    confirmed_lights = potential_lights
                    print(f"已确认 {len(confirmed_lights)} 个红灯")
                    break
                elif confirm_key == ord('n'):
                    break

            # 关闭确认窗口
            for i in range(len(potential_lights)):
                cv2.destroyWindow(f'Confirm Light {i + 1}')

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
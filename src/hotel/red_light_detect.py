import cv2
import numpy as np

# 全局变量
drawing = False
ix, iy = -1, -1
roi = None
roi_selected = False


def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, roi, roi_selected

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            param[0] = param[0].copy()
            cv2.rectangle(param[0], (ix, iy), (x, y), (0, 255, 0), 2)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi = (min(ix, x), min(iy, y), abs(ix - x), abs(iy - y))
        cv2.rectangle(param[0], (ix, iy), (x, y), (0, 255, 0), 2)


def detect_red_light(frame, roi):
    x, y, w, h = roi
    roi_frame = frame[y:y + h, x:x + w]
    hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)

    # 定义红色的HSV范围
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # 创建红色区域的掩码
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    # 计算红色区域的比例
    red_ratio = np.sum(mask) / (w * h * 255)

    return red_ratio > 0.1 # 这个阈值可以根据需要调整


def main():
    global roi, roi_selected
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('Red Light Detection')
    cv2.setMouseCallback('Red Light Detection', draw_rectangle, [None])

    light_on = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if roi is not None:
            x, y, w, h = roi
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow('Red Light Detection', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == 13:  # ENTER 键
            if roi is not None:
                roi_selected = True
                print("区域已选择。开始检测红灯闪烁。")
                break

    while roi_selected:
        ret, frame = cap.read()
        if not ret:
            break

        x, y, w, h = roi
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        current_light_on = detect_red_light(frame, roi)
        if current_light_on and not light_on:
            light_on = True
            cv2.imwrite("red_light_on.jpg", frame)
            print("红灯亮起！已保存截图：red_light_on.jpg")
        elif not current_light_on:
            light_on = False

        cv2.imshow('Red Light Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
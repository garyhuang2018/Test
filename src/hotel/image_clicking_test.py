# encoding= utf-8
# __author__= gary
import cv2
import numpy as np
import os

def click_on_center_points(center_points):
    for point in center_points:
        x, y = point
        adb_click(x,y)


def find_and_mark_image(template_path, screenshot_path):
    # 读取原始屏幕截图和模板图像
    img_rgb = cv2.imread(screenshot_path)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path, 0)

    # 进行模板匹配
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)

    # 提取坐标并标记
    w, h = template.shape[::-1]
    center_points = [(int((x + x + w) / 2), int((y + y + h) / 2)) for x, y in zip(*loc[::-1])]
    click_on_center_points(center_points)
    marked_img = img_rgb.copy()
    for pt in zip(*loc[::-1]):
        cv2.rectangle(marked_img, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)  # 画矩形
        cv2.circle(marked_img, center=pt, radius=5, color=(0, 0, 255), thickness=-1)  # 画红点
    # 确保图像大小适合显示
    scale_percent = 60  # 缩放比例，可根据需要调整
    width = int(img_rgb.shape[1] * scale_percent / 100)
    height = int(img_rgb.shape[0] * scale_percent / 100)
    dim = (width, height)
    marked_img_resized = cv2.resize(marked_img, dim, interpolation=cv2.INTER_AREA)

    # 显示调整尺寸后的带有标记的图像
    cv2.imshow('Detected Points (Resized)', marked_img_resized)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



def find_image(template_path, screenshot_path):
    # 读取原始屏幕截图和模板图像
    img_rgb = cv2.imread(screenshot_path)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path, 0)

    # 进行模板匹配
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)

    # 提取坐标
    points = zip(*loc[::-1])

    return points


def adb_click(x, y):
    os.system(f'adb shell input tap {x} {y}')


if __name__ == "__main__":
    screenshot_path = r'C:\Users\garyh\PycharmProjects\test_tool\src\hotel\screenshot.png'
    template_path = r'C:\Users\garyh\PycharmProjects\test_tool\src\hotel\test.png'
    find_and_mark_image(template_path, screenshot_path)
    #
    # if matched_points:
    #     print("Matched points found:", matched_points)
    #     matched_point = next(iter(matched_points), None)  # 获取第一个匹配点
    #     if matched_point:
    #         x, y = matched_point
    #         adb_click(x, y)
    #         print(f"Clicked at coordinates ({x}, {y})")
    # else:
    #     print("No match found.")

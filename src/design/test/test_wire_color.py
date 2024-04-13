# # encoding= utf-8
# # __author__= gary
#
# import cv2
# import numpy as np
#
#
# def detect_wire_colors(image):
#     # 定义颜色范围和颜色名称
#     color_ranges = [
#         ((0, 100, 100), (10, 255, 255), "Red"),
#         ((160, 100, 100), (180, 255, 255), "Red"),
#         ((0, 0, 0), (90, 90, 90), "Black"),
#         ((110, 50, 50), (130, 255, 255), "Blue"),  # Blue color range
#         ((20, 100, 100), (30, 255, 255), "Yellow"),
#         ((0, 0, 231), (180, 30, 255), "White"),
#         ((85, 100, 100), (100, 255, 255), "Blue")
#     ]
#
#     # 转换图像到HSV色彩空间
#     hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#
#     detected_colors = set()
#
#     # Detect colors and print unique color names
#     for (lower, upper, color_name) in color_ranges:
#         lower = np.array(lower, dtype=np.uint8)
#         upper = np.array(upper, dtype=np.uint8)
#         mask = cv2.inRange(hsv_image, lower, upper)
#         contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         cv2.drawContours(image, contours, -1, (0, 255, 0), 2)  # Draw contours in green
#         if contours:
#             detected_colors.add(color_name)
#
#     # Print the detected unique colors
#     if detected_colors:
#         print("Detected wire colors:")
#         for color in detected_colors:
#             print(color)
#     else:
#         print("No wire colors detected.")
#
#     # Draw color names on the image matching the contours
#     for (lower, upper, color_name) in color_ranges:
#         if color_name in detected_colors:
#             for contour in contours:
#                 M = cv2.moments(contour)
#                 if M["m00"] != 0:
#                     cX = int(M["m10"] / M["m00"])
#                     cY = int(M["m01"] / M["m00"])
#                     cv2.putText(image, color_name, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
#                                 cv2.LINE_AA)
#     # Display the image with contours
#     cv2.imshow("Contours", image)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
#
#     return detected_colors
#
# # 读取图像
# image_path = 'your_image_path.jpg'
# image = cv2.imread(r'C:\Users\garyh\Desktop\test_wire.png')
#
# # 检测网线颜色
# colors = detect_wire_colors(image)
#
# # 打印检测到的颜色
# if colors:
#     print("Detected wire colors (from left to right):")
#     for color in colors:
#         print(color)
# else:
#     print("No wire colors detected.")
#
#
#

import cv2
import numpy as np

# def detect_wire_colors(image):
#     color_ranges = [
#         ((0, 100, 100), (10, 255, 255), "Red"),
#         ((160, 100, 100), (180, 255, 255), "Red"),
#         ((0, 0, 0), (90, 90, 90), "Black"),
#         ((110, 50, 50), (130, 255, 255), "Blue"),
#         ((20, 100, 100), (30, 255, 255), "Yellow"),
#         ((0, 0, 231), (180, 30, 255), "White"),
#         ((85, 100, 100), (100, 255, 255), "Blue")
#     ]
#
#     hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#
#     detected_colors = []
#
#     for (lower, upper, color_name) in color_ranges:
#         lower = np.array(lower, dtype=np.uint8)
#         upper = np.array(upper, dtype=np.uint8)
#         mask = cv2.inRange(hsv_image, lower, upper)
#         contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         if contours:
#             for contour in contours:
#                 area = cv2.contourArea(contour)
#                 if area > 100:  # Filter out small contours (noise)
#                     detected_colors.append((color_name, contour))
#
#     # Sort contours by x coordinate
#     detected_colors.sort(key=lambda x: cv2.boundingRect(x[1])[0])
#
#     for color, contour in detected_colors:
#         M = cv2.moments(contour)
#         if M["m00"] != 0:
#             cX = int(M["m10"] / M["m00"])
#             cY = int(M["m01"] / M["m00"])
#             cv2.putText(image, color, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
#                         cv2.LINE_AA)
#             cv2.drawContours(image, [contour], -1, (0, 255, 0), 2)  # Draw contours in green
#
#     cv2.imshow("Contours", image)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
#
#     return [color for color, _ in detected_colors]
#
# image_path = 'your_image_path.jpg'
# image = cv2.imread(r'C:\Users\garyh\Desktop\test_wire.png')
#
# colors = detect_wire_colors(image)
#
# if colors:
#     print("Detected wire colors (from left to right):")
#     for color in colors:
#         print(color)
# else:
#     print("No wire colors detected.")

import cv2
import numpy as np


def detect_wire_colors(image):
    color_ranges = [
        ((0, 100, 100), (10, 255, 255), "Red"),
        ((160, 100, 100), (180, 255, 255), "Red"),
        ((0, 0, 0), (90, 90, 90), "Black"),
        ((110, 50, 50), (130, 255, 255), "Blue"),
        ((20, 100, 100), (30, 255, 255), "Yellow"),
        ((0, 0, 231), (180, 30, 255), "White"),
        ((85, 100, 100), (100, 255, 255), "Blue")
    ]

    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    detected_colors = []

    for (lower, upper, color_name) in color_ranges:
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        mask = cv2.inRange(hsv_image, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Filter out small contours (noise)
                    if color_name not in [color for color, _ in detected_colors]:  # Check if color is already detected
                        detected_colors.append((color_name, contour))

    # Sort contours by x coordinate
    detected_colors.sort(key=lambda x: cv2.boundingRect(x[1])[0])

    for color, contour in detected_colors:
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.putText(image, color, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.drawContours(image, [contour], -1, (0, 255, 0), 2)  # Draw contours in green

    cv2.imshow("Contours", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return [color for color, _ in detected_colors]

image_path = 'your_image_path.jpg'
image = cv2.imread(r'C:\Users\garyh\Desktop\test_wire.png')

colors = detect_wire_colors(image)

if colors:
    print("Detected wire colors (from left to right):")
    for color in colors:
        print(color)
else:
    print("No wire colors detected.")


# # encoding= utf-8
# #__author__= gary
#
# import cv2
# import numpy as np
#
# # 全局变量用于存储最近一帧中的箭头轮廓
# last_arrow_contour = None
#
#
# def find_best_arrow_contour(contours):
#     global last_arrow_contour
#
#     best_contour = None
#     best_similarity = 0.0  # 相似度度量，可以根据实际需要调整
#
#     for contour in contours:
#         perimeter = cv2.arcLength(contour, True)
#         approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
#
#         # 计算当前轮廓与上一帧箭头轮廓的相似度（这里示意性地用面积作为相似度）
#         current_area = cv2.contourArea(approx)
#         if last_arrow_contour is not None:
#             last_area = cv2.contourArea(last_arrow_contour)
#             similarity = abs(current_area - last_area)  # 可以根据需要改进相似度计算
#         else:
#             similarity = 0.0
#
#         # 更新最相似的轮廓
#         if similarity > best_similarity:
#             best_similarity = similarity
#             best_contour = contour
#
#     # 更新箭头轮廓变量
#     last_arrow_contour = best_contour
#
#     return best_contour
#
#
# # 主程序
# cap = cv2.VideoCapture('your_rtsp_url')
#
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     # 预处理帧
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     edges = cv2.Canny(gray, 50, 150)
#     contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     # 查找最像的箭头轮廓
#     arrow_contour = find_best_arrow_contour(contours)
#
#     # 绘制箭头轮廓
#     if arrow_contour is not None:
#         cv2.drawContours(frame, [arrow_contour], -1, (0, 255, 0), 2)
#
#     # 显示结果
#     cv2.imshow('Arrows Detected', frame)
#
#     # 退出条件
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# # 清理资源
# cap.release()
# cv2.destroyAllWindows()
#
# # RTSP地址，替换成你自己的视频流地址
# rtsp_url = 'rtsp://admin:gemvary2020@192.192.0.111'
#
# # 创建视频捕捉对象
# cap = cv2.VideoCapture(rtsp_url)
#
# # 检查视频流是否打开
# if not cap.isOpened():
#     print("Error: Cannot open RTSP stream.")
#     exit()
#
# # 循环读取和显示视频帧
# while True:
#     # 从视频流中读取一帧
#     ret, frame = cap.read()
#
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     edges = cv2.Canny(gray, 50, 150)
#
#     # detect edge
#     contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     arrow_contours = []
#     for contour in contours:
#         perimeter = cv2.arcLength(contour, True)
#         approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
#         if len(approx) == 7:  # 假设箭头是一个由7个顶点组成的多边形
#             arrow_contours.append(contour)
#
#     cv2.drawContours(frame, arrow_contours, -1, (0, 255, 0), 2)
#
#     if not ret:
#         print("Error: Failed to capture frame.")
#         break
#
#     cv2.imshow('Arrows Detected', frame)
#     # # 显示视频帧
#     # cv2.imshow('RTSP Stream', frame)
#
#     # 按 'q' 键退出循环
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# # 释放资源
# cap.release()
# cv2.destroyAllWindows()
import cv2
import numpy as np

# 全局变量用于存储最近一帧中的箭头轮廓
last_arrow_contour = None


def find_best_arrow_contour(contours):
    global last_arrow_contour

    best_contour = None
    best_similarity = 0.0  # 相似度度量，可以根据实际需要调整

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

        # 计算当前轮廓与上一帧箭头轮廓的相似度（这里示意性地用面积作为相似度）
        current_area = cv2.contourArea(approx)
        if last_arrow_contour is not None:
            last_area = cv2.contourArea(last_arrow_contour)
            similarity = abs(current_area - last_area)  # 可以根据需要改进相似度计算
        else:
            similarity = 0.0

        # 更新最相似的轮廓
        if similarity > best_similarity:
            best_similarity = similarity
            best_contour = contour

    # 更新箭头轮廓变量
    last_arrow_contour = best_contour

    return best_contour


# 主程序
cap = cv2.VideoCapture('rtsp://admin:gemvary2020@192.192.0.111')

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 预处理帧
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    arrow_contours = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) == 7:  # 假设箭头是一个由7个顶点组成的多边形
            arrow_contours.append(contour)
    cv2.drawContours(frame, arrow_contours, -1, (0, 255, 0), 2)

    # 查找最像的箭头轮廓
    arrow_contour = find_best_arrow_contour(contours)

    # 绘制箭头轮廓
    if arrow_contour is not None:
        print('arr')
        cv2.drawContours(frame, [arrow_contour], -1, (0, 255, 0), 2)

    # 显示结果
    cv2.imshow('Arrows Detected', frame)

    # 退出条件
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 清理资源
cap.release()
cv2.destroyAllWindows()

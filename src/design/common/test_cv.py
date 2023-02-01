# -*- encoding utf-8 -*-
import cv2
import imutils
import math
import operator


img = cv2.imread('test_1.jpg')
img_target = cv2.imread('test_1_correct.jpg')
print(img)
print(type(img))
source_img = cv2.split(img)


target_img = cv2.split(img_target)
print(source_img)
histSize = [256]
histRange = [0, 256]
hist_origin = cv2.calcHist(source_img, [0], None, histSize, histRange, True)  # 第一个参数是输入图像列表， 第二个是需要处理的通道列表， 第三个是图像掩膜
hist_target = cv2.calcHist(target_img, [0], None, histSize, histRange, True)  # 第一个参数是输入图像列表， 第二个是需要处理的通道列表， 第三个是图像掩膜
result = cv2.compareHist(hist_origin, hist_target, cv2.HISTCMP_CORREL)

print('测试:', result)
print(result)
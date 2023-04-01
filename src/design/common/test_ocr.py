import math
import os
from datetime import datetime
from time import sleep

import loguru
import pytesseract
from PIL import Image

import numpy as np
import cv2 as cv


def ocr_detect(img_path):
    print('enter ocr detect')
    image = Image.open(img_path)
    print(pytesseract.image_to_string(image, lang='chi_sim'))


def harr_corner_detect(filename):
    img = cv.imread(filename)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gray = np.float32(gray)
    dst = cv.cornerHarris(gray,2,3,0.04)
    #result is dilated for marking the corners, not important
    dst = cv.dilate(dst,None)
    # Threshold for an optimal value, it may vary depending on the image.
    img[dst>0.01*dst.max()]=[0,0,255]
    cv.imshow('dst',img)
    if cv.waitKey(0) & 0xff == 27:
        cv.destroyAllWindows()


def new_corner_detect(filename):
    img = cv.imread(filename)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # find Harris corners
    gray = np.float32(gray)
    # cv.cornerHarris(	src, blockSize, ksize, k[, dst[, borderType]]	) ->	dst
    dst = cv.cornerHarris(gray, 0.2, 0.3, 0.04)
    dst = cv.dilate(dst, None)
    ret, dst = cv.threshold(dst, 0.01 * dst.max(), 255, 0)
    dst = np.uint8(dst)
    # find centroids
    ret, labels, stats, centroids = cv.connectedComponentsWithStats(dst)
    # define the criteria to stop and refine the corners
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 100, 0.001)
    corners = cv.cornerSubPix(gray, np.float32(centroids), (5, 5), (-1, -1), criteria)
    # Now draw them
    res = np.hstack((centroids, corners))
    res = np.int0(res)
    img[res[:, 1], res[:, 0]] = [0, 0, 255]
    img[res[:, 3], res[:, 2]] = [0, 255, 0]
    cv.imwrite('subpixel5.png', img)


def compare_two_pics(sample_image, test_image):

    """
    :return Boolean  return True if the black screen occurs
    """
    img = cv.imread(sample_image)
    img_target = cv.imread(test_image)
    source_img = cv.split(img)
    target_img = cv.split(img_target)
    histSize = [256]
    histRange = [0, 256]
    hist_origin = cv.calcHist(source_img, [0], None, histSize, histRange,
                               True)  # 第一个参数是输入图像列表， 第二个是需要处理的通道列表， 第三个是图像掩膜
    hist_target = cv.calcHist(target_img, [0], None, histSize, histRange,
                               True)  # 第一个参数是输入图像列表， 第二个是需要处理的通道列表， 第三个是图像掩膜
    result = cv.compareHist(hist_origin, hist_target, cv.HISTCMP_CORREL)
    loguru.logger.debug('comparing result' + str(result))
    if result <= 0.75:  # 判断相似度<=0.75 时为出现黑屏现象
        return True


def take_photo(camera_id, device_id):
    print(camera_id)
    cap = cv.VideoCapture(int(camera_id))
    index = 1
    if cap.isOpened():
        ret, frame = cap.read()
        sleep(1)
        cv.imshow("USB", frame)
        sleep(3)
        # 将这个文件pull到本地电脑上
        local_dir = str(device_id).replace(':', '_')
        if os.path.exists(local_dir) is not True:
            os.mkdir(local_dir)  # if dir is not exists, make a new dir
        curr_time = datetime.now()
        timestamp = datetime.strftime(curr_time, '%Y-%m-%d-%H-%M-%S')
        export_img_path = os.getcwd() + '/' + local_dir + '/' + timestamp + ".jpg"
        print(export_img_path)
        sleep(1)
        cv.imwrite(export_img_path, frame)
        print("save usb capture:" + str(index) + ".jpg successfuly!")
        cap.release()
        cv.destroyAllWindows()
        return export_img_path
    cap.release()
    cv.destroyAllWindows()


def midian_blur(img):
    Gn = cv.imread(img)
    # 转成灰度图
    gray = cv.cvtColor(Gn, cv.COLOR_BGR2GRAY)
    Gf = cv.medianBlur(gray, 3)
    ret, thresh1 = cv.threshold(Gf, 135, 255, cv.THRESH_BINARY)
    cv.imshow("噪声图像", Gn)
    cv.imshow("二值化处理结果图像", thresh1)
    # canny 边缘检测
    binary = cv.Canny(thresh1, 100, 200)
    # 显示边缘检测的结果
    cv.imshow("Canny", binary)
    # 提取轮廓
    contours, _ = cv.findContours(thresh1, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    ## 输出轮廓数目
    print("the count of contours is  %d \n"%(len(contours)))
    # find the main island (biggest area)
    cnt = contours[0]
    max_area = cv.contourArea(cnt)

    for cont in contours:
        if cv.contourArea(cont) > max_area:
            cnt = cont
            max_area = cv.contourArea(cont)

    cv.drawContours(Gn, cnt, -1, (0, 255, 0), 3)
    cv.imshow("img", Gn)

    #
    # mask = np.zeros(Gn.shape, np.uint8)  # 生成黑背景，即全为0
    # mask = cv.drawContours(mask, cnt, -1, (255, 255, 255), -1)  # 绘制轮廓，形成掩膜
    # cv.imshow("mask", mask)  # 显示掩膜
    # result = cv.bitwise_and(Gn, mask)  # 按位与操作，得到掩膜区域
    # cv.imshow("result", result)  # 显示图像中提取掩膜区域

   # mask = cv.drawContours(Gn, cnt, -1, (0, 255, 0), 3)
 #   result = cv.bitwise_and(Gn, mask)  # 按位与操作，得到掩膜区域
 #   cv.imshow("result", result)  # 显示图像中提取掩膜区域
  #  cv.imshow("img", Gn)
    epsilon = 0.01 * cv.arcLength(cnt, True)
    print(epsilon)
    cv.waitKey()
    cv.destroyAllWindows()
    return thresh1


def black_proportion(thresh1):
    """
    :get the black proportion
    """
    x, y = thresh1.shape
    bk = 0
    wt = 0
    # 遍历二值图，为0则bk+1，否则wt+1
    for i in range(x):
        for j in range(y):
            if thresh1[i, j] == 0:
                bk += 1
            else:
                wt += 1
    rate1 = wt / (x * y)
    rate2 = bk / (x * y)
    # round()第二个值为保留几位有效小数。
    print("白色占比:", round(rate1 * 100, 2), '%')
    print("黑色占比:", round(rate2 * 100, 2), '%')
    cv.destroyAllWindows()


# 找出外接四边形, c是轮廓的坐标数组
def boundingBox(idx, c):
    if len(c) < 2:
        return None
    epsilon = 15
    while True:
        approxBox = cv.approxPolyDP(c,epsilon,True)
        #求出拟合得到的多边形的面积
        theArea = math.fabs(cv.contourArea(approxBox))
        #输出拟合信息
        print("contour idx: %d ,contour_len: %d ,epsilon: %d ,approx_len: %d ,approx_area: %s"%(idx,len(c),epsilon,len(approxBox),theArea))
        if (len(approxBox) < 4):
            return None
        #if theArea > Config.min_area:
        if theArea > 20:
            if (len(approxBox) > 4):
                # epsilon 增长一个步长值
                epsilon += 5
                continue
            else: #approx的长度为4，表明已经拟合成矩形了
                #转换成4*2的数组
                approxBox = approxBox.reshape((4, 2))
                return approxBox
        else:
            print("failed to find boundingBox,idx = %d area=%f"%(idx, theArea))
            return None


def new_method(img):
    img = cv.imread(img)  # 载入图像
    h, w = img.shape[:2]  # 获取图像的高和宽
    cv.imshow("Origin", img)  # 显示原始图像

    blured = cv.blur(img, (5, 5))  # 进行滤波去掉噪声
    cv.imshow("Blur", blured)  # 显示低通滤波后的图像

    mask = np.zeros((h + 2, w + 2), np.uint8)  # 掩码长和宽都比输入图像多两个像素点，满水填充不会超出掩码的非零边缘
    # 进行泛洪填充
    cv.floodFill(blured, mask, (w - 1, h - 1), (255, 255, 255), (2, 2, 2), (3, 3, 3), 8)
    cv.imshow("floodfill", blured)

    # 得到灰度图
    gray = cv.cvtColor(blured, cv.COLOR_BGR2GRAY)
    cv.imshow("gray", gray)

    # 定义结构元素
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (50, 50))
    # 开闭运算，先开运算去除背景噪声，再继续闭运算填充目标内的孔洞
    opened = cv.morphologyEx(gray, cv.MORPH_OPEN, kernel)
    closed = cv.morphologyEx(opened, cv.MORPH_CLOSE, kernel)
    cv.imshow("closed", closed)

    # 求二值图
    ret, binary = cv.threshold(closed, 250, 255, cv.THRESH_BINARY)
    cv.imshow("binary", binary)

    # 找到轮廓
    contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    # find the main island (biggest area)
    cnt = contours[0]
    max_area = cv.contourArea(cnt)

    for cont in contours:
        if cv.contourArea(cont) > max_area:
            cnt = cont
            max_area = cv.contourArea(cont)
    # 绘制轮廓
    cv.drawContours(img, contours, -1, (0, 0, 255), 3)
    # 绘制结果
    cv.imshow("result", img)
    cv.waitKey(0)
    cv.destroyAllWindows()
    return img


def cut_photo(img):
    img = cv.imread(img)  # 载入图像
    h, w = img.shape[:2]  # 获取图像的高和宽
    print(h,w)
    # Select ROI
    r = cv.selectROI("select the area", img)

    # Crop image
    cropped_image = img[int(r[1]):int(r[1] + r[3]),
                    int(r[0]):int(r[0] + r[2])]

    # Display cropped image
    cv.imshow("Cropped image", cropped_image)
    local_dir = str("tefe").replace(':', '_')
    if os.path.exists(local_dir) is not True:
        os.mkdir(local_dir)  # if dir is not exists, make a new dir
    curr_time = datetime.now()
    timestamp = datetime.strftime(curr_time, '%Y-%m-%d-%H-%M-%S')
    export_img_path = os.getcwd() + '/' + local_dir + '/' + timestamp + ".jpg"
    print(export_img_path)
    sleep(1)
    cv.imwrite(export_img_path, cropped_image)
    # cv.imwrite('test', cropped_image)
    cv.waitKey(0)
    # ret, thresh1 = cv.threshold(img, 135, 255, cv.THRESH_BINARY)
#    black_proportion(thresh1)
    cv.destroyAllWindows()
    # cv.imshow("thresh1", thresh1)
    return cropped_image


def crop_black_rate(image, r):
    # Crop image
    cropped_image = image[int(r[1]):int(r[1] + r[3]),
                    int(r[0]):int(r[0] + r[2])]
    # show crop imgage
    cv.imshow('cut', cropped_image)

    gray = cv.cvtColor(cropped_image, cv.COLOR_BGR2GRAY)
    Gf = cv.medianBlur(gray, 3)
    ret, thresh1 = cv.threshold(Gf, 135, 255, cv.THRESH_BINARY)
    cv.imshow("二值化处理结果图像", thresh1)
    black_proportion(thresh1)
    cv.waitKey()
    cv.destroyAllWindows()


if __name__ == '__main__':
    #
    src = cv.imread('m3pro.jpg')
    target = cv.imread('bad.jpg')
    h, w = src.shape[:2]
    print(h, w)

    # Select ROI
    area = cv.selectROI("select the area", src)
    crop_black_rate(src, area)
    crop_black_rate(target, area)
    # ocr_detect('IMG_19700101_092822.jpg')
    #new_corner_detect('IMG_19700101_092822.jpg')
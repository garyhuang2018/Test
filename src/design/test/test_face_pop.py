import datetime
import subprocess
import time

import cv2


# ADB命令模拟输入*键
def input_key():
    subprocess.run(['adb', 'shell', 'input', 'keyevent', 'STAR'])


# ADB命令获取设备屏幕截图
def take_screenshot_reference():
    subprocess.run(['adb', 'shell', 'screencap', '/sdcard/screenshot.png'])
    subprocess.run(['adb', 'pull', '/sdcard/screenshot.png', 'reference_image.png'])


# ADB命令获取设备屏幕截图
def take_screenshot():
    subprocess.run(['adb', 'shell', 'screencap', '/sdcard/screenshot.png'])
    subprocess.run(['adb', 'pull', '/sdcard/screenshot.png', 'test.png'])


# 图像比较
def compare_images(image1_path, image2_path):

    image1 = cv2.imread(image1_path)
    image2 = cv2.imread(image2_path)
    # Crop images on the x-axis
    image1_cropped = image1[300:800, :]
    image2_cropped = image2[300:800, :]
    # cv2.imshow('hso', image1_cropped)
    difference = cv2.subtract(image1_cropped, image2_cropped)
    b, g, r = cv2.split(difference)
    # cv2.waitKey()
    # cv2.destroyAllWindows()
    if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
        return True
    else:
        return False


def save_comparison_result(result):
    with open('comparison_records.txt', 'a') as file:
        file.write(result + '\n')


# Function to compare images and save the result
def compare_and_save_result(num_runs):
    for _ in range(num_runs):

        # Compare images
        if compare_images("test.png", "reference_image.png"):
            result = "截图与参考图像相同, 人脸识未弹框"
        else:
            result = "截图与参考图像不同, 人脸识别有弹框"

        # Add timestamp to the result
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_with_timestamp = f"{timestamp} - {result}"

        # Save the comparison result with timestamp
        save_comparison_result(result_with_timestamp)

        # Wait for 10 minutes
        time.sleep(600)  # 10 minutes = 600 seconds


if __name__ == "__main__":

    # Output guide for the user
    print("Before running the input_key function, take a screenshot of the reference image.")

    # Input the number of runs from the user
    num_runs = int(input("Enter the number of times you want to run the comparison and saving process: "))

    # 执行ADB命令获取截图
    take_screenshot_reference()

    # 模拟输入*键
    input_key()

    # 等待一小段时间确保输入被处理
    subprocess.run(['adb', 'shell', 'sleep', '2'])

    # 执行ADB命令获取截图
    take_screenshot()

    # Run the comparison and saving process based on the user's input
    compare_and_save_result(num_runs)

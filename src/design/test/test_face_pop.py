import datetime
import os
import subprocess
import time

import cv2


# Function to get the list of connected devices
def get_connected_devices():
    devices_output = subprocess.check_output(['adb', 'devices']).decode('utf-8').split('\n')[1:-2]
    devices = [device.split('\t')[0]for device in devices_output]
    return devices


# Create folders for each device
def create_device_folders(devices):
    for device in devices:
        device_folder = device.replace(':', '_')
        os.makedirs(device_folder, exist_ok=True)


# ADB命令模拟输入*键
def input_key(device_id):
    subprocess.run(['adb', '-s', device_id, 'shell', 'input', 'keyevent', 'STAR'])


# ADB命令获取设备屏幕截图
def take_screenshot_reference(device_id):
    device = device_id.replace(':', '_')
    screenshot_filename = "reference.png"
    subprocess.run(['adb', '-s', device_id, 'shell', 'screencap', '/sdcard/screenshot.png'])
    subprocess.run(['adb', '-s', device_id, 'pull', '/sdcard/screenshot.png', f'{device}/{screenshot_filename}'])


# ADB命令获取设备屏幕截图
def take_screenshot(device_id, timestamp):
    device = device_id.replace(':', '_')
    screenshot_filename = f"{timestamp}.png"
    subprocess.run(['adb', '-s', device_id, 'shell', 'screencap', '/sdcard/screenshot.png'])
    subprocess.run(['adb', '-s', device_id, 'pull', '/sdcard/screenshot.png', f'{device}/{screenshot_filename}'])


# 图像比较
def compare_images(device_id, image1_filename, image2_filename):
    image1_path = f"{image1_filename}"
    image2_path = f"{image2_filename}"

    image1 = cv2.imread(image1_path)
    image2 = cv2.imread(image2_path)
    # Crop images on the x-axis
    image1_cropped = image1[350:800, :]
    image2_cropped = image2[350:800, :]
    # cv2.imshow('t',image1_cropped)
    # cv2.waitKey()
    cv2.destroyAllWindows()
    difference = cv2.subtract(image1_cropped, image2_cropped)
    b, g, r = cv2.split(difference)
    if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
        return True
    else:
        return False


def save_comparison_result(result, device_id):
    device = device_id.replace(':', '_')
    with open(f'{device}/comparison_records.txt', 'a') as file:
        file.write(result + '\n')


# Function to compare images and save the result
def compare_and_save_result(num_runs, sleep_time, devices):
    for _ in range(num_runs):
        for device_id in devices:
            # Get timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            # 模拟输入*键
            input_key(device_id)
            input_key(device_id)
            # Take comparing screenshot
            take_screenshot(device_id, timestamp)

            # 等待一小段时间确保输入被处理
            subprocess.run(['adb', '-s', device_id, 'shell', 'sleep', '2'])

            device = device_id.replace(':', '_')
            # Compare images
            if compare_images(device_id, f"{device}/{timestamp}.png", f"{device}/reference.png"):
                result = f"截图与参考图像相同, {device_id} 人脸识未弹框"
            else:
                result = f"截图与参考图像不同, {device_id} 人脸识别有弹框"

            # Add timestamp to the result
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_with_timestamp = f"{timestamp} - {result}"

            # Save the comparison result with timestamp
            save_comparison_result(result_with_timestamp, device_id)

        # Wait for specified time
        time.sleep(sleep_time)


if __name__ == "__main__":
    # Output guide for the user
    print("运行前，门口机应进入按键界面，第一次截图为参考图")

    # Input the number of runs from the user
    num_runs = int(input("请输入需要验证的次数: "))

    # Input the interval time in minutes from the user
    sleep_time = int(input("输入间隔时间(分钟):")) * 60

    # Get the list of connected devices
    devices = get_connected_devices()

    # Create folders for each device
    create_device_folders(devices)

    # Execute ADB command to take a reference screenshot for each device
    for device_id in devices:
        subprocess.run(['adb', '-s', device_id, 'shell', 'input', 'keyevent', 'POUND'])
        take_screenshot_reference(device_id)

    # Run the comparison and saving process based on the user's input
    compare_and_save_result(num_runs, sleep_time, devices)

    # # Output guide for the user
    # print("运行前，门口机应进入按键界面，第一次截图为参考图")
    #
    # # Input the number of runs from the user
    # num_runs = int(input("请输入需要验证的次数: "))
    #
    # # Input the number of runs from the user
    # sleep_time = int(input("输入间隔时间(分钟):"))*60
    #
    # # # 执行ADB命令获取截图
    # take_screenshot_reference()
    # #
    # # # Run the comparison and saving process based on the user's input
    # # compare_and_save_result(num_runs, sleep_time)
    # # Get the list of connected devices
    # devices = get_connected_devices()
    #
    # # Create folders for each device
    # create_device_folders(devices)
    #
    # # Run the comparison and saving process based on the user's input
    # compare_and_save_result(num_runs, sleep_time, devices)

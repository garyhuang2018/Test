# encoding= utf-8
# __author__= gary
import os
from datetime import datetime
from time import sleep

import cv2


def tap_screen(x, y):

    os.system(f"adb shell input tap {x} {y}")


def take_photo():
    camera_id = input("Enter camera ID: ")
    times = input("Enter reboot times: ")
    wait_period = input("Enter reboot wait period: ")
    print(camera_id)
    cap = cv2.VideoCapture(int(camera_id))
    for i in range(0, int(times)):
        if cap.isOpened():
            ret, frame = cap.read()
            sleep(1)
            # 将这个文件pull到本地电脑上
            local_dir = 'camera'
            if os.path.exists(local_dir) is not True:
                os.mkdir(local_dir)  # if dir is not exists, make a new dir
            curr_time = datetime.now()
            timestamp = datetime.strftime(curr_time, '%Y-%m-%d-%H-%M-%S')
            export_img_path = os.getcwd() + '/' + local_dir + '/' + timestamp + ".jpg"
            print(export_img_path)
            sleep(1)
            cv2.imwrite(export_img_path, frame)
            cap.release()
        sleep(int(wait_period))


if __name__ == '__main__':
    take_photo()
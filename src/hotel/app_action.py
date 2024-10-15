# encoding= utf-8
# __author__= gary
import subprocess
from time import sleep
import uiautomator2 as ui


class App:
    def __init__(self):
        self.device = None
        try:
            self.device = ui.connect()
            self.device_available = True
        except Exception:
            self.device_available = False

    def get_info(self):
        return self.device.info

    def start_app(self):
        subprocess.run('adb shell am start com.gemvary.vhpsmarthome/.ui.main.LauncherActivity')

    def load_project_name(self):
        if self.device.xpath('//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_project_name"]/android.widget.ImageView[1]').exists:
            self.device.xpath('//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_project_name"]/android.widget.ImageView[1]').click()
            self.device(resourceId="com.gemvary.vhpsmarthome:id/fresh").click()


def unlock(device):
    # 亮屏
    device.unlock()
    # 等待屏幕亮起
    sleep(1)  # 等待 1 秒钟以确保屏幕完全亮起


def device_locate(device):
    try:
        device(resourceId="com.gemvary.vhpsmarthome:id/iv_menu").click()
        device(text="添加网关").click()
        device(resourceId="com.gemvary.vhpsmarthome:id/iv_icon").click()
        # device.click(100,100)
        device_available = True
    except Exception as e:
        print(e)


def delete_gateway(device):
    try:
        if device(resourceId="com.gemvary.vhpsmarthome:id/tv_name", text="蓝牙透传网关").exists(timeout=2):
            device(resourceId="com.gemvary.vhpsmarthome:id/tv_name", text="蓝牙透传网关").long_click()
            device(resourceId="com.gemvary.vhpsmarthome:id/tv_content").click()
            device(resourceId="android:id/button1").click()
    except Exception as e:
        print(e)


def get_logcat_logs():
    # 启动logcat并过滤包含"wx"的日志
    process = subprocess.Popen(['adb', 'logcat', '-s', 'wx'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    hotel_names = []
    try:
        while True:
            # 读取logcat输出
            output = process.stdout.readline()
            if output == b'' and process.poll() is not None:
                break
            if output:
                decoded_output = output.strip().decode('utf-8', errors='ignore')
                # 查找所有"hotelName"的实例
                start_index = 0
                while True:
                    start_index = decoded_output.find('"hotelName":"', start_index)
                    if start_index == -1:
                        break
                    start_index += len('"hotelName":"')
                    end_index = decoded_output.find('"', start_index)
                    if end_index != -1:
                        hotel_name = decoded_output[start_index:end_index]
                        hotel_names.append(hotel_name)
                        print(hotel_name)
                    start_index = end_index
    except KeyboardInterrupt:
        # 捕获Ctrl+C中断
        process.terminate()
        print("Logcat terminated.")


if __name__ == "__main__":
    device = ui.connect()
    print(device.info)
    unlock(device)
    # device_locate(device)
    # sleep(4)
    # delete_gateway(device)
    get_logcat_logs()
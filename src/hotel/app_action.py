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
        subprocess.run('adb shell input keyevent BACK')

    def add_gateway(self):
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/tv_gateway_name")
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/tv_gateway_name", text="添加新网关").click()

    def choose_project_name(self, hotel_name):
        self.device(resourceId="com.gemvary.vhpsmarthome:id/id_treenode_label", text=hotel_name).click()
        self.device(resourceId="com.gemvary.vhpsmarthome:id/tv_gateway_name", text="无网关").click()

    def load_rooms(self):
        self.device(resourceId="com.gemvary.vhpsmarthome:id/fresh").click()
        room_names = []
        # 使用-d参数导出logcat日志
        process = subprocess.Popen(['adb', 'logcat', '-d', '-s', 'wx'], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()  # 获取输出
        if stderr:
            print(f"Error: {stderr.decode('utf-8', errors='ignore')}")  # 错误输出

        # 解析logcat输出
        for line in stdout.decode('utf-8', errors='ignore').splitlines():
            # 查找所有"hotelName"的实例
            start_index = 0
            while True:
                start_index = line.find('"floorAndRoomNumber":"', start_index)
                if start_index == -1:
                    break
                start_index += len('"floorAndRoomNumber":"')
                end_index = line.find('"', start_index)
                if end_index != -1:
                    room_name = line[start_index:end_index]
                    room_names.append(room_name)
                start_index = end_index
        print(room_names)
        return room_names

    def load_project_name(self):
        # 点击首页
        self.click_element_if_exists('//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_home"]/android.widget.ImageView[1]')
        if self.device.xpath(
                '//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_project_name"]/android.widget.ImageView[1]').exists:
            self.device.xpath(
                '//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_project_name"]/android.widget.ImageView[1]').click()

        self.device(resourceId="com.gemvary.vhpsmarthome:id/fresh").click()
        sleep(1)
        hotel_names = []
        # 使用-d参数导出logcat日志
        process = subprocess.Popen(['adb', 'logcat', '-d', '-s', 'wx'], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()  # 获取输出
        if stderr:
            print(f"Error: {stderr.decode('utf-8', errors='ignore')}")  # 错误输出

        # 解析logcat输出
        for line in stdout.decode('utf-8', errors='ignore').splitlines():
            # 查找所有"hotelName"的实例
            start_index = 0
            while True:
                start_index = line.find('"hotelName":"', start_index)
                if start_index == -1:
                    break
                start_index += len('"hotelName":"')
                end_index = line.find('"', start_index)
                if end_index != -1:
                    hotel_name = line[start_index:end_index]
                    hotel_names.append(hotel_name)
                start_index = end_index
        print(hotel_names)
        return hotel_names

    def unlock(self):
        # 亮屏
        self.device.unlock()
        # 等待屏幕亮起
        sleep(1)  # 等待 1 秒钟以确保屏幕完全亮起

    def click_element_if_resource_exists(self, resource_Id):
        # 检查元素是否存在
        if self.device(resourceId=resource_Id):
            self.device(resourceId=resource_Id).click()
            print(f"Clicked on element with resourceId: {resource_Id}")
        else:
            print(f"Element with xpath: {resource_Id} does not exist.")

    def click_element_if_exists(self, xpath):
        # 检查元素是否存在
        if self.device.xpath(xpath).exists:
            self.device.xpath(xpath).click()
            print(f"Clicked on element with xpath: {xpath}")
        else:
            print(f"Element with xpath: {xpath} does not exist.")


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
    d = App()
    d.load_rooms()
    # d.add_gateway()
    # d.unlock()
    # print(d.load_project_name())
    # d.start_app()
    # d.load_project_name()
    # d.click_element_if_exists('//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_home"]/android.widget.ImageView[1]')
    # d.choose_project_name('蓝牙测试酒店')
    # device_locate(device)
    # sleep(4)
    # delete_gateway(device)
    # get_logcat_logs()

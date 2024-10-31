# encoding= utf-8
# __author__= gary
import re
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

    def get_text_from_resource_id(self, resourceId):
        # 根据 resourceId 获取元素
        element = self.device(resourceId=resourceId)

        # 检查元素是否存在
        if element.exists:
            # 获取并打印文本内容
            text_content = element.get_text()
            print(f'Text content: {text_content}')
            return text_content
        else:
            print('Element not found.')

    def switch_phone_wifi(self, ssid, password):
        # 打开设置页面
        self.device.shell("am start -n com.android.settings/.Settings")
        # 进入 Wi-Fi 设置页面
        self.device.shell("input keyevent 20")  # 模拟点击事件，打开 Wi-Fi 设置

    def config_gateway_wifi(self, wifi_keys):
        # (resourceId="com.gemvary.vhpsmarthome:id/edit_wifi_password").click()
        # self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/cl_gw_config_net")
        # self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/edit_wifi_password")
        self.device(resourceId="com.gemvary.vhpsmarthome:id/edit_wifi_password").send_keys(wifi_keys)
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/tv_complete")

    def get_info(self):
        return self.device.info

    def start_app(self):
        subprocess.run('adb shell am start com.gemvary.vhpsmarthome/.ui.main.LauncherActivity')
        # subprocess.run('adb shell input keyevent BACK')

    def login(self, user_name, password):
        self.device(resourceId="com.gemvary.vhpsmarthome:id/engineer_login_account").send_keys(user_name)
        self.device(resourceId="com.gemvary.vhpsmarthome:id/engineer_login_pwd").send_keys(password)
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/engineer_login")

    def add_gateway(self):
        self.unlock()
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/iv_menu")
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/tv_gateway_name")
        self.click_element_if_texts_exists("添加网关")

    def choose_project_name(self, hotel_name):
        self.device(resourceId="com.gemvary.vhpsmarthome:id/id_treenode_label", text=hotel_name).click()
        self.device(resourceId="com.gemvary.vhpsmarthome:id/tv_gateway_name", text="无网关").click()

    def get_selected_room(self):
        if self.device:
            # 使用-d参数导出logcat日志
            process = subprocess.Popen(['adb', 'logcat', '-d', '-s', 'wx'], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()  # 获取输出

            if stderr:
                print(f"Error: {stderr.decode('utf-8', errors='ignore')}")  # 错误输出
                return  # 如果有错误输出，直接返回

            log_data = stdout.decode('utf-8', errors='ignore')  # 解码输出为字符串

            # 正则表达式模式，用于匹配 roomName 的值
            pattern = r"roomName='(.*?)'"
            # 使用 re.findall() 找到所有匹配的 roomName
            room_names = re.findall(pattern, log_data)

            # 输出所有找到的 roomName
            for room_name in room_names:
                print(f"Found roomName: {room_name}")
            if len(room_names) > 0:
                return room_names[0]
            else:
                return

    def load_rooms(self):
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/iv_room_add")
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/edit_name")
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/fresh")
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/fresh").click()
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
        return room_names

    def load_project_name(self):
        #  检查弹出框
        self.click_element_if_exists("com.gemvary.vhpsmarthome:id/save")
        # 点击首页
        self.click_element_if_exists(
            '//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_home"]/android.widget.ImageView[1]')
        if self.device.xpath(
                '//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_project_name"]/android.widget.ImageView[1]').exists:
            self.device.xpath(
                '//*[@resource-id="com.gemvary.vhpsmarthome:id/ll_project_name"]/android.widget.ImageView[1]').click()
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/fresh")
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
        return hotel_names

    def unlock(self):
        if self.device:
            print('unlock')
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
            return

    def click_element_if_exists(self, xpath):
        # 检查元素是否存在
        if self.device.xpath(xpath).exists:
            self.device.xpath(xpath).click()
            print(f"Clicked on element with xpath: {xpath}")
        else:
            print(f"Element with xpath: {xpath} does not exist.")

    def click_element_if_texts_exists(self, text):
        # 检查元素是否存在
        if self.device(text=text):
            # 查找具有指定文本的所有元素
            elements = self.device(text=text)

            # 遍历并依次点击每个元素
            for index in range(len(elements)):
                # 确保元素可点击
                if elements[index].exists:
                    elements[index].click()  # 点击元素
                    print(f"点击第 {index + 1} 个元素")
                    sleep(1)  # 暂停1秒以确保操作完成
        else:
            print(f"Element with text: {text} does not exist.")

    def add_light_switchs(self):
        self.unlock()
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/iv_menu")
        self.device(text="添加设备").click()
        sleep(0.5)
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/tv_search")

    def locate_devices(self):
        self.click_element_if_texts_exists('定位')

    def swipe_up(self):
        # 滑动操作示例
        # swipe(x1, y1, x2, y2, steps)
        # x1, y1 为起始点坐标，x2, y2 为结束点坐标，steps 为滑动的步数
        self.device.swipe(300, 1000, 300, 300, steps=10)  # 从屏幕底部滑动到屏幕中间

    def swipe_down(self):
        # 获取屏幕尺寸
        width = self.device.info['displayWidth']
        height = self.device.info['displayHeight']

        # 计算滑动起始和结束坐标
        start_x = width // 2  # 在屏幕中间的 x 坐标
        start_y = height // 4  # 从屏幕的 1/4 位置开始滑动
        end_y = height * 3 // 4  # 滑动到屏幕的 3/4 位置
        print(start_y, end_y)
        # 执行向下滑动操作
        self.device.swipe(start_x, start_y, start_x, end_y, steps=10)

    def enter_light_control(self):
        # 查找包含“控制盒”文字的控件并点击
        if self.device(textContains='控制盒').exists:
            self.device(textContains='控制盒').click()
        else:
            print("未找到控件")

    def light_on_control(self, i):
        xpath = f'//*[@resource-id="{"com.gemvary.vhpsmarthome:id/recyclerView"}"]/android.view.ViewGroup[{i}]/android.view.ViewGroup[1]/android.widget.TextView[3]'
        # 查找元素
        element = self.device.xpath(xpath)
        if element.exists:
            element.click()
            print(f"点击了元素: {xpath}")
        else:
            print(f"未找到元素: {xpath}")

    def edit_light_name(self, i, text):
        xpath = f'//*[@resource-id="{"com.gemvary.vhpsmarthome:id/recyclerView"}"]/android.view.ViewGroup[{i}]/android.view.ViewGroup[1]/android.widget.ImageView[1]'
        # 查找元素
        element = self.device.xpath(xpath)
        if element.exists:
            element.click()
            self.device(resourceId="com.gemvary.vhpsmarthome:id/edit_content").clear_text()
            self.device(resourceId="com.gemvary.vhpsmarthome:id/edit_content").send_keys(text)
            print(f"点击了元素: {xpath}")
        else:
            print(f"未找到元素: {xpath}")

    def get_room_name(self):
        room_name = self.get_text_from_resource_id("com.gemvary.vhpsmarthome:id/tv_title")
        return room_name

    def get_gateway_name(self):
        element = self.device(resourceId = "com.gemvary.vhpsmarthome:id/tv_content")

        if element.exists:
            gateway_name = element.get_text()
            return gateway_name

    def click_locate(self):
        self.click_element_if_texts_exists("定位")

    def load_room_names(self):
        # 获取所有具有特定 resource-id 的元素
        elements = self.device(resourceId='com.gemvary.vhpsmarthome:id/tv_room_name')
        texts = []
        # 提取文本内容
        for element in elements:
            texts.append(element.get_text())
        print(texts)
        return texts


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
    d.unlock()
    d.config_gateway_wifi("12345678")
    # d.load_room_names()
    # d.click_element_if_texts_exists("定位")
    # print(d.get_gateway_name())
    # d.add_gateway()
    # d.get_room_name()

    # d.get_text_from_resource_id("com.gemvary.vhpsmarthome:id/tv_title")
    # d.switch_phone_wifi("TPLINKE675","12345678")

    # d.config_gateway_wifi()
    # resourceId = "com.gemvary.vhpsmarthome:id/tv_open"
    # d.light_on_control(1)
    # d.edit_light_name(1, "洗手间灯")

    # d.swipe_down()
    # d.login("17881426510","888888")
    # print(d.get_selected_room())
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

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
        if self.device_available:
            self.click_element_if_texts_exists("蓝牙透传网关")
            self.click_element_if_texts_exists("网关配网")
            element = self.device(resourceId="com.gemvary.vhpsmarthome:id/edit_wifi_password")
            if element:
                element.send_keys(wifi_keys)
            else:
                return
            self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/tv_complete")
            return  True

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
        if self.device_available:
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
        if self.device_available:
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
        self.click_element_if_texts_exists("添加设备")
        # self.device(text="添加设备").click()
        sleep(0.5)
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/tv_search")

    def locate_devices(self):
        self.click_element_if_texts_exists('定位')

    def locate_device_according_to_device_name(self, index):
        # 根据文本找到目标元素
        target_text = "定位"
        target_element = d.device(text=target_text)
        text_list = []
        if target_element.exists:
            # 获取目标元素的 xpath
            target_xpath = f'//*[@text="{target_text}"]'
            # 通过 xpath 找到目标元素的父元素
            parent_xpath = f'{target_xpath}/..'
            # 直接使用完整 xpath 查找父元素下的其他文本元素
            other_text_elements_xpath = f'{parent_xpath}//*[@text!=""]'
            other_text_elements = d.device.xpath(other_text_elements_xpath).all()

            # 遍历并筛选出包含“超级设备”文本的元素并输出
            for element in other_text_elements:
                # 过滤掉目标元素本身，并检查元素文本是否包含“超级设备”
                if element.text != target_text and "超级设备" in element.text:
                    text_list.append(element.text)
            print(text_list[index])
        else:
            print("未找到目标文本元素")

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
        if self.device_available:
            # 获取所有具有特定 resource-id 的元素
            elements = self.device(resourceId='com.gemvary.vhpsmarthome:id/tv_room_name')
            texts = []
            # 提取文本内容
            for element in elements:
                texts.append(element.get_text())
            print(texts)
            return texts

    def get_log_data(self, pattern):
        if self.device:
            # 使用-d参数导出logcat日志
            process = subprocess.Popen(['adb', 'logcat', '-d', '-s', 'wx'], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()  # 获取输出

            if stderr:
                print(f"Error: {stderr.decode('utf-8', errors='ignore')}")  # 错误输出
                return []  # 如果有错误输出，返回空列表

            log_data = stdout.decode('utf-8', errors='ignore')  # 解码输出为字符串

            # 使用 re.findall() 找到所有匹配的内容
            matches = re.findall(pattern, log_data)

            # 输出所有找到的匹配内容
            for match in matches:
                print(f"Found match: {match}")
            return matches
        return []

    def get_gateway_ip_address(self):
        # 正则表达式模式，用于匹配 ip 的值
        pattern = r"ip\s*=\s*([\d:]+)"
        ip_addresses = self.get_log_data(pattern)
        if ip_addresses:
            return ip_addresses[0]
        return

    def click_back_icon(self):
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/iv_back")

    def get_app_version(self):
        # 获取应用信息
        package_name = 'com.gemvary.vhpsmarthome'  # 替换为目标应用的包名
        app_info = self.device.app_info(package_name)
        version = app_info['versionName']
        # 打印应用版本信息
        print(f"应用版本: {app_info['versionName']}")
        return version

    def apply_template(self, template_name,  device_name):
        self.click_element_if_resource_exists("com.gemvary.vhpsmarthome:id/iv_menu")
        self.device(text="模 板").click()
        self.device.xpath('//android.widget.RelativeLayout/android.view.ViewGroup[1]/android.widget.ImageView[2]').click()
        self.swipe_and_click_text(template_name)
        self.device(resourceId="android:id/button1").click()
        sleep(1)
        self.click_back_icon()
        # self.add_light_switchs()
        # self.device(text="添加设备").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/iv_show_repeat").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/tv_search").click()
        # self.device.xpath(
        #     '//*[@resource-id="com.gemvary.vhpsmarthome:id/recyclerView"]/android.view.ViewGroup[2]/android.widget.Button[1]').click()
        # self.device.xpath(
        #     '//*[@resource-id="com.gemvary.vhpsmarthome:id/recyclerView"]/android.view.ViewGroup[2]/android.widget.Button[2]').click()
        # self.device.xpath(
        #     '//*[@resource-id="com.gemvary.vhpsmarthome:id/recyclerView"]/android.view.ViewGroup[1]/android.widget.Button[1]').click()
        # self.device.xpath(
        #     '//*[@resource-id="com.gemvary.vhpsmarthome:id/recyclerView"]/android.view.ViewGroup[1]/android.widget.Button[1]').click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/btn_add", text="加入").click()
        # self.device(resourceId="android:id/text1", text=series_name).click()
        # self.device(resourceId="android:id/text1", text=device_name).click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/btn_next").click()
        # self.device.xpath(
        #     '//*[@resource-id="com.gemvary.vhpsmarthome:id/recyclerView"]/android.view.ViewGroup[2]/android.widget.Button[3]').click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/iv_replace_self.device_add").click()
        # self.device(text="6场景2继电器-20A").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/tv_replace").click()
        # self.device(resourceId="android:id/button1").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/btn_replace").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/iv_replace_self.device_add").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/cl").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/tv_replace").click()
        # self.device(resourceId="android:id/button1").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/iv_back").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/iv_back").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/iv_menu").click()
        # self.device(text="重置设备配置").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/tv_confirm").click()
        # self.device.xpath('//android.widget.FrameLayout').click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/iv_menu").click()
        # self.device(text="自动配置设备").click()
        # self.device(resourceId="com.gemvary.vhpsmarthome:id/tv_confirm").click()

    def add_and_replace_devices(self, series_name, device_name):
        self.add_light_switchs()
        sleep(2)  # 等待设备上报
        self.click_element_if_texts_exists("加入")
        self.click_element_if_texts_exists(series_name)
        self.swipe_and_click_text(device_name)
        self.click_element_if_texts_exists("下一步")
        # self.click_element_if_texts_exists("添加")
        # self.click_element_if_texts_exists("完成")

    def swipe_and_click_text(self, target_text, max_swipes=3, swipe_interval=1):
        """
        一边下滑屏幕一边匹配文本，找到匹配文本后点击
        :param device: 已连接的设备对象
        :param target_text: 要匹配的文本
        :param max_swipes: 最大滑动次数，避免无限滑动，默认为 10
        :param swipe_interval: 每次滑动后的等待时间（秒），默认为 1
        :return: 如果找到并点击返回 True，否则返回 False
        """
        swipe_count = 0
        while swipe_count < max_swipes:
            # 查找匹配文本的元素
            element = self.device(text=target_text)
            if element.exists:
                # 找到匹配元素，点击它
                element.click()
                print(f"找到文本 '{target_text}' 并点击")
                return True
            else:
                # 未找到匹配元素，向下滑动屏幕
                self.swipe_up()
                swipe_count += 1
                print(f"未找到文本，进行第 {swipe_count} 次滑动")
                sleep(swipe_interval)  # 等待指定时间，让页面加载

        print(f"滑动 {max_swipes} 次后仍未找到文本 '{target_text}'")
        return False


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
    d.locate_device_according_to_device_name(1)
    # d.start_app()
    # d.swipe_and_click_text("好")
    # d.apply_template("好", "GP系列")
    # d.add_and_replace_devices("GP系列", "4场景1窗帘")
    # d.click_element_if_texts_exists("添加")
    # d.click_element_if_texts_exists("完成")
    try:
        # 获取屏幕尺寸
        width, height = d.device.window_size()

        # 计算屏幕中间的坐标
        middle_x = width // 2
        middle_y = height // 2

        # 定义滑动的起始点和结束点
        start_x = middle_x
        start_y = middle_y
        end_x = middle_x
        end_y = int(middle_y * 0.2)  # 向上滑动到屏幕上方 20% 的位置

        # 执行滑动操作
        d.device.swipe(start_x, start_y, end_x, end_y, duration=0.3)  # 滑动持续时间为 0.3 秒

        # 等待一段时间以便观察效果
        sleep(3)

    except Exception as e:
        print(f"An error occurred: {e}")

    # d(text="模 板").click()
    # d.add_light_switchs()
    # d.add_light_switchs()
    # d.swipe_up()
    # d.click_element_if_texts_exists("加入")
    # d.device.screenshot("1.png")

    # print(d.device(resourceId="com.gemvary.vhpsmarthome:id/tv_device_id").get_text())
    # d.device.xpath('//*[@resource-id="android:id/list"]/android.widget.LinearLayout[1]/android.widget.RelativeLayout[1]/android.widget.TableLayout[1]').set_text("F5111111217A0E")
    # d.device.screenshot("1.png")

    # print(d.device(resourceId="com.gemvary.vhpsmarthome:id/tv_device_id").get_text())
    # 获取应用信息
    # package_name = 'com.gemvary.vhpsmarthome'  # 替换为目标应用的包名
    # app_info = d.device.app_info(package_name)
    #
    # # 打印应用版本信息
    # print(f"应用版本: {app_info['versionName']}")
    # d.unlock()
    # d.add_light_switchs()
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

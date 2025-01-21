# encoding= utf-8
# __author__= gary
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


class UpgradeVdp:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def login(self, browser):
        if self.username is None or self.password is None:
            print("账号或密码错误")
            return

        try:
            # 等待用户名输入框加载出来
            username = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='用户名']"))
            )
            password = browser.find_element(By.XPATH, "//input[@placeholder='密码']")
            login_btn = browser.find_element(By.XPATH, "//button[@type='button']")

            # 输入账号密码
            username.send_keys(self.username)
            password.send_keys(self.password)

            # 点击登录
            login_btn.click()

            # 等待页面加载完成
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入项目名称']"))
            )

            browser.set_window_size(1936, 1056)

            # 输入项目名称
            project_name_input = browser.find_element(By.XPATH, "//input[@placeholder='请输入项目名称']")
            project_name_input.send_keys("蓝牙酒店")

            # 点击搜索按钮
            search_btn = browser.find_element(By.CSS_SELECTOR, ".search span")
            search_btn.click()

            sleep(1)

            # 点击第一个项目
            browser.find_element(By.CSS_SELECTOR, ".item-btns-wrap > span:nth-child(1)").click()

            sleep(1)

            # 点击"今日房态"
            browser.find_element(By.LINK_TEXT, "今日房态").click()

            sleep(1)

            # 鼠标悬停到"授权记录"链接
            element = browser.find_element(By.LINK_TEXT, "授权记录")
            actions = ActionChains(browser)
            actions.move_to_element(element).perform()

            # 点击第22个设备列表项
            browser.find_element(By.CSS_SELECTOR, ".list-item:nth-child(8) .device-list").click()

            # # 18 | click | id=tab-light |
            # browser.find_element(By.ID, "tab-light").click()
            # # 19 | click | css=#pane-light .wrap:nth-child(1) .el-switch__core |
            # browser.find_element(By.CSS_SELECTOR, "#pane-light .wrap:nth-child(1) .el-switch__core").click()
            # sleep(3)
            # # 23 | click | css=#pane-light .wrap:nth-child(1) .el-switch__core |
            # browser.find_element(By.CSS_SELECTOR, "#pane-light .wrap:nth-child(1) .el-switch__core").click()
            # 点击窗帘开关按钮
            browser.find_element(By.ID, "tab-curtains").click()
            browser.find_element(By.CSS_SELECTOR, "#pane-curtains .el-switch__core").click()

        except Exception as e:
            print(f"错误发生: {e}")
            print("跳过此操作，继续执行下一个...")


def run_script(username, password, interval, repetitions, headless=True):
    for i in range(repetitions):
        print(f"执行第 {i+1} 次操作...")

        # 指定 Firefox 浏览器的路径（修改为实际的路径）
        firefox_binary_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"  # Windows 示例
        # firefox_binary_path = "/usr/bin/firefox"  # Linux 示例
        # firefox_binary_path = "/Applications/Firefox.app/Contents/MacOS/firefox"  # macOS 示例

        options = Options()
        options.binary_location = firefox_binary_path
        options.headless = headless  # 设置是否隐藏浏览器窗口

        # 每次操作前重新启动浏览器实例
        browser = webdriver.Firefox(options=options)

        try:
            url = 'http://hotel.gemvary.cn:8090/#/login'  # 替换为实际的上传页面 URL
            browser.get(url)

            # 实例化 UpgradeVdp 类
            upgradeVdp = UpgradeVdp(username, password)

            # 执行登录操作
            upgradeVdp.login(browser)

            # 执行完一次后等待指定的间隔时间
            print(f"等待 {interval} 秒后执行下一次操作...")
            sleep(interval)

        finally:
            # 每次操作后关闭浏览器
            browser.quit()


if __name__ == '__main__':
    # 获取用户输入的参数
    username = '13925716872'
    password = '888888'
    interval = int(input("请输入每次操作间隔时间（秒）: "))
    repetitions = int(input("请输入执行次数: "))
    headless = input("是否隐藏浏览器窗口? (y/n): ").strip().lower() == 'y'

    # 执行脚本
    run_script(username, password, interval, repetitions, headless)

# encoding= utf-8
# __author__= gary
import datetime
from time import sleep

from selenium import webdriver


class UpgradeVdp:
    def __init__(self, browser=None, username=None, password=None, file=None):
        self.username = username
        self.password = password
        self.browser = browser
        self.file = file

    def login(self):
        if self.username is None or self.password is None:
            print("账号或密码错误")
        username = self.browser.find_element_by_xpath("//input[@placeholder='用户名']")
        password = self.browser.find_element_by_xpath("//input[@placeholder='密码']")
        login_btn = self.browser.find_element_by_xpath("//button[@type='button']")

        # 输入账号密码
        username.send_keys(self.username)
        password.send_keys(self.password)
        # 点击登录
        login_btn.click()
        # 等待2秒
        sleep(2)

    def upload(self, upload_time=90):
        if self.file is not None or self.file != '':
            # 切换到智能物联菜单
            self.browser.find_element_by_xpath("//li[text()=' 智能物联 ']").click()
            # 上传升级文件
            # 切换升级文件管理
            self.browser.find_element_by_xpath("//span[text()=' 升级文件管理 ']").click()
            sleep(2)
            # 上传文件
            self.browser.find_element_by_xpath("//span[text()=' 上传文件']").click()
            sleep(2)
            self.browser.find_element_by_xpath("//input[@type='file']").send_keys(self.file)
            # 设置上传时间休眠时间
            sleep(2)
            # 点击确定上传 上传时间可以设置长一点
            self.browser.find_element_by_xpath(
                "//*[@id='app']/div/div[2]/main/div[2]/div/div/div[4]/div/div[2]/div[2]/button[2]").click()
            sleep(upload_time)

    def upgrade(self):
        # 切换到智能物联菜单
        self.browser.find_element_by_xpath("//li[text()=' 智能物联 ']").click()
        # 切换升级文件管理
        self.browser.find_element_by_xpath("//span[text()=' 升级信息配置 ']").click()
        sleep(2)
        # 点击添加
        self.browser.find_element_by_xpath("//span[text()=' 添加 ']").click()
        sleep(2)
        # 选择目标文件
        self.browser.find_element_by_xpath(
            "//*[@id='app']/div/div[2]/main/div[2]/div/div[2]/form/div[1]/div[1]/div[1]/div/div/div/input").click()
        sleep(2)
        # 选择第一个文件
        self.browser.find_element_by_xpath("/html/body/div[2]/div[1]/div[1]/ul/li[1]/span").click()
        sleep(2)

        # 设置时间
        now_day = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        after_day = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        print(now_day)
        print(after_day)

        # 设置开始时间
        self.browser.find_element_by_xpath(
            "/html/body/div[1]/div/div[2]/main/div[2]/div/div[2]/form/div[1]/div[2]/div[5]/div/div/input[1]").send_keys(now_day)
        # 点击确定
        # self.browser.find_element_by_xpath("/html/body/div[3]/div[2]/button[2]").click()
        sleep(2)

        # 设置结束时间
        self.browser.find_element_by_xpath(
            "/html/body/div[1]/div/div[2]/main/div[2]/div/div[2]/form/div[1]/div[2]/div[5]/div/div/input[2]").send_keys(after_day)
        # sleep(1)
        # self.browser.find_element_by_xpath("/html/body/div[4]/div[2]/button[2]").click()
        sleep(2)

        # 点击保存
        self.browser.find_element_by_xpath(
            "//*[@id='app']/div/div[2]/main/div[2]/div/div[2]/form/div[2]/div/button").click()
        self.browser.find_element_by_xpath(
            "//*[@id='app']/div/div[2]/main/div[2]/div/div[2]/form/div[2]/div/button").click()
        sleep(5)


if __name__ == '__main__':
    # 创建 Chrome 浏览器实例
    browser = webdriver.Firefox()

    # 打开目标网站
    url = 'http://192.192.99.101:8080/'  # 替换为实际的上传页面 URL
    browser.get(url)
    upgradeVdp = UpgradeVdp(browser,'15211222211','888888', r"D:\6_测试工具\本地OTA\ota_rk3288_outdoor-P3_20240118.zip")
    upgradeVdp.login()
    upgradeVdp.upload()
    upgradeVdp.upgrade()
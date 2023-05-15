# encoding= utf-8
# __author__= gary
import telnetlib
import time

import openpyxl


def get_ip_address():
    try:
        load_from_excel = input("Do you want to load IP addresses from an Excel file? (y/n): ")
        if load_from_excel.lower() == 'y':
            # Load the IP addresses from the Excel file
            wb = openpyxl.load_workbook('ip_addresses.xlsx')
            ws = wb.active
            ip_addresses = [cell.value for cell in ws['A'] if cell.value is not None]  # Add check for non-empty cells
            if not ip_addresses:
                print("Error: No IP addresses found in Excel file.")
            else:
                return ip_addresses
    except FileNotFoundError as e:
        print(f"Error: {e}. Please make sure that ip_addresses.xlsx exists and try again.")


class TelnetClient(object):

    def __init__(self, *args, **kwargs):
        # 获取 IP 用户名 密码
        self.ip = kwargs.pop("ip")
        self.username = kwargs.pop("username")
        self.password = kwargs.pop("password")
        self.tn = telnetlib.Telnet()

    def login(self):
        try:
            self.tn.open(host=self.ip, port=23)
            self.tn.set_debuglevel(2)
            print(f"telnet {self.ip} ")
        except Exception as e:
            print(e)
            return False
        # 等待login出现后输入用户名，最多等待5秒
        # 输入登录用户名
        print(f"login: {self.username} ")
        self.tn.read_until(b'login: ')
        self.tn.read_until(b'Username:', timeout=2)
        self.tn.write(self.username.encode('ascii') + b'\n')
        # 等待Password出现后输入用户名，最多等待5秒
        print(f"password: {self.password} ")
        self.tn.read_until(b'Password:', timeout=2)
        self.tn.write(self.password.encode('ascii') + b'\n')
        # 延时两秒再收取返回结果，给服务端足够响应时间
        time.sleep(2)
        # 获取登录结果
        # read_very_eager()获取到的是的是上次获取之后本次获取之前的所有输出
        command_result = self.tn.read_very_eager().decode('UTF-8')
        if "error" not in command_result:
            print(f"{self.ip}  登录成功")
            return True
        else:
            print(f"{self.ip}  登录失败，用户名或密码错误")
            return False

    def execute_command(self, command):
        try:
            if command == "reboot":
                print('reboot')
                self.tn.write(command.encode('UTF-8') + b'\n')
                return
            else:
                self.tn.write(command.encode('UTF-8') + b'\n')
            time.sleep(2)
            # 获取命令结果
            command_result = self.tn.read_very_eager().decode('UTF-8')
            return command_result
        except Exception as e:
            print(e)

    def logout(self):
        self.tn.write(b"exit\n")


if __name__ == '__main__':
    ip_address_list = get_ip_address()
    num_rounds = int(input("Enter the number of rounds to run: "))
    r = 0
    while r < num_rounds:
        for ip in ip_address_list:
            tn = TelnetClient(ip=f"{ip}", username="root", password="gemvary")
            tn.login()
            tn.execute_command('reboot')
            time.sleep(5)
            tn.logout()
            print('reboot ')
        if r == (num_rounds-1):
            reboot_again = input("Do you want to retest? (y/n): ")
            if reboot_again.lower() == 'y':
                r = -1
        r = r + 1
import subprocess
import re
import time


def get_meminfo():
    result = subprocess.check_output(['adb', 'shell', 'dumpsys', 'meminfo'])
    result = result.decode('utf-8')
    return result


def parse_meminfo(meminfo_output):
    meminfo = {}
    for line in meminfo_output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)  # 限制在第一个冒号处拆分
            meminfo[key.strip()] = value.strip()

    return meminfo


def monitor_memory(interval=5):
    while True:
        meminfo_output = get_meminfo()
        meminfo = parse_meminfo(meminfo_output)

        # 输出内存信息
        print("RAM Usage (MB):")
        print("Total RAM:", meminfo.get("Total RAM"))
        print("Free RAM:", meminfo.get("Free RAM"))
        print("Used RAM:", meminfo.get("Used RAM"))
        print("\n")

        time.sleep(interval)


if __name__ == "__main__":
    monitor_memory()

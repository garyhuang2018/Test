# encoding= utf-8
# __author__= gary

import os
import time
from smb.SMBConnection import SMBConnection
import subprocess

# SMB连接配置
server_ip = "192.192.0.118"
share_name = "提测中转站"
username = "gary.huang@gemvary.com"  # 替换为你的用户名
password = "gemvary1510"  # 替换为你的密码
domain = ""  # 如果有域，填写域名

# 目标路径
remote_path = r"智能家居产品部\Android\手机APP\蓝牙配置宝\20250210"

# 本地保存路径
local_dir = "downloaded_apps"
if not os.path.exists(local_dir):
    os.makedirs(local_dir)

# 连接SMB服务器
conn = SMBConnection(username, password, "client_machine", server_ip, domain=domain, use_ntlm_v2=True)
if not conn.connect(server_ip, 139):
    print("Failed to connect to SMB server")
    exit(1)

# 获取远程路径下的文件列表
file_list = conn.listPath(share_name, remote_path)
apk_files = [file.filename for file in file_list if file.filename.endswith(".apk")]

if not apk_files:
    print("No APK files found in the remote path")
    exit(1)

# 找到最新的APK文件（按修改时间排序）
apk_files.sort(key=lambda x: conn.getAttributes(share_name, os.path.join(remote_path, x)).last_write_time, reverse=True)
latest_apk = apk_files[0]

# 下载最新的APK文件
local_apk_path = os.path.join(local_dir, latest_apk)
with open(local_apk_path, "wb") as f:
    conn.retrieveFile(share_name, os.path.join(remote_path, latest_apk), f)

print(f"Downloaded latest APK: {latest_apk}")

# 断开SMB连接
conn.close()


# 通过ADB安装APK到手机
def install_apk(apk_path):
    try:
        subprocess.run(["adb", "install", "-r", apk_path], check=True)
        print(f"Successfully installed {apk_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install APK: {e}")

# 安装APK
install_apk(local_apk_path)
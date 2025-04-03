# encoding= utf-8
# __author__= gary
import os
import shutil
import ctypes
import sys


def get_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    else:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, __file__, None, 1)
        return False


def clean_folder(path):
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    pass
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    shutil.rmtree(dir_path)
                except Exception as e:
                    pass
        print(f"已清理: {path}")
    except Exception as e:
        print(f"清理失败 {path}: {str(e)}")


def main():
    if not get_admin():
        return

    targets = [
        os.environ.get('TEMP'),
        r'C:\Windows\Temp',
        r'C:\Windows\Prefetch',
        r'C:\Windows\SoftwareDistribution\Download',
        os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
        os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache')
    ]

    print("开始清理C盘空间...")
    for target in targets:
        if target and os.path.exists(target):
            clean_folder(target)

    try:
        os.system('dism /online /Cleanup-Image /StartComponentCleanup /ResetBase')
        print("已清理系统更新缓存")
    except:
        pass

    print("\n清理完成！建议重启计算机使所有更改生效。")


if __name__ == "__main__":
    main()
    input("按回车键退出...")
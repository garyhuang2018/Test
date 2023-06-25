import pyautogui
import time

# Locate the image on the screen
image_path = 'D:/downloads/reboot.png'
position = pyautogui.locateOnScreen(image_path)
confirm_path = 'C:/Users/garyh/Desktop/confirm.jpg'

# Click on the element 500 times with a 40s wait period between each click
for i in range(500):
    # Click on the element
    print(position)
    pyautogui.click(position)
    time.sleep(1)
    postion_con = pyautogui.locateOnScreen(confirm_path)
    print(postion_con)
    pyautogui.click(postion_con)
    # Wait for 40 seconds
    time.sleep(40)
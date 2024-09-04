from uiautomator2 import Device
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from uiautomator2 import Device
import cv2
import numpy as np
import matplotlib.pyplot as plt


def capture_and_crop_icon(device_serial=None, crop_size=100):
    """
    Capture a screenshot, let the user click the icon center, and automatically crop around it.

    :param device_serial: The serial number of the Android device.
    :param crop_size: Size of the square crop around the clicked point.
    :return: Path to the saved cropped icon image.
    """
    d = Device(device_serial)

    # Capture screenshot
    screenshot = d.screenshot(format='opencv')

    # Display the screenshot
    plt.imshow(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
    plt.title("Click on the center of the '+' icon")

    # Let the user click on the icon center
    icon_center = plt.ginput(1, timeout=-1)[0]
    plt.close()

    # Convert coordinates to integers
    center_x, center_y = map(int, icon_center)

    # Calculate crop boundaries
    half_size = crop_size // 2
    left = max(center_x - half_size, 0)
    top = max(center_y - half_size, 0)
    right = min(center_x + half_size, screenshot.shape[1])
    bottom = min(center_y + half_size, screenshot.shape[0])

    # Crop the image
    cropped_icon = screenshot[top:bottom, left:right]

    # Save the cropped icon
    icon_path = 'cropped_plus_icon.png'
    cv2.imwrite(icon_path, cropped_icon)

    print(f"Cropped icon saved as {icon_path}")
    return icon_path, (center_x, center_y)


def click_add_icon_android(device_serial=None, icon_path=None, icon_center=None):
    """
    Function to find and click the '+' icon in an Android application interface using image recognition.

    :param device_serial: The serial number of the Android device.
    :param icon_path: Path to the '+' icon image file.
    :param icon_center: The center coordinates of the icon in the original screenshot.
    """
    d = Device(device_serial)

    try:
        # Take a screenshot
        screenshot = d.screenshot(format='opencv')

        # Load the icon template
        icon_template = cv2.imread(icon_path, 0)

        if icon_template is None:
            raise FileNotFoundError(f"Icon template not found at {icon_path}")

        # Convert screenshot to grayscale
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        # Perform template matching
        result = cv2.matchTemplate(gray_screenshot, icon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # If the match is good enough, click on the icon
        if max_val > 0.8:  # Adjust this threshold as needed
            d.click(icon_center[0], icon_center[1])
            print(f"Successfully clicked the '+' icon at {icon_center}.")
        else:
            print("Could not find the '+' icon. Make sure you're on the correct screen.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


# Usage example
if __name__ == "__main__":
    device_serial = None  # Replace with your device serial if needed

    # Capture screenshot and let user click the icon center
    icon_path, icon_center = capture_and_crop_icon(device_serial)

    # Use the cropped icon for automation
    click_add_icon_android(device_serial, icon_path, icon_center)
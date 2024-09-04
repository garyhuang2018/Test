from uiautomator2 import Device
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


def capture_and_crop_icon(device_serial=None):
    """
    Capture a screenshot, let the user crop the icon, and save it.

    :param device_serial: The serial number of the Android device.
    :return: Path to the saved cropped icon image.
    """
    d = Device(device_serial)

    # Capture screenshot
    screenshot = d.screenshot(format='opencv')

    # Display the screenshot
    plt.imshow(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
    plt.title("Select the area around the '+' icon")

    # Let the user crop the image
    crop_coords = plt.ginput(2, timeout=-1)
    plt.close()

    if len(crop_coords) != 2:
        raise ValueError("You must select exactly two points to define the crop area.")

    # Convert coordinates to integers
    x1, y1 = map(int, crop_coords[0])
    x2, y2 = map(int, crop_coords[1])

    # Crop the image
    cropped_icon = screenshot[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)]

    # Save the cropped icon
    icon_path = 'cropped_plus_icon.png'
    cv2.imwrite(icon_path, cropped_icon)

    print(f"Cropped icon saved as {icon_path}")
    return icon_path


def click_add_icon_android(device_serial=None, icon_path=None):
    """
    Function to find and click the '+' icon in an Android application interface using image recognition.

    :param device_serial: The serial number of the Android device.
    :param icon_path: Path to the '+' icon image file.
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
            icon_center = (
                max_loc[0] + icon_template.shape[1] // 2,
                max_loc[1] + icon_template.shape[0] // 2
            )
            d.click(icon_center[0], icon_center[1])
            print("Successfully clicked the '+' icon.")
        else:
            print("Could not find the '+' icon. Make sure you're on the correct screen.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


# Usage example
if __name__ == "__main__":
    device_serial = None  # Replace with your device serial if needed

    # Capture screenshot and let user crop the icon
    icon_path = capture_and_crop_icon(device_serial)

    # Use the cropped icon for automation
    click_add_icon_android(device_serial, icon_path)
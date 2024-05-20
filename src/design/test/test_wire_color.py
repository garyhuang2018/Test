import sys

import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QFileDialog
# import tkinter as tk
# from tkinter import filedialog, messagebox, Label, Toplevel
# from PIL import Image, ImageTk
import pandas as pd


def detect_wire_colors(image):
    color_ranges = [
        ((0, 100, 100), (10, 255, 255), "红"),
        ((160, 100, 100), (180, 255, 255), "红"),
        ((0, 0, 0), (90, 90, 90), "黑色"),
        ((110, 50, 50), (130, 255, 255), "蓝色"),
        ((20, 100, 100), (30, 255, 255), "黄色"),
        ((0, 0, 231), (180, 30, 255), "白"),
        ((85, 100, 100), (100, 255, 255), "蓝色")
    ]

    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    detected_colors = []

    for (lower, upper, color_name) in color_ranges:
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        mask = cv2.inRange(hsv_image, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:
                    if color_name not in [color for color, _ in detected_colors]:
                        detected_colors.append((color_name, contour))

    # Sort contours by x coordinate
    detected_colors.sort(key=lambda x: cv2.boundingRect(x[1])[0])

    for color, contour in detected_colors:
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.putText(image, color, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.drawContours(image, [contour], -1, (0, 255, 0), 2)  # Draw contours in green

    # cv2.imshow("Contours", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return [color for color, _ in detected_colors]

def select_image():
    app = QApplication(sys.argv)  # Create an instance of QApplication
    file_path, _ = QFileDialog.getOpenFileName(None, "选择需要识别线序的图像", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
    app.quit()  # Close the QApplication after the file dialog is closed
    return file_path

# def create_gui(image_path, colors):
#     root = tk.Tk()
#     root.title("线序颜色测试结果")
#
#     # Load and display the image
#     img = Image.open(image_path)
#     img = img.resize((500, 500))  # Resize image
#     img_tk = ImageTk.PhotoImage(img)
#     img_label = Label(root, image=img_tk)
#     img_label.image = img_tk
#     img_label.pack(side="left")
#
#     # Display the results
#     results_text = "\n".join(colors)
#     results_label = Label(root, text=results_text, justify="left", padx=10)
#     results_label.pack(side="right")
#
#     root.mainloop()

def export_results_to_excel(results):
    df = pd.DataFrame(results, columns=['Image Path', 'Detected Colors'])
    df.to_excel('wire_color_detection_result.xlsx', index=False)


if __name__ == "__main__":
    image_path = select_image()
    if image_path:
        image = cv2.imread(image_path)
        if image is not None:
            colors = detect_wire_colors(image)
            if colors:
                print("Detected wire colors (from left to right):")
                for color in colors:
                    print(color)
                results = [{'Image Path': image_path, 'Detected Colors': ', '.join(colors)}]
                export_results_to_excel(results)
                # create_gui(image_path, colors)
            else:
                print("No wire colors detected.")
        else:
            print("Failed to load image.")
    else:
        print("No image selected.")


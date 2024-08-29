import cv2
import time
import os


def get_camera():
    cameras = []
    for i in range(10):  # Check for up to 10 cameras
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras.append(i)
            cap.release()

    if len(cameras) == 0:
        print("No cameras found.")
        exit()
    elif len(cameras) == 1:
        return cameras[0]
    else:
        print("Available cameras:")
        for i, cam in enumerate(cameras):
            print(f"{i + 1}. Camera {cam}")
        choice = int(input("Choose a camera (enter the number): ")) - 1
        return cameras[choice]


camera_index = get_camera()
cap = cv2.VideoCapture(camera_index)

local_dir = "output"
if os.path.exists(local_dir) is not True:
    os.mkdir(local_dir)  # if dir is not exists, make a new dir

# Get the current working directory
current_dir = os.getcwd()

# Define the output file path
export_img_path = os.getcwd()

# Ensure the directory exists
if not os.path.exists(current_dir):
    print(f"Error: Directory {current_dir} does not exist.")
    exit()

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
print(export_img_path)
out = cv2.VideoWriter("output.avi", fourcc, 20.0, (640, 480))

# if not out.isOpened():
#     print("Error: VideoWriter not opened")
#     cap.release()
#     cv2.destroyAllWindows()
#     exit()

# Start the stopwatch
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    milliseconds = int((elapsed_time % 1) * 1000)
    elapsed_time_str = f"{elapsed_time_str}.{milliseconds:03d}"

    # Put the stopwatch on the frame
    cv2.putText(frame, elapsed_time_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Display the frame
    cv2.imshow('Video', frame)

    # Write the frame to the output file
    out.write(frame)

    # Break the loop on 'Enter' key press
    if cv2.waitKey(1) & 0xFF == 13:  # 13 is the Enter key
        break

# Release everything when done
cap.release()
cv2.destroyAllWindows()
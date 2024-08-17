import cv2
import time

# Initialize the video capture object
cap = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

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
out.release()
cv2.destroyAllWindows()
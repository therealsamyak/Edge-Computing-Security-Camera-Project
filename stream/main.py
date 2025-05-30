import cv2

# http://webcam01.ecn.purdue.edu/mjpg/video.mjpg
# http://honjin1.miemasu.net/nphMotionJpeg?Resolution=640x480&Quality=Standard
# http://67.53.46.161:65123/mjpg/video.mjpg
url = "http://192.168.137.138/mjpg/video.mjpg"

cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Could not open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Display the frame
    cv2.imshow('Camera', frame)

    # Exit on ESC key
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
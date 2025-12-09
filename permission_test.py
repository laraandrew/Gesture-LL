import cv2

print("Opening camera from:", __file__)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not opened")
else:
    print("Camera opened successfully")
cap.release()

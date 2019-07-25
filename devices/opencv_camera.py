import cv2

cap = cv2.VideoCapture(0)
cap.open(0)
print(cap.isOpened())
print(cap)

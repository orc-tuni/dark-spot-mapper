# If you get the following error on Windows
# "ImportError: DLL load failed: The specified module could not be found."
# Please install Visual C++ redistributable from
# https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads

import cv2

print(cv2.getBuildInformation())

cap = cv2.VideoCapture(0)
cap.open(0)
print(cap.isOpened())
print(cap)

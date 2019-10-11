# If you get the following error on Windows
# "ImportError: DLL load failed: The specified module could not be found."
# Please install Visual C++ redistributable from
# https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads

import enum

import cv2
import numpy as np

from devices import camera


@enum.unique
class VideoCaptureProperties(enum.IntEnum):
    """OpenCV VideoCaptureProperties

    Specified at
    https://docs.opencv.org/4.1.0/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
    """
    POS_MSEC = cv2.CAP_PROP_POS_MSEC
    POS_FRAMES = cv2.CAP_PROP_POS_FRAMES
    POS_AVI_RATIO = cv2.CAP_PROP_POS_AVI_RATIO
    FRAME_WIDTH = cv2.CAP_PROP_FRAME_WIDTH
    FRAME_HEIGHT = cv2.CAP_PROP_FRAME_HEIGHT
    FPS = cv2.CAP_PROP_FPS
    FOURCC = cv2.CAP_PROP_FOURCC
    FRAME_COUNT = cv2.CAP_PROP_FRAME_COUNT
    FORMAT = cv2.CAP_PROP_FORMAT
    MODE = cv2.CAP_PROP_MODE
    BRIGHTNESS = cv2.CAP_PROP_BRIGHTNESS
    CONTRAST = cv2.CAP_PROP_CONTRAST
    SATURATION = cv2.CAP_PROP_SATURATION
    HUE = cv2.CAP_PROP_HUE
    GAIN = cv2.CAP_PROP_GAIN
    EXPOSURE = cv2.CAP_PROP_EXPOSURE
    CONVERT_RGB = cv2.CAP_PROP_CONVERT_RGB
    WHITE_BALANCE_BLUE_U = cv2.CAP_PROP_WHITE_BALANCE_BLUE_U
    RECTIFICATION = cv2.CAP_PROP_RECTIFICATION
    MONOCHROME = cv2.CAP_PROP_MONOCHROME
    SHARPNESS = cv2.CAP_PROP_SHARPNESS
    AUTO_EXPOSURE = cv2.CAP_PROP_AUTO_EXPOSURE
    GAMMA = cv2.CAP_PROP_GAMMA
    TEMPERATURE = cv2.CAP_PROP_TEMPERATURE
    TRIGGER = cv2.CAP_PROP_TRIGGER
    TRIGGER_DELAY = cv2.CAP_PROP_TRIGGER_DELAY
    WHITE_BALANCE_RED_V = cv2.CAP_PROP_WHITE_BALANCE_RED_V
    ZOOM = cv2.CAP_PROP_ZOOM
    FOCUS = cv2.CAP_PROP_FOCUS
    GUID = cv2.CAP_PROP_GUID
    ISO_SPEED = cv2.CAP_PROP_ISO_SPEED
    BACKLIGHT = cv2.CAP_PROP_BACKLIGHT
    PAN = cv2.CAP_PROP_PAN
    TILT = cv2.CAP_PROP_TILT
    ROLL = cv2.CAP_PROP_ROLL
    IRIS = cv2.CAP_PROP_IRIS
    SETTINGS = cv2.CAP_PROP_SETTINGS
    BUFFERSIZE = cv2.CAP_PROP_BUFFERSIZE
    AUTOFOCUS = cv2.CAP_PROP_AUTOFOCUS
    SAR_NUM = cv2.CAP_PROP_SAR_NUM
    SAR_DEN = cv2.CAP_PROP_SAR_DEN
    BACKEND = cv2.CAP_PROP_BACKEND
    CHANNEL = cv2.CAP_PROP_CHANNEL
    AUTO_WB = cv2.CAP_PROP_AUTO_WB
    WB_TEMPERATURE = cv2.CAP_PROP_WB_TEMPERATURE


Props = VideoCaptureProperties


class CameraCV(camera.Camera):
    def __init__(self, address: int = 0):
        super().__init__(address)
        self._cam = cv2.VideoCapture(address)
        if not self._cam.isOpened():
            raise IOError(f"Could not open OpenCV camera with address {address}")

    def __del__(self):
        if hasattr(self, "_cam"):
            self._cam.release()

    # Camera property control

    def get_prop(self, prop: Props) -> float:
        return self._cam.get(prop)

    def set_prop(self, prop: Props, value) -> None:
        ret: bool = self._cam.set(prop, value)
        if not ret:
            raise ValueError("The property is not supported")

    def set_prop_print(self, prop: Props, value) -> None:
        old = self.get_prop(prop)
        self.set_prop(prop, value)
        new = self.get_prop(prop)
        print(f"Property {prop.name} - old {old}, set {value}, new {new}")

    def print_props(self):
        for prop in Props:
            print(f"{prop.name}: {self.get_prop(prop)}")

    # Properties

    @property
    def backend_name(self) -> str:
        return self._cam.getBackendName()

    @property
    def resolution(self):
        return self.get_prop(Props.FRAME_WIDTH), self.get_prop(Props.FRAME_HEIGHT)

    # Public methods

    def get_frame(self, output_array=None) -> np.ndarray:
        if output_array:
            ret, frame = self._cam.read(output_array)
        else:
            ret, frame = self._cam.read()
        if not ret:
            raise IOError("Could not read frame from the camera")
        return frame

    def save_frame(self, path: str, frame: np.ndarray = None):
        if frame is None:
            frame = self.get_frame()
        cv2.imwrite(filename=path, img=frame)

    def set_resolution(self, width: int, height: int):
        self.set_prop(Props.FRAME_WIDTH, width)
        self.set_prop(Props.FRAME_HEIGHT, height)


def __test():
    # print(cv2.getBuildInformation())
    cam = CameraCV()

    # Set FireWire speed to 800 Mbps
    cam.set_prop(Props.ISO_SPEED, 800)
    cam.set_resolution(width=1280, height=960)

    cam.print_props()

    while True:
        gray = cam.get_frame()

        # Display the resulting frame
        cv2.imshow('frame', gray)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    __test()

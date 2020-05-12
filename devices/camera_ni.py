"""This module provides NI Vision / IMAQdx camera support for ORC Dark Spot Mapper"""

__author__ = "Mika Mäki"
__copyright__ = "Copyright 2016-2020, Tampere University"
__credits__ = ["Mika Mäki"]
__maintainer__ = "Mika Mäki"
__email__ = "mika.maki@tuni.fi"

import atexit
import enum
import logging
import os.path
import time

# import matplotlib.image
import nivision
import PIL.Image

from . import camera

logger = logging.getLogger(__name__)


@enum.unique
class CameraSettings(str, enum.Enum):
    AUTO_EXPOSURE = "AutoExposure"
    BRIGHTNESS = "Brightness"
    GAIN = "Gain"
    GAMMA = "Gamma"
    SHARPNESS = "Sharpness"
    SHUTTER = "Shutter"


class NI_Camera:
    """API for a NI Vision / IMAQdx FireWire camera"""
    def __init__(self, cam_name: str, cam_quality: int):
        # super().__init__(cam_name)
        self.__cam_name = bytes(cam_name, encoding="ascii")
        self.__cam_quality = cam_quality

        # Ensuring that the camera is closed after use
        atexit.register(self.close_camera)

        logger.info("Opening camera. This may take a while.")
        try:
            open_start_time = time.perf_counter()
            self.__camid = nivision.IMAQdxOpenCamera(self.__cam_name, nivision.IMAQdxCameraControlModeController)
            # self.__camid = nivision.IMAQdxOpenCamera(self.__camname, nivision.IMAQdxCameraControlModeListener)
            # nivision.IMAQdxConfigureAcquisition(self.__camid, 1, 1)
            open_end_time = time.perf_counter()
            logger.debug(f"Opening camera took {open_end_time - open_start_time:.2f} s")
            nivision.IMAQdxConfigureGrab(self.__camid)
        except (nivision.ImaqError, nivision.ImaqDxError) as e:
            logger.exception(e)
            raise IOError(f"Could not connect to camera {cam_name}: {e}")

        # Initialise image objects
        self.__img_frame = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_frame_flipped = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_frame_flipped2 = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)

        self.__img_pic = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_pic_flipped = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_pic_flipped2 = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)

    def close_camera(self) -> None:
        """
        The camera must be closed with the program or it cannot be reopened
        :return: -
        """
        try:
            logger.info("Closing camera")
            nivision.IMAQdxCloseCamera(self.__camid)
        except (nivision.ImaqError, nivision.ImaqDxError) as e:
            logger.exception(e)
            logger.error(f"Closing camera failed: {e}")
            raise e

    def set_cam_setting(self, name: CameraSettings, value: int) -> None:
        full_name = f"CameraAttributes::{name}::Value"
        try:
            nivision.IMAQdxSetAttribute(self.__camid, bytes(full_name, encoding="ascii"), value)
        except (nivision.ImaqError, nivision.ImaqDxError) as e:
            logger.exception(e)
            error_text = f"Setting value {value} for {name} resulted in error {e}"
            logger.error(error_text)
            raise IOError(error_text)

    def take_pic(self):
        """Captures a single frame"""
        nivision.IMAQdxGrab(self.__camid, self.__img_frame, 0)
        nivision.imaqFlip(self.__img_frame_flipped, self.__img_frame, nivision.IMAQ_HORIZONTAL_AXIS)
        nivision.imaqFlip(self.__img_frame_flipped2, self.__img_frame_flipped, nivision.IMAQ_VERTICAL_AXIS)

        # This does not work due to a memory leak at nivision.imaqImageToArray()
        imgdata = nivision.imaqImageToArray(self.__img_frame_flipped2)
        imgbytes = imgdata[0]
        pilimg = PIL.Image.frombytes("L", (1280, 960), imgbytes)
        # matimg = matplotlib.image.pil_to_array(img)

        # The image is saved on a RAM disk since the transfer of the image from NI Vision to Python as shown above
        # would result in a memory leak
        # The RAM disk is not provided by this program and thereby has to be set up separately
        # nivision.imaqWritePNGFile(self.__img_frame_flipped2, b"R:\\nivisiontemp.png", self.__cam_quality)
        return pilimg

    def save_pic(self, directory: str, filename: str, log: bool = True) -> None:
        """Takes a picture to the hard drive"""
        if not directory or not os.path.isdir(directory):
            raise ValueError(f"Invalid directory: {directory}")
        elif not filename:
            raise ValueError(f"Invalid filename: {filename}")

        nivision.IMAQdxGrab(self.__camid, self.__img_pic, 1)
        nivision.imaqFlip(self.__img_pic_flipped, self.__img_pic, nivision.IMAQ_HORIZONTAL_AXIS)
        nivision.imaqFlip(self.__img_pic_flipped2, self.__img_pic_flipped, nivision.IMAQ_VERTICAL_AXIS)

        path = f"{os.path.join(directory, filename)}.png"

        if log:
            logger.info("Taking picture %s", path)

        nivision.imaqWritePNGFile(self.__img_pic_flipped2, bytes(path, encoding="ascii"), self.__cam_quality)


if __name__ == "__main__":
    print("Connecting to camera")
    NI_Camera("cam0", 10000)

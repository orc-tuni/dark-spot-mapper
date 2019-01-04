"""This module provides NI Vision / IMAQdx camera support for ORC Dark Spot Mapper

Copyright 2016 - 2019 Mika Mäki & Tampere University of Technology
Mika would like to license this program with GPLv3+ but it would require some university bureaucracy
"""

# Basic libraries
import atexit
import logging
# import typing as tp

# Camera support
import nivision

logger = logging.getLogger(__name__)


class NI_Camera:
    """
    This class functions as an API for a NI Vision / IMAQdx FireWire camera
    """
    def __init__(self, cam_name, cam_quality):
        self.__cam_name = cam_name
        self.__cam_quality = cam_quality

        # Ensuring that the camera is closed after use
        atexit.register(self.close_camera)

        logger.info("Opening camera. This may take a while.")
        try:
            self.__camid = nivision.IMAQdxOpenCamera(self.__cam_name, nivision.IMAQdxCameraControlModeController)
            # self.__camid = nivision.IMAQdxOpenCamera(self.__camname, nivision.IMAQdxCameraControlModeListener)
            # nivision.IMAQdxConfigureAcquisition(self.__camid, 1, 1)
            nivision.IMAQdxConfigureGrab(self.__camid)
        except (nivision.ImaqError, nivision.ImaqDxError):
            raise IOError("Could not connect to camera {}".format(cam_name))

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
            logger.error("Closing camera failed: {}".format(e))
            raise e

    def set_cam_settings(self, cam_vars: list) -> bool:
        """
        Sets the desired parameters to the camera
        :param cam_vars: values of the camera parameters to be set
        :return: bool of success
        """
        try:
            cam_setting_texts = ["AutoExposure", "Brightness", "Gain", "Gamma", "Sharpness", "Shutter"]

            for index, var in enumerate(cam_vars):
                value = int(var.get())
                string = "CameraAttributes::" + cam_setting_texts[index] + "::Value"
                nivision.IMAQdxSetAttribute(self.__camid, string.encode("ascii"), value)
            return True
        except (nivision.ImaqError, nivision.ImaqDxError):
            logger.warning("Setting camera attributes failed")
            return False

    def take_frame(self) -> None:
        """
        Captures a single frame to the ramdisk
        :return: -
        """
        nivision.IMAQdxGrab(self.__camid, self.__img_frame, 0)
        nivision.imaqFlip(self.__img_frame_flipped, self.__img_frame, nivision.IMAQ_HORIZONTAL_AXIS)
        nivision.imaqFlip(self.__img_frame_flipped2, self.__img_frame_flipped, nivision.IMAQ_VERTICAL_AXIS)

        # This does not work due to a memory leak at nivision.imaqImageToArray()
        # imgdata = nivision.imaqImageToArray(img)
        # imgbytes = imgdata[0]
        # pilimg = PIL.Image.frombytes("L", (1280, 960), imgbytes)
        # matimg = matplotlib.image.pil_to_array(img)

        # The image is saved on a RAM disk since the transfer of the image from NI Vision to Python as shown above
        # would result in a memory leak
        # The RAM disk is not provided by this program and thereby has to be set up separately
        nivision.imaqWritePNGFile(self.__img_frame_flipped2, b"R:\\nivisiontemp.png", self.__cam_quality)

    def takepic(self, filename: str, directory: str) -> None:
        """
        Takes a picture to the hard drive
        :param filename: file name for the picture
        :param directory: directory for the picture
        :return: -
        """
        if directory == "" or filename == "":
            return

        nivision.IMAQdxGrab(self.__camid, self.__img_pic, 1)
        nivision.imaqFlip(self.__img_pic_flipped, self.__img_pic, nivision.IMAQ_HORIZONTAL_AXIS)
        nivision.imaqFlip(self.__img_pic_flipped2, self.__img_pic_flipped, nivision.IMAQ_VERTICAL_AXIS)

        file_path = directory + "/" + filename + ".png"

        logger.info("Taking picture %s", file_path)
        nivision.imaqWritePNGFile(self.__img_pic_flipped2, file_path.encode("ascii"), self.__cam_quality)

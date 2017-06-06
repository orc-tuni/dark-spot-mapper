# This module provides NI Vision / IMAQdx camera support for
# ORC Dark Spot Mapper

# Copyright 2016 - 2017 Mika Mäki & Tampere University of Technology
# Mika would like to license this program with GPLv3+ but it would require some university bureaucracy


# Basic libraries
import atexit

# Camera support
import nivision


class NI_Camera:
    """
    This class functions as an API for a NI Vision / IMAQdx FireWire camera
    """
    def __init__(self, camname, camquality):
        self.__camname = camname
        self.__camquality = camquality

        # Ensuring that the camera is closed after use
        atexit.register(self.closecamera)

        print("Opening camera. This may take a while.")
        try:
            self.__camid = nivision.IMAQdxOpenCamera(self.__camname, nivision.IMAQdxCameraControlModeController)
            # self.__camid = nivision.IMAQdxOpenCamera(self.__camname, nivision.IMAQdxCameraControlModeListener)
            # nivision.IMAQdxConfigureAcquisition(self.__camid, 1, 1)
            nivision.IMAQdxConfigureGrab(self.__camid)
        except (nivision.ImaqError, nivision.ImaqDxError):
            raise IOError("Could not connect to camera")

        # Initialise image objects
        self.__img_frame = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_frame_flipped = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_frame_flipped2 = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)

        self.__img_pic = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_pic_flipped = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_pic_flipped2 = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)

    def closecamera(self):
        """
        The camera must be closed with the program or it cannot be reopened
        :return: -
        """
        try:
            print("Closing camera")
            nivision.IMAQdxCloseCamera(self.__camid)
        except (nivision.ImaqError, nivision.ImaqDxError):
            raise IOError("Closing camera failed")

    def setcamsettings(self, camvars):
        """
        Sets the desired parameters to the camera
        :param camvars: values of the camera parameters to be set
        :return: bool of success
        """
        try:
            camsettingtexts = ["AutoExposure", "Brightness", "Gain", "Gamma", "Sharpness", "Shutter"]

            for index, var in enumerate(camvars):
                value = int(var.get())
                string = "CameraAttributes::" + camsettingtexts[index] + "::Value"
                nivision.IMAQdxSetAttribute(self.__camid, string.encode("ascii"), value)
            return True
        except (nivision.ImaqError, nivision.ImaqDxError):
            print("Setting camera attributes failed")
            return False

    def takeframe(self):
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
        nivision.imaqWritePNGFile(self.__img_frame_flipped2, b"R:\\nivisiontemp.png", self.__camquality)

    def takepic(self, filename, directory):
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

        filepath = directory + "/" + filename + ".png"

        print("Taking picture", filepath)
        nivision.imaqWritePNGFile(self.__img_pic_flipped2, filepath.encode("ascii"), self.__camquality)

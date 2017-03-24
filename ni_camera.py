# This file provides NI Vision / IMAQdx camera support for
# ORC Dark Spot Mapper

# Copyright 2016 - 2017 Mika Mäki & Tampere University of Technology

# Basic libraries
import atexit

# Camera support
import nivision


class NI_Camera:
    def __init__(self, camname, camquality):
        self.__camname = camname
        self.__camquality = camquality

        # Ensuring that the camera is closed after use
        atexit.register(self.closecamera)

        print("Opening camera. This may take a while.")
        try:
            self.__camid = nivision.IMAQdxOpenCamera(self.__camname, nivision.IMAQdxCameraControlModeController)
            # self.__camid = nivision.IMAQdxOpenCamera(self.__camname, nivision.IMAQdxCameraControlModeListener)
            #  nivision.IMAQdxConfigureAcquisition(self.__camid, 1, 1)
            nivision.IMAQdxConfigureGrab(self.__camid)
        except:
            print("Camera setup failed")
            raise IOError

        self.__img_frame = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_frame_flipped = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_frame_flipped2 = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)

        self.__img_pic = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_pic_flipped = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        self.__img_pic_flipped2 = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)

    def closecamera(self):
        try:
            print("Closing camera")
            nivision.IMAQdxCloseCamera(self.__camid)
        except:
            print("Closing camera failed")

    def setcamsettings(self, camvars):
        try:
            camsettingtexts = ["AutoExposure", "Brightness", "Gain", "Gamma", "Sharpness", "Shutter"]

            for index, var in enumerate(camvars):
                value = int(var.get())
                string = "CameraAttributes::" + camsettingtexts[index] + "::Value"
                nivision.IMAQdxSetAttribute(self.__camid, string.encode("ascii"), value)
            return True
        except:
            return False

    def takeframe(self):
        nivision.IMAQdxGrab(self.__camid, self.__img_frame, 0)
        nivision.imaqFlip(self.__img_frame_flipped, self.__img_frame, nivision.IMAQ_HORIZONTAL_AXIS)
        nivision.imaqFlip(self.__img_frame_flipped2, self.__img_frame_flipped, nivision.IMAQ_VERTICAL_AXIS)

        # This does not work due to a memory leak at nivision.imaqImageToArray()
        # imgdata = nivision.imaqImageToArray(img)
        # imgbytes = imgdata[0]
        # pilimg = PIL.Image.frombytes("L", (1280, 960), imgbytes)
        # matimg = matplotlib.image.pil_to_array(img)

        # Using ramdisk is an ugly hack but it works
        nivision.imaqWritePNGFile(self.__img_frame_flipped2, b"R:\\nivisiontemp.png", self.__camquality)

    def takepic(self, filename, directory):
        try:
            if directory == "" or filename == "":
                return "Directory is not set"

            nivision.IMAQdxGrab(self.__camid, self.__img_pic, 1)
            nivision.imaqFlip(self.__img_pic_flipped, self.__img_pic, nivision.IMAQ_HORIZONTAL_AXIS)
            nivision.imaqFlip(self.__img_pic_flipped2, self.__img_pic_flipped, nivision.IMAQ_VERTICAL_AXIS)

            filepath = directory + "/" + filename + ".png"
            # print(filepath)

            nivision.imaqWritePNGFile(self.__img_pic_flipped, filepath.encode("ascii"), self.__camquality)

            return "Picture successful"
        except:
            return "Picture failed"

    def takepic_chip(self, chipname, chippath, number, timestring):
        nivision.IMAQdxGrab(self.__camid, self.__img_pic, 1)
        nivision.imaqFlip(self.__img_pic_flipped, self.__img_pic, nivision.IMAQ_HORIZONTAL_AXIS)
        nivision.imaqFlip(self.__img_pic_flipped2, self.__img_pic_flipped, nivision.IMAQ_VERTICAL_AXIS)

        filepath = chippath + "/" + chipname + "_" + timestring + "_" + str(number) + ".png"
        print("Saving picture", filepath)
        nivision.imaqWritePNGFile(self.__img_pic_flipped2, filepath.encode("ascii"), self.__camquality)

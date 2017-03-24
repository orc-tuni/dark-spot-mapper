# This software is for controlling the Dark Spot Mapper
# of the Optoelectronics Research Centre of Tampere University of Technology

# Copyright 2016 - 2017 Mika Mäki & Tampere University of Technology

# C++ DLL support for SimpleMotion
import ctypes

# Camera support
import nivision

# GUI
import tkinter
import tkinter.filedialog

# Basic libraries
import time
import atexit
import os.path
import threading

# Graphing
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import PIL.Image
import matplotlib.image
import numpy as np

# Debugging
import gc
import objgraph


class QtDisp:
    def __init__(self,camid, autolevels):
        self.__camid = camid

        self.__autolevels = autolevels

        app = QtGui.QApplication([])

        win = QtGui.QMainWindow()
        win.resize(1200, 700)
        self.imv = pg.ImageView()
        win.setCentralWidget(self.imv)
        win.setWindowTitle("ORC Dark Spot Mapper ")
        win.show()

        # This line prevents a bug at image leveling
        self.imv.setLevels(0.1,0.9)

        self.takepic()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.takepic)
        timer.start(50)

        app.exec()

    def takepic(self):
        img = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        nivision.IMAQdxGrab(self.__camid, img, 0)

        # This does not work due to a memory leak at nivision.imaqImageToArray()
        # imgdata = nivision.imaqImageToArray(img)
        # imgbytes = imgdata[0]
        # pilimg = PIL.Image.frombytes("L", (1280, 960), imgbytes)
        # matimg = matplotlib.image.pil_to_array(img)

        # Using ramdisk is an ugly hack but it works
        nivision.imaqWritePNGFile(img, b"R:\\nivisiontemp.png", 10000)
        matimg = matplotlib.image.imread("R:\\nivisiontemp.png")

        transposed = np.transpose(matimg)

        if self.__autolevels:
            self.imv.setImage(transposed, autoLevels=True)
        else:
            self.imv.setImage(transposed, levels=(0,1))


class DSM:
    def __init__(self):
        print("Starting")

        gc.enable()
        # gc.set_debug(gc.DEBUG_LEAK)
        # gc.set_debug(gc.DEBUG_UNCOLLECTABLE)

        self.__currentdir = ""
        self.__timestring = self.timestringfunc()

        # Ensuring that the camera is closed after use
        atexit.register(self.closecamera)

        # Camera variables
        self.__camname = b"cam0"
        self.__camquality = 10000
        camlabeltexts = ["Auto Exposure", "Brightness", "Gain", "Gamma", "Sharpness", "Shutter"]
        camdefaultsettings = [256, 1500, 0, 0, 4, 230]

        # Device names for TTL adapters
        self.__axis1 = b"TTL232R"
        self.__axis2 = b"TTL232R2"
        self.__axis3 = b"TTL232R3"

        # Loading the SimpleMotion library
        try:
            self.__smdll = ctypes.cdll.LoadLibrary("SimpleMotion64")
            print("Detected SimpleMotion version: " + str(self.__smdll.smGetVersion()))
        except:
            print("Loading of SimpleMotion library failed")
            exit()

        # Testing connection to motor drivers
        try:
            a1err = self.__smdll.smCommand(self.__axis1, b"TESTCOMMUNICATION", 0)
            a2err = self.__smdll.smCommand(self.__axis2, b"TESTCOMMUNICATION", 0)
            a3err = self.__smdll.smCommand(self.__axis3, b"TESTCOMMUNICATION", 0)
            if a1err != 0 or a2err != 0 or a3err != 0:
                print("Connecting to motor drivers returned codes: " + str(a1err) + " " + str(a2err) + " " + str(a3err))
                raise IOError
        except:
            print("Could not connect to motor drivers")
            exit()

        # Opening camera using NI vision
        try:
            print("Opening camera. This may take a while.")
            self.__camid = nivision.IMAQdxOpenCamera(self.__camname, nivision.IMAQdxCameraControlModeController)
            # self.__camid = nivision.IMAQdxOpenCamera(self.__camname, nivision.IMAQdxCameraControlModeListener)
            #  nivision.IMAQdxConfigureAcquisition(self.__camid, 1, 1)
            nivision.IMAQdxConfigureGrab(self.__camid)
            self.__rawimg = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_U8)
        except:
            print("Could not connect to camera")
            exit()

        # Qt thread & window

        self.qt_thread = threading.Thread(target=QtDisp, args=(self.__camid, False))
        self.qt_thread.start()

        # UI creation

        self.__mainWindow = tkinter.Tk()
        self.__mainWindow.title("ORC Dark Spot Mapper")

        # Miscellaneous
        self.__infoVar = tkinter.StringVar()

        infolabel = tkinter.Label(self.__mainWindow, textvar=self.__infoVar)
        infolabel.grid(row=6, columnspan=6)

        # Navigation elements

        self.__upButton = tkinter.Button(self.__mainWindow, text="▲", command=self.up)
        self.__upButton.grid(row=0, column=1)

        self.__leftButton = tkinter.Button(self.__mainWindow, text="◄", command=self.left)
        self.__leftButton.grid(row=1, column=0)

        self.__rightButton = tkinter.Button(self.__mainWindow, text="►", command=self.right)
        self.__rightButton.grid(row=1, column=2)

        self.__downButton = tkinter.Button(self.__mainWindow, text="▼", command=self.down)
        self.__downButton.grid(row=2, column=1)

        self.__zupButton = tkinter.Button(self.__mainWindow, text="+", command=self.zup)
        self.__zupButton.grid(row=0, column=3)

        self.__zdownButton = tkinter.Button(self.__mainWindow, text="-", command=self.zdown)
        self.__zdownButton.grid(row=1, column=3)

        # Picture elements

        self.__stepVar = tkinter.StringVar()
        self.__stepEntry = tkinter.Entry(self.__mainWindow, textvariable=self.__stepVar)
        self.__stepVar.set("18000")
        self.__stepEntry.grid(row=0, column=4)

        self.__picVar = tkinter.StringVar()
        self.__picEntry = tkinter.Entry(self.__mainWindow, textvariable=self.__picVar)
        self.__picVar.set("PicName")
        self.__picEntry.grid(row=1, column=4)

        self.__picButton = tkinter.Button(self.__mainWindow, text="Take picture", command=self.takepic)
        self.__picButton.grid(row=2, column=4)

        self.__folderButton = tkinter.Button(self.__mainWindow, text="Set folder", command=self.choosedir)
        self.__folderButton.grid(row=3, column=4)

        # Elements for measurement

        self.__chipVar = tkinter.StringVar()
        self.__chipEntry = tkinter.Entry(self.__mainWindow, textvariable=self.__chipVar)
        self.__chipVar.set("Chip_Material")
        self.__chipEntry.grid(row=0, column=5)

        self.__measureButton = tkinter.Button(self.__mainWindow, text="Measure Chip", command=self.measurechip)
        self.__measureButton.grid(row=1, column=5)

        # Elements for Qt

        camrangelabel = tkinter.Label(self.__mainWindow, text="Camera autorange")
        camrangelabel.grid(row=0, column=6)

        self.__camRangeVar = tkinter.BooleanVar()
        self.__camRangeVar.set(False)

        self.__camRangeOnButton = tkinter.Radiobutton(self.__mainWindow, text="on", variable=self.__camRangeVar, value=True)
        self.__camRangeOnButton.grid(row=1, column=6)

        self.__camRangeOffButton = tkinter.Radiobutton(self.__mainWindow, text="off", variable=self.__camRangeVar, value=False)
        self.__camRangeOffButton.grid(row=2, column=6)

        self.__qtRestartButton = tkinter.Button(self.__mainWindow, text="Restart View", command=self.qt_restart)
        self.__qtRestartButton.grid(row=3, column=6)

        self.__debugButton = tkinter.Button(self.__mainWindow, text="Debug", command=self.debug)
        self.__debugButton.grid(row=4, column=6)

        # Elements for camera settings

        for index, text in enumerate(camlabeltexts):
            label = tkinter.Label(self.__mainWindow, text=text)
            label.grid(row=index, column=7)

        self.__camVars = []

        for index in range(6):
            self.__camVars.append(tkinter.StringVar())
            self.__camVars[index].set(str(camdefaultsettings[index]))
            entry = tkinter.Entry(self.__mainWindow, textvariable=self.__camVars[index])
            entry.grid(row=index, column=8)

        self.setcamsettings()

        self.__camSetButton = tkinter.Button(self.__mainWindow, text="Set values", command=self.setcamsettings)
        self.__camSetButton.grid(row=len(camlabeltexts), column=8)

        camlimits = ["256-1023", "0-2047", "0-680", "0-3", "0-7", "3-1150"]

        for index, text in enumerate(camlimits):
            label = tkinter.Label(self.__mainWindow, text=text)
            label.grid(row=index, column=9)

        # self.__creatorText = tkinter.Label(self.__mainWindow, text="Created by Mika Mäki, work in progress")
        # self.__creatorText.grid(row=3, columnspan=3)

        print("Program ready")
        self.infotext("")
        self.__mainWindow.mainloop()

    def debug(self):
        print(gc.get_stats())
        print(gc.garbage)
        print(objgraph.show_most_common_types())

    def infotext(self, text):
        self.__infoVar.set(text)

    def closecamera(self):
        try:
            print("Closing camera")
            nivision.IMAQdxCloseCamera(self.__camid)
        except:
            print("Closing camera failed")

    def setcamsettings(self):
        try:
            camsettingtexts = ["AutoExposure", "Brightness", "Gain", "Gamma", "Sharpness", "Shutter"]

            for index, var in enumerate(self.__camVars):
                value = int(var.get())
                string = "CameraAttributes::" + camsettingtexts[index] + "::Value"
                nivision.IMAQdxSetAttribute(self.__camid, string.encode("ascii"), value)

            self.infotext("Camera configuration successful")
        except:
            self.infotext("Camera configuration failed")

    def takepic(self):
        try:
            filename = self.__picVar.get()
            if self.__currentdir == "" or filename == "":
                self.infotext("Directory is not set")
                return

            nivision.IMAQdxGrab(self.__camid, self.__rawimg, 1)
            # The number is somehow related to image quality and bigger is better
            filepath = self.__currentdir + "/" + filename + ".png"
            # print(filepath)
            nivision.imaqWritePNGFile(self.__rawimg, filepath.encode("ascii"), self.__camquality)

            self.infotext("Picture successful")
        except:
            self.infotext("Picture failed")

    def takepic_chip(self, chipname, chippath, number):
        nivision.IMAQdxGrab(self.__camid, self.__rawimg, 1)
        filepath = chippath + "/" + chipname + "_" + self.__timestring + "_" + str(number) + ".png"
        nivision.imaqWritePNGFile(self.__rawimg, filepath.encode("ascii"), self.__camquality)

    def timestringfunc(self):
        year = str(time.localtime().tm_year)
        mon = str(time.localtime().tm_mon)
        if len(mon) == 1:
            mon = "0" + mon
        mday = str(time.localtime().tm_mday)
        if len(mday) == 1:
            mday = "0" + mday

        timestring = year + "-" + mon + "-" + mday
        return timestring

    def qt_restart(self):
        if not self.qt_thread.is_alive():
            autorange = self.__camRangeVar.get()
            self.qt_thread = threading.Thread(target=QtDisp, args=(self.__camid, autorange))
            self.qt_thread.start()

    def choosedir(self):
        newdir = tkinter.filedialog.askdirectory()
        if newdir == "":
            self.infotext("New directory is blank and thereby not set")
        else:
            self.__currentdir = newdir
            self.infotext("Current folder set to: " + self.__currentdir)

    def moveinc(self, axis, steps):
        if abs(steps) > 32760:
            self.infotext("Too many steps")
            return
        self.__smdll.smCommand(axis, b"INCTARGET", steps)

    def up(self):
        self.moveinc(self.__axis2, - int(self.__stepVar.get()))

    def down(self):
        self.moveinc(self.__axis2, int(self.__stepVar.get()))

    def left(self):
        self.moveinc(self.__axis1, - int(self.__stepVar.get()))

    def right(self):
        self.moveinc(self.__axis1, int(self.__stepVar.get()))

    def zup(self):
        self.moveinc(self.__axis3, int(self.__stepVar.get()))

    def zdown(self):
        self.moveinc(self.__axis3, - int(self.__stepVar.get()))

    def measurechip(self):
        if self.__currentdir == "":
            self.infotext("The current directory has not been set")
            return 1

        mstep = 18000
        sleeptime = 1
        chipname = self.__chipVar.get()

        chippath = self.__currentdir + "/" + chipname + "_" + self.__timestring
        # print(chippath)

        if os.path.exists(chippath):
            self.infotext("The chip directory already exists")
            return 1

        self.infotext("Measuring chip")

        os.makedirs(chippath)

        self.moveinc(self.__axis1, mstep)
        self.moveinc(self.__axis1, mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 1)

        self.moveinc(self.__axis1, - mstep)
        self.moveinc(self.__axis1, - mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 2)

        self.moveinc(self.__axis1, - mstep)
        self.moveinc(self.__axis1, - mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 3)

        self.moveinc(self.__axis2, - mstep)
        self.moveinc(self.__axis2, - mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 4)

        self.moveinc(self.__axis1, mstep)
        self.moveinc(self.__axis1, mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 5)

        self.moveinc(self.__axis1, mstep)
        self.moveinc(self.__axis1, mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 6)

        self.moveinc(self.__axis2, - mstep)
        self.moveinc(self.__axis2, - mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 7)

        self.moveinc(self.__axis1, - mstep)
        self.moveinc(self.__axis1, - mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 8)

        self.moveinc(self.__axis1, - mstep)
        self.moveinc(self.__axis1, - mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 9)

        # Stitch the images
        cmdstr = "magick convert bg.png "
        cmdstr += chippath + "/*9.png -gravity Northwest -geometry +0+0 -composite "
        cmdstr += chippath + "/*8.png -geometry +760+0 -composite "
        cmdstr += chippath + "/*7.png -geometry +1520+0 -composite "
        cmdstr += chippath + "/*4.png -geometry +0+760 -composite "
        cmdstr += chippath + "/*5.png -geometry +760+760 -composite "
        cmdstr += chippath + "/*6.png -geometry +1520+760 -composite "
        cmdstr += chippath + "/*3.png -geometry +0+1520 -composite "
        cmdstr += chippath + "/*2.png -geometry +760+1520 -composite "
        cmdstr += chippath + "/*1.png -geometry +1520+1520 -composite "
        cmdstr += chippath + "/" + chipname + "_" + self.__timestring + "_stitch.png"
        os.system(cmdstr)

        self.infotext("Stitch ready")


def main():
    DSM()

main()

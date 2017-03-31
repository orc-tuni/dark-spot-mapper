"""
This software is for controlling the Dark Spot Mapper
of the Optoelectronics Research Centre of Tampere University of Technology

Copyright 2016 - 2017 Mika Mäki & Tampere University of Technology
Mika would like to license this program with GPLv3+ but it would require some university bureaucracy

Requires
- PyQtGraph
- Matplotlib
- Numpy
- NI IMAQdx
- Pynivision
- Granite Devices SimpleMotion DLL (bitness must match that of Python)
- ImageMagick
"""

# Program modules
import ni_camera
import simplemotion

# GUI
import tkinter
import tkinter.filedialog

# Basic libraries
import math
import threading
import time
import os.path

# Graphing
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import matplotlib.image
import numpy as np

# Debugging
import gc
import objgraph


class QtDisp:
    """
    This class provides a window for the camera video
    """
    def __init__(self, camera, autolevels):
        self.camera = camera

        self.__autolevels = autolevels

        app = QtGui.QApplication([])

        win = QtGui.QMainWindow()
        win.resize(1200, 700)
        self.imv = pg.ImageView()
        win.setCentralWidget(self.imv)
        win.setWindowTitle("ORC Dark Spot Mapper ")
        win.show()

        # This line prevents a bug at image leveling
        self.imv.setLevels(0.1, 0.9)

        self.takeframe()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.takeframe)
        timer.start(50)

        app.exec()

    def takeframe(self):
        """
        Fetches a frame from the camera and displays it
        :return: -
        """
        self.camera.takeframe()

        # The camera.takeframe() saves the frame on a RAM disk since transporting the image directly from
        # NI Vision to Python would result in a memory leak
        matimg = matplotlib.image.imread("R:\\nivisiontemp.png")
        transposed = np.transpose(matimg)

        if self.__autolevels:
            self.imv.setImage(transposed, autoLevels=True)
        else:
            self.imv.setImage(transposed, levels=(0, 1))


class DSM:
    """
    This is the primary class of the Dark Spot Mapper
    """
    def __init__(self):
        print("Starting")

        gc.enable()
        # gc.set_debug(gc.DEBUG_LEAK)
        # gc.set_debug(gc.DEBUG_UNCOLLECTABLE)

        self.__currentdir = ""
        self.__timestring = self.timestringfunc()
        self.__measuring = False

        self.__corner1 = (0, 0)
        self.__corner2 = (0, 0)

        # Camera variables
        self.__camname = b"cam0"
        self.__camquality = 10000
        camlabeltexts = ["Auto Exposure", "Brightness", "Gain", "Gamma", "Sharpness", "Shutter"]
        camdefaultsettings = [256, 1500, 0, 0, 4, 230]

        # Stage setup
        try:
            self.stages = simplemotion.SimpleMotion()
        except IOError:
            print("Stage setup failed")
            exit()

        # Camera setup
        try:
            self.camera = ni_camera.NI_Camera(self.__camname, self.__camquality)
        except IOError:
            print("Camera setup failed")
            exit()

        # Qt thread & window

        self.qt_thread = threading.Thread(target=QtDisp, args=(self.camera, False))
        self.qt_thread.start()

        # UI creation

        self.__mainWindow = tkinter.Tk()
        self.__mainWindow.title("ORC Dark Spot Mapper")

        # Miscellaneous
        self.__measuringTextVar = tkinter.StringVar()
        measuring_label = tkinter.Label(self.__mainWindow, textvar=self.__measuringTextVar)
        measuring_label.grid(row=6, columnspan=6)

        self.__infoVar = tkinter.StringVar()

        infolabel = tkinter.Label(self.__mainWindow, textvar=self.__infoVar)
        infolabel.grid(row=8, columnspan=11)

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

        self.__use_mmVar = tkinter.BooleanVar()
        self.__use_mmVar.set(False)

        self.__stepsButton = tkinter.Radiobutton(self.__mainWindow, text="Steps", variable=self.__use_mmVar,
                                                 value=False)
        self.__stepsButton.grid(row=0, column=4, sticky="W")

        self.__mmButton = tkinter.Radiobutton(self.__mainWindow, text="mm", variable=self.__use_mmVar,
                                              value=True)
        self.__mmButton.grid(row=1, column=4, sticky="W")

        self.__stepVar = tkinter.StringVar()
        self.__stepEntry = tkinter.Entry(self.__mainWindow, textvariable=self.__stepVar)
        self.__stepVar.set("18000")
        self.__stepEntry.grid(row=0, column=5)

        self.__mmVar = tkinter.StringVar()
        self.__mmEntry = tkinter.Entry(self.__mainWindow, textvariable=self.__mmVar)
        self.__mmVar.set("1")
        self.__mmEntry.grid(row=1, column=5)

        self.__corner1_Button = tkinter.Button(self.__mainWindow, text="Set corner 1", command=self.set_corner1)
        self.__corner1_Button.grid(row=2, column=5)

        self.__corner2_Button = tkinter.Button(self.__mainWindow, text="Set corner 2", command=self.set_corner2)
        self.__corner2_Button.grid(row=3, column=5)

        self.__resetCoords_Button = tkinter.Button(self.__mainWindow, text="Reset coordinates", command=self.reset_coords)
        self.__resetCoords_Button.grid(row=4, column=5)

        # Picture elements

        self.__picVar = tkinter.StringVar()
        self.__picEntry = tkinter.Entry(self.__mainWindow, textvariable=self.__picVar)
        self.__picVar.set("PicName")
        self.__picEntry.grid(row=0, column=6)

        self.__picButton = tkinter.Button(self.__mainWindow, text="Take picture", command=self.takepic)
        self.__picButton.grid(row=1, column=6)

        self.__folderButton = tkinter.Button(self.__mainWindow, text="Set folder", command=self.choosedir)
        self.__folderButton.grid(row=2, column=6)

        # Elements for measurement

        self.__sampleVar = tkinter.StringVar()
        self.__sampleEntry = tkinter.Entry(self.__mainWindow, textvariable=self.__sampleVar)
        self.__sampleVar.set("Sample_ID")
        self.__sampleEntry.grid(row=3, column=6)

        self.__chipButton = tkinter.Button(self.__mainWindow, text="Measure chip", command=self.measure_chip_threaded)
        self.__chipButton.grid(row=4, column=6)

        self.__waferButton = tkinter.Button(self.__mainWindow, text="Measure wafer",
                                            command=self.measure_wafer_threaded)
        self.__waferButton.grid(row=5, column=6)

        self.__waferFullButton = tkinter.Button(self.__mainWindow, text="Measure entire wafer",
                                                command=self.measure_entire_wafer_threaded)
        self.__waferFullButton.grid(row=6, column=6)

        self.__areaButton = tkinter.Button(self.__mainWindow, text="Measure area", command=self.measure_area_threaded)
        self.__areaButton.grid(row=7, column=6)

        cameracolumn = 7

        # Elements for Qt

        camrangelabel = tkinter.Label(self.__mainWindow, text="Camera autorange")
        camrangelabel.grid(row=0, column=cameracolumn)

        self.__camRangeVar = tkinter.BooleanVar()
        self.__camRangeVar.set(False)

        self.__camRangeOnButton = tkinter.Radiobutton(self.__mainWindow, text="on", variable=self.__camRangeVar,
                                                      value=True)
        self.__camRangeOnButton.grid(row=1, column=cameracolumn)

        self.__camRangeOffButton = tkinter.Radiobutton(self.__mainWindow, text="off", variable=self.__camRangeVar,
                                                       value=False)
        self.__camRangeOffButton.grid(row=2, column=cameracolumn)

        self.__qtRestartButton = tkinter.Button(self.__mainWindow, text="Restart view", command=self.qt_restart)
        self.__qtRestartButton.grid(row=3, column=cameracolumn)

        self.__debugButton = tkinter.Button(self.__mainWindow, text="Debug", command=self.debug)
        self.__debugButton.grid(row=4, column=cameracolumn)

        # Elements for camera settings

        for index, text in enumerate(camlabeltexts):
            label = tkinter.Label(self.__mainWindow, text=text)
            label.grid(row=index, column=cameracolumn+1)

        self.__camVars = []

        for index in range(6):
            self.__camVars.append(tkinter.StringVar())
            self.__camVars[index].set(str(camdefaultsettings[index]))
            entry = tkinter.Entry(self.__mainWindow, textvariable=self.__camVars[index])
            entry.grid(row=index, column=cameracolumn+2)

        self.setcamsettings()

        self.__camSetButton = tkinter.Button(self.__mainWindow, text="Set values", command=self.setcamsettings)
        self.__camSetButton.grid(row=len(camlabeltexts), column=cameracolumn+2)

        camlimits = ["256-1023", "0-2047", "0-680", "0-3", "0-7", "3-1150"]

        for index, text in enumerate(camlimits):
            label = tkinter.Label(self.__mainWindow, text=text)
            label.grid(row=index, column=cameracolumn+3)

        # self.__creatorText = tkinter.Label(self.__mainWindow, text="Created by Mika Mäki, work in progress")
        # self.__creatorText.grid(row=3, columnspan=3)

        # Create a list of buttons that should be disabled when measuring
        self.__sensitiveButtons = [self.__upButton, self.__leftButton, self.__rightButton, self.__downButton,
                                   self.__corner1_Button, self.__corner2_Button, self.__resetCoords_Button,
                                   self.__chipButton, self.__waferButton, self.__waferFullButton, self.__areaButton,
                                   self.__folderButton]

        print("Program ready")
        self.infotext("")
        self.__mainWindow.mainloop()

    @staticmethod
    def debug():
        """
        Prints debug information for hunting NI Vision memory leaks etc.
        :return: -
        """
        print(gc.get_stats())
        print(gc.garbage)
        print(objgraph.show_most_common_types())

    def infotext(self, text):
        self.__infoVar.set(text)

    def setcamsettings(self):
        if self.camera.setcamsettings(self.__camVars):
            self.infotext("Camera configuration successful")
        else:
            self.infotext("Camera configuration failed")

    def takepic(self):
        self.camera.takepic(self.__picVar.get(), self.__currentdir)

    def takepic_chip(self, chipname, chippath, number):
        filename = chipname + "_" + self.__timestring + "_" + str(number)
        self.camera.takepic(filename, chippath)

    def takepic_area(self, name, path, number, total):
        filename = name + "_" + self.__timestring + "_" + str(number).zfill(math.ceil(math.log10(total+1)))
        self.camera.takepic(filename, path)

    @staticmethod
    def timestringfunc():
        """
        Returns the current date in ISO 8601 format
        :return: string of current date
        """
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
            self.qt_thread = threading.Thread(target=QtDisp, args=(self.camera, autorange))
            self.qt_thread.start()

    def choosedir(self):
        newdir = tkinter.filedialog.askdirectory()
        if newdir == "":
            self.infotext("New directory is blank and thereby not set")
        else:
            self.__currentdir = newdir
            self.infotext("Current folder set to: " + self.__currentdir)

    def up(self):
        if self.__use_mmVar.get():
            self.stages.mm_up(float(self.__mmVar.get()))
        else:
            self.stages.step_up(int(self.__stepVar.get()))

    def down(self):
        if self.__use_mmVar.get():
            self.stages.mm_down(float(self.__mmVar.get()))
        else:
            self.stages.step_down(int(self.__stepVar.get()))

    def left(self):
        if self.__use_mmVar.get():
            self.stages.mm_left(float(self.__mmVar.get()))
        else:
            self.stages.step_left(int(self.__stepVar.get()))

    def right(self):
        if self.__use_mmVar.get():
            self.stages.mm_right(float(self.__mmVar.get()))
        else:
            self.stages.step_right(int(self.__stepVar.get()))

    def zup(self):
        if self.__use_mmVar.get():
            self.infotext("Z axis doesn't support mm")
        else:
            self.stages.step_zup(int(self.__stepVar.get()))

    def zdown(self):
        if self.__use_mmVar.get():
            self.infotext("Z axis doesn't support mm")
        else:
            self.stages.step_zdown(int(self.__stepVar.get()))

    def set_measuring(self, status):
        """
        Set whether there currently is a measurement in progress
        :param status: bool
        :return:
        """
        if status:
            self.__measuring = True
            self.__measuringTextVar.set("MEASURING")

            for button in self.__sensitiveButtons:
                button.config(state=tkinter.DISABLED)
        else:
            self.__measuring = False
            self.__measuringTextVar.set("")

            for button in self.__sensitiveButtons:
                button.config(state=tkinter.NORMAL)

    def measure_chip_threaded(self):
        """
        Threading support for chip measurement
        :return: -
        """
        if self.__measuring:
            self.infotext("Measurement already running")
        else:
            thread = threading.Thread(target=self.measure_chip)
            thread.start()

    def measure_chip(self):
        """
        Measure a single pentagon VECSEL chip
        Begins from the "north" corner and returns there
        :return:
        """
        if self.__currentdir == "":
            self.infotext("The base directory has not been set")
            return

        mstep = 36000
        sleeptime = 0.5
        chipname = self.__sampleVar.get()

        chippath = self.__currentdir + "/" + chipname + "_" + self.__timestring
        # print(chippath)

        if os.path.exists(chippath):
            self.infotext("The chip directory already exists")
            return

        self.infotext("Measuring chip")
        self.set_measuring(True)

        os.makedirs(chippath)

        self.stages.step_left(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 1)

        self.stages.step_right(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 2)

        self.stages.step_right(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 3)

        self.stages.step_down(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 4)

        self.stages.step_left(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 5)

        self.stages.step_left(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 6)

        self.stages.step_down(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 7)

        self.stages.step_right(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 8)

        self.stages.step_right(mstep)
        time.sleep(sleeptime)
        self.takepic_chip(chipname, chippath, 9)

        # Return to the previous position
        self.stages.step_up(2*mstep)
        self.stages.step_left(mstep)

        # Stitch the images
        cmdstr = "magick convert background_3x3.png "
        cmdstr += chippath + "/*1.png -gravity Northwest -geometry +0+0 -composite "
        cmdstr += chippath + "/*2.png -geometry +760+0 -composite "
        cmdstr += chippath + "/*3.png -geometry +1520+0 -composite "
        cmdstr += chippath + "/*6.png -geometry +0+760 -composite "
        cmdstr += chippath + "/*5.png -geometry +760+760 -composite "
        cmdstr += chippath + "/*4.png -geometry +1520+760 -composite "
        cmdstr += chippath + "/*7.png -geometry +0+1520 -composite "
        cmdstr += chippath + "/*8.png -geometry +760+1520 -composite "
        cmdstr += chippath + "/*9.png -geometry +1520+1520 -composite "
        cmdstr += chippath + "/" + chipname + "_" + self.__timestring + "_stitch.png"
        os.system(cmdstr)

        """
        # For non-rotated image
        # Stitch the images
        cmdstr = "magick convert background_3x3.png "
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
        """

        self.infotext("Stitch ready")
        self.set_measuring(False)

    def measure_9(self, directory, basename, stitchname):
        """
        Create a stitch of 9 pictures
        Begins and ends at the center
        :param directory: Directory for the stitch
        :param basename: Name of the measurement the stitch is part of
        :param stitchname: Name of this particular stitch
        :return: -
        """
        mstep = 36000
        sleeptime = 0.5

        self.infotext("Measuring " + stitchname)
        print("Measuring", stitchname)
        os.makedirs(directory)

        self.stages.step_left(mstep)
        self.stages.step_up(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_1", directory)

        self.stages.step_right(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_2", directory)

        self.stages.step_right(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_3", directory)

        self.stages.step_down(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_4", directory)

        self.stages.step_left(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_5", directory)

        self.stages.step_left(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_6", directory)

        self.stages.step_down(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_7", directory)

        self.stages.step_right(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_8", directory)

        self.stages.step_right(mstep)
        time.sleep(sleeptime)
        self.camera.takepic(basename + "_" + self.__timestring + "_" + stitchname + "_9", directory)

        self.stages.step_left(mstep)
        self.stages.step_up(mstep)
        time.sleep(sleeptime)

        stitch_thread = threading.Thread(target=self.stitch_9, args=(directory, basename, stitchname))
        stitch_thread.start()

    def stitch_9(self, directory, basename, stitchname):
        """
        Stitches a set of 9 pictures using ImageMagick
        Actually it builds a terminal command and starts ImageMagick using a virtual terminal
        :param directory: directory in which the images are
        :param basename: name of the measurement
        :param stitchname: name of this particular stitch
        :return: -
        """
        cmdstr = "magick convert background_3x3.png "
        cmdstr += directory + "/*1.png -gravity Northwest -geometry +0+0 -composite "
        cmdstr += directory + "/*2.png -geometry +760+0 -composite "
        cmdstr += directory + "/*3.png -geometry +1520+0 -composite "
        cmdstr += directory + "/*6.png -geometry +0+760 -composite "
        cmdstr += directory + "/*5.png -geometry +760+760 -composite "
        cmdstr += directory + "/*4.png -geometry +1520+760 -composite "
        cmdstr += directory + "/*7.png -geometry +0+1520 -composite "
        cmdstr += directory + "/*8.png -geometry +760+1520 -composite "
        cmdstr += directory + "/*9.png -geometry +1520+1520 -composite "
        cmdstr += directory + "/" + basename + "_" + self.__timestring + "_" + stitchname + "_stitch.png"
        os.system(cmdstr)
        print("Stitch", stitchname, "ready")

    def measure_wafer_threaded(self):
        """
        Threading support for wafer measurement
        :return: -
        """
        if self.__measuring:
            self.infotext("Measurement already running")
        else:
            thread = threading.Thread(target=self.measure_wafer)
            thread.start()

    def measure_wafer(self):
        if self.__currentdir == "":
            self.infotext("The base directory has not been set")
            return

        wafername = self.__sampleEntry.get()
        waferpath = self.__currentdir + "/" + wafername + "_" + self.__timestring
        sleeptime = 5

        if os.path.exists(waferpath):
            self.infotext("The wafer directory already exists")
            return 1

        self.infotext("Measuring wafer")
        self.set_measuring(True)

        os.makedirs(waferpath)

        self.stages.mm_up(5)
        time.sleep(sleeptime)
        self.measure_9(waferpath + "/00x-20", wafername, "00x-20")

        self.stages.mm_up(10)
        time.sleep(sleeptime)
        self.measure_9(waferpath + "/00x-10", wafername, "00x-10")

        self.stages.mm_up(10)
        time.sleep(sleeptime)
        self.measure_9(waferpath + "/00x00", wafername, "00x00")

        self.stages.mm_up(10)
        time.sleep(sleeptime)
        self.measure_9(waferpath + "/00x10", wafername, "00x10")

        self.stages.mm_up(10)
        time.sleep(sleeptime)
        self.measure_9(waferpath + "/00x20", wafername, "00x20")

        self.stages.mm_down(20)
        self.stages.mm_left(20)
        time.sleep(3*sleeptime)
        self.measure_9(waferpath + "/-20x00", wafername, "-20x00")

        self.stages.mm_right(10)
        time.sleep(sleeptime)
        self.measure_9(waferpath + "/-10x00", wafername, "-10x00")

        self.stages.mm_right(20)
        time.sleep(2*sleeptime)
        self.measure_9(waferpath + "/10x00", wafername, "10x00")

        self.stages.mm_right(10)
        time.sleep(sleeptime)
        self.measure_9(waferpath + "/20x00", wafername, "20x00")

        self.stages.mm_left(20)
        self.stages.mm_down(25)

        self.infotext("Wafer ready")
        print("Wafer ready")

        self.set_measuring(False)

    def set_corner1(self):
        """
        Sets corner 1 to the current position
        :return: -
        """
        coords = self.stages.where()
        self.__corner1 = coords
        print("Corner 1 set to", coords)
        self.infotext("Corner 1 set to (" + str(coords[0]) + "," + str(coords[1]) + ")")

    def set_corner2(self):
        """
        Sets corner 2 to the current position
        :return: -
        """
        coords = self.stages.where()
        self.__corner2 = coords
        print("Corner 2 set to", coords)
        self.infotext("Corner 2 set to (" + str(coords[0]) + "," + str(coords[1]) + ")")

    def reset_coords(self):
        self.stages.reset_coords()
        self.__corner1 = (0, 0)
        self.__corner2 = (0, 0)

    def measure_area_threaded(self):
        """
        Threading support for area measurements
        :return: -
        """
        if self.__measuring:
            self.infotext("Measurement already running")
        else:
            thread = threading.Thread(target=self.measure_area)
            thread.start()

    def measure_area(self):
        """
        Measures a custom area defined by two corners
        :return: -
        """
        if self.__currentdir == "":
            self.infotext("The base directory has not been set")
            return

        area_name = self.__sampleEntry.get()
        directory = self.__currentdir + "/" + area_name + "_" + self.__timestring

        if os.path.exists(directory):
            self.infotext("The directory already exists")
            return

        if self.__corner1 == self.__corner2:
            self.infotext("The corners should have different coordinates")
            return

        # Start actually doing things

        self.infotext("Measuring Area")
        print("Measuring Area")
        os.makedirs(directory)
        self.set_measuring(True)

        mstep = 36000
        sleeptime_x = 0.3
        sleeptime_y = 0.5
        x_width = int(math.ceil(abs(self.__corner1[0] - self.__corner2[0]) / mstep))
        y_width = int(math.ceil(abs(self.__corner1[1] - self.__corner2[1]) / mstep))
        i = 1
        total = x_width * y_width

        startpos = self.stages.where()

        # Move to upper left corner
        dx = min(self.__corner1[0], self.__corner2[0])
        dy = max(self.__corner1[1], self.__corner2[1])
        self.stages.goto(dx, dy)

        initial_move_time = self.stages.time(startpos[0] - self.__corner1[0], startpos[1] - self.__corner1[1])
        print("Expected initial movement time:", initial_move_time)
        time.sleep(initial_move_time)

        for y in range(1, y_width+1):
            for x in range(1, x_width+1):
                self.takepic_area(area_name, directory, i, total)
                i += 1

                if x < x_width:
                    if y % 2 == 0:
                        self.stages.step_left(mstep)
                    else:
                        self.stages.step_right(mstep)
                    time.sleep(sleeptime_x)
                else:
                    if y < y_width:
                        self.stages.step_down(mstep)
                        time.sleep(sleeptime_y)

        self.set_measuring(False)
        self.infotext("Area measured")

    def measure_entire_wafer_threaded(self):
        """
        Measures an entire 50 mm wafer
        The resulting folder is about 6 GB
        :return: -
        """
        currentpos = self.stages.where()

        self.__corner1 = (int(round(currentpos[0] - (self.stages.mm_to_steps * 26))),
                          int(round(currentpos[1] + (self.stages.mm_to_steps * 52))))

        self.__corner2 = (int(round(currentpos[0] + (self.stages.mm_to_steps * 26))),
                          int(round(currentpos[1])))

        self.measure_area_threaded()

        # Return to the original position
        self.stages.goto(currentpos[0], currentpos[1])


def main():
    DSM()

main()

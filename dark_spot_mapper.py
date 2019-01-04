"""This software is for controlling the Dark Spot Mapper

Dark Spot Mapper is a measurement device at the Optoelectronics Research Centre of Tampere University [of Technology]

Copyright 2016-2019 Mika Mäki & Tampere University of Technology
Mika would like to license this program with GPLv3+ but it would require some university bureaucracy

Requires
- PyQtGraph
- Matplotlib
- Numpy
- NI IMAQdx
- Pynivision
- Granite Devices SimpleMotion DLL (bitness must match that of Python)
- ImageMagick

TODO LIST
- code reorganising & rework
- add focusing spots to the chip view
- save camera parameters
- averaging to remove ripple
- stitching on the numpy level (matrix concatenation?)
- support for multiple cameras
- fix the long camera startup time
- click-to-move
- connection to vxl_intra (log uploads?)
- autofocus
- GUI for changing stitch wait times
"""

# Program modules
import dsm_exceptions
import ni_camera
import simplemotion

# GUI
import tkinter
import tkinter.filedialog

# Basic libraries
import logging
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

logger = logging.getLogger(__name__)

logging.basicConfig(
    handlers=[
        logging.FileHandler("logs/DSM_log_{}.txt".format(time.strftime("%Y-%m-%d_%H-%M-%S"))),
        logging.StreamHandler()
    ],
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-8s %(module)-16s %(message)s'
)

WINDOW_TITLE = "ORC Dark Spot Mapper"


class QtDisp:
    """This class provides a window for the camera video"""
    def __init__(self, camera, auto_levels):
        self.__camera = camera

        self.__auto_levels = auto_levels

        app = pg.mkQApp()

        win = QtGui.QMainWindow()
        win.resize(1200, 700)
        self.__imv = pg.ImageView()
        win.setCentralWidget(self.__imv)
        win.setWindowTitle(WINDOW_TITLE)
        win.show()

        # This line prevents a bug at image leveling
        self.__imv.setLevels(0.1, 0.9)

        self.take_frame()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.take_frame)
        timer.start(50)

        app.exec()

    def take_frame(self) -> None:
        """Fetches a frame from the camera and displays it

        :return: -
        """
        self.__camera.take_frame()

        # The camera.take_frame() saves the frame on a RAM disk since transporting the image directly from
        # NI Vision to Python would result in a memory leak
        mat_img = matplotlib.image.imread("R:\\nivisiontemp.png")
        transposed = np.transpose(mat_img)

        if self.__auto_levels:
            self.__imv.setImage(transposed, autoLevels=True)
        else:
            self.__imv.setImage(transposed, levels=(0, 1))


class DSM:
    """This is the primary class of the Dark Spot Mapper"""
    def __init__(self):
        logger.info("Starting")

        gc.enable()
        # gc.set_debug(gc.DEBUG_LEAK)
        # gc.set_debug(gc.DEBUG_UNCOLLECTABLE)

        self.__current_dir = ""
        self.__time_str = time.strftime("%Y-%m-%d")
        self.__measuring = False
        self.__aborting = False
        self.__stitch_lock = threading.Lock()

        self.__corner1 = (0, 0)
        self.__corner2 = (0, 0)

        # Camera variables
        self.__camname = b"cam0"
        self.__camquality = 10000
        cam_label_texts = ["Auto Exposure", "Brightness", "Gain", "Gamma", "Sharpness", "Shutter"]
        cam_default_settings = [256, 1500, 0, 0, 4, 230]

        # Stage setup
        self.stages = simplemotion.SimpleMotion()

        # Camera setup
        self.camera = ni_camera.NI_Camera(self.__camname, self.__camquality)

        # Qt thread & window

        self.qt_thread = threading.Thread(target=QtDisp, args=(self.camera, False))
        self.qt_thread.start()

        # UI creation

        self.__mainWindow = tkinter.Tk()
        self.__mainWindow.title(WINDOW_TITLE)

        # Miscellaneous
        self.__measuringTextVar = tkinter.StringVar()
        measuring_label = tkinter.Label(self.__mainWindow, textvar=self.__measuringTextVar)
        measuring_label.grid(row=6, columnspan=6)

        self.__infoVar = tkinter.StringVar()

        info_label = tkinter.Label(self.__mainWindow, textvar=self.__infoVar)
        info_label.grid(row=8, columnspan=11)

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

        self.__abortButton = tkinter.Button(self.__mainWindow, text="Abort", command=self.abort)
        self.__abortButton.grid(row=5, column=5)

        # Picture elements

        self.__picVar = tkinter.StringVar()
        self.__picEntry = tkinter.Entry(self.__mainWindow, textvariable=self.__picVar)
        self.__picVar.set("PicName")
        self.__picEntry.grid(row=0, column=6)

        self.__picButton = tkinter.Button(self.__mainWindow, text="Take picture", command=self.takepic)
        self.__picButton.grid(row=1, column=6)

        self.__folderButton = tkinter.Button(self.__mainWindow, text="Set folder", command=self.choose_dir)
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

        cam_column = 7

        # Elements for Qt

        cam_range_label = tkinter.Label(self.__mainWindow, text="Camera autorange")
        cam_range_label.grid(row=0, column=cam_column)

        self.__camRangeVar = tkinter.BooleanVar()
        self.__camRangeVar.set(False)

        self.__camRangeOnButton = tkinter.Radiobutton(self.__mainWindow, text="on", variable=self.__camRangeVar,
                                                      value=True)
        self.__camRangeOnButton.grid(row=1, column=cam_column)

        self.__camRangeOffButton = tkinter.Radiobutton(self.__mainWindow, text="off", variable=self.__camRangeVar,
                                                       value=False)
        self.__camRangeOffButton.grid(row=2, column=cam_column)

        self.__qtRestartButton = tkinter.Button(self.__mainWindow, text="Restart view", command=self.qt_restart)
        self.__qtRestartButton.grid(row=3, column=cam_column)

        self.__debugButton = tkinter.Button(self.__mainWindow, text="Debug", command=self.debug)
        self.__debugButton.grid(row=4, column=cam_column)

        # Elements for camera settings

        for index, text in enumerate(cam_label_texts):
            label = tkinter.Label(self.__mainWindow, text=text)
            label.grid(row=index, column=cam_column+1)

        self.__camVars = []

        for index in range(6):
            self.__camVars.append(tkinter.StringVar())
            self.__camVars[index].set(str(cam_default_settings[index]))
            entry = tkinter.Entry(self.__mainWindow, textvariable=self.__camVars[index])
            entry.grid(row=index, column=cam_column+2)

        self.set_cam_settings()

        self.__camSetButton = tkinter.Button(self.__mainWindow, text="Set values", command=self.set_cam_settings)
        self.__camSetButton.grid(row=len(cam_label_texts), column=cam_column+2)

        cam_limits = ["256-1023", "0-2047", "0-680", "0-3", "0-7", "3-1150"]

        for index, text in enumerate(cam_limits):
            label = tkinter.Label(self.__mainWindow, text=text)
            label.grid(row=index, column=cam_column+3)

        # self.__creatorText = tkinter.Label(self.__mainWindow, text="Created by Mika Mäki, work in progress")
        # self.__creatorText.grid(row=3, columnspan=3)

        # Create a list of buttons that should be disabled when measuring
        self.__sensitiveButtons = [self.__upButton, self.__leftButton, self.__rightButton, self.__downButton,
                                   self.__corner1_Button, self.__corner2_Button, self.__resetCoords_Button,
                                   self.__chipButton, self.__waferButton, self.__waferFullButton, self.__areaButton,
                                   self.__folderButton]

        logger.info("Program ready")
        self.info_text("")
        self.__mainWindow.mainloop()

    def abort(self):
        if not self.__aborting:
            thread = threading.Thread(target=self.abort_threaded)
            thread.start()

    def abort_threaded(self):
        self.info_text("Aborting")
        self.__aborting = True
        for button in self.__sensitiveButtons:
            button.config(state=tkinter.DISABLED)

        self.stages.abort()
        self.__corner1 = (0, 0)
        self.__corner2 = (0, 0)
        self.info_text("Aborted")
        self.__aborting = False
        self.set_measuring(False)

    @staticmethod
    def debug() -> None:
        """Prints debug information for hunting NI Vision memory leaks etc.

        :return: -
        """
        print(gc.get_stats())
        print(gc.garbage)
        print(objgraph.show_most_common_types())

    def info_text(self, text: str) -> None:
        self.__infoVar.set(text)
        logger.info(text)

    def set_cam_settings(self) -> None:
        if self.camera.set_cam_settings(self.__camVars):
            self.info_text("Camera configuration successful")
        else:
            self.info_text("Camera configuration failed")

    def takepic(self) -> None:
        self.camera.takepic(self.__picVar.get(), self.__current_dir)

    def takepic_chip(self, chip_name: str, chip_path: str, number: int) -> None:
        filename = "{}_{}_{}".format(chip_name, self.__time_str, number)
        self.camera.takepic(filename, chip_path)

    def takepic_area(self, name: str, path: str, number: int, total: int) -> None:
        padded_number = str(number).zfill(int(math.ceil(math.log10(total + 1))))
        filename = "{}_{}_{}".format(name, self.__time_str, padded_number)
        self.camera.takepic(filename, path)

    def qt_restart(self) -> None:
        if not self.qt_thread.is_alive():
            autorange = self.__camRangeVar.get()
            self.qt_thread = threading.Thread(target=QtDisp, args=(self.camera, autorange))
            self.qt_thread.start()

    def choose_dir(self) -> None:
        new_dir = tkinter.filedialog.askdirectory()
        if new_dir == "":
            self.info_text("New directory is blank and thereby not set")
        else:
            self.__current_dir = new_dir
            self.info_text("Current folder set to: {}".format(self.__current_dir))

    def up(self) -> None:
        if self.__use_mmVar.get():
            self.stages.mm_up(float(self.__mmVar.get()))
        else:
            self.stages.step_up(int(self.__stepVar.get()))

    def down(self) -> None:
        if self.__use_mmVar.get():
            self.stages.mm_down(float(self.__mmVar.get()))
        else:
            self.stages.step_down(int(self.__stepVar.get()))

    def left(self) -> None:
        if self.__use_mmVar.get():
            self.stages.mm_left(float(self.__mmVar.get()))
        else:
            self.stages.step_left(int(self.__stepVar.get()))

    def right(self) -> None:
        if self.__use_mmVar.get():
            self.stages.mm_right(float(self.__mmVar.get()))
        else:
            self.stages.step_right(int(self.__stepVar.get()))

    def zup(self) -> None:
        if self.__use_mmVar.get():
            self.info_text("Z axis doesn't support mm")
        else:
            self.stages.step_zup(int(self.__stepVar.get()))

    def zdown(self) -> None:
        if self.__use_mmVar.get():
            self.info_text("Z axis doesn't support mm")
        else:
            self.stages.step_zdown(int(self.__stepVar.get()))

    def set_measuring(self, status) -> None:
        """Set whether there currently is a measurement in progress

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

    def measure_chip_threaded(self) -> None:
        """Threading support for chip measurement

        :return: -
        """
        if self.__measuring:
            self.info_text("Measurement already running")
        else:
            thread = threading.Thread(target=self.measure_chip, name="measurement")
            thread.start()

    def measure_chip(self) -> None:
        """Measure a single pentagon VECSEL chip

        Begins from the "north" corner and returns there
        :return:
        """
        try:
            if self.__current_dir == "":
                self.info_text("The base directory has not been set")
                return

            mstep = 36000
            sleep_time = 0.5
            chip_name = self.__sampleVar.get()

            chip_path = self.__current_dir + "/" + chip_name + "_" + self.__time_str
            # print(chip_path)

            if os.path.exists(chip_path):
                self.info_text("The chip directory already exists")
                return

            self.info_text("Measuring chip")
            self.set_measuring(True)

            os.makedirs(chip_path)

            self.stages.step_left(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 1)

            self.stages.step_right(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 2)

            self.stages.step_right(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 3)

            self.stages.step_down(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 4)

            self.stages.step_left(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 5)

            self.stages.step_left(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 6)

            self.stages.step_down(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 7)

            self.stages.step_right(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 8)

            self.stages.step_right(mstep)
            time.sleep(sleep_time)
            self.takepic_chip(chip_name, chip_path, 9)

            # Return to the previous position
            self.stages.step_up(2*mstep)
            self.stages.step_left(mstep)

            self.__stitch_lock.acquire()
            # Stitch the images
            cmdstr = "magick convert background_3x3.png "
            cmdstr += chip_path + "/*1.png -gravity Northwest -geometry +0+0 -composite "
            cmdstr += chip_path + "/*2.png -geometry +760+0 -composite "
            cmdstr += chip_path + "/*3.png -geometry +1520+0 -composite "
            cmdstr += chip_path + "/*6.png -geometry +0+760 -composite "
            cmdstr += chip_path + "/*5.png -geometry +760+760 -composite "
            cmdstr += chip_path + "/*4.png -geometry +1520+760 -composite "
            cmdstr += chip_path + "/*7.png -geometry +0+1520 -composite "
            cmdstr += chip_path + "/*8.png -geometry +760+1520 -composite "
            cmdstr += chip_path + "/*9.png -geometry +1520+1520 -composite "
            cmdstr += chip_path + "/" + chip_name + "_" + self.__time_str + "_stitch.png"
            os.system(cmdstr)
            self.__stitch_lock.release()

            """
            # For non-rotated image
            # Stitch the images
            cmdstr = "magick convert background_3x3.png "
            cmdstr += chip_path + "/*9.png -gravity Northwest -geometry +0+0 -composite "
            cmdstr += chip_path + "/*8.png -geometry +760+0 -composite "
            cmdstr += chip_path + "/*7.png -geometry +1520+0 -composite "
            cmdstr += chip_path + "/*4.png -geometry +0+760 -composite "
            cmdstr += chip_path + "/*5.png -geometry +760+760 -composite "
            cmdstr += chip_path + "/*6.png -geometry +1520+760 -composite "
            cmdstr += chip_path + "/*3.png -geometry +0+1520 -composite "
            cmdstr += chip_path + "/*2.png -geometry +760+1520 -composite "
            cmdstr += chip_path + "/*1.png -geometry +1520+1520 -composite "
            cmdstr += chip_path + "/" + chip_name + "_" + self.__timestring + "_stitch.png"
            os.system(cmdstr)
            """

            self.info_text("Stitch ready")
            self.set_measuring(False)
        except dsm_exceptions.AbortException:
            self.info_text("Chip measurement aborted")

    def measure_9(self, directory: str, basename: str, stitch_name: str) -> None:
        """Create a stitch of 9 pictures

        Begins and ends at the center
        :param directory: Directory for the stitch
        :param basename: Name of the measurement the stitch is part of
        :param stitch_name: Name of this particular stitch
        :return: -
        """

        try:
            mstep = 36000
            sleep_time = 0.5

            self.info_text("Measuring " + stitch_name)
            os.makedirs(directory)

            self.stages.step_left(mstep)
            self.stages.step_up(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_1", directory)

            self.stages.step_right(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_2", directory)

            self.stages.step_right(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_3", directory)

            self.stages.step_down(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_4", directory)

            self.stages.step_left(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_5", directory)

            self.stages.step_left(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_6", directory)

            self.stages.step_down(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_7", directory)

            self.stages.step_right(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_8", directory)

            self.stages.step_right(mstep)
            time.sleep(sleep_time)
            self.camera.takepic(basename + "_" + self.__time_str + "_" + stitch_name + "_9", directory)

            self.stages.step_left(mstep)
            self.stages.step_up(mstep)
            time.sleep(sleep_time)

            stitch_thread = threading.Thread(target=self.stitch_9, name="stitch", args=(directory, basename, stitch_name))
            stitch_thread.start()
        except dsm_exceptions.AbortException:
            raise dsm_exceptions.AbortException

    def stitch_9(self, directory: str, basename: str, stitch_name: str) -> None:
        """Stitches a set of 9 pictures using ImageMagick

        Actually it builds a terminal command and starts ImageMagick using a virtual terminal
        :param directory: directory in which the images are
        :param basename: name of the measurement
        :param stitch_name: name of this particular stitch
        :return: -
        """
        self.__stitch_lock.acquire()
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
        cmdstr += directory + "/" + basename + "_" + self.__time_str + "_" + stitch_name + "_stitch.png"
        os.system(cmdstr)
        self.__stitch_lock.release()
        logger.info("Stitch %s ready", stitch_name)

    def measure_wafer_threaded(self) -> None:
        """Threading support for wafer measurement

        :return: -
        """
        if self.__measuring:
            self.info_text("Measurement already running")
        else:
            thread = threading.Thread(target=self.measure_wafer)
            thread.start()

    def measure_wafer(self):
        try:
            if self.__current_dir == "":
                self.info_text("The base directory has not been set")
                return

            wafer_name = self.__sampleEntry.get()
            wafer_path = self.__current_dir + "/" + wafer_name + "_" + self.__time_str
            sleep_time = 5.5

            if os.path.exists(wafer_path):
                self.info_text("The wafer directory already exists")
                return 1

            self.info_text("Measuring wafer")
            self.set_measuring(True)

            os.makedirs(wafer_path)

            self.stages.mm_up(5)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/00x-20", wafer_name, "00x-20")

            self.stages.mm_up(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/00x-10", wafer_name, "00x-10")

            self.stages.mm_right(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/10x-10", wafer_name, "10x-10")

            self.stages.mm_up(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/10x00", wafer_name, "10x00")

            self.stages.mm_right(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/20x00", wafer_name, "20x00")

            self.stages.mm_left(10)
            self.stages.mm_up(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/10x10", wafer_name, "10x10")

            self.stages.mm_left(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/00x10", wafer_name, "00x10")

            self.stages.mm_up(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/00x20", wafer_name, "00x20")

            self.stages.mm_down(10)
            self.stages.mm_left(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/-10x10", wafer_name, "-10x10")

            self.stages.mm_down(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/-10x00", wafer_name, "-10x00")

            self.stages.mm_left(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/-20x00", wafer_name, "-20x00")

            self.stages.mm_right(10)
            self.stages.mm_down(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/-10x-10", wafer_name, "-10x-10")

            self.stages.mm_up(10)
            self.stages.mm_right(10)
            time.sleep(sleep_time)
            self.measure_9(wafer_path + "/00x00", wafer_name, "00x00")

            self.stages.mm_down(25)

            self.__stitch_lock.acquire()
            self.info_text("Stitching wafer")
            cmdstr = "magick convert background_wafer.png "
            cmdstr += wafer_path + "/00x20/*stitch.png -gravity Northwest -geometry +5800+0 -composite "
            cmdstr += wafer_path + "/00x10/*stitch.png -geometry +5800+2580 -composite "
            cmdstr += wafer_path + "/-10x10/*stitch.png -geometry +2900+2580 -composite "
            cmdstr += wafer_path + "/10x10/*stitch.png -geometry +8700+2580 -composite "
            cmdstr += wafer_path + "/00x00/*stitch.png -geometry +5800+5160 -composite "
            cmdstr += wafer_path + "/-20x00/*stitch.png -geometry +0+5160 -composite "
            cmdstr += wafer_path + "/-10x00/*stitch.png -geometry +2900+5160 -composite "
            cmdstr += wafer_path + "/10x00/*stitch.png -geometry +8700+5160 -composite "
            cmdstr += wafer_path + "/20x00/*stitch.png -geometry +11600+5160 -composite "
            cmdstr += wafer_path + "/00x-10/*stitch.png -geometry +5800+7740 -composite "
            cmdstr += wafer_path + "/-10x-10/*stitch.png -geometry +2900+7740 -composite "
            cmdstr += wafer_path + "/10x-10/*stitch.png -geometry +8700+7740 -composite "
            cmdstr += wafer_path + "/00x-20/*stitch.png -geometry +5800+10320 -composite "
            cmdstr += wafer_path + "/" + wafer_name + "_" + self.__time_str + "_stitch.png"
            os.system(cmdstr)
            self.__stitch_lock.release()
            logger.info("Stitch of %s ready", wafer_name)

            self.info_text("Wafer ready")
            self.set_measuring(False)
        except dsm_exceptions.AbortException:
            self.info_text("Wafer measurement aborted")

    def set_corner1(self) -> None:
        """Sets corner 1 to the current position

        :return: -
        """
        coords = self.stages.where()
        self.__corner1 = coords
        logger.info("Corner 1 set to %s", coords)
        self.info_text("Corner 1 set to (" + str(coords[0]) + "," + str(coords[1]) + ")")

    def set_corner2(self) -> None:
        """Sets corner 2 to the current position

        :return: -
        """
        coords = self.stages.where()
        self.__corner2 = coords
        logger.info("Corner 2 set to %s", coords)
        self.info_text("Corner 2 set to (" + str(coords[0]) + "," + str(coords[1]) + ")")

    def reset_coords(self) -> None:
        self.stages.reset_coords()
        self.__corner1 = (0, 0)
        self.__corner2 = (0, 0)

    def measure_area_threaded(self) -> None:
        """Threading support for area measurements

        :return: -
        """
        if self.__measuring:
            self.info_text("Measurement already running")
        else:
            thread = threading.Thread(target=self.measure_area, name="measurement")
            thread.start()

    def measure_area(self) -> None:
        """Measures a custom area defined by two corners

        :return: -
        """
        try:
            if self.__current_dir == "":
                self.info_text("The base directory has not been set")
                return

            area_name = self.__sampleEntry.get()
            directory = self.__current_dir + "/" + area_name + "_" + self.__time_str

            if os.path.exists(directory):
                self.info_text("The directory already exists")
                return

            if self.__corner1 == self.__corner2:
                self.info_text("The corners should have different coordinates")
                return

            # Start actually doing things

            self.info_text("Measuring Area")
            # print("Measuring Area")
            os.makedirs(directory)
            self.set_measuring(True)

            mstep = 36000
            sleeptime_x = 0.3
            sleeptime_y = 0.5
            x_width = int(math.ceil(abs(self.__corner1[0] - self.__corner2[0]) / mstep))
            y_width = int(math.ceil(abs(self.__corner1[1] - self.__corner2[1]) / mstep))
            i = 1
            total = x_width * y_width

            start_pos = self.stages.where()

            # Move to upper left corner
            dx = min(self.__corner1[0], self.__corner2[0])
            dy = max(self.__corner1[1], self.__corner2[1])
            self.stages.goto(dx, dy)

            initial_move_time = self.stages.time(start_pos[0] - self.__corner1[0], start_pos[1] - self.__corner1[1])
            logger.info("Expected initial movement time: %f", initial_move_time)
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

            self.info_text("Area measured")

            self.set_measuring(False)
        except dsm_exceptions.AbortException:
            self.info_text("Area measurement aborted")

    def measure_entire_wafer_threaded(self) -> None:
        """Measures an entire 50 mm wafer

        The resulting folder is about 6 GB
        :return: -
        """
        if self.__measuring:
            self.info_text("Measurement already running")
        else:
            thread = threading.Thread(target=self.measure_entire_wafer, name="measurement")
            thread.start()

    def measure_entire_wafer(self) -> None:
        current_pos = self.stages.where()

        self.__corner1 = (int(round(current_pos[0] - (self.stages.mm_to_steps * 26))),
                          int(round(current_pos[1] + (self.stages.mm_to_steps * 52))))

        self.__corner2 = (int(round(current_pos[0] + (self.stages.mm_to_steps * 26))),
                          int(round(current_pos[1])))

        self.measure_area()

        if not self.__aborting:
            # Return to the original position
            self.stages.goto(current_pos[0], current_pos[1])


if __name__ == "__main__":
    DSM()

import numpy as np
from PySide2.QtWidgets import \
    QDockWidget, QMainWindow, QLabel, QLineEdit, QPushButton, QRadioButton, QWidget, \
    QBoxLayout, QGridLayout, QVBoxLayout, \
    QApplication, QSizePolicy
from PySide2 import QtCore
import pyqtgraph as pg

import devices.camera_opencv as cv

pg.setConfigOptions(antialias=True)


ALIGNMENT = QtCore.Qt.Alignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)


class ArrowsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fixed = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setSizePolicy(fixed)
        layout = QGridLayout()
        self.up = QPushButton(text="▲")
        self.down = QPushButton(text="▼")
        self.left = QPushButton(text="◄")
        self.right = QPushButton(text="►")
        self.zup = QPushButton(text="▲")
        self.zdown = QPushButton(text="▼")
        layout.addWidget(self.up, 0, 1)
        layout.addWidget(self.down, 2, 1)
        layout.addWidget(self.left, 1, 0)
        layout.addWidget(self.right, 1, 2)
        layout.addWidget(self.zup, 0, 3)
        layout.addWidget(self.zdown, 1, 3)
        self.setLayout(layout)


class StepControls(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.steps_button = QRadioButton("Steps")
        self.steps_button.setChecked(True)
        self.mm_button = QRadioButton("mm")
        self.steps_box = QLineEdit("18000")
        self.mm_box = QLineEdit("1")
        layout = QGridLayout()
        layout.setAlignment(ALIGNMENT)
        layout.addWidget(self.steps_button, 0, 0)
        layout.addWidget(self.mm_button, 1, 0)
        layout.addWidget(self.steps_box, 0, 1)
        layout.addWidget(self.mm_box, 1, 1)
        self.setLayout(layout)


class MeasurementControls(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pic_name_box = QLineEdit("PicName")
        self.take_pic_button = QPushButton("Take picture")
        self.set_folder_button = QPushButton("Set folder")
        self.sample_id_box = QLineEdit("Sample_ID")
        self.measure_chip_button = QPushButton("Measure chip")
        self.measure_wafer_button = QPushButton("Measure wafer")
        self.measure_entire_wafer_button = QPushButton("Measure entire wafer")
        self.measure_area_button = QPushButton("Measure area")
        layout = QVBoxLayout()
        layout.addWidget(self.pic_name_box)
        layout.addWidget(self.take_pic_button)
        layout.addWidget(self.set_folder_button)
        layout.addWidget(self.sample_id_box)
        layout.addWidget(self.measure_chip_button)
        layout.addWidget(self.measure_wafer_button)
        layout.addWidget(self.measure_entire_wafer_button)
        layout.addWidget(self.measure_area_button)
        self.setLayout(layout)


class AutorangeControls(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_button = QRadioButton("on")
        self.on_button.setChecked(True)
        self.off_button = QRadioButton("off")
        layout = QVBoxLayout()
        layout.setAlignment(ALIGNMENT)
        layout.addWidget(QLabel("Camera autorange"))
        layout.addWidget(self.on_button)
        layout.addWidget(self.off_button)
        self.setLayout(layout)


class CameraParamsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QGridLayout()
        labels = [
            ("Auto Exposure", 256, "256-1023", cv.Props.AUTO_EXPOSURE),
            ("Brightness", 1500, "0-2047", cv.Props.BRIGHTNESS),
            ("Gain", 0, "0-680", cv.Props.GAIN),
            ("Gamma", 0, "0-3", cv.Props.GAMMA),
            ("Sharpness", 4, "0-7", cv.Props.SHARPNESS),
            ("Shutter", 230, "3-1150", cv.Props.EXPOSURE)
        ]
        self.boxes = [QLineEdit() for _ in labels]
        for i, label in enumerate(labels):
            layout.addWidget(QLabel(label[0]), i, 0)
            layout.addWidget(self.boxes[i], i, 1)
            layout.addWidget(QLabel(label[2]), i, 2)
        self.set_button = QPushButton("Set parameters")
        layout.addWidget(self.set_button, len(labels), 1)
        self.setLayout(layout)


class Controls(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arrows = ArrowsWidget()
        self.steps = StepControls()
        self.measure = MeasurementControls()
        self.autorange = AutorangeControls()
        self.params = CameraParamsWidget()
        layout = QBoxLayout(QBoxLayout.LeftToRight)
        layout.addWidget(self.arrows)
        layout.addWidget(self.steps)
        layout.addWidget(self.measure)
        layout.addWidget(self.autorange)
        layout.addWidget(self.params)
        self.setLayout(layout)


class CameraView(pg.ImageView):
    # Todo: https://www.pyimagesearch.com/2015/12/21/increasing-webcam-fps-with-python-and-opencv/
    def __init__(self, auto_levels: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_levels = auto_levels

    def show(self, img: np.ndarray):
        transposed = np.transpose(img) / 255
        if self.auto_levels:
            self.__imv.setImage(transposed, autoLevels=True)
        else:
            self.__imv.setImage(transposed, levels=(0, 1))


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ORC & Vexlum Dark Spot Mapper")
        # self.setWindowIcon(QtGui.QIcon("vexlum-favicon.png"))
        self.menu = self.menuBar()

        self.imv = CameraView()
        self.setCentralWidget(self.imv)

        self.controls = Controls()
        self.dock = QDockWidget()
        self.dock.setWidget(self.controls)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.dock)


def __test():
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec_()


if __name__ == "__main__":
    __test()

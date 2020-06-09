import logging
import time

from PySide2 import QtWidgets

from devices.camera_opencv import CameraCV
import dsm_gui


logging.basicConfig(
    handlers=[
        logging.FileHandler("logs/DSM_log_{}.txt".format(time.strftime("%Y-%m-%d_%H-%M-%S"))),
        logging.StreamHandler()
    ],
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-8s %(module)-16s %(message)s'
)


def main():
    app = QtWidgets.QApplication([])
    mw = dsm_gui.MainWindow()
    mw.show()
    app.exec_()


if __name__ == "__main__":
    main()

import os
import unittest

from devices import camera_ni

CAMERA_NAME = "cam0"
QUALITY = 10000


class NICameraTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.camera = camera_ni.NI_Camera(CAMERA_NAME, QUALITY)

    def test_set_setting(self):
        self.camera.set_cam_setting(camera_ni.CameraSettings.SHUTTER, 500)

    def test_take_pic(self):
        self.camera.take_pic()

    def test_save_pic(self):
        path = os.path.dirname(os.path.abspath(__file__))
        filename = "test"
        if os.path.exists(filename):
            raise RuntimeError("Test image already exists")
        self.camera.save_pic(directory=path, filename=filename)
        file_path = "{}.png".format(os.path.join(path, filename))
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            raise AssertionError("Image was not created at {}".format(file_path))

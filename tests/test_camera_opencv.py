import unittest

import cv2

from devices import camera_opencv as cam_cv

print(cv2.getBuildInformation())


class CameraCVTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cam = cam_cv.CameraCV()

    def test_print_props(self):
        self.cam.print_props()

    def test_set_resolution(self):
        self.cam.set_resolution(width=1280, height=960)

    def test_set_firewire_speed(self):
        self.cam.set_prop(cam_cv.Props.ISO_SPEED, 800)

    def test_get_frame(self):
        self.cam.get_frame()

    def test_imshow(self):
        gray = self.cam.get_frame()
        cv2.imshow('frame', gray)
        cv2.destroyAllWindows()

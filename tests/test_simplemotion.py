import unittest

from devices import simplemotion as sm

AXES = ["TTL232R", "TTL232R2", "TTL232R3"]


class SimpleMotionTest(unittest.TestCase):
    # FTDI

    @staticmethod
    def test_list_devices():
        sm.list_devices()

    # SimpleMotion

    @staticmethod
    def test_clear_faults():
        for axis in AXES:
            sm.clear_faults(axis)

    @staticmethod
    def test_communication_all():
        sm.test_multi(AXES)

    @staticmethod
    def test_communication_single():
        for axis in AXES:
            sm.test(axis)

    @staticmethod
    def test_get_param():
        for axis in AXES:
            for param in sm.SmParam:
                sm.get_param(axis, param)

    @staticmethod
    def test_homing():
        for axis in AXES:
            sm.homing(axis)
        for axis in AXES:
            sm.homing(axis, abort=True)

    @staticmethod
    def test_move_inc():
        for axis in AXES:
            sm.move_inc(axis, 100)

    @staticmethod
    def test_move_abs():
        for axis in AXES:
            sm.move_abs(axis, 0)

    @staticmethod
    def test_set_control_mode():
        for axis in AXES:
            sm.set_control_mode(axis, sm.ControlMode.VELOCITY)
            sm.set_control_mode(axis, sm.ControlMode.TORQUE)
            sm.set_control_mode(axis, sm.ControlMode.POSITION)

    @staticmethod
    def test_set_velocity_limit():
        for axis in AXES:
            sm.set_velocity_limit(axis, 8000)

    @staticmethod
    def test_set_accel_limit():
        for axis in AXES:
            sm.set_accel_limit(axis, 40)

    @staticmethod
    def test_version():
        sm.version()

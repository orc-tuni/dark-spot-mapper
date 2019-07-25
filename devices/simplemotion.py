"""This module provides Granite Devices SimpleMotion stage support for ORC Dark Spot Mapper"""

__author__ = "Mika Mäki"
__copyright__ = "Copyright 2016-2019, Tampere University"
__credits__ = ["Mika Mäki"]
__maintainer__ = "Mika Mäki"
__email__ = "mika.maki@tuni.fi"

import ctypes
import enum
import logging
import os.path
import typing as tp

logger = logging.getLogger(__name__)

__ABS_TARGET_MIN = -2147483648
__ABS_TARGET_MAX = 2147483647
__INC_TARGET_MIN = -32768
__INC_TARGET_MAX = 32787

__LIMIT_MIN = 1
__LIMIT_MAX = 32767
__WATCHDOG_MAX = 32767


class ControlMode(enum.IntEnum):
    POSITION = 1
    VELOCITY = 2
    TORQUE = 3


class SmCommand(bytes, enum.Enum):
    ABSTARGET = b"ABSTARGET"
    CLEARFAULTS = b"CLEARFAULTS"
    ENABLE = b"ENABLE"
    HOMING = b"HOMING"
    INCTARGET = b"INCTARGET"
    TESTCOMMUNICATION = b"TESTCOMMUNICATION"


class SmParam(bytes, enum.Enum):
    VELOCITY_LIMIT = b"VelocityLimit"
    ACCELERATION_LIMIT = b"AccelerationLimit"
    CONTROL_MODE = b"ControlMode"
    CURRENT_LIMIT_CONT = b"CurrentLimitCont"
    CURRENT_LIMIT_PEAK = b"CurrentLimitPeak"
    WATCHDOG_TIMEOUT = b"WatchdogTimeout"
    FAULT_BITS = b"FaultBits"
    STATUS_BITS = b"StatusBits"
    SIMPLE_STATUS = b"SimpleStatus"
    FOLLOWING_ERROR = b"FollowingError"
    ACTUAL_TORQUE = b"ActualTorque"


class SmStatus(enum.IntEnum):
    SM_OK = 0
    SM_ERR_NODEVICE = 1
    SM_ERR_BUS = 2
    SM_ERR_COMMUNICATION = 4
    SM_ERR_PARAMETER = 8


class SmException(Exception):
    pass


class SmErrNodevice(IOError, SmException):
    pass


class SmErrBus(IOError, SmException):
    pass


class SmErrCommunication(IOError, SmException):
    pass


class SmErrParameter(ValueError, SmException):
    pass


__sm_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "SimpleMotion64")
try:
    __smdll = ctypes.cdll.LoadLibrary(__sm_path)
    logger.debug("Loaded SimpleMotion version: {}".format(__smdll.smGetVersion()))
except Exception as e:
    logger.error("Loading of SimpleMotion from {} failed with error: {}".format(__sm_path, e))
    raise e


# SimpleMotion API

def abort():
    logger.warning("The abort functionality is a hack and it has not been properly tested yet")
    validate_status(__smdll.smCommand())


def close():
    validate_status(__smdll.smCloseDevices())


def get_param(axis: str, param: SmParam) -> int:
    axis_bytes = bytes(axis, encoding="ascii")
    value = ctypes.c_int32()
    validate_status(__smdll.smGetParam(axis_bytes, param, ctypes.byref(value)))
    return value.value


def __set_param(axis: str, param: SmParam, value: int) -> None:
    axis_bytes = bytes(axis, encoding="ascii")
    validate_status(__smdll.smSetParam(axis_bytes, param, value))


def __smcommand(axis: str, command: SmCommand, value: int) -> None:
    axis_bytes = bytes(axis, encoding="ascii")
    validate_status(__smdll.smCommand(axis_bytes, command, value))


def version() -> int:
    return __smdll.smGetVersion()


# Movement

def homing(axis: str, abort: bool = False):
    __smcommand(axis, SmCommand.HOMING, int(not abort))


def move_abs(axis: str, steps: int):
    if steps < __ABS_TARGET_MIN or steps > __ABS_TARGET_MAX:
        raise ValueError("Invalid absolute step count: {}".format(steps))
    __smcommand(axis, SmCommand.ABSTARGET, steps)


def move_inc(axis: str, steps: int):
    if steps < __INC_TARGET_MIN or steps > __INC_TARGET_MAX:
        raise ValueError("Invalid incremental step count: {}".format(steps))
    __smcommand(axis, SmCommand.INCTARGET, steps)


# Getters and setters

def set_velocity_limit(axis: str, limit: int):
    if limit < __LIMIT_MIN or limit > __LIMIT_MAX:
        raise ValueError("Invalid velocity limit: {}".format(limit))
    __set_param(axis, SmParam.VELOCITY_LIMIT, limit)


def set_accel_limit(axis: str, limit: int):
    if limit < __LIMIT_MIN or limit > __LIMIT_MAX:
        raise ValueError("Invalid acceleration limit: {}".format(limit))
    __set_param(axis, SmParam.ACCELERATION_LIMIT, limit)


def set_control_mode(axis: str, mode: ControlMode):
    if mode not in ControlMode.__members__.values():
        raise ValueError("Invalid control mode: {}".format(mode))
    __set_param(axis, SmParam.CONTROL_MODE, mode)


# Utility functions

def clear_faults(axis: str):
    __smcommand(axis, SmCommand.CLEARFAULTS, 0)


def test(axis: str):
    __smcommand(axis, SmCommand.TESTCOMMUNICATION, 0)


def test_multi(axes: tp.List[str]) -> None:
    error_codes = [__smdll.smCommand(bytes(axis, encoding="ascii"), SmCommand.TESTCOMMUNICATION, 0) for axis in axes]
    if any(code != 0 for code in error_codes):
        error_msg = "SimpleMotion connection test failed with codes {}".format(error_codes)
        logger.error(error_msg)
        raise SmException(error_msg)


def validate_status(status: SmStatus) -> None:
    if status == SmStatus.SM_OK:
        return
    elif status == SmErrNodevice:
        raise SmErrNodevice
    elif status == SmStatus.SM_ERR_BUS:
        raise SmErrBus
    elif status == SmStatus.SM_ERR_COMMUNICATION:
        raise SmErrCommunication
    elif status == SmStatus.SM_ERR_PARAMETER:
        raise SmErrParameter
    else:
        raise RuntimeError("Unknown SM_STATUS: {}".format(status))


if __name__ == "__main__":
    test_multi(["TTL232R", "TTL232R2", "TTL232R3"])

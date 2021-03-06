"""This module provides Granite Devices SimpleMotion stage support for ORC Dark Spot Mapper

See the project readme for further documentation.
"""

__author__ = "Mika Mäki"
__copyright__ = "Copyright 2016-2020, Tampere University"
__credits__ = ["Mika Mäki"]
__maintainer__ = "Mika Mäki"
__email__ = "mika.maki@tuni.fi"

import ctypes
import enum
import logging
import os.path
import platform
import sys
import typing as tp

logger = logging.getLogger(__name__)

__ABS_TARGET_MIN = -2147483648
__ABS_TARGET_MAX = 2147483647
__INC_TARGET_MIN = -32768
__INC_TARGET_MAX = 32787

__LIMIT_MIN = 1
__LIMIT_MAX = 32767
__WATCHDOG_MAX = 32767


@enum.unique
class ControlMode(enum.IntEnum):
    POSITION = 1
    VELOCITY = 2
    TORQUE = 3


class FT_DEVICE_LIST_INFO_NODE(ctypes.Structure):
    _fields_ = [
        ("Flags", ctypes.c_int32),
        ("Type", ctypes.c_int32),
        ("ID", ctypes.c_int32),
        ("LocID", ctypes.c_int32),
        ("SerialNumber", ctypes.c_char * 16),
        ("Description", ctypes.c_char * 64),
        ("ftHandle", ctypes.c_void_p)
    ]


@enum.unique
class FT_Status(enum.IntEnum):
    FT_OK = 0
    FT_DEVICE_NOT_FOUND = 2
    FT_DEVICE_NOT_OPENED = 3
    FT_IO_ERROR = 4
    FT_INSUFFICIENT_RESOURCES = 5
    FT_INVALID_PARAMETER = 6
    FT_INVALID_BAUD_RATE = 7
    FT_DEVICE_NOT_OPENED_FOR_ERASE = 8
    FT_DEVICE_NOT_OPENED_FOR_WRITE = 9
    FT_FAILED_TO_WRITE_DEVICE = 10
    FT_EEPROM_READ_FAILED = 11
    FT_EEPROM_WRITE_FAILED = 12
    FT_EEPROM_ERASE_FAILED = 13
    FT_EEPROM_NOT_PRESENT = 14
    FT_EEPROM_NOT_PROGRAMMED = 15
    FT_INVALID_ARGS = 16
    FT_NOT_SUPPORTED = 17
    FT_OTHER_ERROR = 18


@enum.unique
class SmCommand(bytes, enum.Enum):
    ABSTARGET = b"ABSTARGET"
    CLEARFAULTS = b"CLEARFAULTS"
    ENABLE = b"ENABLE"
    HOMING = b"HOMING"
    INCTARGET = b"INCTARGET"
    TESTCOMMUNICATION = b"TESTCOMMUNICATION"


@enum.unique
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


@enum.unique
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


__sm_name_arch = ""
if sys.platform == "win32":
    __sm_name_type = ".dll"
elif sys.platform == "linux":
    __machine = platform.machine()
    if __machine == "x86_64":
        pass
    # Todo: check if "arm" is correct for 32-bit ARM
    elif __machine in ["arm", "aarch64"]:
        __sm_name_arch = "_arm"
    __sm_name_type = ".so"
else:
    logger.warning("Unknown operating system. Attempting to load SimpleMotion anyway.")
    __sm_name_type = ""

if sys.maxsize > 2**32:
    __sm_name_bitness = "64"
else:
    __sm_name_bitness = ""

# Using an absolute path is necessary especially if Python is installed from Microsoft Store
__sm_name = f"simplemotion{__sm_name_arch}{__sm_name_bitness}{__sm_name_type}"
__sm_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", __sm_name)

try:
    __smdll = ctypes.cdll.LoadLibrary(__sm_path)
    logger.debug(f"Loaded SimpleMotion version: {__smdll.smGetVersion()}")
except Exception as e:
    logger.error(f"Loading of SimpleMotion from {__sm_path} failed with error: {e}")
    raise e


# FTDI

def list_devices() -> None:
    if sys.platform == "win32":
        print("FTDI functions are not supported on Windows")
        return

    num_devs = ctypes.c_int32(0)
    ret = __smdll.FT_CreateDeviceInfoList(ctypes.byref(num_devs))
    print(f"Found {num_devs.value} devices, got return code {FT_Status(ret)}")

    # Create array class
    DeviceArray = FT_DEVICE_LIST_INFO_NODE * num_devs.value
    # Create array instance
    arr = DeviceArray()

    ret = __smdll.FT_GetDeviceInfoList(ctypes.byref(arr), ctypes.byref(num_devs))
    print(f"Got device info list with return code {FT_Status(ret)}")

    for i, dev in enumerate(arr):
        print("Device", i)
        print("- Flags", dev.Flags)
        print("- Type", dev.Type)
        print("- ID", dev.ID)
        print("- LocID", dev.LocID)
        print("- SerialNumber", dev.SerialNumber)
        print("- Description", dev.Description)
        print("- ftHandle", dev.ftHandle)

    for i in range(len(arr)):
        handle = ctypes.c_void_p()
        ret = __smdll.FT_Open(i, ctypes.byref(handle))
        print(f"Opened device {i} to handle {handle.value} with return code {FT_Status(ret)}")

        ret = __smdll.FT_Close(handle)
        print(f"Closed device {i} from handle {handle.value} with return code {ret}")


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
        raise ValueError(f"Invalid absolute step count: {steps}")
    __smcommand(axis, SmCommand.ABSTARGET, steps)


def move_inc(axis: str, steps: int):
    if steps < __INC_TARGET_MIN or steps > __INC_TARGET_MAX:
        raise ValueError(f"Invalid incremental step count: {steps}")
    __smcommand(axis, SmCommand.INCTARGET, steps)


# Getters and setters

def set_velocity_limit(axis: str, limit: int):
    if limit < __LIMIT_MIN or limit > __LIMIT_MAX:
        raise ValueError(f"Invalid velocity limit: {limit}")
    __set_param(axis, SmParam.VELOCITY_LIMIT, limit)


def set_accel_limit(axis: str, limit: int):
    if limit < __LIMIT_MIN or limit > __LIMIT_MAX:
        raise ValueError(f"Invalid acceleration limit: {limit}")
    __set_param(axis, SmParam.ACCELERATION_LIMIT, limit)


def set_control_mode(axis: str, mode: ControlMode):
    if mode not in ControlMode.__members__.values():
        raise ValueError(f"Invalid control mode: {mode}")
    __set_param(axis, SmParam.CONTROL_MODE, mode)


# Utility functions

def clear_faults(axis: str):
    __smcommand(axis, SmCommand.CLEARFAULTS, 0)


def test(axis: str):
    __smcommand(axis, SmCommand.TESTCOMMUNICATION, 0)


def test_multi(axes: tp.List[str]) -> None:
    error_codes = [__smdll.smCommand(bytes(axis, encoding="ascii"), SmCommand.TESTCOMMUNICATION, 0) for axis in axes]
    if any(code != 0 for code in error_codes):
        error_msg = f"SimpleMotion connection test failed with codes {error_codes}"
        logger.error(error_msg)
        raise SmException(error_msg)


def validate_status(status: SmStatus) -> None:
    if status == SmStatus.SM_OK:
        return
    elif status == SmStatus.SmErrNodevice:
        raise SmErrNodevice()
    elif status == SmStatus.SM_ERR_BUS:
        raise SmErrBus()
    elif status == SmStatus.SM_ERR_COMMUNICATION:
        raise SmErrCommunication
    elif status == SmStatus.SM_ERR_PARAMETER:
        raise SmErrParameter
    else:
        raise RuntimeError(f"Unknown SM_STATUS: {status}")


if __name__ == "__main__":
    list_devices()
    import time
    time.sleep(0.5)

    # test("TTL232R")
    test_multi(["TTL232R", "TTL232R2", "TTL232R3"])

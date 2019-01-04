"""This module provides Granite Devices SimpleMotion stage support for ORC Dark Spot Mapper

Copyright 2016 - 2019 Mika Mäki & Tampere University of Technology
Mika would like to license this program with GPLv3+ but it would require some university bureaucracy
"""

import dsm_exceptions

# C++ DLL support for SimpleMotion
import ctypes

import logging
import time
import typing as tp

logger = logging.getLogger(__name__)


class SimpleMotion:
    """This class functions as an API for a set of three Granite Devices SimpleMotion linear stages"""
    def __init__(self):
        # Device names for TTL adapters
        self.__axis1 = b"TTL232R"
        self.__axis2 = b"TTL232R2"
        self.__axis3 = b"TTL232R3"

        self.__x: int = 0
        self.__y: int = 0
        self.__abort = False

        # Experimental values from SL309 Dark Spot Mapper
        self.mm_to_steps = 51122.04724409449
        # Velocities (steps / s)
        self.__vx = 255610.2362204725
        self.__vy = 97375.3280839895

        try:
            self.__smdll = ctypes.cdll.LoadLibrary("SimpleMotion64")
            logger.debug("Detected SimpleMotion version: {}".format(self.__smdll.smGetVersion()))
        except Exception as e:
            logger.error("Loading of SimpleMotion library failed: {}".format(e))
            raise e

        # Testing connection to motor drivers
        a1err = self.__smdll.smCommand(self.__axis1, b"TESTCOMMUNICATION", 0)
        a2err = self.__smdll.smCommand(self.__axis2, b"TESTCOMMUNICATION", 0)
        a3err = self.__smdll.smCommand(self.__axis3, b"TESTCOMMUNICATION", 0)

        if a1err != 0 or a2err != 0 or a3err != 0:
            logger.error("Connecting to motor drivers returned codes: %d %d %d".format(a1err, a2err, a3err))
            raise IOError("Could not connect to motor drivers")

    def abort(self) -> None:
        self.__abort = True
        self.__smdll.smCommand()
        time.sleep(10)
        self.__abort = False
        self.reset_coords()

    def reset_coords(self) -> None:
        """Zero the stage coordinates

        :return: -
        """
        self.__x = 0
        self.__y = 0

    def where(self) -> tp.Tuple[int, int]:
        return self.__x, self.__y

    def goto(self, x, y) -> None:
        self.moveinc(self.__axis1, x - self.__x)
        self.moveinc(self.__axis2, y - self.__y)

    def time(self, x, y) -> float:
        """Returns the time required for movement

        :param x: x coordinate difference
        :param y: y coordinate difference
        :return: float of movement time
        """
        # Multiply with 1.5 just in case
        return abs(x / self.__vx) + abs(y / self.__vy) * 1.5

    def moveinc(self, axis: bytes, steps: int) -> bool:
        """Move incremental steps

        :param axis: bytestring of the axis
        :param steps: amount of stepper steps to be moved
        :return: bool of success
        """

        if abs(steps) > 40000000:
            logger.error("Error: too many steps %s")
            return False

        if axis == self.__axis1:
            self.__x += steps
        elif axis == self.__axis2:
            self.__y += steps

        # Axis x is inverted
        if axis == self.__axis1:
            steps *= -1

        while abs(steps) > 32760:
            if self.__abort:
                self.reset_coords()
                raise dsm_exceptions.AbortException

            if steps < 0:
                self.__smdll.smCommand(axis, b"INCTARGET", -32000)
                steps += 32000
            elif steps > 0:
                self.__smdll.smCommand(axis, b"INCTARGET", 32000)
                steps -= 32000
            else:
                raise ValueError

        self.__smdll.smCommand(axis, b"INCTARGET", steps)
        return True

    def moveinc_mm(self, axis: bytes, mm: float) -> None:
        """Move incremental (mm)

        :param axis: bytestring of the axis
        :param mm: mm to be moved
        :return: -
        """
        self.moveinc(axis, int(round(mm * self.mm_to_steps)))

    def step_up(self, steps: int) -> None:
        self.moveinc(self.__axis2, steps)

    def step_down(self, steps: int) -> None:
        self.moveinc(self.__axis2, - steps)

    def step_left(self, steps: int) -> None:
        self.moveinc(self.__axis1, - steps)

    def step_right(self, steps: int) -> None:
        self.moveinc(self.__axis1, steps)

    def step_zup(self, steps: int) -> None:
        self.moveinc(self.__axis3, steps)

    def step_zdown(self, steps: int) -> None:
        self.moveinc(self.__axis3, - steps)

    def mm_up(self, mm: tp.Union[int, float]) -> None:
        self.moveinc_mm(self.__axis2, mm)

    def mm_down(self, mm: tp.Union[int, float]) -> None:
        self.moveinc_mm(self.__axis2, - mm)

    def mm_left(self, mm: tp.Union[int, float]) -> None:
        self.moveinc_mm(self.__axis1, - mm)

    def mm_right(self, mm: tp.Union[int, float]) -> None:
        self.moveinc_mm(self.__axis1, mm)

    def mm_zup(self, mm: tp.Union[int, float]) -> None:
        self.moveinc_mm(self.__axis3, mm)

    def mm_zdown(self, mm: tp.Union[int, float]) -> None:
        self.moveinc_mm(self.__axis3, - mm)

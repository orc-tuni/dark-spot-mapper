# This module provides Granite Devices SimpleMotion stage support for
# ORC Dark Spot Mapper

# Copyright 2016 - 2017 Mika Mäki & Tampere University of Technology
# Mika would like to license this program with GPLv3+ but it would require some university bureaucracy


# C++ DLL support for SimpleMotion
import ctypes


class SimpleMotion:
    """
    This class functions as an API for a set of three Granite Devices SimpleMotion linear stages
    """
    def __init__(self):
        # Device names for TTL adapters
        self.__axis1 = b"TTL232R"
        self.__axis2 = b"TTL232R2"
        self.__axis3 = b"TTL232R3"

        self.__x = 0
        self.__y = 0

        # Experimental values from SL309 Dark Spot Mapper
        self.mm_to_steps = 51122.04724409449
        # Velocities (steps / s)
        self.__vx = 255610.2362204725
        self.__vy = 97375.3280839895

        try:
            self.__smdll = ctypes.cdll.LoadLibrary("SimpleMotion64")
            print("Detected SimpleMotion version: " + str(self.__smdll.smGetVersion()))
        except:
            print("Loading of SimpleMotion library failed")
            raise IOError

        # Testing connection to motor drivers
        a1err = self.__smdll.smCommand(self.__axis1, b"TESTCOMMUNICATION", 0)
        a2err = self.__smdll.smCommand(self.__axis2, b"TESTCOMMUNICATION", 0)
        a3err = self.__smdll.smCommand(self.__axis3, b"TESTCOMMUNICATION", 0)

        if a1err != 0 or a2err != 0 or a3err != 0:
            print("Connecting to motor drivers returned codes: " + str(a1err) + " " + str(a2err) + " " + str(a3err))
            print("Could not connect to motor drivers")
            raise IOError

    def reset_coords(self):
        """
        Zero the stage coordinates
        :return: -
        """
        self.__x = 0
        self.__y = 0

    def where(self):
        return self.__x, self.__y

    def goto(self, x, y):
        self.moveinc(self.__axis1, x - self.__x)
        self.moveinc(self.__axis2, y - self.__y)

    def time(self, x, y):
        """
        Returns the time required for movement
        :param x: x coordinate difference
        :param y: y coordinate difference
        :return: float of movement time
        """
        # Multiply with 1.5 just in case
        return abs(x / self.__vx) + abs(y / self.__vy) * 1.5

    def moveinc(self, axis, steps):
        """
        :param axis: bytestring of the axis
        :param steps: amount of stepper steps to be moved
        :return: bool of success
        """

        if abs(steps) > 40000000:
            print("Error: too many steps")
            return False

        if axis == self.__axis1:
            self.__x += steps
        elif axis == self.__axis2:
            self.__y += steps

        # Axis x is inverted
        if axis == self.__axis1:
            steps *= -1

        while abs(steps) > 32760:
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

    def moveinc_mm(self, axis, mm):
        """
        :param axis: bytestring of the axis
        :param mm: mm to be moved
        :return: -
        """
        self.moveinc(axis, int(round(mm * self.mm_to_steps)))

    def step_up(self, steps):
        self.moveinc(self.__axis2, steps)

    def step_down(self, steps):
        self.moveinc(self.__axis2, - steps)

    def step_left(self, steps):
        self.moveinc(self.__axis1, - steps)

    def step_right(self, steps):
        self.moveinc(self.__axis1, steps)

    def step_zup(self, steps):
        self.moveinc(self.__axis3, steps)

    def step_zdown(self, steps):
        self.moveinc(self.__axis3, - steps)

    def mm_up(self, mm):
        self.moveinc_mm(self.__axis2, mm)

    def mm_down(self, mm):
        self.moveinc_mm(self.__axis2, - mm)

    def mm_left(self, mm):
        self.moveinc_mm(self.__axis1, - mm)

    def mm_right(self, mm):
        self.moveinc_mm(self.__axis1, mm)

    def mm_zup(self, mm):
        self.moveinc_mm(self.__axis3, mm)

    def mm_zdown(self, mm):
        self.moveinc_mm(self.__axis3, - mm)

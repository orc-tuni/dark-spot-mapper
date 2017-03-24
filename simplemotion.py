# This file provides Granite Devices SimpleMotion stage support for
# ORC Dark Spot Mapper

# Copyright 2016 - 2017 Mika Mäki & Tampere University of Technology

# C++ DLL support for SimpleMotion
import ctypes


class SimpleMotion:
    def __init__(self):
        # Device names for TTL adapters
        self.__axis1 = b"TTL232R"
        self.__axis2 = b"TTL232R2"
        self.__axis3 = b"TTL232R3"

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

    def moveinc(self, axis, steps):
        if abs(steps) > 1000000:
            print("Error: too many steps")
            return False
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

    def step_up(self, steps):
        self.moveinc(self.__axis2, steps)

    def step_down(self, steps):
        self.moveinc(self.__axis2, - steps)

    def step_left(self, steps):
        self.moveinc(self.__axis1, steps)

    def step_right(self, steps):
        self.moveinc(self.__axis1, - steps)

    def step_zup(self, steps):
        self.moveinc(self.__axis3, steps)

    def step_zdown(self, steps):
        self.moveinc(self.__axis3, - steps)

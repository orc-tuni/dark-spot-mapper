__author__ = "Mika Mäki"
__copyright__ = "Copyright 2016-2019, Tampere University"
__credits__ = ["Mika Mäki"]
__maintainer__ = "Mika Mäki"
__email__ = "mika.maki@tuni.fi"

import logging
import time
import typing as tp

import dsm_exceptions
from devices import simplemotion as sm

logger = logging.getLogger(__name__)

# Misc parameters
MAX_INC_STEPS: int = 40000000
AXES = ("TTL232R", "TTL232R2", "TTL232R3")

# Experimental values from SL309 Dark Spot Mapper
MM_TO_STEPS = 51122.04724409449
VX = 255610.2362204725
VY = 97375.3280839895


class StageControl:
    def __init__(
            self,
            mm_to_steps: float = MM_TO_STEPS,
            vx: float = VX,
            vy: float = VY,
            axes: tp.List[str] = AXES):

        # Device names for TTL adapters
        self.__axis1 = axes[0]
        self.__axis2 = axes[1]
        self.__axis3 = axes[2]

        self.__x: int = 0
        self.__y: int = 0
        self.__abort = False

        # Experimental values from SL309 Dark Spot Mapper
        self.mm_to_steps = mm_to_steps
        # Velocities (steps / s)
        self.__vx = vx
        self.__vy = vy

    def abort(self) -> None:
        self.__abort = True
        sm.abort()
        time.sleep(10)
        self.__abort = False
        self.reset_coords()

    def goto(self, x: int, y: int) -> None:
        self.moveinc(self.__axis1, x - self.__x)
        self.moveinc(self.__axis2, y - self.__y)

    def moveinc(self, axis: str, steps: int) -> bool:
        """Move incremental steps

        :param axis: bytestring of the axis
        :param steps: amount of stepper steps to be moved
        :return: bool of success
        """

        if abs(steps) > MAX_INC_STEPS:
            logger.error("Error: too many steps %s")
            return False

        if axis == self.__axis1:
            self.__x += steps
        elif axis == self.__axis2:
            self.__y += steps

        # Axis x is inverted in the Dark Spot Mapper
        if axis == self.__axis1:
            steps *= -1

        while abs(steps) > 32760:
            if self.__abort:
                self.reset_coords()
                raise dsm_exceptions.AbortException

            if steps < 0:
                sm.move_inc(axis, -32000)
                steps += 32000
            elif steps > 0:
                sm.move_inc(axis, 32000)
                steps -= 32000
            else:
                raise ValueError

        sm.move_inc(axis, steps)
        return True

    def moveinc_mm(self, axis: str, mm: float) -> bool:
        return self.moveinc(axis, int(round(mm * self.mm_to_steps)))

    def reset_coords(self) -> None:
        """Zero the stage coordinates"""
        self.__x = 0
        self.__y = 0

    def time(self, x: float, y: float) -> float:
        """Returns the time required for movement

        :param x: x coordinate difference
        :param y: y coordinate difference
        :return: float of movement time
        """
        # Multiply with 1.5 just in case
        return abs(x / self.__vx) + abs(y / self.__vy) * 1.5

    def where(self) -> tp.Tuple[int, int]:
        return self.__x, self.__y

    # Step movement

    def step_up(self, steps: int) -> bool:
        return self.moveinc(self.__axis2, steps)

    def step_down(self, steps: int) -> bool:
        return self.moveinc(self.__axis2, - steps)

    def step_left(self, steps: int) -> bool:
        return self.moveinc(self.__axis1, - steps)

    def step_right(self, steps: int) -> bool:
        return self.moveinc(self.__axis1, steps)

    def step_zup(self, steps: int) -> bool:
        return self.moveinc(self.__axis3, steps)

    def step_zdown(self, steps: int) -> bool:
        return self.moveinc(self.__axis3, - steps)

    # mm movement

    def mm_up(self, mm: float) -> bool:
        return self.moveinc_mm(self.__axis2, mm)

    def mm_down(self, mm: float) -> bool:
        return self.moveinc_mm(self.__axis2, - mm)

    def mm_left(self, mm: float) -> bool:
        return self.moveinc_mm(self.__axis1, - mm)

    def mm_right(self, mm: float) -> bool:
        return self.moveinc_mm(self.__axis1, mm)

    def mm_zup(self, mm: float) -> bool:
        return self.moveinc_mm(self.__axis3, mm)

    def mm_zdown(self, mm: float) -> bool:
        return self.moveinc_mm(self.__axis3, - mm)

from . import simplemotion as sm
from . import stage

import logging

logger = logging.getLogger(__name__)


class StageSimplemotion(stage.Stage):
    def __init__(
            self,
            address: str,
            mm_to_steps: float,
            velocity: float,
            starting_pos: int = 0,
            max_inc_steps: int = 40000000,
            max_inc_steps_per_command: int = 32760):
        super().__init__(address, mm_to_steps, velocity, starting_pos)
        if max_inc_steps_per_command > max_inc_steps:
            raise ValueError
        self.max_inc_steps = max_inc_steps
        self.max_inc_steps_per_command = max_inc_steps_per_command

    # Movement

    def __move_inc_steps(self, steps: int) -> bool:
        if abs(steps) > self.max_inc_steps:
            logger.error(f"Error: too many steps: {steps}")
            return False

        max_steps = ((steps > 0) - (steps < 0)) * self.max_inc_steps_per_command
        while abs(steps) > self.max_inc_steps_per_command:
            if self.abort_lock.locked():
                self.reset_pos()
                return False

            sm.move_inc(self.address, max_steps)
            steps -= max_steps

        sm.move_inc(self.address, steps)
        return True

    # Getters and setters

    def set_velocity_limit(self, limit: int):
        sm.set_velocity_limit(self.address, limit)

    def set_accel_limit(self, limit: int):
        sm.set_accel_limit(self.address, limit)

    def set_control_mode(self, mode: sm.ControlMode):
        sm.set_control_mode(self.address, mode)

    # Utility functions

    def clear_faults(self):
        sm.clear_faults(self.address)

    def test(self):
        sm.test(self.address)

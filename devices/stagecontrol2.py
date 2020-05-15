from .stage import Stage


class StageControl:
    def __init__(self,
                 stage_x: Stage,
                 stage_y: Stage,
                 stage_z: Stage):
        self.stage_x = stage_x
        self.stage_y = stage_y
        self.stage_z = stage_z

    def goto(self, x: int, y: int):
        self.stage_x.move_inc_steps(x)
        self.stage_y.move_inc_steps(y)

    def time(self, steps):
        return max(self.stage_x.time(steps), self.stage_y.time(steps))

    # Step movement

    def steps_up(self, steps: int) -> bool:
        return self.stage_y.move_inc_steps(steps)

    def steps_down(self, steps: int) -> bool:
        return self.stage_y.move_inc_steps(-steps)

    def steps_left(self, steps: int) -> bool:
        return self.stage_x.move_inc_steps(-steps)

    def steps_right(self, steps: int) -> bool:
        return self.stage_y.move_inc_steps(steps)

    def steps_zup(self, steps: int) -> bool:
        return self.stage_z.move_inc_steps(steps)

    def steps_zdown(self, steps: int) -> bool:
        return self.stage_z.move_inc_steps(-steps)

    # mm movement

    def mm_up(self, mm: float) -> bool:
        return self.stage_y.move_inc_mm(mm)

    def mm_down(self, mm: float) -> bool:
        return self.stage_y.move_inc_mm(mm)

    def mm_left(self, mm: float) -> bool:
        return self.stage_x.move_inc_mm(-mm)

    def mm_right(self, mm: float) -> bool:
        return self.stage_x.move_inc_mm(mm)

    def mm_zup(self, mm: float) -> bool:
        return self.stage_z.move_inc_mm(mm)

    def mm_zdown(self, mm: float) -> bool:
        return self.stage_z.move_inc_mm(-mm)

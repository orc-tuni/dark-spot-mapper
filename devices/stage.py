import abc
import threading


class Stage(abc.ABC):
    def __init__(
            self,
            address,
            mm_to_steps: float,
            velocity: float,
            starting_pos: int = 0,
            inverted: bool = False):
        """Velocity is in steps/s, starting_pos is in steps"""
        self.address = address
        self.mm_to_steps: float = mm_to_steps
        self.velocity: float = velocity
        self.pos: int = starting_pos
        self.inverted: bool = inverted
        self.__sign = 1-2*inverted

        self.move_lock = threading.Lock()
        self.abort_lock = threading.Lock()

    def time(self, steps: int) -> float:
        # Multiply with 1.5 just in case
        return abs(steps / self.velocity) * 1.5

    def move_inc_mm(self, mm: float) -> bool:
        return self.move_inc_steps(round(mm * self.mm_to_steps))

    def reset_pos(self):
        with self.move_lock:
            self.pos = 0

    def where(self) -> int:
        return self.pos

    def where_mm(self) -> float:
        return self.pos / self.mm_to_steps

    def move_inc_steps(self, steps: int) -> bool:
        with self.move_lock:
            if self.abort_lock.locked():
                return False
            ret = self.__move_inc_steps(self.__sign*steps)
            if ret:
                self.pos += steps
            return ret

    @abc.abstractmethod
    def __move_inc_steps(self, steps: int):
        pass

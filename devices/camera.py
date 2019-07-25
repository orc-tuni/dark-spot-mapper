import abc


class Camera(abc.ABC):
    @abc.abstractmethod
    def take_pic(self):
        pass

    @abc.abstractmethod
    def save_pic(self, directory: str, filename: str):
        pass

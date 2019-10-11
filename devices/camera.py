import abc
import typing as tp

import cv2
import numpy as np

# Enable OpenCL acceleration (just in case)
# cv2.ocl.setUseOpenCL(True)


class Camera(abc.ABC):
    def __init__(self, address):
        self.__address = address
        self.__writer: tp.Optional[cv2.VideoWriter] = None

    def __del__(self):
        self.stop_video()

    def address(self):
        return self.__address

    @abc.abstractmethod
    def get_frame(self):
        pass

    def save_frame(self, path: str, frame: np.ndarray = None):
        if frame is None:
            frame = self.get_frame()
        cv2.imwrite(filename=path, img=frame)

    def start_video(self, path: str, fps: int = None, fourcc: str = "H264"):
        if self.__writer is not None:
            raise RuntimeError("Video recording is already active")
        if len(fourcc) != 4:
            raise ValueError("Invalid fourcc: {}".format(fourcc))
        fourcc: int = cv2.VideoWriter_fourcc(fourcc[0], fourcc[1], fourcc[2], fourcc[3])
        self.__writer = cv2.VideoWriter(path, fourcc, fps)

    def stop_video(self):
        if self.__writer is None:
            return
        self.__writer.release()

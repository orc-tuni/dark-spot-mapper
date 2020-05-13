# OpenCV cross-compilation for Raspberry Pi
# Not properly tested yet

FROM debian:latest

RUN dpkg --add-architecture armhf \
    && apt-get update \
    # A list of packages required for cross-compilation is available at:
    # https://solarianprogrammer.com/2018/12/18/cross-compile-opencv-raspberry-pi-raspbian/
    && apt-get install -y \
        # ---
        # Required packages
        # ---
        build-essential \
        cmake \
        crossbuild-essential-armhf \
        # For downloading FFmpeg
        git \
        # For finding packages with PKG_CONFIG_LIBDIR etc.
        pkg-config \
        unzip \
        wget \
        # Python
        python-dev \
        python-numpy \
        python-pip \
        python-setuptools \
        python3-dev \
        python3-numpy \
        python3-pip \
        python3-setuptools \
        libpython2-dev:armhf \
        libpython3-dev:armhf \
        # ---
        # Optional packages
        # ---
        # Caffe for the opencv_cnn_obj3d module
        libcaffe-cpu-dev:armhf \
        # OpenCV Structure from Motion (sfm) modules
        # https://docs.opencv.org/4.3.0/db/db8/tutorial_sfm_installation.html
        libgflags-dev:armhf \
        libgoogle-glog-dev:armhf \
        #
        libeigen3-dev:armhf \
        libavcodec-dev:armhf \
        libavformat-dev:armhf \
        libavresample-dev:armhf \
        libswscale-dev:armhf \
        zlib1g-dev:armhf \
        # GUI
        qt5-default:armhf \
        # GTK 3 bindings seem not show up in the OpenCV build configuration
        libgtk-3-dev:armhf \
        libcanberra-gtk3-dev:armhf \
        # The following packages cannot be installed, since they overwrite the x86 Python 2.7 installation
        # libgtk2.0-dev:armhf
        # libgtkglext1-dev:armhf
        #
        # FireWire camera support
        libdc1394-22-dev:armhf \
        # HDF5 support
        libhdf5-dev:armhf \
        # Gstreamer
        libgstreamer1.0-dev:armhf \
        libgstreamer-plugins-base1.0-dev:armhf \
        # Image formats
        libjpeg-dev:armhf \
        libopenexr-dev:armhf \
        libpng-dev:armhf \
        libtiff-dev:armhf \
        libwebp-dev:armhf \
        # Video formats
        libv4l-dev:armhf \
        libx264-dev:armhf \
        libxvidcore-dev:armhf \
        # ---
        # Additional codecs
        # Might not be necessary to be installed during compilation.
        # Installation on target machine may be sufficient.
        # ---
        gstreamer1.0-libav:armhf \
        # Depends on libva2
        gstreamer1.0-vaapi:armhf \
        libavcodec-extra58:armhf \
    #
    && apt-get autoremove -y \
    && apt-get clean

# Download and extract OpenCV
ARG OPENCV_VERSION=4.3.0
RUN mkdir /temp \
    && wget -nv https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.zip -O /temp/opencvcontrib-${OPENCV_VERSION}.zip \
    && wget -nv https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip -O /temp/opencv-${OPENCV_VERSION}.zip \
    && unzip /temp/opencv-${OPENCV_VERSION}.zip \
    && unzip /temp/opencvcontrib-${OPENCV_VERSION}.zip

ARG OPENCV_PYTHON_VERSION=9.2
RUN wget -nv https://github.com/VLAM3D/opencv-python/archive/${OPENCV_PYTHON_VERSION}.zip -O /temp/opencv-python.zip \
    && unzip /temp/opencv-python.zip

# FFmpeg
# https://trac.ffmpeg.org/wiki/CompilationGuide/RaspberryPi
# RUN cd /temp \
#     && git clone https://github.com/FFmpeg/FFmpeg.git \
#     && cd FFmpeg \
#     && ./configure --enable-cross-compile --arch=armhf --target-os=linux --enable-gpl --enable-omx --enable-omx-rpi --enable-nonfree \
#     && sudo make

# BUILD CONFIG

# This has to be off if the resulting binaries are distributed in openly available repositories
ARG OPENCV_ENABLE_NONFREE=ON

# This enables cmake to find libdc1394, FFmpeg and Gstreamer
# https://github.com/opencv/opencv/issues/13396
ENV PKG_CONFIG_LIBDIR="/usr/local/arm-linux-gnueabihf/lib/pkgconfig:/usr/local/lib/arm-linux-gnueabihf/pkgconfig:/usr/lib/arm-linux-gnueabihf/pkgconfig:/usr/arm-linux-gnueabihf/lib/pkgconfig"

# Configuration
RUN cd /opencv-${OPENCV_VERSION} \
    && mkdir build_python \
    && cd build_python \
    && cmake .. \
        # Basic configuration
        -DCMAKE_TOOLCHAIN_FILE=/opencv-${OPENCV_VERSION}/platforms/linux/arm-gnueabi.toolchain.cmake \
        -DBUILD_SHARED_LIBS=OFF \
        -DCMAKE_BUILD_TYPE=RELEASE \
        -DOPENCV_EXTRA_MODULES_PATH=/opencv_contrib-${OPENCV_VERSION}/modules \
        # https://stackoverflow.com/questions/44519982/cross-compiling-opencv-with-ffmpeg
        # CPU configuration
        # Setting CPU_BASELINE does not enable VFPV3 and NEON instruction sets
        # (The option is intended primarily for x86 systems.)
        # -DCPU_BASELINE=NEON,VFPV3,VFPV4
        # Compile specifically for Raspberry Pi 4 model B
        # https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html
        # -DCMAKE_CXX_FLAGS_RELEASE="-mtune=cortex-a72 -mcpu=cortex-a72 -mfloat-abi=hard -march=armv8-a+crc+crypto+sb+predres"
        -DENABLE_VFPV3=ON \
        -DENABLE_NEON=ON \
        # Performance
        -DWITH_EIGEN=ON \
        -DWITH_LAPACK=ON \
        -DWITH_OPENGL=ON \
        -DWITH_OPENCL=ON \
        -DBUILD_TBB=ON \
        -DWITH_TBB=ON \
        # Formats
        -DWITH_V4L=ON \
        -DWITH_FFMPEG=ON \
        # Extra features
        # The GTK flags may not work when Qt is enabled
        -DWITH_GTK=ON \
        -DWITH_GTK3=ON \
        # Building with Qt will likely require manual configuration of the Qt installation path
        # -DWITH_QT=ON
        -DBUILD_TIFF=ON \
        -DBUILD_opencv_java=OFF \
        -DBUILD_opencv_legacy=OFF \
        -DOPENCV_ENABLE_NONFREE=${OPENCV_ENABLE_NONFREE} \
        # Extra binaries
        -DBUILD_TESTS=ON \
        -DBUILD_PERF_TESTS=ON \
        # Python
        -D PYTHON2_INCLUDE_PATH=/usr/include/python2.7 \
        -D PYTHON2_LIBRARIES=/usr/lib/arm-linux-gnueabihf/libpython2.7.so \
        -D PYTHON2_NUMPY_INCLUDE_DIRS=/usr/lib/python2/dist-packages/numpy/core/include \
        -D PYTHON3_INCLUDE_PATH=/usr/include/python3.7m \
        -D PYTHON3_LIBRARIES=/usr/lib/arm-linux-gnueabihf/libpython3.7m.so \
        -D PYTHON3_NUMPY_INCLUDE_DIRS=/usr/lib/python3/dist-packages/numpy/core/include \
        -DCMAKE_INSTALL_PREFIX=/opencv-python-${OPENCV_PYTHON_VERSION}/cv2 \
    #
    # Compilation
    && make -j$(nproc) opencv_python3 \
    && make -j$(nproc) opencv_python2

# Post-processing
RUN cd /opencv-${OPENCV_VERSION}/build_python \
    # Copy Python 3 so files
    && cp /opencv-${OPENCV_VERSION}/build_python/lib/python3/cv2.*.so /opencv-python-${OPENCV_PYTHON_VERSION}/cv2/ \
    # Create a directory for the wheels
    && mkdir -p /usr/local/etc/wheels \
    # Fix for finding OpenCV
    && ln -s /opencv-${OPENCV_VERSION}/modules/core/include/opencv2 /usr/local/include/opencv2 \
    && cd /opencv-python-${OPENCV_PYTHON_VERSION} \
    && python find_version.py \
    # Build Python 3 wheel
    && python3 setup.py bdist_wheel \
    # Remove the Python 3 shared library from which the wheel was built
    && rm /opencv-python-${OPENCV_PYTHON_VERSION}/cv2/cv2.*.so \
    # Copy Python 2 so file
    && cp /opencv-${OPENCV_VERSION}/build_python/lib/cv2.so /opencv-python-${OPENCV_PYTHON_VERSION}/cv2/ \
    # Build Python 2 wheel
    && python2 setup.py bdist_wheel \
    # Copy wheels to target folder
    && cp /opencv-python-${OPENCV_PYTHON_VERSION}/dist/opencv_python-*.whl /usr/local/etc/wheels \
    # Remove temporary files
    && cd / \
    && rm -rf /opencv-python-${OPENCV_PYTHON_VERSION} \
    && rm -rf /opencv-${OPENCV_VERSION} \
    && rm -rf /opencv_contrib-${OPENCV_VERSION} \
    && rm -rf /temp

# TODO: rename the wheels to be arm instead of x86_64

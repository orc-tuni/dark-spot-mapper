FROM ubuntu:latest

# Please note that if OPENCV_ENABLE_NONFREE is enabled, the resulting binaries
# cannot be distributed in openly available repositories.

WORKDIR /

# Install requirements
RUN apt-get update \
    # cmake requires tzdata which would prompt for timezone settings during the installation
    && DEBIAN_FRONTEND="noninteractive" apt-get install -y \
        # ---
        # Required packages
        # ---
        cmake \
        pkg-config \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        unzip \
        wget \
        # Git for OpenCV-Python find_version.py
        git \
        # ---
        # Optional packages
        # ---
        # BLAS & LAPACK
        libatlas-base-dev \
        # For some reason neither liblapack nor libopenblas results in automatic detection of LAPACK installation
        # liblapack-dev \
        # libopenblas-dev \
        # Caffe for the opencv_cnn_obj3d module
        libcaffe-cpu-dev \
        # OpenCV Structure from Motion (sfm) modules
        # https://docs.opencv.org/4.3.0/db/db8/tutorial_sfm_installation.html
        libgflags-dev \
        libgoogle-glog-dev \
        # Optional FFmpeg stuff
        libavresample-dev \
        # GTK+2 and GTK+3 bindings cannot be enabled simultaneously
        # https://docs.opencv.org/4.3.0/d2/de6/tutorial_py_setup_in_ubuntu.html
        # libgtk2.0-dev
        libgtk-3-dev \
        qt5-default \
        # https://en.wikipedia.org/wiki/Eigen_(C%2B%2B_library)
        libeigen3-dev \
        # Multi-core processing
        libtbb-dev \
        # Image formats
        libjpeg-dev \
        libopenexr-dev \
        libpng-dev \
        libtiff-dev \
        libwebp-dev \
        # FireWire camera support
        libdc1394-22-dev \
        # HDF5 support
        libhdf5-dev \
        # Gstreamer
        libgstreamer1.0-dev \
        libgstreamer-plugins-base1.0-dev \
        # OpenGL
        # This package recommended for OpenCV is for GTK+2 only
        libgtkglext1-dev \
        # ---
        # Additional codecs
        # Might not be necessary to be installed during compilation.
        # Installation on target machine may be sufficient.
        # ---
        gstreamer1.0-libav \
        # Depends on libva2
        gstreamer1.0-vaapi \
        libavcodec-extra \
    #
    && apt-get autoremove -y \
    && apt-get clean

# Install dependencies for LibVA and Intel Media SDK
# RUN apt-get install -y \
#     # Required common dependencies
#     git cmake pkg-config \
#     # LibVA dependencies
#     meson libdrm-dev automake libtool \
#     # Optional Media SDK dependencies
#     libpciaccess-dev

# Install LibVA for Intel Media MediaSDK
# The LibVA packages from Ubuntu repositories would result in compilation errors
# RUN git clone https://github.com/intel/libva.git \
#     && cd libva \
#     # Use latest tag for stability
#     && git fetch --tags \
#     && latest_tag=$(git describe --tags `git rev-list --tags --max-count=1`) \
#     && git checkout $latest_tag \
#     && ./autogen.sh \
#     && make \
#     && make install

# Install Intel Media SDK for hardware-accelerated encoding
# https://software.intel.com/en-us/media-sdk
# https://github.com/opencv/opencv/wiki/MediaSDK-encode-decode-backend
# RUN git clone https://github.com/Intel-Media-SDK/MediaSDK msdk \
#     && cd msdk \
#     && mkdir build \
#     && cd build \
#     && cmake .. \
#     && make \
#     && make install

# Use Miniconda to get Numpy linked with Intel MKL for maximum performance
RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh \
    && wget --quiet https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh \
    && /bin/bash ~/miniconda.sh -b -p /opt/conda \
    && rm ~/miniconda.sh \
    && /opt/conda/bin/conda update -n base conda

# Add Conda to path
ENV PATH /opt/conda/bin:$PATH

# Create Conda environment for Python 2
RUN conda create -y -n ocvpy2 python=2.7 blas=*=mkl numpy future mkl-devel

# Create Conda environment for Python 3
ARG PYTHON_VERSION=3.8
RUN conda create -y -n ocvpy3 python=${PYTHON_VERSION} blas=*=mkl numpy future mkl-devel

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

# BUILD CONFIG

# This has to be off if the resulting binaries are distributed in openly available repositories
ARG OPENCV_ENABLE_NONFREE=ON

# Require a somewhat recent CPU (>= 2010)
ARG CPU_BASELINE=POPCNT,SSE,SSE2,SSE3,SSSE3,SSE4_1,SSE4_2
# The CPU_DISPATCH is configured automatically with AVX, AVX2, AVX512, FP16 and other optimizations
# Therefore defining it manually may disable some of the optimizations
# ARG CPU_DISPATCH=AVX,AVX2 \

# OpenCV Python bindings
# Without CUDA, since there is no CUDA support for the Python bindings
# https://stackoverflow.com/questions/43315483/opencv-3-2-cuda-support-python
# Configuration
RUN cd /opencv-${OPENCV_VERSION} \
    && mkdir build_python \
    && cd build_python \
    && cmake .. \
        # Basic configuration
        -DBUILD_SHARED_LIBS=OFF \
        -DCPU_BASELINE=${CPU_BASELINE} \
        -DCMAKE_BUILD_TYPE=RELEASE \
        -DOPENCV_EXTRA_MODULES_PATH=/opencv_contrib-${OPENCV_VERSION}/modules \
        # CUDA
        -DWITH_CUDA=OFF \
        # Performance
        # -DMKL_WITH_TBB=ON
        -DWITH_EIGEN=ON \
        -DWITH_IPP=ON \
        -DWITH_LAPACK=ON \
        -DWITH_OPENGL=ON \
        -DWITH_OPENCL=ON \
        # Enabling MKL would result in
        # "ImportError: libmkl_intel_lp64.so: cannot open shared object file: No such file or directory"
        # -DWITH_MKL=ON
        -DWITH_TBB=ON \
        # Intel Media SDK
        # -DWITH_MFX=ON \
        # Formats
        -DWITH_V4L=ON \
        -DWITH_FFMPEG=ON \
        # Extra features
        # The GTK flags may not work when Qt is enabled
        -DWITH_GTK=ON \
        -DWITH_GTK3=ON \
        -DWITH_QT=ON \
        -DBUILD_TIFF=ON \
        -DBUILD_opencv_java=OFF \
        -DBUILD_opencv_legacy=OFF \
        -DOPENCV_ENABLE_NONFREE=${OPENCV_ENABLE_NONFREE} \
        # Extra binaries
        -DBUILD_TESTS=ON \
        -DBUILD_PERF_TESTS=ON \
        # Python
        -DCMAKE_INSTALL_PREFIX=/opencv-python-${OPENCV_PYTHON_VERSION}/cv2 \
        -DPYTHON2_EXECUTABLE=/opt/conda/envs/ocvpy2/bin/python \
        -DPYTHON2_INCLUDE_DIR=$(/opt/conda/envs/ocvpy2/bin/python -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
        -DPYTHON2_PACKAGES_PATH=$(/opt/conda/envs/ocvpy2/bin/python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
        -DPYTHON3_EXECUTABLE=/opt/conda/envs/ocvpy3/bin/python \
        -DPYTHON3_INCLUDE_DIR=$(/opt/conda/envs/ocvpy3/bin/python -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
        -DPYTHON3_PACKAGES_PATH=$(/opt/conda/envs/ocvpy3/bin/python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
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
    && /bin/bash -c "source /opt/conda/bin/activate ocvpy3 && python setup.py bdist_wheel" \
    # Remove the Python 3 shared library from which the wheel was built
    && rm /opencv-python-${OPENCV_PYTHON_VERSION}/cv2/cv2.*.so \
    # Copy Python 2 so file
    && cp /opencv-${OPENCV_VERSION}/build_python/lib/cv2.so /opencv-python-${OPENCV_PYTHON_VERSION}/cv2/ \
    # Build Python 2 wheel
    && /bin/bash -c "source /opt/conda/bin/activate ocvpy2 && python setup.py bdist_wheel" \
    # Copy wheels to target folder
    && cp /opencv-python-${OPENCV_PYTHON_VERSION}/dist/opencv_python-*.whl /usr/local/etc/wheels \
    # Remove temporary files
    && cd / \
    && rm -rf /opencv-python-${OPENCV_PYTHON_VERSION} \
    && rm -rf /opencv-${OPENCV_VERSION} \
    && rm -rf /opencv_contrib-${OPENCV_VERSION} \
    && rm -rf /temp

# Setuptools wheel files are saved in /usr/local/etc/wheels
# To copy the wheels to the host, create a container for example with
# sudo docker run -it <image_name> /bin/bash
# Then open another shell on the host and run (but with the correct version number)
# sudo docker cp <container_name>:/usr/local/etc/wheels/opencv_python-4.3.0-cp38-cp38m-linux_x86_64.whl .
# The container name is not the same as the image name, and you can get the container name with
# sudo docker container ls

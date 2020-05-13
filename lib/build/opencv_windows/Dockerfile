# escape=`

# Build script for OpenCV with libdc1394 on Windows.
# The resulting binary is not yet properly tested and may produce the error
# "libdc1394 error: Failed to initialize libdc1394" when run.

# -----
# Instructions
# -----
# Please note that if OPENCV_ENABLE_NONFREE is enabled, the resulting binaries
# cannot be distributed in openly available repositories.

# Building may take a lot of RAM, and by default Windows containers are limited to
# something like 2 GB, which may not be enough. You can increase the maximum memory by running
# docker build --memory=16G .

# -----
# Script starts here
# -----

# It should be possible to use a newer container version.
# 1909 is selected since it's the Windows version on my work computer and therefore the latest supported container version.
FROM mcr.microsoft.com/windows/servercore:1909

# -----
# Build Tools for Visual Studio 2019 installation
# -----

# Based on
# https://github.com/microsoft/vs-dockerfiles/blob/master/native-desktop/Dockerfile
# https://devblogs.microsoft.com/cppblog/using-msvc-in-a-docker-container-for-your-c-projects/
# https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2019

# Reset the shell.
SHELL ["cmd", "/S", "/C"]

# Set up environment to collect install errors.
COPY Install.cmd C:\TEMP\

# Download channel for fixed install.
ARG CHANNEL_URL=https://aka.ms/vs/16/release/channel

# Download required files
# ADD https://aka.ms/vscollect.exe C:\TEMP\collect.exe
# ADD ${CHANNEL_URL} C:\TEMP\VisualStudio.chman
# ADD https://aka.ms/vs/16/release/vs_buildtools.exe C:\TEMP\vs_buildtools.exe
RUN powershell -Command " `
	[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
	Invoke-WebRequest https://aka.ms/vscollect.exe -OutFile C:\TEMP\collect.exe; `
	Invoke-WebRequest %CHANNEL_URL% -OutFile C:\TEMP\VisualStudio.chman; `
	Invoke-WebRequest https://aka.ms/vs/16/release/vs_buildtools.exe -OutFile C:\TEMP\vs_buildtools.exe;"

# Download and install build tools for native desktop workload.
RUN C:\TEMP\Install.cmd C:\TEMP\vs_buildtools.exe --quiet --wait --norestart --nocache `
    --channelUri C:\TEMP\VisualStudio.chman `
    --installChannelUri C:\TEMP\VisualStudio.chman `
    --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended`
    --installPath C:\BuildTools

# -----

# Install Chocolatey
RUN powershell Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install Chocolatey packages
# Cmake is required for configuring the libdc1394 and OpenCV projects
# Git is required by the config scripts of libdc1394-cmake
# 7zip is required for extracting libusb sources (.tar.bz2)
RUN choco install 7zip cmake git -y

# Install Python 2
RUN powershell -Command " `
	[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
	Invoke-WebRequest https://repo.anaconda.com/miniconda/Miniconda2-latest-Windows-x86_64.exe -OutFile C:\TEMP\Miniconda2-latest-Windows-x86_64.exe;" `
	&& C:\TEMP\Miniconda2-latest-Windows-x86_64.exe /InstallationType=AllUsers /AddToPath=1 /S /D=C:\Miniconda2 `
	&& del C:\TEMP\Miniconda2-latest-Windows-x86_64.exe

# Conda invocation needs to be on a separate RUN command since PATH has been updated by the installer
RUN C:\Miniconda2\Scripts\conda.exe update -n base conda `
    && C:\Miniconda2\Scripts\conda.exe install blas=*=mkl numpy future mkl-devel

# Install Python 3
RUN powershell -Command " `
	[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
	Invoke-WebRequest https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -OutFile C:\TEMP\Miniconda3-latest-Windows-x86_64.exe;" `
	&& C:\TEMP\Miniconda3-latest-Windows-x86_64.exe /InstallationType=AllUsers /AddToPath=1 /RegisterPython=1 /S /D=C:\Miniconda3 `
	&& del C:\TEMP\Miniconda3-latest-Windows-x86_64.exe

RUN C:\Miniconda3\Scripts\conda.exe update -n base conda `
	&& C:\Miniconda3\Scripts\conda.exe install blas=*=mkl numpy future mkl-devel

# Python installation with conda environments
# Does not work on Windows, since calling the python.exe of an environment does not activate the environment,
# so OpenCV cannot find Numpy installations of the environments
# COPY ".\Miniconda3-latest-Windows-x86_64.exe" "C:\Temp\miniconda.exe"
# RUN C:\Temp\miniconda.exe /InstallationType=AllUsers /AddToPath=1 /RegisterPython=1 /S /D=C:\Miniconda
# RUN conda update -n base conda
# Create Conda environment for Python 2
# RUN conda create -y -n ocvpy2 python=2.7 blas=*=mkl numpy future mkl-devel
# Create Conda environment for Python 3
# ARG PYTHON_VERSION=3.7
# RUN conda create -y -n ocvpy3 python=%PYTHON_VERSION% blas=*=mkl numpy future mkl-devel

# Install Gstreamer
# RUN powershell -Command " `
# 	[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
# 	Invoke-WebRequest https://gstreamer.freedesktop.org/data/pkg/windows/1.16.2/gstreamer-1.0-msvc-x86_64-1.16.2.msi -OutFile C:\TEMP\gstreamer.msi; `
# 	Invoke-WebRequest https://gstreamer.freedesktop.org/data/pkg/windows/1.16.2/gstreamer-1.0-devel-msvc-x86_64-1.16.2.msi -OutFile C:\TEMP\gstreamer-devel.msi;" `
# 	&& C:\TEMP\gstreamer.msi `
# 	&& C:\TEMP\gstreamer-devel.msi `
# 	&& del C:\TEMP\gstreamer.msi `
# 	&& del C:\TEMP\gstreamer-devel.msi

# Download Eigen
ARG EIGEN_VERSION=3.3.7
RUN powershell -Command " `
	[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
	Invoke-WebRequest https://gitlab.com/libeigen/eigen/-/archive/%EIGEN_VERSION%/eigen-%EIGEN_VERSION%.zip -OutFile C:\TEMP\eigen.zip; `
	Expand-Archive -Path C:\TEMP\eigen.zip -DestinationPath C:\;" `
	&& del C:\TEMP\eigen.zip

# Download and extract OpenCV
ARG OPENCV_VERSION=4.3.0
# By default the Invoke-WebRequest uses old crypto which GitHub does not support
# https://github.com/cretueusebiu/valet-windows/issues/78#issuecomment-369824766
RUN powershell -Command " `
	[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
	Invoke-WebRequest https://github.com/opencv/opencv_contrib/archive/%OPENCV_VERSION%.zip -OutFile C:\TEMP\opencvcontrib-%OPENCV_VERSION%.zip; `
    Invoke-WebRequest https://github.com/opencv/opencv/archive/%OPENCV_VERSION%.zip -OutFile C:\TEMP\opencv-%OPENCV_VERSION%.zip; `
    Expand-Archive -Path C:\TEMP\opencv-%OPENCV_VERSION%.zip -DestinationPath C:\; `
    Expand-Archive -Path C:\TEMP\opencvcontrib-%OPENCV_VERSION%.zip -DestinationPath C:\;" `
	&& del C:\TEMP\opencvcontrib-%OPENCV_VERSION%.zip `
	&& del C:\TEMP\opencv-%OPENCV_VERSION%.zip

ARG OPENCV_PYTHON_VERSION=9.2
RUN powershell -Command " `
	[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
	Invoke-WebRequest https://github.com/VLAM3D/opencv-python/archive/%OPENCV_PYTHON_VERSION%.zip -OutFile C:\TEMP\opencv-python-%OPENCV_PYTHON_VERSION%.zip; `
    Expand-Archive -Path C:\TEMP\opencv-python-%OPENCV_PYTHON_VERSION%.zip -DestinationPath C:\;" `
	&& del C:\TEMP\opencv-python-%OPENCV_PYTHON_VERSION%.zip

# Monkey-patching cmake config to avoid the following error when building
# cl : command line error D8004: '/FI' requires an argument
# https://stackoverflow.com/questions/17144355/how-can-i-replace-every-occurrence-of-a-string-in-a-file-with-powershell
# RUN powershell -Command " `
#     cd C:\opencv-%OPENCV_VERSION%\cmake; `
#     (Get-Content .\OpenCVModule.cmake).replace('${CMAKE_CURRENT_SOURCE_DIR}/${pch_path}precomp.hpp', 'C:/${CMAKE_CURRENT_SOURCE_DIR}/${pch_path}precomp.hpp') | Set-Content .\OpenCVModule.cmake;"

# Libusb
# RUN powershell -Command " `
#	[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
#	Invoke-WebRequest https://github.com/libusb/libusb/releases/download/v1.0.23/libusb-1.0.23.tar.bz2 -OutFile C:\TEMP\libusb.tar.bz2;"
#	&& "C:\Program Files\7-Zip\7z.exe" e C:\TEMP\libusb.tar.bz2 -y -o"C:\libusb"

# Libdc1394 using MinGW-compiled binaries
# COPY ./artifacts.zip C:\TEMP\libdc1394.zip
# RUN powershell -Command " `
#     Expand-Archive -Path C:\TEMP\libdc1394.zip -DestinationPath C:\TEMP\libdc1394;"

# Libdc1394 using cmake
RUN cd C:\ `
	&& git clone https://github.com/aimotive/libdc1394-cmake.git

RUN cd C:\libdc1394-cmake `
	# Having libusb results in linker errors with this build configuration.
	# We don't need IIDC over USB our lab, so we can remove it.
	&& rmdir C:\libdc1394-cmake\libusb-1.0.20-windows /S /Q `
	&& mkdir build `
	&& cd build `
	&& "C:\Program Files\CMake\bin\cmake.exe" .. `
		# This is required to prevent MSVC error LNK4098
		# https://docs.microsoft.com/en-us/cpp/error-messages/tool-errors/linker-tools-warning-lnk4098?view=vs-2019
		-DBUILD_SHARED_LIBS=OFF `
		# -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL
		# -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded
		# Something in this library requires msvcrt.lib, so we cannot disable linking to it.
		# However, we can still ensure that no debug crt linking ends up in the final binary
		-DCMAKE_EXE_LINKER_FLAGS="/NODEFAULTLIB:libcmtd.lib /NODEFAULTLIB:msvcrtd.lib" `
		# You can use the following options for debugging library linking
		# -DMSVC_RUNTIME_LIBRARY=MultiThreaded
		# -DCMAKE_CXX_FLAGS_RELEASE="/MT"
		# Compiling without any default libraries results in linker errors
		# -DCMAKE_EXE_LINKER_FLAGS="/NODEFAULTLIB"
		# -DCMAKE_EXE_LINKER_FLAGS="/VERBOSE:LIB"
	&& "C:\Program Files\CMake\bin\cmake.exe" --build . --config Release --parallel

# BUILD CONFIG

# This has to be off if the resulting binaries are distributed in openly available repositories
# Currently enabling this results in a crash when processing opencv_tracking.vcxproj:
# --- Crash output ---
#  Generating Code...
#  opencv_tracking.vcxproj -> C:\opencv-4.3.0\build_python\lib\Release\opencv_tracking430.lib
# The command 'cmd /S /C cd C:\opencv-%OPENCV_VERSION%\build_python       && "C:\Program Files\CMake\bin\cmake.exe" --build . --config Release --target opencv_python3 --parallel       && "C:\Program Files\CMake\bin\cmake.exe" --build . --config Release --target opencv_python2 --parallel' returned a non-zero code: 1
# ---
ARG OPENCV_ENABLE_NONFREE=OFF

# Require a somewhat recent CPU (>= 2010)
ARG CPU_BASELINE=POPCNT,SSE,SSE2,SSE3,SSSE3,SSE4_1,SSE4_2
# The CPU_DISPATCH is configured automatically with AVX, AVX2, AVX512, FP16 and other optimizations
# Therfore defining it manually may disable some of the optimizations
# ARG CPU_DISPATCH=AVX,AVX2

# OpenCV Python bindings
# Without CUDA, since there is no CUDA support for the Python bindings
# https://stackoverflow.com/questions/43315483/opencv-3-2-cuda-support-python
# Configuration
RUN cd C:\opencv-%OPENCV_VERSION% `
    && mkdir build_python `
    && cd build_python `
    && "C:\Program Files\CMake\bin\cmake.exe" .. `
        # Basic configuration
		# Python bindings require static libraries
        -DBUILD_SHARED_LIBS=OFF `
		# This has to be off when using libdc1394, since it depends on shared CRT
		-DBUILD_WITH_STATIC_CRT=OFF `
		# -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded
		# Ensure that no debug crt linking ends up in the final binary
		-DCMAKE_EXE_LINKER_FLAGS_RELEASE="/NODEFAULTLIB:libcmtd.lib /NODEFAULTLIB:msvcrtd.lib" `
		# -DCMAKE_CXX_FLAGS_RELEASE="/MT"
		# -DMSVC_RUNTIME_LIBRARY=MultiThreaded
		# -DCMAKE_EXE_LINKER_FLAGS="/VERBOSE:LIB"
		# -DENABLE_SOLUTION_FOLDERS=ON
		-DENABLE_PRECOMPILED_HEADERS=OFF `
        -DCPU_BASELINE=%CPU_BASELINE% `
        -DCMAKE_BUILD_TYPE=RELEASE `
        -DOPENCV_EXTRA_MODULES_PATH=/opencv_contrib-%OPENCV_VERSION%/modules `
		# Disabling modules when testing different settings speeds up building
		# -DBUILD_opencv_calib3d=OFF
		# -DBUILD_opencv_dnn=OFF
		# -DBUILD_opencv_features2d=OFF
		# -DBUILD_opencv_flann=OFF
		# -DBUILD_opencv_highgui=OFF
		# -DBUILD_opencv_ml=OFF
		# -DBUILD_opencv_objdetect=OFF
		# -DBUILD_opencv_stitching=OFF
		# -DBUILD_opencv_ts=OFF
        # CUDA
        -DWITH_CUDA=OFF `
		# libdc1394
		-DDC1394_INCLUDE=C:\libdc1394-cmake\libdc1394\libdc1394 `
		-DDC1394_LIBRARY=C:\libdc1394-cmake\build\dc1394\Release\libdc1394.lib `
		# For MinGW
		# -DDC1394_INCLUDE=C:\TEMP\libdc1394\install\include `
		# -DDC1394_LIBRARY=C:\TEMP\libdc1394\install\lib\libdc1394.a `
        # Performance
        # -DMKL_WITH_TBB=ON
		-DWITH_DIRECTX=ON `
		-DWITH_DSHOW=ON `
        -DWITH_EIGEN=ON `
		# The Eigen path must have only forward slashes
		-DEIGEN_INCLUDE_PATH=C:/eigen-%EIGEN_VERSION% `
        -DWITH_IPP=ON `
		# This may point to mkl_rt.lib, and result in requiring mkl_rt.dll to run
        -DWITH_LAPACK=OFF `
        -DWITH_OPENGL=ON `
        -DWITH_OPENCL=ON `
        # Enabling MKL would result in
        # "ImportError: libmkl_intel_lp64.so: cannot open shared object file: No such file or directory"
		# or
		# "ImportError: DLL load failed: The specified module could not be found."
		# The latter is caused by missing mkl_rt.dll
        -DWITH_MKL=OFF `
        -DWITH_TBB=ON `
		# Gstreamer
		# Building with Gstreamer works, but the binary will require the following Gstreamer dlls when run:
		# gstreamer-1.0-0.dll, gstapp-1.0-0.dll, gstriff-1.0-0.dll, gstpbutils-1.0-0.dll, glib-2.0-0.dll, gobject-2.0-0.dll
		# Otherwise running the binary will result in
		# "ImportError: DLL load failed: The specified module could not be found."
		# However, so far I haven't been able to make this error go away, as adding these to PATH etc. has not helped.
		# -DWITH_GSTREAMER=ON `
		# -DGSTREAMER_DIR=C:\gstreamer\1.0\x86_64 `
        # Formats
        -DWITH_FFMPEG=ON `
        # Extra features
        -DBUILD_TIFF=ON `
        -DBUILD_opencv_java=OFF `
        -DBUILD_opencv_legacy=OFF `
        -DOPENCV_ENABLE_NONFREE=%OPENCV_ENABLE_NONFREE% `
        # Extra binaries
        -DBUILD_TESTS=ON `
        -DBUILD_PERF_TESTS=ON `
        # Python
        -DCMAKE_INSTALL_PREFIX=/opencv-python-%OPENCV_PYTHON_VERSION%/cv2 `
        # -DPYTHON2_EXECUTABLE=C:\Miniconda\envs\ocvpy2\python.exe `
        # -DPYTHON2_INCLUDE_DIR=C:\Miniconda\envs\ocvpy2\include `
        # -DPYTHON2_PACKAGES_PATH=C:\Miniconda\envs\ocvpy3\Lib\site-packages `
        # -DPYTHON3_EXECUTABLE=C:\Miniconda\envs\ocvpy3\python.exe `
        # -DPYTHON3_INCLUDE_DIR=C:\Miniconda\envs\ocvpy3\include `
        # -DPYTHON3_PACKAGES_PATH=C:\Miniconda\envs\ocvpy3\Lib\site-packages
		-DPYTHON2_EXECUTABLE=C:\Miniconda2\python.exe `
        -DPYTHON2_INCLUDE_DIR=C:\Miniconda2\include `
        -DPYTHON2_PACKAGES_PATH=C:\Miniconda2\Lib\site-packages `
        -DPYTHON3_EXECUTABLE=C:\Miniconda3\python.exe `
        -DPYTHON3_INCLUDE_DIR=C:\Miniconda3\include `
        -DPYTHON3_PACKAGES_PATH=C:\Miniconda3\Lib\site-packages

# Monkey-patching OpenCV
COPY .\patch_opencv.txt C:\TEMP\cv2_temp.cpp
RUN powershell -Command " `
	cd C:\opencv-%OPENCV_VERSION%\modules\videoio\src\; `
	(Get-Content .\cap_dc1394_v2.cpp).replace('#include <unistd.h>', '').replace('#include <winsock2.h>', '#include <windows.h>') | Set-Content .\cap_dc1394_v2.cpp; `
	cd C:\opencv-%OPENCV_VERSION%\modules\python\src2; `
	# New-Item .\cv2_temp.cpp; `
	# Set-Content .\cv2_temp.cpp -Value "#pragma comment(lib, 'ws2_32.lib')`n";
	Copy-Item -Path C:\TEMP\cv2_temp.cpp -Destination C:\opencv-%OPENCV_VERSION%\modules\python\src2\; `
	Add-Content -Path .\cv2_temp.cpp -Value (Get-Content .\cv2.cpp); `
	del .\cv2.cpp; `
	mv .\cv2_temp.cpp .\cv2.cpp;"

# Compilation
RUN cd C:\opencv-%OPENCV_VERSION%\build_python `
	&& "C:\Program Files\CMake\bin\cmake.exe" --build . --config Release --target opencv_python3 --parallel `
	&& "C:\Program Files\CMake\bin\cmake.exe" --build . --config Release --target opencv_python2 --parallel
# --parallel %NUMBER_OF_PROCESSORS%

# Alternative compilation with Microsoft tools
# RUN C:\BuildTools\Common7\Tools\VsDevCmd.bat `
# 	&& cd C:\opencv-%OPENCV_VERSION%\build_python `
# 	&& MSBuild OpenCV.sln /maxcpucount /validate


RUN cd C:\opencv-%OPENCV_VERSION%\build_python `
    # Copy Python 3 so files
    && copy C:\opencv-%OPENCV_VERSION%\build_python\lib\python3\Release\cv2.*.pyd C:\opencv-python-%OPENCV_PYTHON_VERSION%\cv2\ `
    # Create a directory for the wheels
    && mkdir C:\Wheels `
    # Fix for finding OpenCV
	&& mkdir C:\usr\local\include\ `
    && powershell -Command "New-Item -ItemType SymbolicLink -Target C:\opencv-%OPENCV_VERSION%\modules\core\include\opencv2 -Path C:\usr\local\include\opencv2" `
    && cd C:\opencv-python-%OPENCV_PYTHON_VERSION% `
    && C:\Miniconda3\python.exe find_version.py `
    # Build Python 3 wheel
    && C:\Miniconda3\python.exe setup.py bdist_wheel `
    # Remove the Python 3 shared library from which the wheel was built
    && del C:\opencv-python-%OPENCV_PYTHON_VERSION%\cv2\cv2.*.pyd `
    # Copy Python 2 so file
    && copy C:\opencv-%OPENCV_VERSION%\build_python\lib\Release\cv2.pyd C:\opencv-python-%OPENCV_PYTHON_VERSION%\cv2\ `
    # Build Python 2 wheel
    && C:\Miniconda2\python.exe setup.py bdist_wheel `
    # Copy wheels to target folder
    && copy C:\opencv-python-%OPENCV_PYTHON_VERSION%\dist\opencv_python-*.whl C:\Wheels\ `
    # Remove temporary files
    && cd C:\ `
    && rmdir C:\opencv-python-%OPENCV_PYTHON_VERSION% /S /Q `
    && rmdir C:\opencv-%OPENCV_VERSION% /S /Q `
    && rmdir C:\opencv_contrib-%OPENCV_VERSION% /S /Q `
    && rmdir C:\TEMP /S /Q

# Analyze the wheels
RUN mkdir C:\TEMP `
	&& "C:\Program Files\7-Zip\7z.exe" e C:\Wheels\opencv_python-*.whl -y -o"C:\TEMP" `
	&& C:\BuildTools\Common7\Tools\VsDevCmd.bat `
	&& dumpbin.exe C:\TEMP\cv2*.pyd /IMPORTS > C:\Wheels\Import_analysis.txt `
	&& rmdir C:\TEMP /S /Q `
	&& powershell -Command " `
		cat C:\Wheels\Import_analysis.txt | Select-String -Pattern '.dll|.pyd' > C:\Wheels\Import_analysis_summary.txt;" `
	&& echo If you get the error "ImportError: DLL load failed: The specified module could not be found.", please ensure that you have the following dll files in your system. You may need to add their locations to the PATH environment variable. `
	&& type C:\Wheels\Import_analysis_summary.txt

CMD ["powershell"]

# Setuptools wheel files are saved in C:\Wheels
# To copy the wheels to the host, create a container for example with
# docker run -it <image_name>
# Then open another shell on the host and run
# docker cp <container_name>:"C:\Wheels\opencv_python-4.3.0-cp37-cp37m-win_amd64.whl" .
# If you get the error "Error response from daemon: filesystem operations against a running Hyper-V container are not supported"
# then you have to close the running container before copying

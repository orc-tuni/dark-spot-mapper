#!/bin/sh

CMU_URL=https://www.cs.cmu.edu/~iwan/1394/downloads/1394camera646.exe
LIBDC1394_URL=https://netix.dl.sourceforge.net/project/libdc1394/libdc1394-2/2.2.6/libdc1394-2.2.6.tar.gz
CWD=$(pwd)

apt-get update
apt-get install g++-mingw-w64 make p7zip-full wget -y

mkdir temp
mkdir build
mkdir build/deps
mkdir install

wget ${CMU_URL} -O temp/cmu.exe
wget ${LIBDC1394_URL} -O temp/libdc1394.tar.gz

cd temp || return
tar -xvzf libdc1394.tar.gz
cd "${CWD}" || return
mv temp/libdc1394-*/* build
7z e temp/cmu.exe -o"temp/cmu/include" -y include/*
7z e temp/cmu.exe -o"temp/cmu/lib" -y lib64/x64/*
mkdir build/deps/include
mkdir build/deps/lib
cp temp/cmu/lib/1394camera.lib build/deps/lib/lib1394camera.a
cp temp/cmu/include/1394camapi.h build/deps/include/
cp temp/cmu/include/1394common.h build/deps/include/

cd "${CWD}"/build || return
./configure --host=x86_64-w64-mingw32 CFLAGS="-L${CWD}/build/deps/lib -I${CWD}/build/deps/include" --prefix="${CWD}"/install/
make -j"$(nproc)"
make install

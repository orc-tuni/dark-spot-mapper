#!/bin/sh

FTD2XX_URL=https://www.ftdichip.com/Drivers/CDM/CDM%20v2.12.28%20WHQL%20Certified.zip
SIMPLEMOTION_URL=https://granitedevices.com/assets/files/simplemotion-latest.zip
CWD=$(pwd)

apt-get update
apt-get install g++-mingw-w64 unzip wget -y

# Download the source code and libraries
mkdir download
wget ${FTD2XX_URL} -O download/ftd2xx.zip
wget ${SIMPLEMOTION_URL} -O download/simplemotion.zip

# Move the necessary files to the build folder
unzip download/ftd2xx.zip -d download/ftd2xx/
unzip download/simplemotion.zip -d download/simplemotion
mkdir build
mkdir build/x86
mkdir build/x86_64
cp download/simplemotion/SimpleMotion*/SimpleMotion_lib/* build/x86/ -r
cp download/simplemotion/SimpleMotion*/SimpleMotion_lib/* build/x86_64/ -r
rm build/x86/ftdilib/*
rm build/x86_64/ftdilib/*
cp download/ftd2xx/ftd2xx.h build/x86/ftdilib/
cp download/ftd2xx/ftd2xx.h build/x86_64/ftdilib/
mv download/ftd2xx/i386/* build/x86/ftdilib/
mv download/ftd2xx/amd64/* build/x86_64/ftdilib/

# Build 32-bit
cd $CWD/build/x86
i686-w64-mingw32-g++ -O2 -Wall -c -DBUILD_DLL simplemotion.cpp sm_consts.cpp 
i686-w64-mingw32-g++ -O2 -Wall -shared simplemotion.o sm_consts.o -o simplemotion.dll -Iftdilib -Lftdilib -lftd2xx

# Build 64-bit
cd ${CWD}/build/x86_64
x86_64-w64-mingw32-g++ -O2 -Wall -c -DBUILD_DLL simplemotion.cpp sm_consts.cpp
x86_64-w64-mingw32-g++ -O2 -Wall -shared simplemotion.o sm_consts.o -o simplemotion64.dll -Iftdilib -Lftdilib -lftd2xx

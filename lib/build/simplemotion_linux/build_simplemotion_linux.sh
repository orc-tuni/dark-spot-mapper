#!/bin/sh

FTD2XX_URL=https://www.ftdichip.com/Drivers/D2XX/Linux/libftd2xx-x86_64-1.4.8.gz
SIMPLEMOTION_URL=https://granitedevices.com/assets/files/simplemotion-latest.zip
CWD=$(pwd)

apk --no-cache add g++ unzip wget

# Download the source code and libraries
mkdir download
wget ${FTD2XX_URL} -O download/ftd2xx.gz
wget ${SIMPLEMOTION_URL} -O download/simplemotion.zip

# Move the necessary files to the build folder
mkdir build
mkdir download/ftd2xx
tar -xf download/ftd2xx.gz -C download/ftd2xx/
unzip download/simplemotion.zip -d download/simplemotion
cp download/simplemotion/SimpleMotion*/SimpleMotion_lib/* build/ -r
rm build/ftdilib/*
mv download/ftd2xx/release/ftd2xx.h build/ftdilib
mv download/ftd2xx/release/WinTypes.h build/ftdilib
mv download/ftd2xx/release/build/* build/ftdilib/

# Monkey-patch the SimpleMotion source code for Linux support
sed -i 's@#include <windows.h>@typedef unsigned char byte;@g' build/simplemotion_private.h
sed -i 's@__declspec(dllexport)@__attribute__((visibility("default")))@g' build/simplemotion.h
sed -i 's@stricmp(@strcasecmp(@g' build/simplemotion.cpp

cd ${CWD}/build
g++ -O2 -Wall -c -fPIC -DBUILD_DLL simplemotion.cpp sm_consts.cpp -I/usr/include
g++ -O2 -Wall -shared simplemotion.o sm_consts.o -o simplemotion64.so -I/build/ftdilib -L/build/ftdilib -lftd2xx

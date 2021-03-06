FROM debian:latest

RUN apt-get update \
    && apt-get install -y g++ unzip wget \
    && apt-get autoremove -y \
    && apt-get clean

ARG FTD2XX_URL=https://www.ftdichip.com/Drivers/D2XX/Linux/libftd2xx-x86_64-1.4.8.gz
ARG SIMPLEMOTION_URL=https://granitedevices.com/assets/files/simplemotion-latest.zip

# Download the source code and libraries
RUN mkdir download \
    && wget -nv ${FTD2XX_URL} -O download/ftd2xx.gz \
    && wget -nv ${SIMPLEMOTION_URL} -O download/simplemotion.zip

# Move the necessary files to the build folder
RUN mkdir build \
    && mkdir download/ftd2xx \
    && tar -xf download/ftd2xx.gz -C download/ftd2xx/ \
    && unzip download/simplemotion.zip -d download/simplemotion \
    && cp download/simplemotion/SimpleMotion*/SimpleMotion_lib/* build/ -r \
    && rm build/ftdilib/* \
    && mv download/ftd2xx/release/ftd2xx.h build/ftdilib \
    && mv download/ftd2xx/release/WinTypes.h build/ftdilib \
    && mv download/ftd2xx/release/build/* build/ftdilib/

# Monkey-patch the SimpleMotion source code for Linux support
RUN sed -i 's@#include <windows.h>@typedef unsigned char byte;@g' build/simplemotion_private.h \
    && sed -i 's@__declspec(dllexport)@__attribute__((visibility("default")))@g' build/simplemotion.h \
    && sed -i 's@stricmp(@strcasecmp(@g' build/simplemotion.cpp

RUN cd build \
    && g++ -O2 -Wall -ftree-vectorize -fopt-info-vec -c -fPIC -DBUILD_DLL simplemotion.cpp sm_consts.cpp \
    && g++ -O2 -Wall -ftree-vectorize -fopt-info-vec -shared simplemotion.o sm_consts.o -o simplemotion64.so -Iftdilib -Lftdilib -lftd2xx

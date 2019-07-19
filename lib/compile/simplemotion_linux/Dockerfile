FROM debian:latest
RUN apt-get update \
    && apt-get install g++ unzip -y

ARG ftd2xx_url=https://www.ftdichip.com/Drivers/D2XX/Linux/libftd2xx-x86_64-1.4.8.gz
ARG simplemotion_url=https://granitedevices.com/assets/files/simplemotion-latest.zip

ADD $ftd2xx_url /download/ftd2xx.gz
ADD $simplemotion_url /download/simplemotion.zip

WORKDIR /build
RUN mkdir /download/ftd2xx \
    && tar -xf /download/ftd2xx.gz -C /download/ftd2xx/ \
    && unzip /download/simplemotion.zip -d /download/simplemotion
RUN cp /download/simplemotion/SimpleMotion*/SimpleMotion_lib/* /build/ -r \
    && rm /build/ftdilib/* \
    && mv /download/ftd2xx/release/ftd2xx.h /build/ftdilib \
    && mv /download/ftd2xx/release/WinTypes.h /build/ftdilib \
    && mv /download/ftd2xx/release/build/* /build/ftdilib/ \
    && sed -i 's@#include <windows.h>@typedef unsigned char byte;@g' /build/simplemotion_private.h \
    && sed -i 's@__declspec(dllexport)@__attribute__((visibility("default")))@g' /build/simplemotion.h \
    && sed -i 's@stricmp(@strcasecmp(@g' /build/simplemotion.cpp

RUN g++ -O2 -Wall -c -fPIC -DBUILD_DLL simplemotion.cpp sm_consts.cpp -I/usr/include \
    && g++ -O2 -Wall -shared simplemotion.o sm_consts.o -o simplemotion64.so -I/build/ftdilib -L/build/ftdilib -lftd2xx

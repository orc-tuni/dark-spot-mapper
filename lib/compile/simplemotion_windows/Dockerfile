FROM debian:latest
RUN apt-get update \
    && apt-get install mingw-w64 unzip -y

ARG ftd2xx_url=https://www.ftdichip.com/Drivers/CDM/CDM%20v2.12.28%20WHQL%20Certified.zip
ARG simplemotion_url=https://granitedevices.com/assets/files/simplemotion-latest.zip

ADD $ftd2xx_url /download/ftd2xx.zip
ADD $simplemotion_url /download/simplemotion.zip

RUN unzip /download/ftd2xx.zip -d /download/ftd2xx/ \
    && unzip /download/simplemotion.zip -d /download/simplemotion
RUN mkdir /build \
    && mkdir /build/x86 \
    && mkdir /build/x86_64 \
    && cp /download/simplemotion/SimpleMotion*/SimpleMotion_lib/* /build/x86/ -r \
    && cp /download/simplemotion/SimpleMotion*/SimpleMotion_lib/* /build/x86_64/ -r \
    && rm /build/x86/ftdilib/* \
    && rm /build/x86_64/ftdilib/* \
    && cp /download/ftd2xx/ftd2xx.h /build/x86/ftdilib/ \
    && cp /download/ftd2xx/ftd2xx.h /build/x86_64/ftdilib/ \
    && mv /download/ftd2xx/i386/* /build/x86/ftdilib/ \
    && mv /download/ftd2xx/amd64/* /build/x86_64/ftdilib/

WORKDIR /build/x86
RUN i686-w64-mingw32-g++ -O2 -Wall -c -DBUILD_DLL simplemotion.cpp sm_consts.cpp \
    && i686-w64-mingw32-g++ -O2 -Wall -shared simplemotion.o sm_consts.o -o simplemotion.dll -I/build/x86/ftdilib -L/build/x86/ftdilib -lftd2xx

WORKDIR /build/x86_64
RUN x86_64-w64-mingw32-g++ -O2 -Wall -c -DBUILD_DLL simplemotion.cpp sm_consts.cpp \
    && x86_64-w64-mingw32-g++ -O2 -Wall -shared simplemotion.o sm_consts.o -o simplemotion64.dll -I/build/x86_64/ftdilib -L/build/x86_64/ftdilib -lftd2xx

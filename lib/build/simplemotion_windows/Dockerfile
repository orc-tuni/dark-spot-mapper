FROM debian:latest

RUN apt-get update \
    && apt-get install g++-mingw-w64 unzip wget -y

ARG FTD2XX_URL=https://www.ftdichip.com/Drivers/CDM/CDM%20v2.12.28%20WHQL%20Certified.zip
ARG SIMPLEMOTION_URL=https://granitedevices.com/assets/files/simplemotion-latest.zip

# Download the source code and libraries
RUN mkdir download \
    && wget -nv ${FTD2XX_URL} -O download/ftd2xx.zip \
    && wget -nv ${SIMPLEMOTION_URL} -O download/simplemotion.zip

# Move the necessary files to the build folder
RUN unzip download/ftd2xx.zip -d download/ftd2xx/ \
    && unzip download/simplemotion.zip -d download/simplemotion \
    && mkdir build \
    && mkdir build/x86 \
    && mkdir build/x86_64 \
    && cp download/simplemotion/SimpleMotion*/SimpleMotion_lib/* build/x86/ -r \
    && cp download/simplemotion/SimpleMotion*/SimpleMotion_lib/* build/x86_64/ -r \
    && rm build/x86/ftdilib/* \
    && rm build/x86_64/ftdilib/* \
    && cp download/ftd2xx/ftd2xx.h build/x86/ftdilib/ \
    && cp download/ftd2xx/ftd2xx.h build/x86_64/ftdilib/ \
    && mv download/ftd2xx/i386/* build/x86/ftdilib/ \
    && mv download/ftd2xx/amd64/* build/x86_64/ftdilib/

# Build 32-bit
RUN cd build/x86 \
    && i686-w64-mingw32-g++ -O2 -Wall -ftree-vectorize -fopt-info-vec -c -DBUILD_DLL simplemotion.cpp sm_consts.cpp \
    && i686-w64-mingw32-g++ -O2 -Wall -ftree-vectorize -fopt-info-vec -shared simplemotion.o sm_consts.o -o simplemotion.dll -Iftdilib -Lftdilib -lftd2xx

# Build 64-bit
RUN cd build/x86_64 \
    && x86_64-w64-mingw32-g++ -O2 -Wall -ftree-vectorize -fopt-info-vec -c -DBUILD_DLL simplemotion.cpp sm_consts.cpp \
    && x86_64-w64-mingw32-g++ -O2 -Wall -ftree-vectorize -fopt-info-vec -shared simplemotion.o sm_consts.o -o simplemotion64.dll -Iftdilib -Lftdilib -lftd2xx

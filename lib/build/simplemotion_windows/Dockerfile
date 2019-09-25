FROM debian:latest
RUN apt-get update \
    && apt-get install g++-mingw-w64 unzip wget -y
COPY ./build_simplemotion_windows.sh /build.sh
# Convert CRLF line endings to LF
RUN tr -d '\015' </build.sh >/build-temp.sh \
    && mv /build-temp.sh /build.sh
RUN sh /build.sh

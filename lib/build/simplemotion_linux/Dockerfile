FROM alpine:latest
RUN apk --no-cache add g++ unzip wget
COPY ./build_simplemotion_linux.sh /build.sh
RUN sh /build.sh

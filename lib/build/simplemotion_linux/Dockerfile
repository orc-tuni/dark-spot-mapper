FROM alpine:latest
RUN apk --no-cache add g++ unzip wget
COPY ./build_simplemotion_linux.sh /build.sh
# Convert CRLF line endings to LF
RUN tr -d '\015' </build.sh >/build-temp.sh \
    && mv /build-temp.sh /build.sh
RUN sh /build.sh

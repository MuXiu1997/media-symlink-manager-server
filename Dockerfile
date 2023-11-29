FROM ubuntu:23.10

# ref: https://stackoverflow.com/questions/28405902/how-to-set-the-locale-inside-a-debian-ubuntu-docker-container#answer-41648500
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN mkdir -p /data

COPY dist/media-symlink-manager /usr/local/bin/media-symlink-manager

EXPOSE 80

VOLUME ["/data"]

ENTRYPOINT ["/usr/local/bin/media-symlink-manager"]

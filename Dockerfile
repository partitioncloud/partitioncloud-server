FROM python:latest

ARG VERSION=unknown
LABEL org.opencontainers.image.source="https://github.com/partitioncloud/partitioncloud-server"
LABEL org.opencontainers.image.version="${VERSION}"

# Dependencies are managed by the image: migration hooks must not use pip
ENV PARTITIONCLOUD_DOCKER=1

WORKDIR /app

EXPOSE 5000

COPY . /app

RUN apt-get update
RUN apt-get install -y python3-pip sqlite3 ghostscript

RUN rm /app/instance -rf
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

# Fonts are downloaded once at build time (make.sh retries at start if it failed)
RUN bash make.sh fonts

ENTRYPOINT [ "bash", "docker-entrypoint.sh" ]
CMD [ "server" ]

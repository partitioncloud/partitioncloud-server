FROM python:3.13-slim

WORKDIR /app

EXPOSE 5000

RUN apt-get update \
    && apt-get install -y sqlite3 ghostscript curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt gunicorn

# TODO I need to install npm & make in the build container ?
RUN bash make.sh score-display

# Run as a non-root user. instance/ and backups/ are created here so that
# new volumes mounted on them are owned by this user
RUN useradd --system --uid 1000 --no-create-home app \
    && mkdir instance backups \
    && chown app:app . instance backups

ARG VERSION=unknown
LABEL org.opencontainers.image.source="https://github.com/partitioncloud/partitioncloud-server"
LABEL org.opencontainers.image.version="${VERSION}"

# Dependencies are managed by the image: migration hooks must not use pip
ENV PARTITIONCLOUD_DOCKER=1
ENV PARTITIONCLOUD_VERSION="${VERSION}"

COPY --chown=app:app . .
USER app

# Fonts are downloaded once at build time (make.sh retries at start if it failed)
RUN bash make.sh fonts

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD [ "python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/', timeout=4)" ]

ENTRYPOINT [ "bash", "docker-entrypoint.sh" ]
CMD [ "server" ]

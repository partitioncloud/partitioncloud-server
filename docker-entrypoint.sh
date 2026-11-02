#!/bin/bash
set -e

case "${1:-server}" in
    server)
        # First start on an empty volume: create folders, config and database
        if ! test -f instance/partitioncloud.sqlite; then
            bash make.sh init
        fi
        exec bash make.sh production
        ;;
    migrate)
        # Interactive, run with `docker run -it`
        shift
        exec python3 scripts/migration.py "$@"
        ;;
    *)
        exec "$@"
        ;;
esac

#!/bin/bash
set -e

case "${1:-server}" in
    server)
        # Local builds without VERSION skip version tracking
        version="${PARTITIONCLOUD_VERSION:-unknown}"

        if ! test -f instance/partitioncloud.sqlite; then
            # First start on an empty volume: create folders, config and database
            bash make.sh init
            [ "$version" = "unknown" ] || echo "$version" > instance/VERSION
        elif [ "$version" != "unknown" ]; then
            # Refuse to start on data that needs a migration
            python3 scripts/migration.py --check --target "$version" || {
                echo "Run the 'migrate' command of this image first" >&2
                exit 1
            }
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

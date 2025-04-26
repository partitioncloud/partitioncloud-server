#!/bin/bash

[[ $FLASK_CONFIG_PATH ]] || FLASK_CONFIG_PATH="default_config.py"

init () {
    mkdir -p "$INSTANCE_PATH"
    mkdir -p "$INSTANCE_PATH/partitions"
    mkdir -p "$INSTANCE_PATH/attachments"
    mkdir -p "$INSTANCE_PATH/search-partitions"
    mkdir -p "$INSTANCE_PATH/cache/thumbnails"
    mkdir -p "$INSTANCE_PATH/cache/search-thumbnails"

    if ! test -f "$INSTANCE_PATH/config.py"; then
        echo "SECRET_KEY=\"$(python3 -c 'import secrets; print(secrets.token_hex())')\"" > "$INSTANCE_PATH/config.py"
    fi

    if test -f "$INSTANCE_PATH/partitioncloud.sqlite"; then
        printf "Souhaitez vous supprimer la base de données existante ? [y/n] "
        read -r CONFIRMATION
        [[ $CONFIRMATION == y ]] || exit 1
        rm "$INSTANCE_PATH/partitioncloud.sqlite"
    fi
    sqlite3 "$INSTANCE_PATH/partitioncloud.sqlite" '.read partitioncloud/schema.sql'
    echo "Base de données créé"
    sqlite3 "$INSTANCE_PATH/partitioncloud.sqlite" '.read partitioncloud/init.sql'
    echo "Utilisateur root:root ajouté"
}

translations () {
    # Rajouter les chaînes non traduites
    pybabel extract -F babel.cfg -k _l -o partitioncloud/translations/messages.pot .
    pybabel update -i partitioncloud/translations/messages.pot -d partitioncloud/translations/
    # Compiler
    pybabel compile -d partitioncloud/translations/
}

start () {
    pybabel compile -d partitioncloud/translations/
    flask run --port=$PORT
}

fonts () {
    # Download "Readex Pro" from google fonts, an @import would break GDPR, and not be convenient
    mkdir -p partitioncloud/static/font

    echo "Downloading fonts from google fonts"

    fonts_urls=$(curl -sSf 'https://fonts.googleapis.com/css2?family=Readex+Pro:wght@160..700&display=swap' \
        -H 'User-Agent: Mozilla/5.0 Gecko/20100101 Firefox/138.0' \
        | grep -Eo "(http|https)://[a-zA-Z0-9./?=_%:-]*")

    # Expecting 4 urls
    latin_ext_url=$(echo $fonts_urls | cut -d " " -f 3)
    latin_url=$(echo $fonts_urls | cut -d " " -f 4)

    echo "Downloading 'ReadexPro-latin-ext.woff2' from ${latin_ext_url}"
    curl -sSf ${latin_ext_url} > 'partitioncloud/static/font/ReadexPro-latin-ext.woff2'

    echo "Downloading 'ReadexPro-latin.woff2' from ${latin_url}"
    curl -sSf ${latin_url} > 'partitioncloud/static/font/ReadexPro-latin.woff2'

    # If the two files are empty, we remove the directory to do another attempt next time
    ([ -s 'partitioncloud/static/font/ReadexPro-latin-ext.woff2' ]&& \
        [ -s 'partitioncloud/static/font/ReadexPro-latin.woff2' ])   \
        || rm -r partitioncloud/static/font
}

production () {
    pybabel compile -d partitioncloud/translations/
    if ! test -f partitioncloud/static/font; then
        fonts
    fi
    FLASK_APP=partitioncloud gunicorn \
    wsgi:app \
    --bind 0.0.0.0:$PORT
}

load_config () {
    # Load variables PORT and INSTANCE_PATH
    eval $(cat $1 | grep -E "^PORT=")
    eval $(cat $1 | grep -E "^INSTANCE_PATH=")
}


usage () {
    echo "Usage:"
    echo -e "\t$0 init"
    echo -e "\t$0 fonts"
    echo -e "\t$0 start"
    echo -e "\t$0 production"
    echo -e "\t$0 translations"
}


RESULT=$(type "$1")
if [[ $1 && $RESULT = *"is a"*"function"* || $RESULT == *"est une fonction"* ]]; then
    # Import config
    load_config "$FLASK_CONFIG_PATH"

    if test -f "$INSTANCE_PATH/config.py"; then
        load_config "$INSTANCE_PATH/config.py"
    fi

    $1 ${*:2} # Call the function
else
	usage
	echo $RESULT
	exit 1
fi

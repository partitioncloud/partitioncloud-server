#!/bin/bash

INSTANCE_PATH="instance"

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
    flask run --port=$PORT
}

production () {
    FLASK_APP=partitioncloud /usr/bin/gunicorn \
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
    echo -e "\t$0 start"
    echo -e "\t$0 production"
    echo -e "\t$0 translations"

}

RESULT=$(type "$1")
if [[ $1 && $RESULT = *"is a"*"function"* || $RESULT == *"est une fonction"* ]]; then
    # Import config
    load_config "default_config.py"
    [[ ! -x "$INSTANCE_PATH/config.py" ]] && load_config "$INSTANCE_PATH/config.py"
    $1 ${*:2} # Call the function
else
	usage
	echo $RESULT
	exit 1
fi

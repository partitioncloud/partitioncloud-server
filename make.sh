#!/bin/bash

init () {
    mkdir -p "instance"
    mkdir -p "partitioncloud/partitions"
    mkdir -p "partitioncloud/static/thumbnails"
    if [ ! -x instance/partitioncloud.sqlite ]; then
        printf "Souhaitez vous supprimer la base de données existante ? [y/n] "
        read -r CONFIRMATION
    fi
    [[ $CONFIRMATION == y ]] || exit 1
    sqlite3 "instance/partitioncloud.sqlite" '.read partitioncloud/schema.sql'
    echo "Base de données initialisée"
}

start () {
    flask run
}


usage () {
    echo "Usage:"
    echo -e "\t$0 init"
    echo -e "\t$0 start"
}

if [[ $1 && $(type "$1") = *"is a"*"function"* || $(type "$1") == *"est une fonction"* ]]; then
	$1 ${*:2} # Call the function
else
	usage
	echo $(type "$1")
	exit 1
fi

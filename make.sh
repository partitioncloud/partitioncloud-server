#!/bin/bash

init () {
    if [ ! -x partitioncloud/partitioncloud.db ]; then
        printf "Souhaitez vous supprimer la base de données existante ? [y/n] "
        read -r CONFIRMATION
    fi
    [[ $CONFIRMATION == y ]] || exit 1
    sqlite3 "partitioncloud/partitioncloud.db" '.read partitioncloud/schema.sql'
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
fi;

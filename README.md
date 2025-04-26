# partitioncloud-server

Serveur web (basé sur Flask) pour gérer sa collection de partitions musicales

## Features

### Liste non exhaustive
- recherche de partitions en ligne et ajout à la base de données (par recherche Google)
- partage d'un album par un lien direct sans nécessité de connexion (en lecture seule)
- Thème sombre
- dashboard administrateur: gestion de tous les albums, partitions et utilisateurs
- [CLI](https://github.com/partitioncloud/partitioncloud-cli) uniquement à des fins de synchronisation. Il serait bon d'ajouter une BDD locale avec les UUIDs des partitions
- ~~Pas de Javascript~~ Complètement fonctionnel sans JavaScript, cela vient juste ajouter des [toutes petites améliorations](partitioncloud/static/scripts)

## Points à noter
- Les partitions ajoutées sont accessibles à tous les utilisateurs depuis la recherche même si ils ne sont pas dans un album leur y donnant accès, pour limiter la redondance
- Il est possible d'entrer des paroles en créant une partition, celles-ci sont utilisées uniquement pour la fonctionalité de recherche pour le moment
- Les résultats de la recherche web sont téléchargés automatiquement pour en générer un aperçu, donc `MAX_ONLINE_QUERIES` doit rester raisonnable
- Le fichier de configuration est un script lu par python *et* bash, il ne faut donc pas écrire `CONFIG_PARAM = 2` mais `CONFIG_PARAM=2` (pour bash)

## Installation

### Installation via Docker (recommandé)

```bash
# Clone this repo
git clone https://github.com/partitioncloud/partitioncloud-server.git
cd partitioncloud-server
# Create an image named "partitioncloud"
docker build -t partitioncloud .
# You can then run the container, replace $PORT with the port you want to be exposed
PORT=5000
docker run -d \
    -p $PORT:5000 \
    --restart=unless-stopped \
    --name partitioncloud \
    partitioncloud:latest
```
L'utilisateur par défaut est `root` avec le mot de passe `root`

### Installation manuelle

Installer le serveur
```bash
# Clone this repo
git clone https://github.com/partitioncloud/partitioncloud-server.git
cd partitioncloud-server
# Install dependencies
pip install -r requirements.txt
pybabel compile -d partitioncloud/translations
# Create database and folders
./make.sh init
```

Démarrer le serveur
```bash
./make.sh start
```

Pour démarrer sur un environnement complet (plus que pour du dev/test),  
Installer [`gunicorn`](https://github.com/benoitc/gunicorn) puis:
```bash
./make.sh prod
```

## Configuration

```bash
cp default_config.py instance/config.py
```
Modifier le fichier de configuration créé dans `instance/`

## Screenshots

### Interface principale
![Interface principale](https://github.com/user-attachments/assets/e4be140a-1e4a-448c-83db-8380966ed608)
![Mode sombre](https://github.com/user-attachments/assets/78a72a48-bd52-4aee-bda1-9d8c8fcc9cfc)


### Tableau administrateur
![Admin dashboard](https://github.com/user-attachments/assets/80af24c6-58e8-4c13-9226-44fe0514f1ee)


### Recherche en ligne et locale

![Recherche](https://github.com/user-attachments/assets/dc1a0cda-47eb-49c4-b2d2-921d0e10ed52)


## Translations

### Créer une nouvelle traduction

```bash
# Extraire les données
pybabel extract -F babel.cfg -k _l -o partitioncloud/translations/messages.pot .
# Créer un nouveau fichier
pybabel init -i partitioncloud/translations/messages.pot -d partitioncloud/translations/ -l $COUNTRY_CODE
# Modifier translations/$COUNTRY_CODE/LC_MESSAGES/messages.po
# Ajouter $COUNTRY_CODE dans default_config.py: LANGUAGES
# Compiler les nouvelles translations avant de démarrer le serveur
pybabel compile -d partitioncloud/translations/
```

### Mettre à jour une traduction

```bash
# Récupérer les données les plus récentes
pybabel extract -F babel.cfg -k _l -o partitioncloud/translations/messages.pot .
# Les ajouter aux traductions
pybabel update -i partitioncloud/translations/messages.pot -d partitioncloud/translations/
```

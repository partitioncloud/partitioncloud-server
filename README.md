# partitioncloud-server

Serveur web (basé sur Flask) pour gérer sa collection de partitions musicales

## Features

### Liste non exhaustive
- recherche de partitions en ligne et ajout à la base de données (par recherche Google)
- partage d'un album par un lien direct sans nécessité de connexion (en lecture seule)
- Thème sombre (je ne suis pas satisfait du résultat, mais il est à peu près correct)
- dashboard administrateur: gestion de tous les albums, partitions et utilisateurs
- [CLI](https://github.com/partitioncloud/partitioncloud-cli) uniquement à des fins de synchronisation. Il serait bon d'ajouter une BDD locale avec les UUIDs des partitions
- ~~Pas de Javascript~~ Complètement fonctionnel sans JavaScript, cela vient juste ajouter des [toutes petites améliorations](partitioncloud/static/main.js)

## Points à noter
- Les partitions ajoutées sont accessibles à tous les utilisateurs depuis la recherche même si ils ne sont pas dans un album leur y donnant accès, pour limiter la redondance
- Il est possible d'entrer des paroles en créant une partition, celles-ci sont utilisées uniquement pour la fonctionalité de recherche pour le moment
- Les résultats de la recherche web sont téléchargés automatiquement pour en générer un aperçu, donc `MAX_ONLINE_QUERIES` doit rester raisonnable
- Le fichier de configuration est un script lu par python *et* bash, il ne faut donc pas écrire `CONFIG_PARAM = 2` mais `CONFIG_PARAM=2` (pour bash)

## Installation

Installer le serveur
```bash
# Clone this repo
git clone https://github.com/partitioncloud/partitioncloud-server.git
cd partitioncloud-server
# Install dependencies
pip install -r requirements.txt
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
![Interface principale](https://user-images.githubusercontent.com/67148092/222953263-f779fdc8-b92d-479d-a7d1-1a71ca519a29.png)
![Mode sombre](https://user-images.githubusercontent.com/67148092/222953282-622a3c0b-bdcd-495a-880c-5b12d0f8921c.png)

### Tableau administrateur
![Admin dashboard](https://user-images.githubusercontent.com/67148092/222953310-6f1b1705-8e8f-4e93-b5e3-352f7225af46.png)
![add-user](https://user-images.githubusercontent.com/67148092/222953312-9dd12cc5-c416-4666-a00f-9d429afc13d6.png)

### Recherche en ligne et locale

_Les noms des sites webs ont volontairement été supprimés_
![Recherche](https://user-images.githubusercontent.com/67148092/222953333-db0633d7-3dd4-4405-8d87-8411db630724.png)


## TODO
- [ ] Modifier son mot de passe
- [ ] Supprimer un utilisateur
- [ ] Ajouter config:DISABLE_DARK_MODE
- [ ] Ajouter config:DISABLE_REGISTER
- [ ] Ajouter config:ONLINE_SEARCH_BASE_QUERY pour la recherche google, actuellement 'filetype:pdf partition'

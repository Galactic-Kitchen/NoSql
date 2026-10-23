# Leaderboard

Projet NoSql

## Fonctionnalités

- Créer des joueurs et des jeux individuels ou en équipe.
- Enregistrer les scores individuels ou un score d'équipe.
- Relier deux matchs adverses.
- Consulter les matchs récents et les détails d'un match.

## Prérequis

- Docker Compose
- Linux

## Démarrer le projet

Le fichier `.env` est volontairement inclus dans le dépôt. Il s'agit de la configuration locale de démonstration, identique à `.env.example`, afin qu'un clonage puisse être suivi directement du démarrage, sans copie ou configuration préalable.

Depuis la racine du dépôt :

```sh
docker compose up
```

Compose construit l'image de l'application si nécessaire et démarre PostgreSQL, Redis et Flask. Ouvre ensuite [http://localhost:8000](http://localhost:8000). L'application crée les tables PostgreSQL au démarrage.

Pour arrêter les conteneurs tout en conservant les données :

```sh
docker compose down
```

Pour supprimer également les données persistées dans les volumes PostgreSQL et Redis :

```sh
docker compose down --volumes
```

## Configuration

`docker-compose.yml` lit les variables suivantes depuis `.env` :

| Variable | Rôle |
| --- | --- |
| `POSTGRES_USER` | Compte d’administration PostgreSQL, utilisé uniquement pendant l’initialisation |
| `POSTGRES_PASSWORD` | Mot de passe du compte d’administration PostgreSQL |
| `APP_DB_USER` | Compte PostgreSQL à privilèges limités utilisé par l’application |
| `APP_DB_PASSWORD` | Mot de passe du compte PostgreSQL de l’application |
| `FLASK_SECRET_KEY` | Clé utilisée par Flask pour signer les sessions |

Les valeurs fournies sont publiques et réservées au développement local; elles ne doivent pas être réutilisées en production. Le nom de la base est fixé à `leaderboard` dans Compose. Le compte applicatif ne peut pas créer de tables ni administrer PostgreSQL. La clé Flask est transmise au conteneur et reste identique entre ses redémarrages. Elle signe également les jetons CSRF : si elle est modifiée entre les démarrages, les sessions ouvertes seront invalidées.

Compose configure également l'application avec `FLASK_POSTGRE_USER` et `FLASK_POSTGRE_PASSWORD`.

## Stockage

- **PostgreSQL** : joueurs, jeux, matchs, scores individuels et scores d'équipe.
- **Redis** : nombre de matchs par jeu et identifiants des matchs récents. Redis est configuré avec AOF (`appendonly yes`).
- **Volumes Docker** : les données restent disponibles après `docker compose down` et sont supprimées avec `docker compose down --volumes`.

Les services de base de données sont sur un réseau interne Compose et ne publient pas leurs ports sur l'hôte. Seule l'application publie le port `8000`.

## Se connecter aux bases

Avec les conteneurs démarrés, ouvre un client PostgreSQL interactif :

```sh
docker compose exec postgre sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Pour ouvrir le client Redis :

```sh
docker compose exec redis redis-cli
```

## Périmètre et limites

Ce dépôt est un projet de démonstration centré sur l'utilisation combinée de PostgreSQL et Redis pour gérer un classement. Certains éléments de production sont volontairement hors périmètre :

- **Pas d'authentification ni de gestion des comptes** : l'application est destinée à être utilisée localement dans un contexte de démonstration.
- **Pas de mot de passe Redis** : Redis n'est accessible que depuis le réseau interne Docker Compose; cette configuration ne convient pas à une instance exposée à un réseau non fiable.
- **Pas de suite de tests automatisés** : les tests ne font pas partie du périmètre actuel du projet.
- **Pas de TLS, de limitation de débit ou de stratégie de sauvegarde applicative** : Ces choix sont gérés en dehors du dépôt

Ces choix délimitent le sujet du projet et ne constituent pas des recommandations pour une application exposée à Internet.

## Structure

```text
.
├── app/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   └── src/leaderboard/
├── redis/redis.conf
├── docker-compose.yml
├── .env
├── .env.example
└── README.md
```

# \# TP4 — API Iris et compteur Redis

# 

# \*\*Réalisé par : Aya Kmaiti\*\*  

# \*\*Filière et groupe : 3A DS AI\*\*  

# \*\*Module : Cloud Computing et Déploiement IA\*\*  

# \*\*Année universitaire : 2026–2027\*\*

# 

# \## Table des matières

# 

# 1\. \[Objectif du TP](#objectif-du-tp)

# 2\. \[Préparation du projet](#1-préparation-du-projet)

# 3\. \[Ajout de Redis à l’API](#2-ajout-de-redis-à-lapi)

# 4\. \[Configuration de Docker Compose](#3-configuration-de-docker-compose)

# 5\. \[Démarrage des services](#4-démarrage-des-services)

# 6\. \[Vérification du compteur initial](#5-vérification-du-compteur-initial)

# 7\. \[Envoi de cinq prédictions](#6-envoi-de-cinq-prédictions)

# 8\. \[Tests de persistance](#7-tests-de-persistance)

# 9\. \[Bilan des résultats](#bilan-des-résultats)

# 10\. \[Conclusion](#conclusion)

# 

# \## Objectif du TP

# 

# Ce travail pratique reprend l’API de classification des fleurs Iris du

# TP précédent pour lui ajouter une mémoire avec Redis.

# 

# L’API réalise les prédictions avec le modèle Random Forest, tandis que

# Redis conserve le nombre de fleurs prédites. Les tests permettent de

# vérifier l’incrémentation du compteur et sa persistance après la

# suppression et la recréation des conteneurs.

# 

# \## 1 Préparation du projet

# 

# Nous repartons du projet Iris existant, qui contient les scripts Python,

# les dépendances et les Dockerfiles d’entraînement et d’inférence.

# 

# Nous vérifions la présence du volume contenant le modèle déjà entraîné :

# 

# ```powershell

# docker volume ls

# ```

# 

# Le volume utilisé est :

# 

# ```text

# iris-docker\_iris-model

# ```

# 

# Il est monté en lecture seule dans le conteneur de l’API.

# 

# Nous ajoutons ensuite le client Python Redis dans `requirements.txt` :

# 

# ```text

# redis==5.2.1

# ```

# 

# Cette dépendance permet à l’API de communiquer avec le serveur Redis.

# 

# \## 2 Ajout de Redis à l’API

# 

# Nous modifions le fichier `src/serve.py`.

# 

# Le modèle Iris reste chargé depuis le fichier :

# 

# ```text

# /models/iris.joblib

# ```

# 

# Nous ajoutons un client Redis :

# 

# ```python

# database = redis.Redis(

# &#x20;   host=os.environ.get("REDIS\_HOST", "base"),

# &#x20;   port=6379,

# &#x20;   decode\_responses=True,

# &#x20;   socket\_connect\_timeout=3,

# &#x20;   socket\_timeout=3,

# )

# ```

# 

# La variable `REDIS\_HOST` désigne le service Redis. Sa valeur par défaut,

# `base`, correspond au nom du service dans Docker Compose.

# 

# Le compteur est enregistré sous la clé :

# 

# ```python

# COUNTER\_KEY = "iris:predictions"

# ```

# 

# \### Fonctionnement des routes

# 

# | Route | Méthode | Fonction |

# |---|---|---|

# | `/health` | GET | Vérifier la disponibilité de Redis depuis l’API |

# | `/predict` | POST | Prédire la classe et incrémenter le compteur |

# | `/stats` | GET | Lire le nombre total de fleurs prédites |

# 

# La route `/stats` lit la valeur enregistrée dans Redis :

# 

# ```python

# total = int(database.get(COUNTER\_KEY) or 0)

# ```

# 

# Si la clé n’existe pas, le compteur vaut zéro.

# 

# Après une prédiction réussie, le compteur est incrémenté selon le nombre

# de fleurs prédites :

# 

# ```python

# total = database.incrby(COUNTER\_KEY, len(predictions))

# ```

# 

# \## 3 Configuration de Docker Compose

# 

# Nous définissons deux services dans le fichier `docker-compose.yml` :

# 

# \- `api` : exécute l’API de classification Iris.

# \- `base` : exécute Redis et conserve le compteur.

# 

# ```yaml

# services:

# &#x20; api:

# &#x20;   build:

# &#x20;     context: .

# &#x20;     dockerfile: Dockerfile.serve.opt

# &#x20;   image: iris-api:redis

# &#x20;   ports:

# &#x20;     - "8000:8000"

# &#x20;   environment:

# &#x20;     MODEL\_PATH: /models/iris.joblib

# &#x20;     REDIS\_HOST: base

# &#x20;   volumes:

# &#x20;     - modele:/models:ro

# &#x20;   depends\_on:

# &#x20;     base:

# &#x20;       condition: service\_healthy

# 

# &#x20; base:

# &#x20;   image: redis:7.4-alpine

# &#x20;   command: \["redis-server", "--appendonly", "yes"]

# &#x20;   volumes:

# &#x20;     - redis-data:/data

# &#x20;   healthcheck:

# &#x20;     test: \["CMD", "redis-cli", "ping"]

# &#x20;     interval: 5s

# &#x20;     timeout: 3s

# &#x20;     retries: 10

# 

# volumes:

# &#x20; modele:

# &#x20;   external: true

# &#x20;   name: iris-docker\_iris-model

# 

# &#x20; redis-data:

# ```

# 

# \### Organisation des volumes

# 

# | Volume | Utilisation |

# |---|---|

# | `modele` | Contient le modèle entraîné du TP précédent |

# | `redis-data` | Stocke les données persistantes de Redis |

# 

# Le volume du modèle est déclaré externe. Son cycle de vie est donc

# indépendant de celui de cette application Compose.

# 

# Redis écrit ses données dans `/data`. L’option `--appendonly yes`

# active la persistance AOF, qui journalise les opérations modifiant

# les données.

# 

# La condition `service\_healthy` attend que Redis réponde à

# `redis-cli ping` avant de démarrer l’API.

# 

# \### Vérification de la configuration

# 

# ```powershell

# docker compose config

# docker compose config --services

# ```

# 

# La liste des services obtenue contient :

# 

# ```text

# base

# api

# ```

# 

# \## 4 Démarrage des services

# 

# Nous démarrons l’application avec :

# 

# ```powershell

# docker compose up --build

# ```

# 

# Les journaux montrent la construction de l’image de l’API,

# la récupération de l’image Redis et la création des ressources

# nécessaires.

# 

# Redis devient prêt à accepter les connexions. L’API annonce ensuite

# son démarrage sur le port `8000`.

# 

# Les appels périodiques à `/health` reçoivent une réponse HTTP `200`,

# ce qui confirme que le contrôle de santé répond correctement.

# 

# \## 5 Vérification du compteur initial

# 

# Depuis un second terminal PowerShell, nous consultons les services :

# 

# ```powershell

# docker compose ps

# ```

# 

# Nous interrogeons ensuite le compteur :

# 

# ```powershell

# Invoke-RestMethod http://localhost:8000/stats

# ```

# 

# Avant l’envoi des prédictions, le résultat observé est :

# 

# ```text

# predictions

# \-----------

# 0

# ```

# 

# Cette valeur constitue le point de départ du test d’incrémentation.

# 

# \## 6 Envoi de cinq prédictions

# 

# Nous envoyons cinq requêtes à `/predict`. Chaque requête contient

# les mesures d’une fleur :

# 

# ```powershell

# $body = '{"instances":\[\[5.1,3.5,1.4,0.2]]}'

# 

# 1..5 | ForEach-Object {

# &#x20;   Invoke-RestMethod `

# &#x20;       -Uri http://localhost:8000/predict `

# &#x20;       -Method Post `

# &#x20;       -ContentType "application/json" `

# &#x20;       -Body $body

# }

# ```

# 

# Les réponses observées sont :

# 

# ```text

# model          predictions total\_predictions

# \-----          ----------- -----------------

# random\_forest  {setosa}                     1

# random\_forest  {setosa}                     2

# random\_forest  {setosa}                     3

# random\_forest  {setosa}                     4

# random\_forest  {setosa}                     5

# ```

# 

# Les cinq requêtes retournent la classe `setosa`. Le champ

# `total\_predictions` augmente progressivement de 1 à 5.

# 

# Nous consultons de nouveau `/stats` :

# 

# ```powershell

# Invoke-RestMethod http://localhost:8000/stats

# ```

# 

# Résultat observé :

# 

# ```text

# predictions

# \-----------

# 5

# ```

# 

# La lecture confirme l’enregistrement du compteur dans Redis.

# 

# \## 7 Tests de persistance

# 

# \### Arrêt avec down puis redémarrage

# 

# Nous arrêtons les services :

# 

# ```powershell

# docker compose down

# ```

# 

# Nous les redémarrons en arrière-plan :

# 

# ```powershell

# docker compose up -d

# ```

# 

# Après le démarrage, nous consultons le compteur :

# 

# ```powershell

# Invoke-RestMethod http://localhost:8000/stats

# ```

# 

# Résultat observé :

# 

# ```text

# predictions

# \-----------

# 5

# ```

# 

# Le compteur conserve sa valeur. La commande `down` supprime les

# conteneurs et le réseau de l’application, mais conserve le volume

# nommé `redis-data`.

# 

# Redis retrouve donc ses données lors du redémarrage.

# 

# \### Arrêt avec down -v puis redémarrage

# 

# Nous recommençons avec :

# 

# ```powershell

# docker compose down -v

# docker compose up -d

# ```

# 

# Puis :

# 

# ```powershell

# Invoke-RestMethod http://localhost:8000/stats

# ```

# 

# Résultat observé :

# 

# ```text

# predictions

# \-----------

# 0

# ```

# 

# L’option `-v` supprime le volume `redis-data`. Au redémarrage,

# un nouveau volume vide est créé et le compteur revient à zéro.

# 

# Le volume du modèle reste conservé, car il est déclaré externe.

# 

# \## Bilan des résultats

# 

# | Test | Compteur observé | Interprétation |

# |---|---:|---|

# | Premier démarrage | 0 | Aucune prédiction enregistrée |

# | Cinq requêtes contenant chacune une fleur | 5 | Incrémentation du compteur |

# | `down`, puis `up -d` | 5 | Volume Redis conservé |

# | `down -v`, puis `up -d` | 0 | Volume Redis supprimé et recréé |

# 

# \## Conclusion

# 

# Ce TP montre comment associer une API de prédiction à Redis avec

# Docker Compose.

# 

# L’API réalise les prédictions et Redis conserve leur nombre.

# Les tests confirment que les données survivent à la recréation des

# conteneurs lorsque le volume est conservé. La suppression du volume

# avec `down -v` réinitialise le compteur.


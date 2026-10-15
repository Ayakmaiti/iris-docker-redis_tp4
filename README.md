# \# TP4 — API Iris avec Redis et Docker Compose

# 

# \*\*Réalisé par : Aya Kmaiti\*\*  

# \*\*Filière : 3A DS AI\*\*  

# \*\*Année universitaire : 2026–2027\*\*

# 

# \## Objectif

# 

# Ajouter une mémoire à une API de classification des fleurs Iris :

# l’API réalise les prédictions avec Random Forest et Redis conserve

# le nombre de fleurs prédites.

# 

# Le TP vérifie également la persistance du compteur après la suppression

# et la recréation des conteneurs.

# 

# \## Architecture

# 

# Deux services sont orchestrés avec Docker Compose :

# 

# | Service | Fonction |

# |---|---|

# | `api` | Charge le modèle Iris et expose les routes HTTP |

# | `base` | Exécute Redis et stocke le compteur |

# 

# L’API communique avec Redis à l’adresse `base:6379` sur le réseau

# interne de Docker Compose.

# 

# Deux volumes sont utilisés :

# 

# \- `modele` : modèle entraîné, monté en lecture seule et déclaré externe.

# \- `redis-data` : données Redis, avec la persistance AOF activée.

# 

# \## Prérequis

# 

# \- Docker Desktop démarré avec le moteur Linux.

# \- Docker Compose disponible.

# \- PowerShell pour exécuter les exemples ci-dessous.

# 

# Vérification :

# 

# ```powershell

# docker version

# docker compose version

# ```

# 

# \## Installation

# 

# ```powershell

# git clone https://github.com/Ayakmaiti/iris-docker-redis\_tp4.git

# cd iris-docker-redis\_tp4

# ```

# 

# \## Préparer le modèle Iris

# 

# Le modèle est stocké dans un volume Docker et n’est pas inclus dans Git.

# 

# Sur une nouvelle machine, construire l’image d’entraînement :

# 

# ```powershell

# docker build -f Dockerfile.train.opt -t iris-train:opt .

# ```

# 

# Créer le volume attendu par le fichier Compose :

# 

# ```powershell

# docker volume create iris-docker\_iris-model

# ```

# 

# Entraîner et enregistrer le modèle :

# 

# ```powershell

# docker run --rm -v iris-docker\_iris-model:/models iris-train:opt

# ```

# 

# Si ce volume contient déjà le modèle entraîné, cette préparation

# n’est pas nécessaire.

# 

# \## Vérifier et démarrer l’application

# 

# Vérifier le fichier Compose :

# 

# ```powershell

# docker compose config

# docker compose config --services

# ```

# 

# Les services attendus sont `api` et `base`.

# 

# Démarrer en affichant les journaux :

# 

# ```powershell

# docker compose up --build

# ```

# 

# Pour démarrer en arrière-plan :

# 

# ```powershell

# docker compose up --build -d

# ```

# 

# Consulter les services et les journaux :

# 

# ```powershell

# docker compose ps

# docker compose logs api base

# ```

# 

# \## Routes de l’API

# 

# | Méthode | Route | Description |

# |---|---|---|

# | GET | `/health` | Vérifie la disponibilité de l’API et de Redis |

# | POST | `/predict` | Prédit l’espèce et incrémente le compteur |

# | GET | `/stats` | Renvoie le total des fleurs prédites |

# 

# L’API est accessible à l’adresse `http://localhost:8000`.

# 

# \## Tester une prédiction

# 

# Les quatre mesures sont exprimées en centimètres :

# longueur du sépale, largeur du sépale, longueur du pétale

# et largeur du pétale.

# 

# ```powershell

# $body = '{"instances":\[\[5.1,3.5,1.4,0.2]]}'

# 

# Invoke-RestMethod `

# &#x20;   -Uri http://localhost:8000/predict `

# &#x20;   -Method Post `

# &#x20;   -ContentType "application/json" `

# &#x20;   -Body $body

# ```

# 

# Pour cet exemple, la classe attendue est `setosa`.

# 

# \## Envoyer cinq requêtes

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

# Lire le compteur :

# 

# ```powershell

# Invoke-RestMethod http://localhost:8000/stats

# ```

# 

# Avec une fleur par requête, le compteur augmente de cinq.

# Sa valeur finale dépend des requêtes déjà effectuées.

# 

# \## Tester la persistance

# 

# \### Arrêt sans suppression du volume

# 

# ```powershell

# docker compose down

# docker compose up -d

# ```

# 

# Après le démarrage :

# 

# ```powershell

# Invoke-RestMethod http://localhost:8000/stats

# ```

# 

# Le compteur conserve sa valeur grâce au volume `redis-data`

# et à la persistance AOF.

# 

# \### Arrêt avec suppression du volume

# 

# Cette commande supprime les données du compteur Redis :

# 

# ```powershell

# docker compose down -v

# docker compose up -d

# ```

# 

# Après le démarrage :

# 

# ```powershell

# Invoke-RestMethod http://localhost:8000/stats

# ```

# 

# Le compteur revient à zéro. Le volume du modèle reste conservé,

# car il est déclaré externe.

# 

# \## Résultats observés pendant le TP

# 

# | Test | Compteur observé | Explication |

# |---|---:|---|

# | Premier démarrage | 0 | Aucune prédiction enregistrée |

# | Cinq requêtes contenant chacune une fleur | 5 | Incrémentation du compteur |

# | `down`, puis `up -d` | 5 | Volume Redis conservé |

# | `down -v`, puis `up -d` | 0 | Volume Redis supprimé et recréé |

# 

# \## Compte rendu

# 

# Le rapport du TP est disponible dans

# \[docs/Rapport\_TP4\_Aya\_Kmaiti.pdf](docs/Rapport\_TP4\_Aya\_Kmaiti.pdf)

# après son ajout au dépôt.

# 

# \## Fichiers du TP précédent

# 

# Les Dockerfiles naïfs et optimisés, `benchmark.py`,

# `comparaison.csv` et les rapports Trivy correspondent au travail

# de conteneurisation et d’optimisation réalisé avant l’ajout de Redis.

# 

# Le fichier `compose-tp-precedent.yaml` conserve l’ancienne

# orchestration d’entraînement et d’inférence.

# 

# \## Arrêter l’application

# 

# ```powershell

# docker compose down

# ```


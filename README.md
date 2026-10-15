# TP Iris : entraînement, inférence et optimisation Docker

## 1. Préparation sous Windows
Installer et démarrer Docker Desktop avec des conteneurs Linux. Extraire le ZIP, ouvrir PowerShell dans le dossier iris-docker. Vérifier `docker version` et `docker compose version`. Python local sert seulement au benchmark : `py --version`.

Les quatre mesures d'entrée, en cm, sont : longueur du sépale, largeur du sépale, longueur du pétale, largeur du pétale. Le dataset Iris est inclus dans scikit-learn : aucun téléchargement de données.

## 2. Version naïve et volume
```powershell
docker build -f Dockerfile.train.naif -t iris-train:naif .
docker build -f Dockerfile.serve.naif -t iris-serve:naif .
docker volume create iris-model-naif
docker run --rm -v iris-model-naif:/models iris-train:naif
docker run --rm -p 8000:8000 -v iris-model-naif:/models:ro iris-serve:naif
```
Dans un second terminal :
```powershell
Invoke-RestMethod http://localhost:8000/health
$body = '{"instances":[[5.1,3.5,1.4,0.2]]}'
Invoke-RestMethod http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $body
```
Résultat attendu : `iris setosa` est nommé `setosa` dans la réponse. Ctrl+C arrête l'API. Le modèle persiste dans le volume.

## 3. Mesures chiffrées
Avant Compose et avant de créer de gros fichiers dans le projet :
```powershell
py benchmark.py
```
Le script mesure les quatre images et produit `comparaison.csv`, lisible dans Excel. Il exige Docker Buildx. Le build chaud est une reconstruction identique, sans modification du code. Le froid utilise `--no-cache --pull`; chaque variante a un builder isolé. La seconde image de chaque variante peut réutiliser l'image de base déjà téléchargée, mais pas les couches applicatives (no-cache). Le temps inclut téléchargement éventuel et export vers Docker. Ce n'est donc pas une mesure de réseau complètement froid. Pour un rapport, préciser CPU, RAM, architecture, Docker, connexion et date. Répéter trois fois et prendre la médiane si nécessaire.

| Image | Taille (MiB) | Build froid (s) | Build chaud (s) |
|---|---:|---:|---:|
| iris-train:naif | À mesurer | À mesurer | À mesurer |
| iris-train:opt | À mesurer | À mesurer | À mesurer |
| iris-serve:naif | À mesurer | À mesurer | À mesurer |
| iris-serve:opt | À mesurer | À mesurer | À mesurer |

Gain de taille (%) = 100 × (taille naïve − taille optimisée) / taille naïve. Ne pas présenter des valeurs estimées comme des résultats.

## 4. Pourquoi ces optimisations ?
- slim : moins de paquets système dans l'image.
- requirements copié avant le code : une modification Python préserve la couche des dépendances.
- .dockerignore : seul le code nécessaire entre dans le contexte. Les fichiers Dockerfile.*.naif.dockerignore désactivent intentionnellement ce filtrage pour la référence naïve.
- --no-cache-dir : pas de cache pip dans les couches.
- multi-étapes : seul l'environnement virtuel est transféré. Ici les dépendances sont des wheels : le multi-étapes ne garantit pas un gain supplémentaire par rapport à un bon build slim mono-étape.
- utilisateur app : API et entraînement optimisés ne tournent pas en root.
- healthcheck : vérifie que l'API répond sans installer curl.

Les dépendances sont épinglées pour assurer la compatibilité entre entraînement et inférence. Ces versions initiales ne sont pas certifiées sans vulnérabilités. Les tags Python restent mobiles : noter les digests dans le rapport, puis épingler un digest vérifié pour une reproduction stricte. Builder et runtime doivent employer la même base.

## 5. Docker Compose : entraîner puis servir
```powershell
docker compose up --build -d
docker compose logs train
docker compose ps -a
Invoke-RestMethod http://localhost:8000/health
$body = '{"instances":[[5.1,3.5,1.4,0.2],[6.7,3.0,5.2,2.3]]}'
Invoke-RestMethod http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $body
docker compose down
```
`service_completed_successfully` attend la réussite de l'entraînement. Celui-ci écrit iris.joblib et metrics.json dans le volume partagé. L'API monte le volume en lecture seule. Un entraînement avec exit code 0 et état Exited est normal. Une API en état healthy est attendue.
Pour refaire l'entraînement sans supprimer le modèle stocké : `docker compose down`, puis `docker compose up --build -d`. Ne pas utiliser `down -v` si tu veux garder les modèles.

## 6. Trivy : preuves avant/après
Installer Trivy depuis sa distribution officielle et vérifier `trivy --version`. Suivre les restrictions de versions de ton support. Scanner les images réellement construites :
```powershell
trivy image --scanners vuln --severity HIGH,CRITICAL --format json --output trivy-naif.json iris-serve:naif
trivy image --scanners vuln --severity HIGH,CRITICAL --format json --output trivy-opt-avant.json iris-serve:opt
$report = Get-Content trivy-naif.json -Raw | ConvertFrom-Json
$critical = foreach ($result in $report.Results) {
  foreach ($v in $result.Vulnerabilities) {
    if ($v.Severity -eq 'CRITICAL') {
      [PSCustomObject]@{CVE=$v.VulnerabilityID;Package=$v.PkgName;Installed=$v.InstalledVersion;Fixed=$v.FixedVersion;Target=$result.Target}
    }
  }
}
$critical | Format-Table -AutoSize
```
Choisir deux CVE CRITICAL distinctes avec un correctif disponible, réellement présentes dans le scan initial. Ne pas inventer de CVE et ne pas abaisser leur sévérité.

Corrections selon l'origine :
1. Paquet Debian : actualiser la base avec --pull; la version optimisée exécute déjà apt-get upgrade. Vérifier que la version corrigée est disponible dans la distribution. Si ce n'est pas le cas, choisir une base compatible maintenue contenant le correctif; aligner builder et runtime.
2. Bibliothèque Python : remplacer la version concernée dans requirements.txt par une version corrigée compatible, à partir de FixedVersion et de l'avis officiel. Réentraîner et reconstruire aussi l'API : scikit-learn/joblib doivent rester compatibles.
3. Paquet inutile présent seulement dans la base complète : son retrait avec slim peut supprimer la CVE de l'image finale. Documenter le retrait.

Après modifications :
```powershell
docker build --pull --no-cache -f Dockerfile.train.opt -t iris-train:opt .
docker build --pull --no-cache -f Dockerfile.serve.opt -t iris-serve:opt .
docker compose down
docker compose up -d
trivy image --scanners vuln --severity HIGH,CRITICAL --format json --output trivy-opt-apres.json iris-serve:opt
trivy image --scanners vuln --severity CRITICAL --exit-code 1 iris-serve:opt
trivy image --scanners vuln --severity CRITICAL --exit-code 1 iris-train:opt
```
Refaire le test /predict. Comparer les deux CVE choisies dans le JSON avant/après. Un scan `--ignore-unfixed` peut aider à prioriser, mais ne prouve pas l'absence de critiques non corrigées. Conserver des scans complets.

| CVE réellement détectée | Paquet | Version avant | Correction appliquée | Version après / paquet retiré | Absente après ? |
|---|---|---|---|---|---|
| À relever | À relever | À relever | À documenter | À relever | À vérifier |
| À relever | À relever | À relever | À documenter | À relever | À vérifier |

Si le scan initial contient moins de deux critiques, le signaler à l'enseignant avec le rapport : on ne peut pas prouver deux corrections critiques inexistantes. Ne pas dégrader volontairement l'image utilisée pour l'API.

## Limites de validation du projet fourni
Les fichiers Python sont vérifiés syntaxiquement. Docker et Trivy ne sont pas disponibles dans l'environnement de préparation : builds, prédictions en conteneur, performances et corrections CVE restent à valider sur ton PC. L'API HTTP standard est un prototype pédagogique, à usage local.

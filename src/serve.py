import json
import math
import os

import joblib
import redis

from http.server import BaseHTTPRequestHandler, HTTPServer


bundle = joblib.load(
    os.environ.get("MODEL_PATH", "/models/iris.joblib")
)

database = redis.Redis(
    host=os.environ.get("REDIS_HOST", "base"),
    port=6379,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)

COUNTER_KEY = "iris:predictions"


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload):
        body = json.dumps(payload).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            try:
                database.ping()
                self.reply(200, {"status": "ok"})
            except redis.RedisError:
                self.reply(503, {"error": "Redis indisponible"})
            return

        if self.path == "/stats":
            try:
                total = int(database.get(COUNTER_KEY) or 0)
                self.reply(200, {"predictions": total})
            except redis.RedisError:
                self.reply(503, {"error": "Redis indisponible"})
            return

        self.reply(404, {"error": "Route inconnue"})

    def do_POST(self):
        if self.path != "/predict":
            self.reply(404, {"error": "Route inconnue"})
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))

            if not 0 < size <= 65536:
                raise ValueError("Taille de requete invalide")

            payload = json.loads(self.rfile.read(size))
            rows = payload["instances"]

            if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
                raise ValueError("Envoyer entre 1 et 100 fleurs")

            for row in rows:
                if (
                    not isinstance(row, list)
                    or len(row) != 4
                    or any(
                        type(value) not in (int, float)
                        or not math.isfinite(value)
                        or value <= 0
                        for value in row
                    )
                ):
                    raise ValueError(
                        "Chaque fleur doit avoir 4 mesures positives"
                    )

            # Compatible avec les deux versions du projet :
            # modèle unique ou dictionnaire de modèles.
            name = payload.get("model", "random_forest")

            if "models" in bundle:
                if (
                    not isinstance(name, str)
                    or name not in bundle["models"]
                ):
                    raise ValueError("Modele inconnu")

                model = bundle["models"][name]
            else:
                if name != "random_forest":
                    raise ValueError(
                        "Cette version contient seulement Random Forest"
                    )

                model = bundle["model"]

            ids = model.predict(rows)

            predictions = [
                bundle["classes"][int(index)]
                for index in ids
            ]

        except (ValueError, KeyError, TypeError):
            self.reply(400, {"error": "Donnees ou modele invalides"})
            return

        try:
            total = database.incrby(COUNTER_KEY, len(predictions))
        except redis.RedisError:
            self.reply(503, {"error": "Redis indisponible"})
            return

        self.reply(
            200,
            {
                "model": name,
                "predictions": predictions,
                "total_predictions": total,
            },
        )


print("API Iris demarree sur le port 8000", flush=True)
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()

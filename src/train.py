import os, json, tempfile
from pathlib import Path
import joblib
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42, stratify=iris.target)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
out = Path(os.environ.get('MODEL_DIR', '/models'))
out.mkdir(parents=True, exist_ok=True)
bundle = {'model': model, 'classes': iris.target_names.tolist()}
with tempfile.NamedTemporaryFile(dir=out, delete=False) as f:
    tmp = f.name
joblib.dump(bundle, tmp)
os.replace(tmp, out / 'iris.joblib')
metrics = {'accuracy': accuracy_score(y_test, model.predict(X_test)), 'test_samples': len(y_test)}
(out / 'metrics.json').write_text(json.dumps(metrics, indent=2))
print(json.dumps(metrics), flush=True)

# HMM Sense OCC

## Projektüberblick

HMM Sense OCC ist eine Pipeline zur Abschätzung der Raumbelegung an der Hochschule München. Rohdaten aus der HM-Sense-API (CO2, Bewegung, Licht, Temperatur, Feuchtigkeit) werden zu Feature-Vektoren verarbeitet, mit einem Gaussian-HMM interpretiert und über FastAPI-Endpunkte bereitgestellt. Die Architektur trennt Feature-Erzeugung und Modellinferenz in zwei eigenständige Services, die sich per REST austauschen und in Docker oder Kubernetes betrieben werden können.

## Funktionen

- Automatisierter Abruf der HM-Sense-Daten inklusive Zeitfenster- und Formatparametern
- Feature-Engineering (Glättung, Fenstern, Normalisierung) mit Ausgabe als JSON Feature-Vektoren
- GaussianHMM-basierte Zustandsklassifikation mit Wahrscheinlichkeiten und Sensor-Snapshots
- FastAPI-Endpoints `/api/features` und `/api/predictions` samt Healthchecks
- Bereitgestellte Dockerfiles und Kubernetes-Manifeste (Deployments, Services, HPAs)

## Voraussetzungen

- Python 3.12 und `pip`
- Ein UNIX-kompatibles Terminal (getestet auf macOS/Linux)
- Optional: Docker 24+ zum Container-Build sowie `kubectl` + Kubernetes-Cluster für Deployments

## Installation

1. Repository beziehen und wechseln:
	```bash
	git clone <REPO_URL>
	cd hm-sense-pipeline
	```
2. Virtuelle Umgebung anlegen und aktivieren:
	```bash
	python -m venv .venv
	source .venv/bin/activate  # Windows: .venv\Scripts\activate
	```
3. Abhängigkeiten installieren:
	```bash
	pip install -r services/feature_producer/requirements.txt
	pip install -r services/model_consumer/requirements.txt
	```

## Konfiguration

1. [.env.example](.env.example) nach `.env` kopieren.
2. Die Werte mit dem Präfix `FEATURE_PRODUCER_` anpassen (API-URL, Zeitfenster, interne Service-URL, Timeouts).
3. Beide Services laden die Einstellungen zentral über [services/settings.py](services/settings.py); in Docker/Kubernetes werden dieselben Variablen als Environment bereitgestellt (z. B. via ConfigMap oder Secret).

## Nutzung

### Feature-Producer starten
```bash
uvicorn services.feature_producer.app:app --reload
```
Standard-Endpunkte:
- http://localhost:8000/health
- http://localhost:8000/api/features

### Model-Consumer starten
```bash
python -m uvicorn services.model_consumer.app:app --host 0.0.0.0 --port 8002
```
Standard-Endpunkte:
- http://localhost:8002/health
- http://localhost:8002/api/predictions

Der Model-Consumer verwendet `FEATURE_PRODUCER_FEATURE_ENDPOINT_BASE_URL`, um den Feature-Producer zu erreichen. Für Docker- oder Kubernetes-Setups muss hier die interne Service-URL (z. B. `http://feature-producer:8000/api`) gesetzt werden.

### Container-Build (optional)
```bash
docker build -f services/feature_producer/Dockerfile -t feature-producer .
docker build -f services/model_consumer/Dockerfile -t model-consumer .
```

### Kubernetes-Deployment (optional)
1. Container-Images pushen und Tags in `deploy/k8s/*.yaml` eintragen.
2. Ressourcen anwenden:
	```bash
	kubectl apply -f deploy/k8s/namespace.yaml
	kubectl apply -f deploy/k8s/configmap.yaml
	kubectl apply -f deploy/k8s/feature-producer-deployment.yaml
	kubectl apply -f deploy/k8s/model-consumer-deployment.yaml
	```
3. Die bereitgestellten Services und HorizontalPodAutoscaler ermöglichen eine skalierbare Ausführung auf dem Cluster.

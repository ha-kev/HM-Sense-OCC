# Projekt Big Data

## Forschungsfrage & Zieldefinition

### Was ist das Ziel ?
Erkennung von Raumbelegung anhand bestimmter Sensormesswerte

### Ziel ?
- Prognose der prozentualen Raumbelegung mit Hilfe von ML, analytish
- Wahrscheinlichkeiten der Raumbelegung
- Visualisierung der zusammenspielenden Messwerte -> Präsentation
- API Endpoint / Vollwertige Dashboard als Service anbieten

### Erfolgskriterium ?
- Minimum ob Raum belegt oder nicht (Vorlesung, minimal belegt, freier Raum)
- Echtzeit Kapabilität (alle 5 Minuten)
- Nutzung der Studenten für Raumsuche

## Recherche & Konzepte

### Bestehende Lösung
- https://doi.org/10.1016/j.enbuild.2015.11.071
- https://www.researchgate.net/publication/391306996_Indoor_Occupancy_Detection_Using_Machine_Learning_and_Environmental_Sensors

- Standard ML Ansätzen wurden in Paperes genutzt (Logistic Regression, Random Forest, Decision Tree, KNN, SVM, GBM, CART, LDA)

Bestehende Lösungen haben nur einen supervised Ansatz keinen supervised -> Mehrwert = unsupervised

## Datenquellen & Exploration

### HM-Sense API
https://hm-sense-open-data-api.kube.cs.hm.edu/

### Exploration
-> Siehe eda_sensor.ipynb
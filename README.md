# 🚗 PrediAuto - Estimation IA de Véhicules

**PrediAuto** est une application web intelligente permettant d'estimer la valeur actuelle et future (dépréciation à 2 ans) des véhicules d'occasion. 

Le projet se distingue par une architecture à **double modèle d'Intelligence Artificielle** (Random Forest) pour traiter séparément et avec haute précision les véhicules à énergie fossile (Thermique/Hybride) et les véhicules 100% électriques.

---

## ✨ Fonctionnalités Principales
* **Double Cerveau IA :** Un modèle entraîné pour la mécanique (Thermique) et un autre spécialisé sur les batteries (Électrique).
* **Data Augmentation :** Génération de données synthétiques pour pallier le manque d'historique sur le marché électrique.
* **Imputation Intelligente :** L'utilisateur peut laisser des champs vides (Kilométrage, Capacité batterie...), l'IA devinera les valeurs les plus probables selon la médiane du marché.
* **Interface Dynamique :** Formulaire qui s'adapte en temps réel selon le type d'énergie choisi.

---

## 🛠️ Architecture Technique


[Image of client server architecture]

* **Frontend :** HTML5, CSS3 (Variables natives, Grid/Flexbox), JavaScript Vanilla.
* **Backend :** Python 3, Flask (API REST), Flask-CORS.
* **Machine Learning :** Scikit-Learn (Pipelines, RandomForestRegressor, OneHotEncoder), Pandas, NumPy.

---

## ⚙️ Installation & Prérequis

Assurez-vous d'avoir **Python 3.8+** installé sur votre machine.

### 1. Cloner le projet
Ouvrez votre terminal et placez-vous dans le dossier du projet.

### 2. Créer un environnement virtuel (Recommandé)
```bash
python -m venv env
# Sur Mac/Linux :
source env/bin/activate
# Sur Windows :
env\Scripts\activate
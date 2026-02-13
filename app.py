from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error

app = Flask(__name__)
CORS(app)

# --- STOCKAGE GLOBAL ---
models_cache = {
    "fossil": {"model": None, "df": None, "features": None, "scores": {}},
    "electric": {"model": None, "df": None, "features": None, "scores": {}}
}

# --- 1. NETTOYAGE & OPTIMISATION ---
def nettoyer_donnees(df):
    # --- CORRECTION DU BUG ---
    # On supprime les colonnes strictement identiques (doublons) dès le chargement
    df = df.loc[:, ~df.columns.duplicated()]

    # Standardisation Colonnes
    col_map = {
        "price": "Prix", "Price": "Prix",
        "kilométragecompteur": "km", "kilométrage": "km",
        "premièremain(déclaratif)": "premièremain",
        "autonomiebatterie": "autonomie",
        "capacitébatterie": "capacite"
    }
    df.rename(columns=col_map, inplace=True)
    
    # On resupprime les doublons au cas où le renommage en a créé (ex: 'price' et 'Prix' existaient tous les deux)
    df = df.loc[:, ~df.columns.duplicated()]

    for col in df.columns:
        # On vérifie que la colonne n'est pas vide avant de travailler
        if df[col].empty:
            continue

        if df[col].dtype == 'object':
            # Nettoyage texte
            df[col] = df[col].astype(str).str.strip().str.replace(r'\n', '', regex=True).str.replace('"', '').str.replace("'", "")
            
            # Nettoyage Département (ex: "75001" -> "75")
            if col == "departement":
                df[col] = df[col].astype(str).str[:2]
            
            # Optimisation Modèles (Troncature pour vitesse)
            if col == "carmodel":
                df[col] = df[col].str[:25].str.strip().str.upper()

            # Nettoyage Première Main (Oui/Non)
            if col == "premièremain":
                df[col] = df[col].str.lower().replace({'oui': 'oui', 'non': 'non', 'nan': 'non'})

    return df

def get_smart_value(df, target_col, criteria):
    """Cherche la valeur médiane/mode intelligente"""
    subset = df.copy()
    for col, val in criteria.items():
        if col in subset.columns:
            if subset[col].dtype == 'object':
                val_str = str(val).upper().strip()[:25]
                subset = subset[subset[col].astype(str).str.contains(val_str, regex=False, na=False)]
            else:
                subset = subset[subset[col] == val]
    
    if subset.empty or subset[target_col].isna().all(): return None
    
    if pd.api.types.is_numeric_dtype(subset[target_col]):
        return subset[target_col].median()
    else:
        mode = subset[target_col].mode()
        return mode.iloc[0] if not mode.empty else None

def entrainer_modele(csv_path, type_modele):
    print(f"\n🚀 Entraînement modèle {type_modele.upper()} ({csv_path})...")
    try:
        # Lecture flexible (virgule ou point-virgule)
        df = pd.read_csv(csv_path, sep=None, engine='python', skipinitialspace=True)
        df = nettoyer_donnees(df)
    except FileNotFoundError:
        print(f"❌ Erreur : {csv_path} introuvable.")
        return False

    if "Prix" not in df.columns:
        print(f"❌ Erreur : Colonne 'Prix' introuvable dans {csv_path}.")
        return False

    # --- SÉLECTION DES FEATURES ÉTENDUES ---
    # 1. Numériques (Communes + Spécifiques)
    num_features = ["year", "km", "puissancefiscale", "puissancedin", "nombredeportes", "nombredeplaces"]
    
    if type_modele == "fossil":
        num_features += ["émissionsdeco2", "consommationmixte", "crit'air"]
    elif type_modele == "electric":
        num_features += ["autonomie", "capacite"]
        if "crit'air" in df.columns: num_features.append("crit'air")

    # On ne garde que ce qui existe vraiment dans le CSV
    num_features = [c for c in num_features if c in df.columns]

    # 2. Catégorielles
    cat_features = ["brand", "carmodel", "gearbox", "fuel", "departement", "premièremain"]
    cat_features = [c for c in cat_features if c in df.columns]

    print(f"   ℹ️ Features utilisées : {len(num_features)} num + {len(cat_features)} cat")

    # Préparation X, y
    X = df[num_features + cat_features]
    y = df["Prix"]

    # Suppression des lignes où le prix est vide ou aberrant
    mask = (y.notna()) & (y > 500)
    X = X[mask]
    y = y[mask]

    # Split Train/Test pour calculer le score
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Pipeline
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False, max_categories=50))
    ])
    
    preprocessor = ColumnTransformer(transformers=[
        ("num", numeric_transformer, num_features),
        ("cat", categorical_transformer, cat_features)
    ])

    model = Pipeline(steps=[
        ("preprocessing", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42))
    ])

    # Entraînement sur Log(Prix) pour précision
    y_train_log = np.log1p(y_train)
    model.fit(X_train, y_train_log)

    # --- CALCUL DU SCORE D'EFFICACITÉ ---
    y_pred_log = model.predict(X_test)
    y_pred = np.expm1(y_pred_log) # Retour en Euros
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"   ✅ Modèle Entraîné !")
    print(f"   📊 SCORE R² (Précision) : {r2:.2%} (Plus c'est proche de 100%, mieux c'est)")
    print(f"   💶 ERREUR MOYENNE (MAE) : {mae:.0f} €")

    models_cache[type_modele] = {
        "model": model, 
        "df": df, 
        "features": num_features + cat_features,
        "scores": {"r2": r2, "mae": mae}
    }
    return True

# --- ROUTE PREDICT ---
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    engine_type = data.get('engine_type', 'fossil')
    
    cache = models_cache.get(engine_type)
    if not cache or cache["model"] is None:
        return jsonify({"error": "Modèle non chargé"}), 500

    input_data = {}
    
    # --- 1. CHAMPS OBLIGATOIRES ---
    try:
        input_data['brand'] = data.get('brand')
        input_data['carmodel'] = str(data.get('carmodel'))[:25].upper()
        input_data['year'] = float(data.get('year'))
        input_data['fuel'] = data.get('fuel')
    except:
        return jsonify({"error": "Marque, Modèle, Année ou Carburant manquants."}), 400

    # --- 2. CHAMPS OPTIONNELS (Directs) ---
    # Si l'user remplit, on prend. Sinon None (et l'IA devinera)
    opt_cols = ['km', 'gearbox', 'departement', 'nombredeportes', 'nombredeplaces', 'puissancedin', 'puissancefiscale', 'premièremain']
    if engine_type == 'electric':
        opt_cols += ['autonomie', 'capacite']
    else:
        opt_cols += ["crit'air", "émissionsdeco2"]

    for col in opt_cols:
        val = data.get(col)
        if val and str(val).strip() != "":
            try:
                # Conversion numérique si besoin
                if col in ['km', 'autonomie', 'capacite', 'puissancedin', 'puissancefiscale', 'nombredeportes', 'nombredeplaces', "crit'air", "émissionsdeco2"]:
                    input_data[col] = float(val)
                else:
                    input_data[col] = str(val)
            except:
                input_data[col] = None # Erreur de saisie -> IA devinera
        else:
            input_data[col] = None

    # --- 3. INTELLIGENCE ARTIFICIELLE (Remplissage) ---
    df_orig = cache["df"]
    ia_guesses = {}

    for col in cache["features"]:
        if col in input_data and input_data[col] is not None:
            continue # Déjà rempli
            
        if col in ['brand', 'carmodel', 'year', 'fuel']: continue

        # Recherche
        found = get_smart_value(df_orig, col, {'brand': input_data['brand'], 'carmodel': input_data['carmodel'], 'year': input_data['year']})
        if found is None: found = get_smart_value(df_orig, col, {'brand': input_data['brand'], 'carmodel': input_data['carmodel']})
        if found is None: found = get_smart_value(df_orig, col, {'brand': input_data['brand']})
        
        # Valeurs par défaut ultimes
        if found is None:
            if col == 'km': found = 150000.0 if engine_type == 'fossil' else 80000.0
            elif col == 'gearbox': found = 'Manuelle' if engine_type == 'fossil' else 'Automatique'
            elif col == 'nombredeportes': found = 5.0
            elif col == 'nombredeplaces': found = 5.0
            elif col == 'puissancefiscale': found = 6.0
            elif col == 'puissancedin': found = 110.0
            elif col == 'departement': found = '75'
            elif col == 'premièremain': found = 'non'
            else: found = 0

        input_data[col] = found
        ia_guesses[col] = found

    # --- 4. PRÉDICTION ---
    try:
        df_new = pd.DataFrame([input_data])
        # Force le type str pour département
        if 'departement' in df_new.columns:
            df_new['departement'] = df_new['departement'].astype(str)

        prix_log = cache["model"].predict(df_new)[0]
        prix_final = np.expm1(prix_log)
        
        depreciation = 0.80 if engine_type == 'electric' else 0.85
        prix_futur = prix_final * depreciation

        return jsonify({
            "prix_estime": round(prix_final, 2),
            "prix_futur": round(prix_futur, 2),
            "details_ia": ia_guesses,
            "model_score": cache["scores"] # On renvoie le score au front
        })
    except Exception as e:
        print("Erreur prediction:", e)
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    # Chargement
    entrainer_modele("dataset_fossil.csv", "fossil")
    # Tente le boosté, sinon le normal
    if not entrainer_modele("dataset_electric_boosted.csv", "electric"):
        entrainer_modele("dataset_electric.csv", "electric")
        
    app.run(debug=True, port=5000)
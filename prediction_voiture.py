import pandas as pd
import numpy as np
import joblib
import datetime

# On importe le Random Forest
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
# On n'utilise plus PCA
from sklearn.metrics import mean_absolute_error, r2_score

# --- 1. FONCTIONS UTILES (NETTOYAGE & INTELLIGENCE) ---

def nettoyer_donnees(df):
    """
    Nettoie tout le dataset en profondeur dès le chargement.
    """
    for col in df.columns:
        if df[col].dtype == 'object':
            # 1. Force le texte, enlève les espaces et les retours à la ligne
            df[col] = df[col].astype(str).str.strip().str.replace(r'\n', '', regex=True).str.replace('"', '').str.replace("'", "")
            
            # Correction spécifique département
            if col == "departement":
                df[col] = df[col].str.replace(r'\.0$', '', regex=True)
    return df

def get_smart_value(df, target_col, criteria):
    subset = df.copy()
    for col, val in criteria.items():
        if col in subset.columns:
            if subset[col].dtype == 'object':
                subset = subset[subset[col].astype(str).str.upper() == str(val).upper()]
            else:
                subset = subset[subset[col] == val]
    
    if subset.empty or subset[target_col].isna().all():
        return None

    if pd.api.types.is_numeric_dtype(subset[target_col]):
        return subset[target_col].median()
    else:
        mode_values = subset[target_col].mode()
        if not mode_values.empty:
            return mode_values.iloc[0]
        return None

def verifier_existence(df, col, valeur, filtre_col=None, filtre_val=None):
    subset = df
    if filtre_col and filtre_val:
        subset = df[df[filtre_col].astype(str).str.upper() == str(filtre_val).upper()]
        
    if subset.empty:
        return None

    masque = subset[col].astype(str).str.upper() == str(valeur).strip().upper()
    if masque.any():
        return subset.loc[masque, col].iloc[0]
    return None

def afficher_options(df, col, filtre_col=None, filtre_val=None):
    subset = df
    if filtre_col and filtre_val:
        subset = df[df[filtre_col].astype(str).str.upper() == str(filtre_val).upper()]
    
    options = sorted(subset[col].dropna().astype(str).unique())
    print(f"\n👇 Voici la liste complète des options ({len(options)}) :")
    print(" | ".join(options))
    print("-" * 30)

# --- 2. ENTRAÎNEMENT (MODIFIÉ POUR RANDOM FOREST) ---

def entrainer_modele():
    print("Chargement et nettoyage des données...")
    try:
        # skipinitialspace=True aide pour les fichiers mal formatés
        df = pd.read_csv("dataset_fossil.csv", sep=None, engine='python', skipinitialspace=True)
        df = nettoyer_donnees(df)
        
    except FileNotFoundError:
        print("Erreur : Le fichier 'dataset_fossil.csv' est introuvable.")
        return None, None, None, None

    target = "Prix"
    
    num_features = [
        "year", "km", "puissancefiscale", "puissancedin", 
        "émissionsdeco2", "nombredeportes", "nombredeplaces", "garantie",
        "crit'air", "consommationmixte"
    ]
    
    cat_features = [
        "brand", "carmodel", "gearbox", "fuel", "couleurextérieure",
        "premièremain(déclaratif)", "contrôletechnique", "garantieconstructeur",
        "normeeuro", "vendeur", "departement"
    ]

    missing_cols = [c for c in num_features + cat_features + [target] if c not in df.columns]
    if missing_cols:
        print(f"Colonnes manquantes : {missing_cols}")
        return None, None, None, None

    X = df[num_features + cat_features]
    y = df[target]

    # Pipeline de transformation (On garde Scaling et OneHot)
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()) # Le Random Forest n'en a pas obligatoirement besoin, mais ça ne fait pas de mal
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, num_features),
            ("cat", categorical_transformer, cat_features)
        ]
    )

    # --- CHANGEMENT MAJEUR ICI ---
    # Remplacement de Ridge/PCA par Random Forest
    model = Pipeline(steps=[
        ("preprocessing", preprocessor),
        # Pas de PCA pour le Random Forest, il gère mieux les données brutes
        ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    print("Entraînement du modèle Random Forest en cours (cela peut prendre quelques secondes)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    score_r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"\n--- Résultats ---")
    print(f"✅ R² Score : {score_r2:.2f} (Objectif > 0.80)")
    print(f"💶 Erreur moyenne (MAE) : {mae:.0f} €")
    
    return model, num_features, cat_features, df

# --- 3. PRÉDICTION ---

def predire_prix_intelligent(model, df_original, num_features, cat_features):
    print("\n-------------------------------------------")
    print("--- 🚗 ESTIMATION INTELLIGENTE ---")
    print("-------------------------------------------")
    print("Astuce : Pour quitter le programme, faites Ctrl+C")
    
    input_data = {}
    
    # A. MARQUE
    while True:
        val = input("\nMarque (ex: RENAULT) * : ").strip()
        vraie_marque = verifier_existence(df_original, 'brand', val)
        if vraie_marque:
            input_data['brand'] = vraie_marque
            break
        print(f"❌ Marque inconnue.")
        afficher_options(df_original, 'brand')

    # B. MODÈLE
    while True:
        val = input(f"Modèle de {input_data['brand']} (ex: CLIO) * : ").strip()
        vrai_modele = verifier_existence(df_original, 'carmodel', val, filtre_col='brand', filtre_val=input_data['brand'])
        if vrai_modele:
            input_data['carmodel'] = vrai_modele
            break
        print(f"❌ Modèle inconnu chez {input_data['brand']}.")
        afficher_options(df_original, 'carmodel', 'brand', input_data['brand'])

    # C. ANNÉE
    current_year = datetime.datetime.now().year
    while True:
        val = input("Année (ex: 2008) * : ").strip()
        try:
            year_val = float(val)
            if 1950 <= year_val <= current_year + 1:
                input_data['year'] = year_val
                break
            else:
                print(f"❌ Année invalide (Doit être entre 1950 et {current_year}).")
        except ValueError:
            print("❌ Veuillez entrer un chiffre valide.")

    # D. CARBURANT
    while True:
        val = input("Carburant (ex: Diesel) * : ").strip()
        vrai_fuel = verifier_existence(df_original, 'fuel', val)
        if vrai_fuel:
            input_data['fuel'] = vrai_fuel
            break
        print(f"❌ Carburant inconnu.")
        afficher_options(df_original, 'fuel')

    # E. CRIT'AIR (Correction demandée)
    while True:
        val = input("Crit'Air (1, 2, 3, 4, 5) * : ").strip()
        try:
            float_val = float(val)
            if 1 <= float_val <= 5: 
                input_data["crit'air"] = float_val
                break
            else:
                print("⚠️ Pour les véhicules fossiles, Crit'Air est entre 1 et 5.")
                print("   (0 est réservé aux électriques).")
        except ValueError:
            print("❌ Chiffre attendu.")

    # --- INFOS TECHNIQUES ---
    smart_fields = {
        'km': "Kilométrage",
        'gearbox': "Boîte de vitesse",
        'puissancedin': "Puissance DIN (ch)",
        'puissancefiscale': "Puissance Fiscale (CV)"
    }
    
    print("\n--- Infos Techniques (Appuyez sur Entrée pour laisser le modèle deviner) ---")
    
    for field, label in smart_fields.items():
        val = input(f"{label} : ").strip()
        
        if val:
            try:
                if field in ['km', 'puissancedin', 'puissancefiscale']:
                    input_data[field] = float(val)
                else:
                    input_data[field] = val
            except ValueError:
                val = "" 

        if not val:
            found_val = get_smart_value(df_original, field, 
                                     {'brand': input_data['brand'], 
                                      'carmodel': input_data['carmodel'], 
                                      'year': input_data['year']})
            
            if found_val is None:
                found_val = get_smart_value(df_original, field, 
                                         {'brand': input_data['brand'], 
                                          'carmodel': input_data['carmodel']})

            if found_val is None:
                if field == 'gearbox': found_val = 'manuelle'
                elif field == 'km': found_val = 150000.0
                elif field == 'puissancedin': found_val = 90.0
                elif field == 'puissancefiscale': found_val = 5.0

            print(f"   🤖 {label} déduit(e) : {found_val}")
            input_data[field] = found_val

    # VALEURS PAR DÉFAUT
    defaults = {
        'émissionsdeco2': 120, 'nombredeportes': 5, 'nombredeplaces': 5,
        'garantie': 0, 'consommationmixte': 5.5, 'couleurextérieure': 'gris',
        'premièremain(déclaratif)': 'non', 'contrôletechnique': 'ok',
        'garantieconstructeur': 'non', 'normeeuro': 'EURO4', 'vendeur': 'Particulier',
        'departement': '75'
    }
    
    for col in num_features + cat_features:
        if col not in input_data:
            input_data[col] = defaults.get(col)

    # PRÉDICTION
    df_new = pd.DataFrame([input_data])
    df_new["departement"] = df_new["departement"].astype(str)

    try:
        prix = model.predict(df_new)[0]
        print(f"\n💰 PRIX ESTIMÉ : {prix:,.2f} €")
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    modele, nums, cats, df_complet = entrainer_modele()
    
    if modele:
        while True:
            reponse = input("\nNouvelle estimation ? (oui/non) : ")
            if reponse.lower() not in ['oui', 'o', 'y', 'yes']:
                break
            predire_prix_intelligent(modele, df_complet, nums, cats)
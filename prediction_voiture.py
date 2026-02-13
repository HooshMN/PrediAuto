import pandas as pd
import numpy as np
import joblib
import datetime

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

# ==========================================
# 1. FONCTIONS DE NETTOYAGE & INTELLIGENCE
# ==========================================

def nettoyer_donnees(df):
    """
    Nettoie le dataset en profondeur :
    - Enlève les espaces, retours à la ligne, guillemets.
    - Corrige les départements (.0).
    """
    # Renommage colonne Prix si nécessaire (gestion minuscules/majuscules)
    if "price" in df.columns:
        df.rename(columns={"price": "Prix"}, inplace=True)
        
    for col in df.columns:
        if df[col].dtype == 'object':
            # Nettoyage agressif
            df[col] = df[col].astype(str).str.strip().str.replace(r'\n', '', regex=True).str.replace('"', '').str.replace("'", "")
            
            # Correction spécifique département (75.0 -> 75)
            if col == "departement":
                df[col] = df[col].str.replace(r'\.0$', '', regex=True)
    return df

def get_smart_value(df, target_col, criteria):
    """
    Cherche la valeur la plus logique (Médiane ou Mode) en fonction de critères.
    Ex: Si on cherche la puissance d'une CLIO 2012, on prend la médiane des CLIO 2012.
    """
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
    """Vérifie si une valeur existe dans la base (Insensible à la casse)."""
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
    """Affiche les options disponibles pour aider l'utilisateur."""
    subset = df
    if filtre_col and filtre_val:
        subset = df[df[filtre_col].astype(str).str.upper() == str(filtre_val).upper()]
    
    options = sorted(subset[col].dropna().astype(str).unique())
    print(f"\n👇 Options disponibles ({len(options)}) :")
    # On affiche les 50 premiers pour ne pas inonder l'écran
    print(" | ".join(options[:50]))
    if len(options) > 50:
        print("... (liste tronquée)")
    print("-" * 30)

# ==========================================
# 2. ENTRAÎNEMENT OPTIMISÉ (LOG + RANDOM FOREST)
# ==========================================

def entrainer_modele():
    print("Chargement et nettoyage des données...")
    try:
        # skipinitialspace=True est crucial pour vos données
        df = pd.read_csv("dataset_fossil.csv", sep=None, engine='python', skipinitialspace=True)
        df = nettoyer_donnees(df)
        
    except FileNotFoundError:
        print("Erreur : Le fichier 'dataset_fossil.csv' est introuvable.")
        return None, None, None, None

    target = "Prix"
    if target not in df.columns:
        if "price" in df.columns: target = "price"
        else:
            print(f"Erreur : Colonne '{target}' introuvable. Colonnes : {df.columns.tolist()}")
            return None, None, None, None

    # On ne supprime PAS les outliers, on garde tout le dataset.
    print(f"📊 Données chargées : {len(df)} véhicules.")

    # Définition des colonnes
    num_features = ["year", "km", "puissancefiscale", "puissancedin", "crit'air"]
    # Ajout dynamique si elles existent
    possibles = ["émissionsdeco2", "nombredeportes", "nombredeplaces", "garantie", "consommationmixte"]
    num_features += [c for c in possibles if c in df.columns]

    cat_features = ["brand", "carmodel", "gearbox", "fuel", "departement"]
    possibles_cat = ["couleurextérieure", "premièremain(déclaratif)", "contrôletechnique", "garantieconstructeur", "normeeuro", "vendeur"]
    cat_features += [c for c in possibles_cat if c in df.columns]

    X = df[num_features + cat_features]
    y = df[target]

    # Pipeline de transformation
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()) 
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

    # MODELE : RANDOM FOREST BOOSTÉ
    model = Pipeline(steps=[
        ("preprocessing", preprocessor),
        ("regressor", RandomForestRegressor(
            n_estimators=500,       # 500 arbres pour la précision
            min_samples_leaf=1,     # Autorise les règles fines
            n_jobs=-1,              # Utilise toute la puissance CPU
            random_state=42
        ))
    ])

    print("Entraînement en cours avec Log-Transformation...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # --- ASTUCE PRO : LOG-TRANSFORMATION ---
    # On entraîne sur log(Prix). Cela réduit l'impact des très gros prix.
    # L'erreur est minimisée en POURCENTAGE et non en EUROS absolus.
    y_train_log = np.log1p(y_train)
    model.fit(X_train, y_train_log)

    # Évaluation (On convertit le résultat log en euros avec expm1)
    y_pred_log = model.predict(X_test)
    y_pred = np.expm1(y_pred_log) 

    score_r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    median_error = np.median(np.abs(y_test - y_pred)) # Erreur médiane (plus représentative)
    
    print(f"\n--- 🏆 RÉSULTATS ---")
    print(f"✅ R² Score : {score_r2:.2f}")
    print(f"📉 Erreur Moyenne (MAE) : {mae:.0f} €")
    print(f"🎯 Erreur Médiane : {median_error:.0f} € (C'est l'erreur la plus fréquente)")
    
    return model, num_features, cat_features, df

# ==========================================
# 3. INTERFACE DE PRÉDICTION INTELLIGENTE
# ==========================================

def predire_prix_intelligent(model, df_original, num_features, cat_features):
    print("\n-------------------------------------------")
    print("--- 🚗 ESTIMATION INTELLIGENTE ---")
    print("-------------------------------------------")
    print("Astuce : Pour quitter le programme, faites Ctrl+C")
    
    input_data = {}
    
    # --- A. SAISIE MARQUE ---
    while True:
        val = input("\nMarque * : ").strip()
        res = verifier_existence(df_original, 'brand', val)
        if res: 
            input_data['brand'] = res
            break
        print("❌ Marque inconnue.")
        afficher_options(df_original, 'brand')

    # --- B. SAISIE MODÈLE ---
    while True:
        val = input(f"Modèle de {input_data['brand']} * : ").strip()
        res = verifier_existence(df_original, 'carmodel', val, filtre_col='brand', filtre_val=input_data['brand'])
        if res: 
            input_data['carmodel'] = res
            break
        print(f"❌ Modèle inconnu chez {input_data['brand']}.")
        afficher_options(df_original, 'carmodel', 'brand', input_data['brand'])

    # --- C. SAISIE ANNÉE ---
    current_year = datetime.datetime.now().year
    while True:
        try:
            val = float(input("Année * : ").strip())
            if 1900 <= val <= current_year + 1:
                input_data['year'] = val
                break
            else:
                print(f"❌ Année invalide (1900-{current_year}).")
        except ValueError:
            print("❌ Chiffre requis.")

    # --- D. SAISIE CARBURANT ---
    while True:
        val = input("Carburant * : ").strip()
        res = verifier_existence(df_original, 'fuel', val)
        if res:
            input_data['fuel'] = res
            break
        print("❌ Carburant inconnu.")
        afficher_options(df_original, 'fuel')

    # --- E. SAISIE CRIT'AIR ---
    while True:
        try:
            val_input = input("Crit'Air (1-5) * : ").strip()
            v = float(val_input)
            if 1 <= v <= 5:
                input_data["crit'air"] = v
                break
            else:
                print("⚠️ Pour une voiture fossile, Crit'Air est entre 1 et 5.")
        except ValueError:
            print("❌ Chiffre requis.")

    # --- F. CHAMPS TECHNIQUES (AUTO-COMPLÉTION) ---
    smart_fields = {
        'km': "Kilométrage",
        'gearbox': "Boîte de vitesse",
        'puissancedin': "Puissance DIN (ch)",
        'puissancefiscale': "Puissance Fiscale (CV)"
    }
    
    print("\n--- Infos Techniques (Appuyez sur Entrée pour laisser l'IA deviner) ---")
    
    for field, label in smart_fields.items():
        val = input(f"{label} : ").strip()
        
        if val:
            try:
                if field != 'gearbox':
                    input_data[field] = float(val)
                else:
                    input_data[field] = val
            except ValueError:
                val = "" # Si erreur de conversion, on force le mode auto

        if not val:
            # Recherche hiérarchique : 1. Marque+Modele+Annee -> 2. Marque+Modele -> 3. Défaut
            found_val = get_smart_value(df_original, field, 
                                     {'brand': input_data['brand'], 
                                      'carmodel': input_data['carmodel'], 
                                      'year': input_data['year']})
            
            if found_val is None:
                found_val = get_smart_value(df_original, field, 
                                         {'brand': input_data['brand'], 
                                          'carmodel': input_data['carmodel']})

            # Valeurs de secours ultimes
            if found_val is None:
                if field == 'gearbox': found_val = 'manuelle'
                elif field == 'km': found_val = 150000.0
                elif field == 'puissancedin': found_val = 90.0
                elif field == 'puissancefiscale': found_val = 5.0

            print(f"   🤖 {label} estimé : {found_val}")
            input_data[field] = found_val

    # VALEURS PAR DÉFAUT (Pour les colonnes secondaires)
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

    # --- PRÉDICTION FINALE ---
    df_new = pd.DataFrame([input_data])
    df_new["departement"] = df_new["departement"].astype(str)

    try:
        # On prédit le log, puis on convertit en euros
        prix_log = model.predict(df_new)[0]
        prix = np.expm1(prix_log)
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
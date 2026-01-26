import pandas as pd
import re
from sklearn.impute import KNNImputer, SimpleImputer
import numpy as np

def clean_split_encode_impute_final():
    print("Lecture du fichier dataset.csv...")
    try:
        df = pd.read_csv('dataset.csv')
    except FileNotFoundError:
        print("Erreur : Le fichier dataset.csv est introuvable.")
        return

    print(f"Total lignes brutes : {len(df)}")

    # ==========================================
    # 1. NETTOYAGE GÉNÉRAL (PRIX & KM)
    # ==========================================
    def clean_price(x):
        if pd.isna(x): return None
        x = str(x)
        if '€' in x: x = x.split('€')[0]
        elif 'T.T.C' in x: x = x.split('T.T.C')[0]
        clean_str = re.sub(r'[^\d]', '', x)
        return float(clean_str) if clean_str else None

    df['price'] = df['price'].apply(clean_price)

    def clean_km_std(x):
        if pd.isna(x): return None
        x = str(x)
        if 'km' in x.lower(): x = x.lower().split('km')[0]
        clean_str = re.sub(r'[^\d]', '', x)
        return float(clean_str) if clean_str else None

    col_km_source = 'kilométragecompteur' if 'kilométragecompteur' in df.columns else 'km'
    if col_km_source in df.columns:
        df['km'] = df[col_km_source].apply(clean_km_std)
    else:
        df['km'] = None

    if 'carmodel' in df.columns:
        df['model_full'] = df['carmodel'].str.strip()
        df['brand'] = df['model_full'].apply(lambda x: str(x).split(' ')[0] if pd.notnull(x) else 'Inconnu')
    else:
        df['brand'] = 'Inconnu'
        df['model_full'] = 'Inconnu'

    rename_map = {
        'année': 'year',
        'énergie': 'fuel',
        'boîtedevitesse': 'gearbox',
        'boîtedevitesses': 'gearbox'
    }
    df = df.rename(columns=rename_map)

    # ==========================================
    # 2. ENCODAGE & NETTOYAGE STRICT
    # ==========================================
    print("\n--- ENCODAGE ET NETTOYAGE ---")

    # Nettoyage des nombres (enlève "ch", "CV", "mois"...)
    def extract_number(x):
        if pd.isna(x): return None
        x = str(x).lower().replace(',', '.')
        match = re.search(r'(\d+\.?\d*)', x)
        if match: return float(match.group(1))
        return None

    cols_to_clean_numbers = [
        'kilométragecompteur', 'garantie', 'puissancefiscale', 'puissancedin',
        'émissionsdeco2', 'autonomiebatterie', 'voltagebatterie', 
        'capacitébatterie', 'consommationmixte'
    ]

    for col in cols_to_clean_numbers:
        if col in df.columns:
            df[col] = df[col].apply(extract_number)

    # --- NETTOYAGE COULEURS AVEC STRATÉGIE "UNKNOWN -> NaN" ---
    def clean_color(x):
        if pd.isna(x): return np.nan
        x = str(x).lower().strip()
        
        # Mapping des couleurs connues
        if any(v in x for v in ['gris', 'grey', 'silver', 'argent', 'metal', 'anthracite', 'titan']): return 'gris'
        if any(v in x for v in ['bleu', 'blue', 'cyan', 'azur', 'nuit', 'marine']): return 'bleu'
        if any(v in x for v in ['noir', 'black', 'sombre', 'schwarz', 'nero']): return 'noir'
        if any(v in x for v in ['blanc', 'white', 'ivoire', 'polar']): return 'blanc'
        if any(v in x for v in ['rouge', 'red', 'bordeaux', 'flamme']): return 'rouge'
        if any(v in x for v in ['vert', 'green', 'olive']): return 'vert'
        if any(v in x for v in ['jaune', 'yellow', 'or', 'gold']): return 'jaune'
        if any(v in x for v in ['orange', 'cuivre']): return 'orange'
        if any(v in x for v in ['marron', 'brown', 'beige', 'chocolat', 'bronze', 'cafe', 'sable']): return 'marron'
        if any(v in x for v in ['violet', 'purple', 'aubergine']): return 'violet'
        
        # ICI : Si la couleur n'est pas reconnue ("canna di fucile", "moonlight"...), 
        # on retourne np.nan pour que l'imputer s'en charge plus tard.
        return np.nan 

    if 'couleurextérieure' in df.columns:
        print("   -> Nettoyage couleurs : Les inconnues deviennent NaN (pour imputation future).")
        df['couleurextérieure'] = df['couleurextérieure'].apply(clean_color)

    # Encodage binaire Garantie Constructeur
    if 'garantieconstructeur' in df.columns:
        df['garantieconstructeur'] = df['garantieconstructeur'].apply(
            lambda x: 'oui' if pd.notnull(x) and str(x).strip() != '' else 'non'
        )

    cols_to_drop = ['id', 'waranty']
    df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True)

    # ==========================================
    # 3. NETTOYAGE LIGNES CRITIQUES
    # ==========================================
    cols_critical = ['price', 'year', 'fuel']
    existing_critical = [c for c in cols_critical if c in df.columns]
    df_clean = df.dropna(subset=existing_critical)
    
    if 'year' in df_clean.columns:
        df_clean['year'] = pd.to_numeric(df_clean['year'], errors='coerce')

    print(f"Lignes valides après nettoyage critique : {len(df_clean)}")

    # ==========================================
    # 4. SÉPARATION
    # ==========================================
    print("\n--- SÉPARATION DES DATASETS ---")
    if 'fuel' in df_clean.columns:
        mask_electric = df_clean['fuel'].astype(str).str.lower().str.contains('lectrique', na=False)
        df_electric = df_clean[mask_electric].copy()
        df_fossil = df_clean[~mask_electric].copy()
    else:
        df_electric = pd.DataFrame(columns=df_clean.columns)
        df_fossil = df_clean.copy()

    # ==========================================
    # 5. OPTIMISATION DES COLONNES
    # ==========================================
    def clean_empty_columns(dataframe, name):
        if len(dataframe) == 0: return dataframe
        threshold = len(dataframe) * 0.5 
        non_na_counts = dataframe.count()
        cols_to_keep = non_na_counts[non_na_counts >= threshold].index.tolist()
        cols_to_drop = non_na_counts[non_na_counts < threshold].index.tolist()
        
        print(f"\n📊 {name} : {len(cols_to_drop)} colonnes supprimées (trop vides).")
        return dataframe[cols_to_keep]

    df_electric_opt = clean_empty_columns(df_electric, "DATASET ÉLECTRIQUE")
    df_fossil_opt = clean_empty_columns(df_fossil, "DATASET FOSSILE")

    # ==========================================
    # 6. IMPUTATION (REMPLISSAGE DES VIDES)
    # ==========================================
    print("\n--- IMPUTATION DES DONNÉES MANQUANTES ---")

    def apply_imputation(df_target, name):
        if len(df_target) == 0: return df_target
        
        df_imputed = df_target.copy()
        
        # 1. CATEGORIEL -> MODE (Valeur la plus fréquente)
        # C'est ICI que les couleurs devenues NaN (ex: "canna di fucile" -> NaN)
        # seront remplacées par la couleur la plus fréquente (ex: "gris").
        cat_cols = df_imputed.select_dtypes(include=['object']).columns
        if len(cat_cols) > 0:
            print(f"   -> {name} : Imputation 'Mode' pour {len(cat_cols)} colonnes texte.")
            imputer_mode = SimpleImputer(strategy='most_frequent')
            
            # On s'assure que les NaN sont bien traités
            df_imputed[cat_cols] = imputer_mode.fit_transform(df_imputed[cat_cols].astype(str).replace('nan', np.nan))

        # 2. NUMÉRIQUE SIMPLE -> MÉDIANE
        cols_median_target = ['km', 'year', 'nombredeportes', 'nombredeplaces', 'garantie']
        cols_median = [c for c in cols_median_target if c in df_imputed.columns]
        
        if cols_median:
            print(f"   -> {name} : Imputation 'Médiane' pour {cols_median}")
            imputer_median = SimpleImputer(strategy='median')
            df_imputed[cols_median] = imputer_median.fit_transform(df_imputed[cols_median])

        # 3. NUMÉRIQUE TECHNIQUE -> KNN (K-Nearest Neighbors)
        cols_tech_target = [
            'puissancedin', 'puissancefiscale', 'consommationmixte', 'émissionsdeco2',
            'autonomiebatterie', 'capacitébatterie', 'voltagebatterie'
        ]
        # On prend toutes les colonnes numériques restantes sauf le prix et celles déjà traitées
        num_cols = df_imputed.select_dtypes(include=['float64', 'int64']).columns
        cols_knn = [c for c in num_cols if c not in cols_median and c != 'price']
        
        if cols_knn:
            print(f"   -> {name} : Imputation 'KNN' (5 voisins) pour {cols_knn}")
            imputer_knn = KNNImputer(n_neighbors=5)
            df_imputed[num_cols] = imputer_knn.fit_transform(df_imputed[num_cols])

        return df_imputed

    df_electric_final = apply_imputation(df_electric_opt, "Électrique")
    df_fossil_final = apply_imputation(df_fossil_opt, "Fossile")

    # ==========================================
    # 7. SAUVEGARDE
    # ==========================================
    file_elec = 'dataset_electric.csv'
    file_foss = 'dataset_fossil.csv'

    df_electric_final.to_csv(file_elec, index=False)
    df_fossil_final.to_csv(file_foss, index=False)

    print("\n" + "="*30)
    print(f"✅ TRAITEMENT TERMINÉ AVEC SUCCÈS !")
    print(f"Fichiers générés : '{file_elec}' et '{file_foss}'")

if __name__ == "__main__":
    clean_split_encode_impute_final()
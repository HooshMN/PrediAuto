import pandas as pd
import re

def clean_and_split_data():
    print("Lecture du fichier dataset.csv...")
    try:
        df = pd.read_csv('dataset.csv')
    except FileNotFoundError:
        print("Erreur : Le fichier dataset.csv est introuvable.")
        return

    print(f"Total lignes brutes : {len(df)}")

    # --- 1. NETTOYAGE DU PRIX ---
    def clean_price(x):
        if pd.isna(x): return None
        x = str(x)
        # On coupe au symbole € ou T.T.C pour éviter de prendre les centimes ou le HT
        if '€' in x:
            x = x.split('€')[0]
        elif 'T.T.C' in x: 
            x = x.split('T.T.C')[0]
            
        clean_str = re.sub(r'[^\d]', '', x)
        if clean_str:
            return float(clean_str)
        return None

    print("Nettoyage de la colonne Prix...")
    # On nettoie la colonne 'price' existante
    df['price'] = df['price'].apply(clean_price)

    # --- 2. NETTOYAGE DU KILOMÉTRAGE ---
    def clean_km(x):
        if pd.isna(x): return None
        x = str(x)
        if 'km' in x.lower():
            x = x.lower().split('km')[0]
        clean_str = re.sub(r'[^\d]', '', x)
        if clean_str:
            return float(clean_str)
        return None

    print("Création de la colonne 'km' standardisée...")
    # On crée 'km' basé sur 'kilométragecompteur' (si elle existe, sinon on cherche une variante)
    col_km = 'kilométragecompteur' if 'kilométragecompteur' in df.columns else 'km'
    if col_km in df.columns:
        df['km'] = df[col_km].apply(clean_km)
    else:
        df['km'] = None # Fallback

    # --- 3. EXTRACTION DE LA MARQUE & MODÈLE ---
    if 'carmodel' in df.columns:
        df['model_full'] = df['carmodel'].str.strip()
        df['brand'] = df['model_full'].apply(lambda x: str(x).split(' ')[0] if pd.notnull(x) else 'Inconnu')
    else:
        df['brand'] = 'Inconnu'
        df['model_full'] = 'Inconnu'

    # --- 4. RENOMMAGE (Pour compatibilité Dashboard) ---
    # On renomme les colonnes vitales pour le dashboard, mais on garde le reste tel quel
    rename_map = {
        'année': 'year',
        'énergie': 'fuel',
        'boîtedevitesse': 'gearbox',
        'boîtedevitesses': 'gearbox'
    }
    df = df.rename(columns=rename_map)

    # --- 5. FILTRAGE MINIMAL ---
    # On ne supprime que les lignes où les infos CRITIQUES pour l'analyse manquent.
    # On garde les lignes même si "options" ou "couleur" sont vides.
    cols_critical = ['price', 'year', 'fuel']
    # Vérifier que ces colonnes existent avant de dropna
    existing_critical = [c for c in cols_critical if c in df.columns]
    
    df_clean = df.dropna(subset=existing_critical)
    
    # Conversion de l'année en entier si possible
    if 'year' in df_clean.columns:
        df_clean['year'] = pd.to_numeric(df_clean['year'], errors='coerce')

    print(f"Lignes après nettoyage des valeurs nulles critiques : {len(df_clean)}")

    # --- 6. SÉPARATION ÉLECTRIQUE vs FOSSILE ---
    print("Séparation des datasets selon l'énergie...")
    
    # On normalise la colonne fuel en minuscule et string pour la recherche
    if 'fuel' in df_clean.columns:
        # On cherche "lectrique" pour capturer "Electrique" et "électrique"
        mask_electric = df_clean['fuel'].astype(str).str.lower().str.contains('lectrique', na=False)
        
        df_electric = df_clean[mask_electric]
        df_fossil = df_clean[~mask_electric]
    else:
        print("Attention : Pas de colonne 'fuel'/'énergie' trouvée. Tout est mis dans 'fossil'.")
        df_electric = pd.DataFrame(columns=df_clean.columns)
        df_fossil = df_clean

    # --- 7. SAUVEGARDE ---
    file_elec = 'dataset_electric.csv'
    file_foss = 'dataset_fossil.csv'

    df_electric.to_csv(file_elec, index=False)
    df_fossil.to_csv(file_foss, index=False)

    print("-" * 30)
    print(f"✅ TERMINÉ !")
    print(f"⚡ Voitures Électriques : {len(df_electric)} -> Sauvegardé dans '{file_elec}'")
    print(f"⛽ Voitures Thermiques/Autres : {len(df_fossil)} -> Sauvegardé dans '{file_foss}'")
    print(f"Total : {len(df_electric) + len(df_fossil)}")
    print(f"Colonnes conservées : {len(df_clean.columns)}")

if __name__ == "__main__":
    clean_and_split_data()
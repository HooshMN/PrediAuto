import pandas as pd
import numpy as np
import random

def booster_dataset():
    print("🔄 Chargement du dataset électrique...")
    try:
        df = pd.read_csv("dataset_electric.csv", sep=None, engine='python')
    except FileNotFoundError:
        print("❌ Fichier introuvable.")
        return

    # 1. DICTIONNAIRE DE RÉFÉRENCE (Pour remplir les trous techniques)
    # On aide l'IA avec les specs des voitures les plus courantes
    specs_ref = {
        'ZOE': {'capacitébatterie': 52.0, 'autonomiebatterie': 395.0, 'puissancedin': 110.0},
        'MODEL 3': {'capacitébatterie': 60.0, 'autonomiebatterie': 491.0, 'puissancedin': 285.0},
        'MODEL Y': {'capacitébatterie': 60.0, 'autonomiebatterie': 455.0, 'puissancedin': 299.0},
        '208': {'capacitébatterie': 50.0, 'autonomiebatterie': 362.0, 'puissancedin': 136.0}, # e-208
        '2008': {'capacitébatterie': 50.0, 'autonomiebatterie': 345.0, 'puissancedin': 136.0}, # e-2008
        'SPRING': {'capacitébatterie': 27.0, 'autonomiebatterie': 230.0, 'puissancedin': 44.0},
        '500': {'capacitébatterie': 42.0, 'autonomiebatterie': 320.0, 'puissancedin': 118.0}, # Fiat 500e
        'LEAF': {'capacitébatterie': 40.0, 'autonomiebatterie': 270.0, 'puissancedin': 150.0},
        'ID.3': {'capacitébatterie': 58.0, 'autonomiebatterie': 420.0, 'puissancedin': 204.0},
        'MEGANE': {'capacitébatterie': 60.0, 'autonomiebatterie': 450.0, 'puissancedin': 220.0},
        'KONA': {'capacitébatterie': 64.0, 'autonomiebatterie': 484.0, 'puissancedin': 204.0}
    }

    print("🔧 Étape 1 : Remplissage intelligent des données manquantes...")
    
    # Harmonisation des colonnes Km
    if 'kilométragecompteur' in df.columns and 'km' not in df.columns:
        df['km'] = df['kilométragecompteur']
    elif 'km' in df.columns:
        df['km'] = df['km'].fillna(df.get('kilométragecompteur', 0))

    # Nettoyage prix
    if 'price' in df.columns: df.rename(columns={'price': 'Price'}, inplace=True)
    elif 'Price' not in df.columns and 'prix' in df.columns: df.rename(columns={'prix': 'Price'}, inplace=True)

    def remplir_specs(row):
        modele = str(row['carmodel']).upper()
        # On cherche si un mot clé (ex: ZOE) est dans le nom du modèle
        for key, specs in specs_ref.items():
            if key in modele:
                # Si la colonne existe et est vide (NaN), on remplit
                if pd.isna(row.get('capacitébatterie')):
                    row['capacitébatterie'] = specs['capacitébatterie']
                if pd.isna(row.get('autonomiebatterie')):
                    row['autonomiebatterie'] = specs['autonomiebatterie']
                if pd.isna(row.get('puissancedin')):
                    row['puissancedin'] = specs['puissancedin']
        return row

    df = df.apply(remplir_specs, axis=1)

    print(f"📊 Taille originale : {len(df)} lignes.")
    
    # 2. DATA AUGMENTATION (Clonage avec variations)
    print("🧬 Étape 2 : Génération de données synthétiques...")
    
    new_rows = []
    
    # Nombre de clones par voiture (ex: 5 copies pour chaque vraie voiture)
    NB_COPIES = 5 
    
    for index, row in df.iterrows():
        try:
            # On ignore les lignes sans prix ou sans km
            if pd.isna(row['Price']) or pd.isna(row['km']):
                continue
                
            base_price = float(row['Price'])
            base_km = float(row['km'])
            
            # On crée N variations
            for _ in range(NB_COPIES):
                clone = row.copy()
                
                # Variation KM : entre -15% et +15%
                variation_km = random.uniform(0.85, 1.15)
                new_km = base_km * variation_km
                
                # Variation Prix logique : 
                # Si KM augmente, Prix baisse (et inversement), avec un peu de bruit aléatoire
                # Formule : Prix * (AncienKM / NouveauKM)^0.1 * Bruit(±5%)
                price_factor = (base_km / new_km) ** 0.15 
                noise = random.uniform(0.95, 1.05)
                new_price = base_price * price_factor * noise
                
                clone['km'] = int(new_km)
                clone['Price'] = int(new_price)
                
                # On garde le reste identique (Marque, Modèle, Année...)
                new_rows.append(clone)
                
        except Exception as e:
            continue

    # On ajoute les clones au dataset original
    df_augmented = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    
    # Mélanger le tout
    df_augmented = df_augmented.sample(frac=1).reset_index(drop=True)
    
    # Sauvegarde
    output_name = "dataset_electric_boosted.csv"
    df_augmented.to_csv(output_name, index=False, sep=',')
    
    print(f"\n✅ Terminé ! Nouveau fichier généré : {output_name}")
    print(f"📈 Nouvelle taille : {len(df_augmented)} lignes (x{len(df_augmented)/len(df):.1f})")
    print("👉 Utilisez 'dataset_electric_boosted.csv' dans votre app.py maintenant !")

if __name__ == "__main__":
    booster_dataset()
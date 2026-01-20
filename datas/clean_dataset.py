import pandas as pd
import re

def clean_and_save_data():
    print("Lecture du fichier dataset.csv...")
    try:
        df = pd.read_csv('dataset.csv')
    except FileNotFoundError:
        print("Erreur : Le fichier dataset.csv est introuvable.")
        return

    # --- 1. NETTOYAGE DU PRIX (CORRIGÉ) ---
    def clean_price(x):
        if pd.isna(x): return None
        x = str(x)
        
        # CORRECTIF IMPORTANT : 
        # On coupe la chaîne dès qu'on voit le signe "€" ou "T.T.C"
        # Exemple : "6 850 € T.T.C. (5 708 € H.T.)" devient "6 850 "
        if '€' in x:
            x = x.split('€')[0]
        elif 'T.T.C' in x: 
            x = x.split('T.T.C')[0]
            
        # Ensuite, on ne garde que les chiffres
        clean_str = re.sub(r'[^\d]', '', x)
        
        if clean_str:
            return float(clean_str)
        return None

    print("Nettoyage de la colonne Prix...")
    df['price'] = df['price'].apply(clean_price)

    # --- 2. NETTOYAGE DU KILOMÉTRAGE ---
    def clean_km(x):
        if pd.isna(x): return None
        x = str(x)
        # On coupe aussi au cas où il y aurait des commentaires
        if 'km' in x.lower():
            x = x.lower().split('km')[0]
            
        clean_str = re.sub(r'[^\d]', '', x)
        if clean_str:
            return float(clean_str)
        return None

    print("Nettoyage de la colonne Kilométrage...")
    df['km'] = df['kilométragecompteur'].apply(clean_km)

    # --- 3. EXTRACTION DE LA MARQUE ---
    df['model_full'] = df['carmodel'].str.strip()
    df['brand'] = df['model_full'].apply(lambda x: str(x).split(' ')[0] if pd.notnull(x) else 'Inconnu')

    # --- 4. RENOMMAGE ET SÉLECTION ---
    # On essaie de gérer les variantes de noms de colonnes
    df = df.rename(columns={
        'année': 'year',
        'énergie': 'fuel',
        'boîtedevitesse': 'gearbox',
        'boîtedevitesses': 'gearbox' # Au cas où il y a un "s"
    })

    cols_to_keep = ['brand', 'model_full', 'year', 'km', 'fuel', 'gearbox', 'price']
    
    # On supprime les lignes incomplètes
    df_clean = df[cols_to_keep].dropna()

    # Sauvegarde
    output_file = 'dataset_cleaned.csv'
    df_clean.to_csv(output_file, index=False)
    
    print(f"✅ Nettoyage terminé avec succès !")
    print(f"Lignes initiales : {len(df)}")
    print(f"Lignes nettoyées : {len(df_clean)}")
    print(f"Fichier sauvegardé : {output_file}")
    
    # Petit test d'affichage pour vérifier
    print("\nAperçu des prix nettoyés (Top 5):")
    print(df_clean[['model_full', 'price']].head())

if __name__ == "__main__":
    clean_and_save_data()
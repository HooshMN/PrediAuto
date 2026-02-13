import pandas as pd

def nettoyer_csv():
    print("🔄 Chargement du dataset...")
    try:
        # On utilise le moteur python pour détecter automatiquement les séparateurs (; ou ,)
        df = pd.read_csv("dataset_fossil.csv", sep=None, engine='python')
    except FileNotFoundError:
        print("❌ Erreur : Le fichier 'dataset_fossil.csv' est introuvable.")
        return

    # Vérification que les colonnes existent
    if 'brand' not in df.columns or 'carmodel' not in df.columns:
        print("❌ Erreur : Les colonnes 'brand' ou 'carmodel' sont introuvables.")
        print(f"Colonnes trouvées : {df.columns.tolist()}")
        return

    print("🧹 Nettoyage en cours...")
    
    # Compteurs pour le rapport
    modifs = 0

    # Fonction qui nettoie une ligne
    def remove_brand_from_model(row):
        nonlocal modifs
        
        # On convertit tout en texte et en majuscules pour comparer sans erreur
        marque = str(row['brand']).strip().upper()
        modele = str(row['carmodel']).strip().upper()
        
        # Si le modèle commence par la marque (ex: "RENAULT CLIO" commence par "RENAULT")
        if modele.startswith(marque):
            # On enlève la marque du début du modèle
            nouveau_modele = modele[len(marque):].strip()
            
            # Si après nettoyage il ne reste rien (ex: modèle = "RENAULT"), on garde l'original ou on met un placeholder
            if not nouveau_modele:
                return modele
            
            modifs += 1
            return nouveau_modele
        
        return modele

    # Appliquer la fonction ligne par ligne
    df['carmodel'] = df.apply(remove_brand_from_model, axis=1)

    # Sauvegarde dans un NOUVEAU fichier pour ne pas écraser l'ancien par sécurité
    nouveau_nom = "dataset_fossil_clean.csv"
    df.to_csv(nouveau_nom, index=False, sep=';') # On force le séparateur ';' pour Excel/Mac

    print(f"\n✅ Terminé !")
    print(f"📊 Nombre de lignes corrigées : {modifs}")
    print(f"💾 Nouveau fichier créé : {nouveau_nom}")
    print("👉 Pensez à modifier votre script principal pour lire ce nouveau fichier !")

if __name__ == "__main__":
    nettoyer_csv()
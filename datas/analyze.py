import pandas as pd
import plotly.express as px
import plotly.io as pio

def generate_dashboard():
    print("Chargement des données nettoyées...")
    try:
        df = pd.read_csv('dataset_cleaned.csv')
    except FileNotFoundError:
        print("Erreur : Veuillez d'abord lancer le script de nettoyage (clean_data.py).")
        return

    print(f"{len(df)} véhicules chargés pour l'analyse.")

    # --- CRÉATION DES GRAPHIQUES ---

    # 1. GRAPHIQUE DÉPRÉCIATION (Line Chart)
    # Création des tranches de km
    bins = [0, 20000, 50000, 80000, 120000, 160000, 200000, 500000]
    labels = ['0-20k', '20-50k', '50-80k', '80-120k', '120-160k', '160-200k', '+200k']
    df['km_range'] = pd.cut(df['km'], bins=bins, labels=labels)

    # Calcul prix moyen par tranche
    depr_data = df.groupby('km_range', observed=True)['price'].mean().reset_index()

    fig1 = px.line(depr_data, x='km_range', y='price', markers=True,
                   title='📉 Dépréciation : Chute du prix selon le kilométrage',
                   labels={'km_range': 'Kilométrage', 'price': 'Prix Moyen (€)'})
    fig1.update_traces(line_color='#3b82f6', line_width=4)

    # 2. GRAPHIQUE TOP MARQUES (Bar Chart)
    # On garde les marques avec au moins 20 annonces pour éviter les biais
    brand_counts = df['brand'].value_counts()
    major_brands = brand_counts[brand_counts > 20].index
    df_brands = df[df['brand'].isin(major_brands)]

    # Top 20 par prix moyen
    brand_price = df_brands.groupby('brand')['price'].mean().sort_values(ascending=False).head(20).reset_index()

    fig2 = px.bar(brand_price, x='brand', y='price',
                  title='🏆 Top 20 Marques (Valeur Moyenne)',
                  labels={'brand': 'Marque', 'price': 'Prix Moyen (€)'},
                  color='price', color_continuous_scale='Bluyl')

    # 3. GRAPHIQUE CARBURANT (Pie Chart)
    # Nettoyage rapide des noms de carburant pour le graph (regrouper les rares)
    top_fuels = df['fuel'].value_counts().nlargest(4).index
    df['fuel_clean'] = df['fuel'].apply(lambda x: x if x in top_fuels else 'Autre')
    
    fuel_counts = df['fuel_clean'].value_counts().reset_index()
    fuel_counts.columns = ['Carburant', 'Nombre']

    fig3 = px.pie(fuel_counts, values='Nombre', names='Carburant', hole=0.4,
                  title='⛽ Répartition des Motorisations',
                  color_discrete_sequence=px.colors.sequential.RdBu)
    
    # 4. PRIX PAR ANNÉE (Line Chart)
    # On filtre les années trop vieilles (<1990) pour garder une échelle lisible
    df_year = df[df['year'] > 1990]
    year_data = df_year.groupby('year')['price'].mean().reset_index()

    fig4 = px.line(year_data, x='year', y='price', markers=True,
                   title='📅 Évolution du Prix par Année',
                   labels={'year': 'Année', 'price': 'Prix Moyen (€)'})
    fig4.update_traces(line_color='#f59e0b', line_width=4) # Orange
    
    # 5.  NOMBRE DE VOITURES PAR ANNÉE (Bar Chart)
    # On compte le nombre d'occurrences par année
    year_count_data = df_year['year'].value_counts().sort_index().reset_index()
    year_count_data.columns = ['year', 'count']

    fig5 = px.line(year_count_data, x='year', y='count', markers=True,
                   title='📊 Nombre de Voitures par Année (Volume)',
                   labels={'year': 'Année', 'count': 'Nombre d\'annonces'})
    fig5.update_traces(line_color='#10b981', line_width=4) # Vert Émeraude
    
    # 6. GRAPHIQUE BOITE DE VITESSE (Pie Chart )
    gearbox_counts = df['gearbox'].value_counts().reset_index()
    gearbox_counts.columns = ['Boite', 'Nombre']

    fig6 = px.pie(gearbox_counts, values='Nombre', names='Boite',
                  title='⚙️ Boîte Manuelle vs Automatique',
                  color_discrete_sequence=['#6366f1', '#a855f7']) # Violet / Indigo

    # --- STYLE DARK MODE ---
    for fig in [fig1, fig2, fig3, fig4, fig5, fig6]:
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(30, 41, 59, 0.5)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif", size=14, color="#f8fafc"),
            margin=dict(t=50, l=20, r=20, b=20)
        )

    # --- GÉNÉRATION HTML ---
    print("Génération du dashboard.html...")
    
    html_fig1 = pio.to_html(fig1, full_html=False, include_plotlyjs='cdn')
    html_fig2 = pio.to_html(fig2, full_html=False, include_plotlyjs=False)
    html_fig3 = pio.to_html(fig3, full_html=False, include_plotlyjs=False)
    html_fig4 = pio.to_html(fig4, full_html=False, include_plotlyjs=False)
    html_fig5 = pio.to_html(fig5, full_html=False, include_plotlyjs=False)
    html_fig6 = pio.to_html(fig6, full_html=False, include_plotlyjs=False)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PrediAuto - Analytics</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{ --bg-color: #0f172a; --card-bg: #1e293b; --text: #f8fafc; --accent: #3b82f6; }}
            body {{ background-color: var(--bg-color); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 40px 20px; }}
            
            .header {{ text-align: center; margin-bottom: 50px; }}
            .header h1 {{ font-size: 3rem; margin-bottom: 10px; font-weight: 800; }}
            .header span {{ color: var(--accent); }}
            
            /* Style pour la boite d'intro */
            .intro-box {{ 
                max-width: 1000px; margin: 0 auto 40px; 
                background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); 
                padding: 25px; border-radius: 16px; line-height: 1.6; color: #e2e8f0;
            }}
            .intro-box h3 {{ color: var(--accent); margin-top: 0; }}
            .intro-box a {{ color: var(--accent); text-decoration: underline; }}
            
            /* Style pour la zone de texte à remplir */
            .edit-zone {{
                background: rgba(255, 255, 255, 0.05);
                border-left: 4px solid #f59e0b; /* Orange pour attirer l'attention */
                padding: 15px;
                margin-bottom: 15px;
                color: #94a3b8;
                font-style: italic;
                font-size: 0.9rem;
            }}
            .edit-zone strong {{ color: #f59e0b; display: block; margin-bottom: 5px; font-style: normal; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }}

            .container {{ max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 30px; }}
            .card {{ background: var(--card-bg); border-radius: 16px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); display: flex; flex-direction: column; }}
            .full-width {{ grid-column: 1 / -1; }}
            
            @media (max-width: 900px) {{ .container {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        
        <div class="header">
            <h1>Predi<span>Auto</span> Analytics</h1>
            <p>Analyse Data du Marché Automobile Français</p>
        </div>

        <div class="intro-box">
            <h3>📂 Le Dataset & Objectifs</h3>
            <p>
                <strong>🎯 Objectif :</strong> Analyser les facteurs de dépréciation (Kilométrage, Âge, Marque) pour prédire la valeur des véhicules d'occasion.
                <br><br>
                <strong>📊 Source :</strong> <a href="https://www.kaggle.com/datasets/spicemix/french-second-hand-car" target="_blank">Kaggle - French Second Hand Car</a>.
                <br><br>
                <strong>✅ Forces :</strong> Données du marché français, cohérence mécanique (Prix/Km vérifiée), diversité des modèles.
                <br>
                <strong>⚠️ Faiblesses :</strong> Taille de l'échantillon limitée pour les modèles rares ("Outliers"), données déclaratives nécessitant un nettoyage.
            </p>
        </div>

        <div class="container">
            
            <div class="card full-width">
                <div class="edit-zone">
                    <strong>✍️ ZONE D'ANALYSE À REMPLIR</strong>
                    [Double-cliquez ici dans le code HTML pour écrire votre observation sur la dépréciation et le kilométrage...]
                </div>
                {html_fig1}
            </div>
            
            <div class="card full-width">
                <div class="edit-zone">
                    <strong>✍️ ZONE D'ANALYSE À REMPLIR</strong>
                    [Écrivez ici votre analyse sur le classement des marques...]
                </div>
                {html_fig2}
            </div>
            
            <div class="card">
                <div class="edit-zone">
                    <strong>✍️ ZONE D'ANALYSE À REMPLIR</strong>
                    [Écrivez ici votre commentaire sur les carburants...]
                </div>
                {html_fig3}
            </div>
            
            <div class="card">
                <div class="edit-zone">
                    <strong>✍️ ZONE D'ANALYSE À REMPLIR</strong>
                    [Écrivez ici votre commentaire sur les boîtes de vitesse...]
                </div>
                {html_fig6}
            </div>
            
            <div class="card full-width">
                <div class="edit-zone">
                    <strong>✍️ ZONE D'ANALYSE À REMPLIR</strong>
                    [Écrivez ici l'impact de l'année sur le prix...]
                </div>
                {html_fig4}
            </div>
            
            <div class="card full-width">
                <div class="edit-zone">
                    <strong>✍️ ZONE D'ANALYSE À REMPLIR</strong>
                    [Écrivez ici votre observation sur le volume d'annonces par année...]
                </div>
                {html_fig5}
            </div>
        </div>
    </body>
    </html>
    """

    with open("generated_dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ SUCCÈS : Ouvrez 'generated_dashboard.html' pour voir les résultats !")

if __name__ == "__main__":
    generate_dashboard()
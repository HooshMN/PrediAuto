// document.getElementById('predictionForm').addEventListener('submit', function(e) {
//     e.preventDefault(); // Empêche la page de se recharger

//     // 1. Récupération des valeurs
//     const make = document.getElementById('make').value;
//     const model = document.getElementById('model').value;
//     const year = parseInt(document.getElementById('year').value);
//     const km = parseInt(document.getElementById('km').value);
    
//     // Affichage de la carte résultat et du loader
//     const resultCard = document.getElementById('resultCard');
//     const loader = document.getElementById('loader');
//     const content = document.getElementById('resultContent');
    
//     resultCard.classList.remove('hidden');
//     content.classList.add('hidden');
//     loader.style.display = 'block';

//     // Scroller vers le résultat (sur mobile c'est utile)
//     resultCard.scrollIntoView({ behavior: 'smooth' });

//     // 2. SIMULATION DE L'IA (Délai de 2 secondes)
//     setTimeout(() => {
//         // --- LOGIQUE FACTICE POUR LA DEMO ---
//         // Dans le vrai projet, ici tu feras un fetch('http://api.prediauto.com/predict', ...)
        
//         let basePrice = 25000; // Prix de base arbitraire
//         if(make === 'Audi' || make === 'BMW' || make === 'Mercedes') basePrice = 45000;
        
//         // Calcul simple pour simuler : Prix - (Age * dépréciation) - (KM * usure)
//         const age = 2024 - year;
//         let estimatedPrice = basePrice - (age * 1500) - (km * 0.05);
        
//         // On évite les prix négatifs pour la démo
//         if (estimatedPrice < 1000) estimatedPrice = 1000;

//         // Projection FUTURE (+2 ans, +30k km)
//         let futurePrice = estimatedPrice - (2 * 1500) - (30000 * 0.05);
//         if (futurePrice < 500) futurePrice = 500;
        
//         const diff = futurePrice - estimatedPrice;

//         // --- MISE A JOUR DU DOM ---
//         document.getElementById('carTitle').innerText = `${make} ${model} (${year})`;
//         document.getElementById('currentPrice').innerText = formatCurrency(estimatedPrice);
//         document.getElementById('futurePrice').innerText = formatCurrency(futurePrice);
//         document.getElementById('diffPrice').innerText = `${formatCurrency(diff)} (Perte estimée)`;
        
//         // Affichage final
//         loader.style.display = 'none';
//         content.classList.remove('hidden');

//     }, 1500); // 1.5 secondes d'attente
// });

// function resetForm() {
//     document.getElementById('resultCard').classList.add('hidden');
//     window.scrollTo({ top: 0, behavior: 'smooth' });
// }

// function formatCurrency(num) {
//     return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(num);
// }

document.getElementById('predictionForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Empêche la page de se recharger

    // 1. Récupération des valeurs (juste pour l'affichage du titre)
    const make = document.getElementById('make').value;
    const model = document.getElementById('model').value;
    const year = document.getElementById('year').value;
    
    // Affichage de la carte résultat et du loader
    const resultCard = document.getElementById('resultCard');
    const loader = document.getElementById('loader');
    const content = document.getElementById('resultContent');
    
    resultCard.classList.remove('hidden');
    content.classList.add('hidden');
    loader.style.display = 'block';

    // Scroller vers le résultat
    resultCard.scrollIntoView({ behavior: 'smooth' });

    // 2. SIMULATION (Délai de 1.5 secondes)
    setTimeout(() => {
        
        // On masque le loader
        loader.style.display = 'none';
        content.classList.remove('hidden');

        // --- NOUVEAU CONTENU : MESSAGE "À VENIR" ---
        // On remplace tout le HTML intérieur de la div de résultat
        content.innerHTML = `
            <div class="badge">Projet académique en cours</div>
            
            <h2 id="carTitle" style="margin-bottom: 2rem;">${make} ${model} (${year})</h2>
            
            <div class="price-box" style="text-align: center; padding: 3rem 1rem;">
                <i class="fa-solid fa-robot" style="font-size: 3rem; color: #3b82f6; margin-bottom: 1rem;"></i>
                <span class="price" style="font-size: 1.5rem;">Modèle de prédiction à venir</span>
            </div>

            <button class="btn-secondary full-width" onclick="resetForm()">Nouvelle recherche</button>
        `;

    }, 1500); 
});

function resetForm() {
    document.getElementById('resultCard').classList.add('hidden');
    // On remet le formulaire à zéro si besoin, ou on scrolle juste en haut
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// La fonction formatCurrency n'est plus utile ici, mais on peut la laisser si besoin plus tard
function formatCurrency(num) {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(num);
}
/**
 * PREDIAUTO - SCRIPT PRINCIPAL
 * Gestion de l'interface, de l'autocomplétion et de la communication avec l'API Python.
 */

// ============================================================
// 1. CONFIGURATION ET DONNÉES
// ============================================================

const MODES = {
    fossil: {
        title: 'VALEUR <span style="color:var(--accent)">THERMIQUE</span>',
        desc: 'Estimation précise pour véhicules Essence, Diesel et Hybrides.',
        fuels: ['Essence', 'Diesel', 'Hybride'],
        bodyClass: 'mode-fossil'
    },
    electric: {
        title: 'VALEUR <span style="color:var(--accent-elec)">ÉLECTRIQUE</span>',
        desc: 'Analyse spécialisée batterie et autonomie pour véhicules EV.',
        fuels: ['Electrique', 'Hybride Rechargeable'], 
        bodyClass: 'mode-elec'
    }
};

// Base de données : on sépare bien les marques Fossiles et Électriques
const CAR_DATABASE = {
    fossil: {
        'Renault': ['Clio IV', 'Clio V', 'Megane 3', 'Megane 4', 'Captur', 'Kadjar', 'Austral', 'Arkana', 'Twingo 3', 'Scenic 3', 'Scenic 4', 'Espace 5', 'Talisman', 'Koleos'],
        'Peugeot': ['208', '208 II', '2008', '2008 II', '308', '308 II', '308 III', '3008', '3008 II', '5008', '5008 II', '508', '508 II', '108', 'Rifter'],
        'Citroën': ['C3', 'C3 Aircross', 'C4', 'C4 Cactus', 'C5 Aircross', 'Berlingo', 'C1', 'C4 Picasso', 'Grand C4 Picasso', 'C5 X'],
        'Dacia': ['Sandero', 'Sandero Stepway', 'Duster', 'Duster 2', 'Jogger', 'Lodgy', 'Dokker', 'Logan'],
        'Volkswagen': ['Golf 6', 'Golf 7', 'Golf 8', 'Polo 5', 'Polo 6', 'Tiguan', 'Tiguan 2', 'T-Roc', 'T-Cross', 'Passat', 'Touran', 'Arteon', 'Touareg'],
        'Audi': ['A1', 'A3 Sportback', 'A4', 'A5', 'A6', 'Q2', 'Q3', 'Q3 Sportback', 'Q5', 'Q7', 'Q8', 'TT'],
        'BMW': ['Série 1', 'Série 2 Active Tourer', 'Série 3', 'Série 4', 'Série 5', 'X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'M2', 'M3', 'M4'],
        'Mercedes': ['Classe A', 'Classe B', 'Classe C', 'Classe E', 'CLA', 'GLA', 'GLB', 'GLC', 'GLE', 'Classe V'],
        'Toyota': ['Yaris', 'Yaris Cross', 'Corolla', 'C-HR', 'RAV4', 'Aygo', 'Aygo X', 'Prius', 'Highlander', 'Land Cruiser'],
        'Ford': ['Fiesta', 'Focus', 'Puma', 'Kuga', 'EcoSport', 'Mondeo', 'S-Max', 'Galaxy', 'Ranger', 'Mustang'],
        'Kia': ['Picanto', 'Rio', 'Stonic', 'Ceed', 'XCeed', 'Sportage', 'Niro', 'Sorento'],
        'Hyundai': ['i10', 'i20', 'i30', 'Bayon', 'Kona', 'Tucson', 'Santa Fe'],
        'Fiat': ['500', '500X', '500L', 'Panda', 'Tipo', 'Punto']
        // PAS DE TESLA ICI (Sauf si vous avez des données fossiles, ce qui est rare)
    },
    electric: {
        'Tesla': ['Model 3', 'Model Y', 'Model S', 'Model X'],
        'Renault': ['Zoe', 'Twingo E-Tech', 'Megane E-Tech', 'Kangoo E-Tech', 'Scenic E-Tech', 'Twizy'],
        'Peugeot': ['e-208', 'e-2008', 'e-Rifter', '3008 Hybrid', '308 Hybrid', '508 Hybrid'],
        'Citroën': ['ë-C4', 'ë-C4 X', 'C5 Aircross Hybrid', 'ë-Berlingo', 'Ami'],
        'Dacia': ['Spring'],
        'Volkswagen': ['ID.3', 'ID.4', 'ID.5', 'ID.Buzz', 'e-Golf', 'e-Up!', 'Golf GTE', 'Passat GTE'],
        'Audi': ['Q4 e-tron', 'Q8 e-tron', 'e-tron GT', 'Q5 TFSI e', 'A3 TFSI e'],
        'BMW': ['i3', 'i4', 'iX1', 'iX3', 'iX', 'i7', 'Série 2 Active Tourer 225xe', 'X5 xDrive45e'],
        'Mercedes': ['EQA', 'EQB', 'EQC', 'EQE', 'EQS', 'GLC 300e', 'Classe A 250e'],
        'Toyota': ['bZ4X', 'Prius Plug-in', 'RAV4 Rechargeable', 'Mirai'],
        'Ford': ['Mustang Mach-E', 'Kuga PHEV', 'Explorer PHEV'],
        'Kia': ['EV6', 'EV9', 'Niro EV', 'e-Soul', 'Sportage PHEV', 'Sorento PHEV'],
        'Hyundai': ['Ioniq 5', 'Ioniq 6', 'Kona Electric', 'Tucson PHEV', 'Santa Fe PHEV'],
        'Fiat': ['500e']
    }
};

// ============================================================
// 2. INITIALISATION & UI LOGIC
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    switchMode('fossil'); // Mode par défaut
});

// Écouteurs pour l'autocomplétion
document.getElementById('make').addEventListener('change', function() {
    updateModelSuggestions();
    document.getElementById('modelHelp').style.display = 'none';
});

document.getElementById('model').addEventListener('focus', function() {
    if (!document.getElementById('make').value) {
        document.getElementById('modelHelp').style.display = 'block';
    }
});

function switchMode(mode) {
    const config = MODES[mode];
    document.getElementById('engineType').value = mode;
    
    // UI Updates
    document.body.className = config.bodyClass;
    document.getElementById('mainTitle').innerHTML = config.title;
    document.getElementById('mainDesc').innerText = config.desc;

    // Tabs Style
    const btns = document.querySelectorAll('.tab-btn');
    btns.forEach(b => b.className = 'tab-btn'); 
    if(mode === 'fossil') btns[0].classList.add('active-fossil');
    else btns[1].classList.add('active-elec');

    // 1. Update Carburants
    const fuelSelect = document.getElementById('fuel');
    fuelSelect.innerHTML = '';
    config.fuels.forEach(f => {
        let opt = document.createElement('option');
        opt.value = f;
        opt.innerText = f;
        fuelSelect.appendChild(opt);
    });

    // 2. Update Marques (Dynamique)
    const brandSelect = document.getElementById('make');
    brandSelect.innerHTML = '<option value="" disabled selected>Choisir...</option>';
    
    // On récupère les marques disponibles dans la base de données selon le mode
    const availableBrands = Object.keys(CAR_DATABASE[mode]);
    availableBrands.forEach(brand => {
        let opt = document.createElement('option');
        opt.value = brand;
        opt.innerText = brand;
        brandSelect.appendChild(opt);
    });

    // 3. Gestion Champs Dynamiques
    const dynamicField = document.getElementById('dynamicField');
    const batteryRow = document.getElementById('batteryRow');

    if (mode === 'fossil') {
        dynamicField.innerHTML = `
            <label>Boîte de vitesse</label>
            <select id="gearbox">
                <option value="" selected>Indifférent</option>
                <option value="Manuelle">Manuelle</option>
                <option value="Automatique">Automatique</option>
            </select>`;
        batteryRow.classList.add('hidden');
    } else {
        dynamicField.innerHTML = `
            <label>Crit'Air</label>
            <select id="critair">
                <option value="0" selected>0 (Vert)</option>
                <option value="1">1 (Violet)</option>
            </select>`;
        batteryRow.classList.remove('hidden');
    }

    // Reset du champ modèle car les marques ont changé
    document.getElementById('model').value = '';
    updateModelSuggestions();
}

function updateModelSuggestions() {
    const make = document.getElementById('make').value;
    const mode = document.getElementById('engineType').value; 
    const dataList = document.getElementById('modelList');
    const modelInput = document.getElementById('model');

    dataList.innerHTML = '';
    modelInput.value = '';

    if (make && CAR_DATABASE[mode] && CAR_DATABASE[mode][make]) {
        const models = CAR_DATABASE[mode][make];
        
        models.forEach(modelName => {
            const option = document.createElement('option');
            option.value = modelName;
            dataList.appendChild(option);
        });
        // Placeholder contextuel
        modelInput.placeholder = `Entrez le nom de votre modèle...`;
    } else {
        modelInput.placeholder = "Entrez le nom de votre modèle";
    }
}

// ============================================================
// 3. SOUMISSION & API
// ============================================================

document.getElementById('predictionForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const mode = document.getElementById('engineType').value;
    const rawKm = document.getElementById('km').value;

    let formData = {
        engine_type: mode,
        brand: document.getElementById('make').value,
        carmodel: document.getElementById('model').value,
        year: document.getElementById('year').value,
        fuel: document.getElementById('fuel').value,
        km: rawKm ? parseInt(rawKm) : "",
        
        puissancedin: document.getElementById('puissancedin').value,
        puissancefiscale: document.getElementById('puissancefiscale').value,
        nombredeportes: document.getElementById('portes').value,
        nombredeplaces: document.getElementById('places').value,
        departement: document.getElementById('dept').value,
        premiere_main: document.getElementById('premiereMain').checked ? 'oui' : 'non'
    };

    if (mode === 'fossil') {
        formData.gearbox = document.getElementById('gearbox').value;
    } else {
        const auto = document.getElementById('autonomie').value;
        const cap = document.getElementById('capacite').value;
        formData.autonomie = auto ? parseFloat(auto) : "";
        formData.capacite = cap ? parseFloat(cap) : "";
        
        if(document.getElementById('critair')) {
            formData.critair = document.getElementById('critair').value;
        }
    }

    const resultCard = document.getElementById('resultCard');
    const loader = document.getElementById('loader');
    const content = document.getElementById('resultContent');
    
    resultCard.classList.remove('hidden');
    content.classList.add('hidden');
    loader.style.display = 'block';
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

    fetch('http://127.0.0.1:5000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        loader.style.display = 'none';
        content.classList.remove('hidden');

        if (data.error) {
            content.innerHTML = `<p style="color:red">Erreur : ${data.error}</p><button class="btn-secondary" onclick="resetForm()">Réessayer</button>`;
            return;
        }

        const fmt = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
        const prix = fmt.format(data.prix_estime);
        const prixFutur = fmt.format(data.prix_futur);
        const score = data.model_score ? Math.round(data.model_score.r2 * 100) : 85;
        const colorClass = mode === 'fossil' ? 'var(--accent)' : 'var(--accent-elec)';

        let iaDetails = "";
        if (data.details_ia) {
            Object.keys(data.details_ia).forEach(k => {
                if(k === 'km') iaDetails += `<li>KM estimé : <b>${Math.round(data.details_ia[k])}</b></li>`;
                if(k === 'autonomiebatterie') iaDetails += `<li>Autonomie est. : <b>${Math.round(data.details_ia[k])} km</b></li>`;
                if(k === 'puissancedin') iaDetails += `<li>Puissance est. : <b>${Math.round(data.details_ia[k])} ch</b></li>`;
                if(k === 'capacitébatterie') iaDetails += `<li>Batterie est. : <b>${Math.round(data.details_ia[k])} kWh</b></li>`;
            });
        }

        let iaBlock = "";
        if (iaDetails !== "") {
            const bg = mode === 'fossil' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(59, 130, 246, 0.1)';
            iaBlock = `
                <div style="background:${bg}; border:1px solid ${colorClass}; color:${colorClass}; padding:10px; border-radius:8px; margin-bottom:15px; font-size:0.85rem; text-align:left;">
                    <i class="fa-solid fa-robot"></i> <b>L'IA a complété :</b>
                    <ul style="margin:5px 0 0 20px; padding:0;">${iaDetails}</ul>
                </div>`;
        }

        content.innerHTML = `
            <div style="background:${colorClass}; color:white; padding:5px 15px; border-radius:20px; display:inline-block; margin-bottom:10px; font-weight:800; text-transform:uppercase; font-size:0.8rem;">
                Confiance Modèle : ${score}%
            </div>
            
            <h2 style="margin: 0 0 20px 0; color:white;">${formData.brand} ${formData.carmodel} (${formData.year})</h2>
            
            ${iaBlock}
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-bottom:20px;">
                <div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:12px; border:1px solid #3f3f46;">
                    <div style="color:var(--text-muted); font-size:0.8rem; text-transform:uppercase;">Cote Actuelle</div>
                    <div style="font-size:2rem; font-weight:800; color:white; margin-top:5px;">${prix}</div>
                </div>
                <div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:12px; border:1px solid #3f3f46;">
                    <div style="color:var(--text-muted); font-size:0.8rem; text-transform:uppercase;">Projection 2 ans</div>
                    <div style="font-size:2rem; font-weight:800; color:var(--text-muted); margin-top:5px;">${prixFutur}</div>
                </div>
            </div>

            <button onclick="resetForm()" style="width:100%; padding:14px; background:transparent; border:1px solid #3f3f46; color:white; border-radius:8px; cursor:pointer; transition:0.3s; font-weight:600;">
                Nouvelle recherche
            </button>
        `;
    })
    .catch(error => {
        console.error(error);
        loader.style.display = 'none';
        content.classList.remove('hidden');
        content.innerHTML = `<p style="color:red">Erreur de connexion au serveur.</p>`;
    });
});

function resetForm() {
    document.getElementById('resultCard').classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
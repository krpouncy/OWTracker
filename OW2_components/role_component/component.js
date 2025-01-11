// A map of heroes to roles for synergy calculations
const heroRoleMap = {
    Ana: 'Support',
    Mercy: 'Support',
    Moira: 'Support',
    Genji: 'Damage',
    Kiriko: 'Support',
    Cassidy: 'Damage',
    Soldier_76: 'Damage',
    Hanzo: 'Damage',
    Widowmaker: 'Damage',
    Reinhardt: 'Tank',
    DVa: 'Tank',
    Lucio: 'Support',
    Zenyatta: 'Support',
    Tracer: 'Damage',
    Ashe: 'Damage',
    Junkrat: 'Damage',
    Sombra: 'Damage',
    Zarya: 'Tank',
    Roadhog: 'Tank',
    Baptiste: 'Support',
    Reaper: 'Damage',
    Doomfist: 'Tank',
    Pharah: 'Damage',
    Lifeweaver: 'Support',
    Orisa: 'Tank',
    Sigma: 'Tank',
    Sojourn: 'Damage',
    Brigitte: 'Support',
    Mei: 'Damage',
    Winston: 'Tank',
    Illari: 'Support',
    Bastion: 'Damage',
    Junker_Queen: 'Tank',
    Torbjorn: 'Damage',
    Echo: 'Damage',
    Symmetra: 'Damage',
    Wrecking_Ball: 'Tank',
    Ramattra: 'Tank',
    Juno: 'Support',
    Mauga: 'Tank',
    Venture: 'Damage',
};

/**
 * Called when the synergy data from /api/get_rules_table returns.
 * It then calculates role proportions from the "rules" returned.
 */
function handleRulesTableResponse(json) {
    console.log('Received rules table data:', json);

    const rulesContainer = document.getElementById('rules-container');
    if (!rulesContainer) {
        console.warn('No rules-container element found.');
        return;
    }

    // Insert the new table HTML
    rulesContainer.innerHTML = json.table_html;

    // Store the full rules data in a hidden div for further role proportion analysis
    const fullRulesDiv = document.getElementById('full-rules-data');
    if (fullRulesDiv) {
        fullRulesDiv.textContent = JSON.stringify(json.rules);
        // Then update role proportions
        updateRoleProportionsFromHiddenDiv();
    }
}

socket.on('team_rules', (data) => {
    console.log('Received team_rules data:', data);
    handleRulesTableResponse(data);
})

socket.on('update_hidden_rules_div', (rules) => {
    // put the rules in the hidden div
    console.log('Received updated rules:', rules);
    const fullRulesDiv = document.getElementById('full-rules-data');
    if (fullRulesDiv) {
        fullRulesDiv.textContent = JSON.stringify(rules);
        // Then update role proportions
        updateRoleProportionsFromHiddenDiv();
    }
});


function updateRoleProportionsFromHiddenDiv() {
    const fullRulesDiv = document.getElementById('full-rules-data');
    if (!fullRulesDiv) return;

    const fullRulesJSON = fullRulesDiv.textContent.trim();
    if (!fullRulesJSON) {
        console.log('No synergy rules in hidden div.');
        updateRoleIndicators(0, 0, 0, 0);
        return;
    }

    let allRules;
    try {
        allRules = JSON.parse(fullRulesJSON);
    } catch (e) {
        console.error('Error parsing synergy JSON:', e);
        updateRoleIndicators(0, 0, 0, 0);
        return;
    }

    let allHeroes = [];
    allRules.forEach((rule) => {
        const rhs = rule['rhs']; // e.g. "{YOU=Illari, OTHER=Moira}"
        let text = rhs.trim().replace(/[{}]/g, '').trim();
        if (!text) return;
        const items = text.split(',').map((s) => s.trim()).filter(Boolean);
        items.forEach((item) => {
            const [label, hero] = item.split('=').map((s) => s.trim());
            if (hero) allHeroes.push(hero);
        });
    });

    console.log('All heroes from synergy rules:', allHeroes);

    let tankCount = 0;
    let dmgCount = 0;
    let suppCount = 0;
    allHeroes.forEach((hero) => {
        const role = heroRoleMap[hero];
        if (role === 'Tank') tankCount++;
        else if (role === 'Damage') dmgCount++;
        else if (role === 'Support') suppCount++;
    });

    const total = tankCount + dmgCount + suppCount;
    if (total === 0) {
        updateRoleIndicators(0, 0, 0, 0);
    } else {
        updateRoleIndicators(tankCount, dmgCount, suppCount, total);
    }
}

/**
 * Updates visual indicators for synergy.
 */
function updateRoleIndicators(tankCount, dmgCount, suppCount, total) {
    const tankPropDiv = document.getElementById('tank-prop');
    const dmgPropDiv = document.getElementById('dmg-prop');
    const suppPropDiv = document.getElementById('supp-prop');

    if (!tankPropDiv || !dmgPropDiv || !suppPropDiv) return;

    // Example weighting (softmax style)
    let tankProp = Math.exp(tankCount);
    let dmgProp = Math.exp(dmgCount / 2);
    let suppProp = Math.exp(suppCount / 2);

    const sum = tankProp + dmgProp + suppProp;
    tankProp /= sum;
    dmgProp /= sum;
    suppProp /= sum;

    // Show numeric values
    document.getElementById('tank-count').textContent = `${tankCount * 2}`;
    document.getElementById('dmg-count').textContent = `${dmgCount}`;
    document.getElementById('supp-count').textContent = `${suppCount}`;

    tankPropDiv.style.backgroundColor = getGradientColor(tankProp);
    dmgPropDiv.style.backgroundColor = getGradientColor(dmgProp);
    suppPropDiv.style.backgroundColor = getGradientColor(suppProp);
}

/**
 * Simple gradient color function.
 */
function getGradientColor(proportion) {
    const startColor = [21, 21, 21];  // #151515
    const endColor = [0, 123, 255]; // Bootstrap primary blue

    const r = Math.round(startColor[0] + proportion * (endColor[0] - startColor[0]));
    const g = Math.round(startColor[1] + proportion * (endColor[1] - startColor[1]));
    const b = Math.round(startColor[2] + proportion * (endColor[2] - startColor[2]));

    return `rgb(${r}, ${g}, ${b})`;
}


socket.on('performance_update', (data) => {
    console.log('Received performance_update:', data);

    // Update the performance rows
    const {tank, damage, support} = data;
    updatePerformanceRow('tank-row', tank);
    updatePerformanceRow('damage-row', damage);
    updatePerformanceRow('support-row', support);

});


function updatePerformanceRow(rowId, performance) {
    const row = document.getElementById(rowId);
    if (!row) return;

    row.textContent = performance.text;
    switch (performance.status) {
        case 'good':
            row.className = 'p-2 my-2 text-center bg-success';
            break;
        case 'average':
            row.className = 'p-2 my-2 text-center bg-warning';
            break;
        case 'poor':
            row.className = 'p-2 my-2 text-center bg-danger';
            break;
        default:
            row.className = 'p-2 my-2 text-center bg-secondary';
            break;
    }
}

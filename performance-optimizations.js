/**
 * MILLORA: Debouncing per optimitzar la generació de codi
 * 
 * Evita regenerar el codi Python en cada canvi petit,
 * millorant la performance especialment amb workspaces grans
 */

// ==================== FUNCIÓ DEBOUNCE ====================

/**
 * Crea una funció debounced que retarda l'execució
 * @param {Function} func - Funció a executar
 * @param {number} wait - Temps d'espera en ms
 * @returns {Function} - Funció debounced
 */
function debounce(func, wait = 300) {
    let timeout;

    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== APLICACIÓ EN WORKSPACE ====================

// Versió optimitzada de onWorkspaceChange
function setupOptimizedWorkspaceListener(workspace) {
    // Debounced versions
    const debouncedUpdateCode = debounce(updateGeneratedCode, 300);
    const debouncedUpdateStatus = debounce(updateStatusBar, 100);

    // Event listener optimitzat
    workspace.addChangeListener((event) => {
        // Filtrar només events rellevants
        const relevantEvents = [
            Blockly.Events.BLOCK_CHANGE,
            Blockly.Events.BLOCK_CREATE,
            Blockly.Events.BLOCK_DELETE,
            Blockly.Events.BLOCK_MOVE,
            Blockly.Events.BLOCK_FIELD_INTERMEDIATE_CHANGE
        ];

        if (!relevantEvents.includes(event.type)) {
            return; // Ignorar altres events
        }

        // Events que necessiten actualització immediata
        if (event.type === Blockly.Events.BLOCK_DELETE) {
            // Actualitzar immediatament quan s'esborra
            updateStatusBar();
        } else {
            // Altres canvis: fer debouncing
            debouncedUpdateStatus();
        }

        // Generació de codi sempre amb debouncing
        debouncedUpdateCode();
    });
}

// ==================== MILLORA ADICIONAL: CACHE ====================

let codeCache = {
    hash: null,
    code: null
};

/**
 * Genera el hash d'un workspace per detectar canvis
 */
function getWorkspaceHash(workspace) {
    const blocks = workspace.getAllBlocks(false);
    const blockIds = blocks.map(b => b.id).sort().join(',');
    const blockTypes = blocks.map(b => b.type).sort().join(',');
    return `${blockIds}-${blockTypes}`;
}

/**
 * Actualitza el codi generat NOMÉS si ha canviat el workspace
 */
function updateGeneratedCodeCached(workspace) {
    const currentHash = getWorkspaceHash(workspace);

    // Si no ha canviat, usar cache
    if (codeCache.hash === currentHash && codeCache.code !== null) {
        console.log('📦 Usant codi des de cache');
        return codeCache.code;
    }

    // Si ha canviat, regenerar
    console.log('🔄 Regenerant codi Python...');
    const code = generateCompletePythonCode(workspace);

    // Actualitzar cache
    codeCache.hash = currentHash;
    codeCache.code = code;

    // Actualitzar UI
    document.getElementById('generatedCode').textContent = code;

    return code;
}

// ==================== MONITORING DE PERFORMANCE ====================

/**
 * Mesura el temps d'execució d'una funció
 */
function measurePerformance(name, func) {
    return function (...args) {
        const start = performance.now();
        const result = func(...args);
        const end = performance.now();

        const time = (end - start).toFixed(2);
        if (time > 100) {
            console.warn(`⚠️ ${name} va trigar ${time}ms (lent)`);
        } else {
            console.log(`✅ ${name}: ${time}ms`);
        }

        return result;
    };
}

// Wrapping en funcions existents
const updateGeneratedCode = measurePerformance(
    'Generació de codi',
    updateGeneratedCodeCached
);

// ==================== EXPORTAR ====================

export {
    debounce,
    setupOptimizedWorkspaceListener,
    updateGeneratedCodeCached,
    measurePerformance,
    getWorkspaceHash
};

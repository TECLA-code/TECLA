/**
 * TeclaSkins — RESERVA, no el carrega ningú (vegeu README.md).
 *
 * El motor de TEMES que es va provar i aparcar.
 *
 * Un TEMA no és una paleta: és un sistema de disseny sencer (geometria,
 * tipografia, materialitat i color). La PALETA és un eix a part —les 17
 * combinacions de color de sempre— i només té sentit dins del tema Clàssic,
 * que és l'únic que no imposa rols estrictes d'acent.
 *
 * El contracte que ha de complir un tema és a css/reserva-estetica/CONTRACTE.md. Aquest
 * mòdul no sap res de cap tema en concret: només aplica la classe, la desa i
 * avisa. Per afegir-ne un de nou n'hi ha prou amb un fitxer CSS i una entrada
 * a SKINS — cap altra línia de codi.
 *
 * Pensat per compartir-lo amb el MacroPad i el Blocks: no depèn de res de
 * l'app d'Instrument.
 */

/** Els temes disponibles. `id: null` és el Clàssic (absència de classe). */
export const SKINS = [
    {
        id: null,
        nom: 'Clàssic',
        rev: 'v1',
        desc: 'El de sempre: fosc neutre, fonts del sistema.',
        // L'únic tema amb selector de paleta: no imposa rols d'accent.
        paletes: true,
        mostra: ['#0c0c0c', '#141414', '#1c1c1c', '#4a80f0'],
    },
    {
        id: 'oniric',
        nom: 'Oníric',
        rev: 'maker console',
        desc: 'Consola tècnica: fosc càlid, Inter + IBM Plex Mono, serigrafia i tecles amb pressió.',
        paletes: false,
        mostra: ['#171512', '#1E1C18', '#E8622C', '#3FBF9F'],
    },
    {
        id: 'estudi',
        nom: 'Estudi',
        rev: 'paper',
        desc: 'Taller de dia: paper càlid, aire i tipografia editorial. Vores fines en comptes de caixes.',
        paletes: false,
        mostra: ['#F4F2EE', '#FFFFFF', '#B4531B', '#1E7F68'],
    },
    {
        id: 'terminal',
        nom: 'Terminal',
        rev: 'phosphor',
        desc: 'Una sola família tipogràfica, cantonades a zero i fòsfor ambre. Sense resplendor.',
        paletes: false,
        mostra: ['#0C0E0C', '#121512', '#E0A32E', '#5FCF8A'],
    },
];

const CLAU = 'tecla-skin';

/** Tots els ids reals (sense el Clàssic), per netejar classes. */
export const SKIN_IDS = SKINS.map(s => s.id).filter(Boolean);

/** El tema d'un id, o el Clàssic si no existeix. */
export function skinPerId(id) {
    return SKINS.find(s => s.id === (id || null)) || SKINS[0];
}

/** El tema desat a l'últim cop (null = Clàssic). */
export function skinDesat() {
    try {
        const id = localStorage.getItem(CLAU);
        return SKIN_IDS.includes(id) ? id : null;
    } catch { return null; }
}

/**
 * Aplica un tema.
 * @param {string|null} id  l'id del tema, o null per al Clàssic
 * @param {object} [opc]
 * @param {boolean} [opc.desa=true]  si ho ha de recordar
 * @param {Document} [opc.doc]       on aplicar-ho (per a finestres PiP)
 * @returns {object} el tema aplicat
 */
export function aplicaSkin(id, opc = {}) {
    const { desa = true, doc = document } = opc;
    const skin = skinPerId(id);
    const body = doc.body;
    if (!body) return skin;
    SKIN_IDS.forEach(s => body.classList.remove(`skin-${s}`));
    if (skin.id) body.classList.add(`skin-${skin.id}`);
    if (desa && doc === document) {
        try { localStorage.setItem(CLAU, skin.id || ''); } catch { }
    }
    return skin;
}

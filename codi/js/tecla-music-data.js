/**
 * tecla-music-data.js — Constants musicals i de la UI de TECLA
 * Extret d'index.html (dades pures, sense estat compartit).
 * SCALES_JS i companyia són el port de device_files/music_constants.py.
 */

export const ALL_KEYS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'];

export const KEYBOARD_SCALES = [
  [0, "Jònic (Major)"], [1, "Dòric"], [2, "Frigi"], [3, "Lidi"],
  [4, "Mixolidi"], [5, "Eòlic (Menor)"], [6, "Locri"],
  [7, "Pentat. Major"], [8, "Pentat. Menor"],
  [9, "Japonesa"], [10, "Egípcia"], [11, "Aràbiga"], [12, "Hongaresa"],
  [13, "Lídia Dominant"], [14, "Alterada"], [15, "Menor Melòdica"],
  [16, "Raga Bhairav"], [17, "Raga Todi"],
  [18, "Flamenca"], [19, "Catalana"], [20, "Frígia"], [21, "Balcànica"],
  [22, "Tons Sencers"], [23, "Harmònica Major"]
];
export const ARP_PATTERNS = [
  [0, "Amunt"], [1, "Avall"], [2, "Ping-Pong"], [3, "Aleatori"], [4, "Ordre"],
  [5, "Alberti"], [6, "Alberti Alt"], [7, "Vals"], [8, "Broken"], [9, "Trèmolo"],
  [10, "Zig-Zag"], [11, "Block"], [12, "Rolled"], [13, "Octaves"], [14, "Contrari"], [15, "Spread"]
];
export const AVAILABLE_EFFECTS = ['Sustain', 'Pausa', 'Gate', 'Modulation', 'PitchBend', 'Harmonia Negativa'];

export const KB_BTN_FN_META = {
  note:        { name: 'Nota MIDI',     color: '#4a80f0', icon: '♩', multi: true },
  scale:       { name: 'Escala',        color: '#2eb87e', icon: '𝄞' },
  tonality:    { name: 'Tonalitat',     color: '#e09020', icon: '♭' },
  chord:       { name: 'Acords',        color: '#9b59b6', icon: '♪' },
  arp:         { name: 'Arpegiador',    color: '#e74c3c', icon: '≈' },
  octave_down:     { name: 'Oct ▼',         color: '#607080', icon: '▼' },
  octave_up:       { name: 'Oct ▲',         color: '#607080', icon: '▲' },
  neg_harmony:     { name: 'H. Negativa',   color: '#c0392b', icon: '↕' },
  diatonic:        { name: 'Acords Diatòn.', color: '#16a085', icon: 'Δ' },
  latch:           { name: 'Latch (manté)', color: '#d4a017', icon: '∞' },
  looper:          { name: 'Looper',        color: '#e67e22', icon: '⟳' },
  looper_q:        { name: 'Looper ♩ quant.', color: '#d35400', icon: '◈' },
  looper_dub:      { name: 'Overdub',        color: '#c0392b', icon: '➕' },
  voice_lead:      { name: 'Cond. de veus',  color: '#27ae60', icon: '𝆔' },
  modes_layer:     { name: 'Capa de Modes', color: '#888',    icon: '⇄', locked: true },
  stop:            { name: 'Aturar So',     color: '#888',    icon: '■', locked: true },
};
// 'looper_q' s'ha integrat dins 'looper' (auto-quantitza quan l'arp intervé) i ja
// no és assignable: una sola funció de loop. La metadata es conserva per a configs
// antigues que encara el referencien.
export const KB_BTN_FN_DRAGGABLE = ['note','scale','tonality','chord','arp','octave_down','octave_up','neg_harmony','diatonic','latch','looper','looper_dub','voice_lead'];
export const NEG_HARMONY_TYPES = [
  [0, 'Quinta (Levy)', 3.5],
  [1, 'Unisonant',     0.0],
  [2, 'Tercera M',     2.0],
  [3, 'Tercera m',     1.5],
  [4, 'Tritó',          6.0],
  [5, 'Quarta',        2.5],
  [6, 'Sexta M',       4.5],
  [7, 'Sèptima m',     5.5],
];
export const DIATONIC_FNS = [
  { id: 'diatonic',       name: 'Acords Diatònics',        desc: 'Qualitat natural de cada grau (I Maj, ii min, iii min, IV Maj, V Maj, vi min, vii° dim)' },
  { id: 'sec_dominant',  name: 'Dominants Secundàries',   desc: 'V7/x — dominant del grau (arrel+5a, dom7). A7→ii, B7→iii, C7→IV, D7→V, E7→vi' },
  { id: 'sec_leading',   name: 'Sensibles Secundàries',   desc: 'vii°/x — disminuït un semitò per sota de cada grau' },
  { id: 'borrowed',      name: 'Acords Prestats',         desc: 'Acords de la tonalitat paral·lela menor (iv, ♭VI, ♭VII…)' },
  { id: 'subdominant_m', name: 'Subdominant Menor',       desc: 'IV → iv menor — nostàlgia o ombra abans de la tònica' },
  { id: 'tritone_sub',   name: 'Substitució de Tritó',    desc: 'Dominant substituïda per acord a un tritó (jazz, D♭7→C)' },
  { id: 'dominant_chain',name: 'Cadena de Dominants',     desc: 'Tots els acords en dom7 — cascada de gravetat' },
  { id: 'dim_passing',   name: 'Disminuïts de Pas',       desc: 'Acord disminuït un semitò per sota del grau següent (C→C#°→Dm)' },
  { id: 'neapolitan',    name: 'Acords Napol·litans',     desc: '♭II Major — força dramàtica (D♭→G→C)' },
  { id: 'aug6_ger',      name: 'Sisena Aug. Alemanya',    desc: 'Ger+6 → V — dom7 sobre ♭6 (enharmon. Ab7→G en Do M)' },
  { id: 'aug6_it',       name: 'Sisena Aug. Italiana',    desc: 'It+6 → V — tríada augmentada sobre ♭6 sense quinta' },
  { id: 'aug6_fr',       name: 'Sisena Aug. Francesa',    desc: 'Fr+6 → V — ♭6 amb #4 afegit (color impressionista)' },
  { id: 'tonics',        name: 'Tonalitza (7ens)',         desc: 'Acords de 7a diatònica: Imaj7, iim7, iiim7, IVmaj7, V7, vim7, viiø7' },
  { id: 'modulation',    name: 'Modulació',               desc: 'V7 del grau següent — cada botó anticipa la nova tonalitat' },
];

// ══════════════════════════════════════════════════════════════
// FUNCIONS HARMÒNIQUES / ACORDS DIATÒNICS (port de device_files/modes/kbd_notes.py)
// Mantenir SINCRONITZAT amb _apply_harmonic_fn i helpers (test de paritat headless).
// ══════════════════════════════════════════════════════════════
const _MINOR_SCALE_JS = [0, 2, 3, 5, 7, 8, 10];
const _MINOR_QUALITIES_JS = ['m', 'dim', 'Major', 'm', 'm', 'Major', 'Major'];
const _DIATONIC_QUALITIES_JS = {
  0:  ['Major', 'm', 'm', 'Major', 'Major', 'm', 'dim'],
  1:  ['m', 'm', 'Major', 'Major', 'm', 'dim', 'Major'],
  2:  ['m', 'Major', 'Major', 'm', 'dim', 'Major', 'm'],
  3:  ['Major', 'Major', 'm', 'dim', 'Major', 'm', 'm'],
  4:  ['Major', 'm', 'dim', 'Major', 'm', 'm', 'Major'],
  5:  ['m', 'dim', 'Major', 'm', 'm', 'Major', 'Major'],
  6:  ['dim', 'Major', 'm', 'm', 'Major', 'Major', 'm'],
  11: ['Major', 'dim', 'aug', 'm', 'Major', 'Major', 'dim'],
  15: ['m', 'dim', 'Major', 'Major', 'Major', 'dim', 'dim'],
  23: ['Major', 'm', 'aug', 'Major', 'm', 'dim', 'Major'],
};
const _DIATONIC_7TH_JS = {
  0: ['maj7', 'm7', 'm7', 'maj7', '7', 'm7', 'm7b5'],
  1: ['m7', 'm7', 'maj7', '7', 'm7', 'm7b5', 'maj7'],
  2: ['m7', 'maj7', '7', 'm7', 'm7b5', 'maj7', 'm7'],
  3: ['maj7', '7', 'm7', 'm7b5', 'maj7', 'm7', 'm7'],
  4: ['7', 'm7', 'm7b5', 'maj7', 'm7', 'm7', 'maj7'],
  5: ['m7', 'm7b5', 'maj7', 'm7', 'm7', 'maj7', '7'],
  6: ['m7b5', 'maj7', 'm7', 'm7', 'maj7', '7', 'm7'],
};
const _mod = (a, n) => ((a % n) + n) % n;  // mòdul no-negatiu (com Python)

export function diatonicChordType(scaleIntervals, degree, scaleId) {
  const n = scaleIntervals.length;
  const d = _mod(degree, n);
  if (scaleId != null && _DIATONIC_QUALITIES_JS[scaleId]) {
    const q = _DIATONIC_QUALITIES_JS[scaleId];
    return q[d % q.length];
  }
  if (n < 3) return 'Major';
  const root = scaleIntervals[d];
  const t = _mod(scaleIntervals[(d + 2) % n] - root, 12);
  const f = _mod(scaleIntervals[(d + 4) % n] - root, 12);
  if (t === 4 && f === 7) return 'Major';
  if (t === 3 && f === 7) return 'm';
  if (t === 3 && f === 6) return 'dim';
  if (t === 4 && f === 8) return 'aug';
  return 'Major';
}

export function diatonic7thType(scaleIntervals, degree, scaleId) {
  const n = scaleIntervals.length;
  const d = _mod(degree, n);
  if (scaleId != null && _DIATONIC_7TH_JS[scaleId]) {
    const q = _DIATONIC_7TH_JS[scaleId];
    return q[d % q.length];
  }
  if (n < 7) return diatonicChordType(scaleIntervals, d, scaleId);
  const root = scaleIntervals[d];
  const t = _mod(scaleIntervals[(d + 2) % n] - root, 12);
  const f = _mod(scaleIntervals[(d + 4) % n] - root, 12);
  const s = _mod(scaleIntervals[(d + 6) % n] - root, 12);
  if (t === 4 && f === 7 && s === 11) return 'maj7';
  if (t === 4 && f === 7 && s === 10) return '7';
  if (t === 3 && f === 7 && s === 10) return 'm7';
  if (t === 3 && f === 6 && s === 10) return 'm7b5';
  return diatonicChordType(scaleIntervals, d, scaleId);
}

// Retorna [rootSemitoneOffset, chordTypeName | arrayD'intervals]
export function applyHarmonicFn(scaleIntervals, scaleDegree, fn, scaleId) {
  const n = scaleIntervals.length;
  const d = _mod(scaleDegree, n);
  if (fn === 'diatonic' || !fn) return [0, diatonicChordType(scaleIntervals, d, scaleId)];
  if (fn === 'sec_dominant') return [7, '7'];
  if (fn === 'sec_leading') return [-1, 'dim'];
  if (fn === 'borrowed') {
    const d7 = d % 7;
    if (n >= 7) {
      const currentRoot = _mod(scaleIntervals[d], 12);
      let offset = _mod(_MINOR_SCALE_JS[d7] - currentRoot, 12);
      if (offset > 6) offset -= 12;
      return [offset, _MINOR_QUALITIES_JS[d7]];
    }
    return [0, 'm'];
  }
  if (fn === 'subdominant_m') {
    if (d % 7 === 3) return [0, 'm'];
    return [0, diatonicChordType(scaleIntervals, d)];
  }
  if (fn === 'tritone_sub') return [6, '7'];
  if (fn === 'dominant_chain') return [0, '7'];
  if (fn === 'dim_passing') {
    const nextD = (d + 1) % n;
    let nextRoot = scaleIntervals[nextD];
    if (nextD === 0) nextRoot += 12;
    return [(nextRoot - scaleIntervals[d]) - 1, 'dim'];
  }
  if (fn === 'neapolitan') return [-1, 'Major'];
  if (fn === 'aug6_ger') return [-4, '7'];
  if (fn === 'aug6_it') return [-4, [0, 4, 10]];
  if (fn === 'aug6_fr') return [-4, [0, 4, 6, 10]];
  if (fn === 'tonics') return [0, diatonic7thType(scaleIntervals, d, scaleId)];
  if (fn === 'modulation') {
    const nextD = (d + 1) % n;
    let nextRoot = scaleIntervals[nextD];
    if (nextD === 0) nextRoot += 12;
    let offset = (nextRoot - scaleIntervals[d]) + 7;
    if (offset > 12) offset -= 12;
    return [offset, '7'];
  }
  return [0, diatonicChordType(scaleIntervals, d, scaleId)];
}

// ══════════════════════════════════════════════════════════════
// MUSIC CONSTANTS (ported from device_files/music_constants.py)
// ══════════════════════════════════════════════════════════════
export const SCALES_JS = [
  [0, 2, 4, 5, 7, 9, 11], [0, 2, 3, 5, 7, 9, 10], [0, 1, 3, 5, 7, 8, 10], [0, 2, 4, 6, 7, 9, 11],
  [0, 2, 4, 5, 7, 9, 10], [0, 2, 3, 5, 7, 8, 10], [0, 1, 3, 5, 6, 8, 10], [0, 2, 4, 7, 9],
  [0, 3, 5, 7, 10], [0, 1, 4, 6, 7], [0, 2, 5, 7, 9], [0, 1, 4, 5, 7, 8, 11],
  [0, 2, 3, 6, 7, 9, 10], [0, 2, 4, 6, 7, 9, 10], [0, 1, 3, 4, 6, 8, 10], [0, 2, 3, 5, 7, 9, 11],
  [0, 1, 4, 5, 7, 8, 11], [0, 1, 3, 6, 7, 8, 11], [0, 1, 4, 5, 7, 8, 10], [0, 1, 4, 5, 7, 9, 11],
  [0, 1, 3, 5, 7, 8, 10], [0, 1, 4, 5, 7, 8, 11], [0, 2, 4, 6, 8, 10], [0, 2, 4, 5, 7, 8, 11]
];
export const SCALE_NAMES_JS = [
  'Jònic (Major)', 'Dòric', 'Frigi', 'Lidi', 'Mixolidi', 'Eòlic (Minor)', 'Locri',
  'Pentatònica Major', 'Pentatònica Menor', 'Japonesa', 'Egípcia', 'Aràbiga',
  'Hongaresa Menor', 'Lídia Dominant', 'Alterada', 'Menor Melòdica',
  'Raga Bhairav', 'Raga Todi', 'Flamenca', 'Catalana', 'Frígia', 'Balcànica',
  'Tons Sencers', 'Harmònica Major'
];
export const KEY_CIRCLE_JS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'];
export const KEY_OFFSETS_JS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
export const NOTES_JS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
export const ARP_NAMES_JS = {
  0: 'Amunt', 1: 'Avall', 2: 'Ping-Pong', 3: 'Aleatori', 4: 'Ordre Premut',
  5: 'Alberti', 6: 'Alberti Alt', 7: 'Waltz', 8: 'Trencat', 9: 'Tremolo',
  10: 'Zigzag', 11: 'Bloc', 12: 'Rodat', 13: 'Octaves', 14: 'Contrari', 15: 'Spread'
};
export const CHORDS_JS = {
  'Major':[0,4,7],'m':[0,3,7],'7':[0,4,7,10],'maj7':[0,4,7,11],'m7':[0,3,7,10],
  'dim':[0,3,6],'aug':[0,4,8],'sus4':[0,5,7],'sus2':[0,2,7],'m7b5':[0,3,6,10],
  'add9':[0,4,7,14],'6':[0,4,7,9],'add11':[0,4,7,17],'add13':[0,4,7,21],
  '9':[0,4,7,10,14],'9#5':[0,4,8,10,14],'9b5':[0,4,6,10,14],
  '9#11':[0,4,7,10,14,18],'11':[0,4,7,10,14,17],'13':[0,4,7,10,14,21],
  '13b9':[0,4,7,10,13,21],'13#9':[0,4,7,10,15,21],
  '7b9':[0,4,7,10,13],'7#9':[0,4,7,10,15],'7sus4':[0,5,7,10],'7b13':[0,4,7,10,20],
  '69':[0,4,7,9,14],'m9':[0,3,7,10,14],'m11':[0,3,7,10,14,17],
  'm13':[0,3,7,10,14,21],'m69':[0,3,7,9,14]
};
export function _getChordIntervals(name) { return CHORDS_JS[name] || [0,4,7]; }

// ══════════════════════════════════════════════════════════════
// SYSTEM VOLUME HELPER (via server.py local, macOS only)
// ══════════════════════════════════════════════════════════════
export let _sysVolTimer = 0;
export function _setSysVol(midiVal) {
  const now = Date.now();
  if (now - _sysVolTimer < 80) return; // throttle ~12/s
  _sysVolTimer = now;
  const vol = Math.round((midiVal / 127) * 100);
  // URL relativa si la pàgina se serveix des de server.py (funciona amb
  // qualsevol port, també els de fallback 8081, 8082…); absoluta només
  // com a últim recurs si s'obre via file://
  const volUrl = location.protocol.startsWith('http')
    ? '/sys/volume'
    : 'http://127.0.0.1:8080/sys/volume';
  fetch(volUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value: vol })
  }).catch(() => {}); // no-op si el servidor no corre
}

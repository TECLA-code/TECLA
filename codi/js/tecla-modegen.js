/**
 * Generador de modes TECLA — d'una especificació a un mode de CircuitPython.
 *
 * El constructor de modes de l'app recull una especificació i aquí es
 * converteix en un fitxer .py de debò, del mateix estil que els modes de la
 * casa: compacte, sense dependències més enllà de BaseMode, i pensat per a la
 * RAM d'una Pico. L'usuari se l'acaba trobant a modes/ i el pot obrir i
 * modificar — que en un projecte obert és mitja gràcia.
 *
 * L'especificació viatja INCRUSTADA al capdamunt del fitxer com a comentari
 * (# TECLA-SPEC {...}), així el mode es pot tornar a obrir a l'editor més
 * endavant i l'especificació no es perd quan el comparteixes.
 *
 * Convenció de potes: al dispositiu, el pot FÍSIC X és pot_values[1], el Y és
 * pot_values[0] i el Z és pot_values[2] (vegeu modes/kbd_pots.py). Els modes
 * de la casa fan `x, y, z = pot_values` i per tant el seu "X" és, en realitat,
 * el pot físic Y. Aquí es fa bé: el que l'usuari assigna a X va al pot X.
 */

// La teoria harmònica (qualitats diatòniques, dominants secundàries, napolità,
// sisenes augmentades…) no es torna a escriure aquí: és la MATEIXA que fa
// servir la capa teclat, i la família d'acords l'aprofita tal qual.
import { applyHarmonicFn } from './tecla-music-data.js';

// ── Utilitats de noms ──────────────────────────────────────────────────────

// Els apòstrofs i guions tipogràfics es tornen espai: així fan de separador i
// "Cançó de l'Àvia" dona mode_canco_de_l_avia i no mode_canco_de_lavia.
const _ACCENTS = {
  à: 'a', á: 'a', ä: 'a', â: 'a', è: 'e', é: 'e', ë: 'e', ê: 'e', í: 'i', ï: 'i', ì: 'i', î: 'i',
  ò: 'o', ó: 'o', ö: 'o', ô: 'o', ú: 'u', ù: 'u', ü: 'u', û: 'u', ç: 'c', ñ: 'n',
  '’': ' ', '‘': ' ', '´': ' ', '–': ' ', '—': ' ', '·': ' ',
};

/** Treu accents i caràcters estranys: el nom ha de sobreviure a un nom de fitxer. */
export function asciiFold(text) {
  return String(text || '').toLowerCase().replace(/[^\x00-\x7f]/g, ch => _ACCENTS[ch] ?? '');
}

/** "El meu mode" → "ElMeuMode" (nom de classe darrere de "Mode") */
export function className(nom) {
  const parts = asciiFold(nom).split(/[^a-z0-9]+/).filter(Boolean);
  const cap = parts.map(p => p[0].toUpperCase() + p.slice(1)).join('');
  return 'Mode' + (/^[A-Za-z]/.test(cap) ? cap : 'Meu' + cap);
}

/** "El meu mode" → "mode_el_meu_mode.py" */
export function fileName(nom) {
  const slug = asciiFold(nom).split(/[^a-z0-9]+/).filter(Boolean).join('_') || 'meu';
  return `mode_${/^[a-z]/.test(slug) ? slug : 'm' + slug}.py`;
}

/** El nom que veurà l'usuari a la llista de modes (el que va a self.name). */
export function modeName(nom) {
  return String(nom || '').trim().slice(0, 20) || 'Meu';
}

// ── Ajudes de codi ────────────────────────────────────────────────────────

const py = {
  tuple: a => `(${a.join(', ')}${a.length === 1 ? ',' : ''})`,
  tuples: rows => `(\n${rows.map(r => `    ${py.tuple(r)},`).join('\n')}\n)`,
  f: (n, d = 3) => {
    const s = Number(n).toFixed(d).replace(/0+$/, '').replace(/\.$/, '.0');
    return s.startsWith('.') ? '0' + s : s;
  },
};

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// Dinàmica: els tres nivells de la graella → velocity MIDI
const DIN_VEL = [46, 74, 104];

// ── Potes ─────────────────────────────────────────────────────────────────
// Cada funció assignable és un tros de codi que llegeix el seu pot. 'v' és el
// valor 0-127 del pot que li toca.

function potCode(fn, spec, indent = '        ') {
  const i = indent;
  switch (fn) {
    case 'Tempo': {
      const lo = clamp(spec.tempoMin, 20, 240), hi = clamp(spec.tempoMax, 20, 240);
      const min = Math.min(lo, hi), max = Math.max(lo, hi);
      return `${i}# Tempo en negres per minut (${min}-${max}); l'escaló és una nota\n`
           + `${i}self.speed = 60.0 / (${py.f(min)} + (v / 127.0) * ${py.f(max - min)})`;
    }
    case 'Patró':
      return `${i}p = min(len(_PATRONS) - 1, int((v / 128.0) * len(_PATRONS)))\n`
           + `${i}if p != self.pat:\n${i}    self.pat = p\n${i}    self.step = 0\n`
           + `${i}    print("${'%'}s: patro ${'%'}d" % (self.name, p + 1))`;
    case 'Octava':
      return `${i}o = _OCT + int((v / 127.0) * 2.99)\n`
           + `${i}if o != self.octave:\n${i}    self.octave = o`;
    case 'Dinàmica':
      // CONTRAST, no volum. Un multiplicador de velocity no es notava: les
      // dinàmiques ja surten de 46 a 104 i al primer terç del pot ja topaven a
      // 127. Un exponent sí que es nota: en repòs (1.0) sona la dinàmica que
      // vas dibuixar, i girant-lo els passos fluixos es van fonent fins que
      // només queden els forts. És el mateix que fa un pianista.
      return `${i}self.din_k = 1.0 + (v / 127.0) * 2.2`;
    case 'Articulació':
      return `${i}self.artic = _ARTIC + (v / 127.0) * (1.0 - _ARTIC)`;
    case 'Tonalitat':
      // Desplaçament des de la tonalitat que has triat, no des de Do: amb el
      // pot en repòs el mode ha de sonar tal com el vas fer.
      return `${i}k = (_KEY + int((v / 127.0) * 11.99)) % 12\n`
           + `${i}if k != self.key:\n${i}    self.key = k\n`
           + `${i}    print("${'%'}s: ${'%'}s" % (self.name, _KEYS[k]))`;
    case 'Silencis':
      // Aprima la melodia sense tocar el patró: el buit és el recurs més vell
      // que hi ha per fer que una frase respiri. En repòs sonen totes.
      return `${i}self.silenci = (v / 127.0) * 0.85`;
    case 'Sentit':
      return `${i}s = min(3, int((v / 128.0) * 4))\n${i}if s != self.sentit:\n${i}    self.sentit = s`;
    case 'Longitud del patró':
      // Escurça el bucle: amb el pot girat del tot en queda un sol pas, que és
      // el gest hipnòtic de tota la música de patró.
      return `${i}n = len(_GRAUS[self.pat])\n`
           + `${i}self.llarg = n - int((v / 127.0) * (n - 1))`;
    case 'Humanització':
      return `${i}self.human = v / 127.0`;
    case 'Brillantor (CC74)':
      return `${i}self._cc_once(74, v)`;
    case 'Modulació (CC1)':
      return `${i}self._cc_once(1, v)`;
    default:
      return `${i}pass`;
  }
}

/** Els potes que la família melòdica sap fer servir. */
export const MELODIC_POT_FNS = ['Tempo', 'Patró', 'Octava', 'Dinàmica', 'Articulació',
  'Silencis', 'Sentit', 'Longitud del patró', 'Humanització',
  'Tonalitat', 'Brillantor (CC74)', 'Modulació (CC1)', '—'];

// ── Família MELÒDICA ──────────────────────────────────────────────────────

function generateMelodic(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  const n = clamp(spec.passos | 0, 1, 16);
  const escala = (spec.escalaIntervals && spec.escalaIntervals.length ? spec.escalaIntervals : [0, 2, 4, 5, 7, 9, 11]).map(x => x | 0);
  const oct = clamp(spec.octava | 0, 1, 7);
  const key = clamp(spec.tonalitat | 0, 0, 11);
  const artic = clamp((spec.articulacio ?? 55) / 100, .15, 1);
  const v2 = spec.veu2 || {};
  const potX = spec.pots?.x || 'Tempo', potY = spec.pots?.y || 'Patró', potZ = spec.pots?.z || 'Octava';

  // Patrons: graus (−1 = silenci) i dinàmica, tots del mateix llarg
  const patrons = (spec.patrons && spec.patrons.length ? spec.patrons : [{ graus: [0], din: [1] }]);
  const graus = patrons.map(p => Array.from({ length: n }, (_, c) => (p.graus?.[c] ?? -1) | 0));
  const vels = patrons.map(p => Array.from({ length: n }, (_, c) => DIN_VEL[clamp((p.din?.[c] ?? 1) | 0, 0, 2)]));

  const bpm0 = Math.round((clamp(spec.tempoMin, 20, 240) + clamp(spec.tempoMax, 20, 240)) / 2);

  // La segona veu és el contrapunt de Bach i el tintinnabuli de Pärt: segueix
  // la primera a un interval fix, cada tantes notes i amb un retard.
  const v2on = !!v2.on;
  const v2iv = clamp((v2.interval ?? -12) | 0, -24, 24);
  const v2cada = clamp((v2.cada ?? 3) | 0, 1, 16);
  const v2ret = clamp((v2.retard ?? 45) / 100, 0, 1);

  const spec4json = JSON.stringify({ ...spec, cat: 'melodic' });

  return `"""${nom} — mode melòdic fet amb el constructor de TECLA.
X: ${potX}  Y: ${potY}  Z: ${potZ}
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa.
"""
# TECLA-SPEC ${spec4json}
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_ESCALA = ${py.tuple(escala)}
_GRAUS = ${py.tuples(graus)}
_VELS = ${py.tuples(vels)}
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_OCT = ${oct}
_KEY = ${key}
_ARTIC = ${py.f(artic)}
_PATRONS = _GRAUS


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.key = ${key}
        self.octave = _OCT
        self.pat = 0
        self.step = 0
        self.speed = ${py.f(60 / bpm0)}
        self.artic = _ARTIC
        self.din_k = 1.0        # exponent de contrast dinàmic (1.0 = com el vas fer)
        self.next_t = 0.0
        self.off_t = 0.0
        self.playing = -1
${v2on ? `        self.v2_note = -1
        self.v2_on_t = 0.0
        self.v2_off_t = 0.0
        self.v2_pend = -1
        self.notes_fetes = 0
` : ''}        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        self._cc_cache = {}
        self.silenci = 0.0      # quina part dels passos es queden muts
        self.sentit = 0         # 0 endavant · 1 enrere · 2 ping-pong · 3 atzar
        self.llarg = 0          # 0 = el patró sencer
        self.human = 0.0        # quant balla el pols
        self.amunt = True       # fase del ping-pong
        self._llavor = 22222

    def setup(self):
        self.initialized = True
        self.step = 0
        self.next_t = time.monotonic()
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        self._cc_cache = {}
        print("${nom}: %s (oct %d)" % (_KEYS[self.key], self.octave))

    def _cc_once(self, cc, v):
        """Un CC només quan el valor s'ha mogut de debò: el bus MIDI no s'ha
        d'inundar amb el mateix missatge cada volta del bucle."""
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _arrel(self):
        return self.octave * 12 + self.key

    def _nota(self, grau):
        """Grau de l'escala → nota MIDI. Els graus que passen de l'escala
        pugen d'octava, com faria qualsevol músic llegint xifrat."""
        n = len(_ESCALA)
        return self._arrel() + _ESCALA[grau % n] + 12 * (grau // n)

    def _apaga(self):
        if self.playing >= 0:
            self.midi_out.send(self.note_off(self.playing, 0))
            self.playing = -1

    def _atzar(self, n):
        """Congruencial lineal: sense el mòdul random, que a la Pico pesa."""
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _seguent(self, i, n):
        """El pas següent segons el sentit."""
        if self.sentit == 1:                     # enrere
            return (i - 1) % n
        if self.sentit == 2:                     # ping-pong
            if self.amunt:
                if i + 1 >= n:
                    self.amunt = False
                    return n - 2 if n > 1 else 0
                return i + 1
            if i - 1 < 0:
                self.amunt = True
                return 1 if n > 1 else 0
            return i - 1
        if self.sentit == 3:                     # atzar
            return self._atzar(n)
        return (i + 1) % n

    def _toca(self, now):
        graus = _GRAUS[self.pat]
        vels = _VELS[self.pat]
        n = len(graus)
        # Longitud: en repòs el patró sencer; girant el pot, només els primers
        if 0 < self.llarg < n:
            n = self.llarg
        i = self.step % n
        self.step = self._seguent(self.step % n, n)
        g = graus[i]
        if g < 0:                       # silenci: el buit també és música
            return
        # Silencis: el pas existeix però aquesta volta no sona
        if self.silenci > 0.0 and self._atzar(1000) < int(self.silenci * 1000):
            return
        nota = self._nota(g)
        nota = self.negharm(nota, self._arrel() % 12)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        # Contrast: amb din_k = 1 surt la dinàmica dibuixada; per damunt, els
        # passos fluixos cauen molt més que els forts.
        vel = int(127.0 * (vels[i] / 127.0) ** self.din_k)
        vel = 10 if vel < 10 else (127 if vel > 127 else vel)
        self._apaga()
        self.midi_out.send(self.note_on(nota, vel))
        self.playing = nota
        self.off_t = now + self.speed * self.artic
${v2on ? `        self.notes_fetes += 1
        if self.notes_fetes % ${v2cada} == 0:
            n2 = nota + (${v2iv})
            if 24 <= n2 <= 108:
                self.v2_pend = n2
                self.v2_on_t = now + self.speed * ${py.f(v2ret)}
` : ''}
    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()
        self.poll_negharm(button_states, pz)

        if self.playing >= 0 and now >= self.off_t:
            self._apaga()
${v2on ? `        if self.v2_pend >= 0 and now >= self.v2_on_t:
            self.midi_out.send(self.note_on(self.v2_pend, 60))
            self.v2_note = self.v2_pend
            self.v2_pend = -1
            self.v2_off_t = now + self.speed * ${py.f(Math.max(.3, artic))} * 2
        if self.v2_note >= 0 and now >= self.v2_off_t:
            self.midi_out.send(self.note_off(self.v2_note, 0))
            self.v2_note = -1
` : ''}
        # ── Els tres potes, tal com s'han assignat ──
        v = px
${potCode(potX, spec)}
        v = py_
${potCode(potY, spec)}
        if not self.neg_active:      # Z congelada mentre tria l'eix d'harmonia
            v = pz
${potCode(potZ, spec, '            ')}

        if now >= self.next_t:
            self._toca(now)
            # Humanització: el pas següent es desplaça una mica, com un músic
            # que no toca damunt del clic. Va al RELLOTGE, no a la nota, així
            # el desviament no s'acumula.
            d = 0.0
            if self.human > 0.0:
                d = (self._atzar(2000) / 1000.0 - 1.0) * self.human * self.speed * 0.3
            self.next_t = now + self.speed + d

        # Doble clic a qualsevol tecla: tonalitat següent
        for i in range(min(len(button_states), 16)):
            if i == 15:
                continue
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                if 0.05 < (now - self.last_rel[i]) < 0.4:
                    self.last_rel[i] = 0.0
                    self.key = (self.key + 1) % 12
                    self.step = 0
                    print("${nom}: %s" % _KEYS[self.key])
                else:
                    self.last_rel[i] = now
            self.last_btn[i] = cur

        return {'key': _KEYS[self.key], 'oct': self.octave, 'pat': self.pat + 1,
                'neg': self.neg_active}

    def cleanup(self):
        self._apaga()
${v2on ? `        if self.v2_note >= 0:
            self.midi_out.send(self.note_off(self.v2_note, 0))
            self.v2_note = -1
        self.v2_pend = -1
` : ''}        self.stop_tracked_notes()
        for cc in (1, 74, 64, 123, 120):
            try:
                self.midi_out.send(ControlChange(cc, 0))
            except Exception:
                pass
`;
}

// ── Família RÍTMICA ───────────────────────────────────────────────────────
// Els nou modes rítmics del firmware són tots la mateixa cosa: una graella de
// 16 passos amb unes quantes pistes de percussió, una línia de baix per graus,
// un pas que dura 60/bpm/4 (semicorxeres) i un pot que va tirant capes enrere
// per fer el breakdown. Això és exactament el que es genera aquí.

function potCodeRitmic(fn, spec, capes, indent = '        ') {
  const i = indent;
  switch (fn) {
    case 'Tempo': {
      const lo = clamp(spec.bpmMin, 40, 240), hi = clamp(spec.bpmMax, 40, 240);
      const min = Math.min(lo, hi), max = Math.max(lo, hi);
      return `${i}# Tempo de negra (${min}-${max}); cada pas és una semicorxera\n`
           + `${i}b = ${py.f(min)} + (v / 127.0) * ${py.f(max - min)}\n`
           + `${i}if b < self.bpm - 0.3 or b > self.bpm + 0.3:\n`
           + `${i}    self.bpm = b\n${i}    self._calc()`;
    }
    case 'Patró':
      return `${i}p = min(len(_GRAELLES) - 1, int((v / 128.0) * len(_GRAELLES)))\n`
           + `${i}if p != self.pat:\n${i}    self.pat = p\n${i}    self.step = 0\n`
           + `${i}    print("${'%'}s: patro ${'%'}d" % (self.name, p + 1))`;
    case 'Capes (breakdown)':
      // Al mínim hi són totes (el ritme tal com el vas fer) i girant el pot
      // se'n van retirant: abans el pot en repòs deixava només la capa 0 i el
      // ritme sonava pelat només d'engegar.
      return `${i}c = ${capes} - int((v / 127.0) * ${py.f(capes + .99, 2)})\n`
           + `${i}c = 0 if c < 0 else c\n`
           + `${i}if c != self.capa:\n${i}    self.capa = c\n`
           + `${i}    print("${'%'}s: capa ${'%'}d/${capes}" % (self.name, c))`;
    case 'Swing':
      return `${i}self.swing = _SWING + (v / 127.0) * (0.34 - _SWING)`;
    case 'Densitat':
      // Aprima la graella sense esborrar-la: cada cop té una probabilitat de
      // no sonar. En repòs sona tot el que has dibuixat.
      return `${i}self.dens = (v / 127.0) * 0.8`;
    case 'Accent':
      // Contrast entre el temps fort i la resta. En repòs, la força tal com
      // l'has posada; girant-lo, els contratemps es fonen.
      return `${i}self.accent = (v / 127.0) * 0.85`;
    case 'Repicons':
      // Redoblament: un cop pot repetir-se dins del mateix pas. És el gest de
      // la caixa del drum'n'bass i del trap.
      return `${i}self.repic = (v / 127.0) * 0.5`;
    case 'Longitud del compàs': {
      // Escurça el bucle: del compàs sencer fins a un sol pas.
      const np = clamp(spec.passos ?? 16, 1, 64);
      return `${i}self.llarg = ${np} - int((v / 127.0) * ${np - 1})`;
    }
    case 'Humanització':
      return `${i}self.human = v / 127.0`;
    case 'Octava del baix':
      return `${i}o = _OCT_BAIX + int((v / 127.0) * 2.99)\n`
           + `${i}if o != self.oct_baix:\n${i}    self.oct_baix = o`;
    case 'Brillantor (CC74)':
      return `${i}self._cc_once(74, v)`;
    default:
      return `${i}pass`;
  }
}

/** Els potes que la família rítmica sap fer servir. */
export const RITMIC_POT_FNS = ['Tempo', 'Patró', 'Capes (breakdown)', 'Swing',
  'Densitat', 'Accent', 'Repicons', 'Longitud del compàs', 'Humanització',
  'Octava del baix', 'Brillantor (CC74)', '—'];

function generateRhythmic(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  const n = clamp(spec.passos | 0, 4, 32);
  const escala = (spec.escalaIntervals && spec.escalaIntervals.length ? spec.escalaIntervals : [0, 2, 4, 5, 7, 9, 11]).map(x => x | 0);
  const key = clamp(spec.tonalitat | 0, 0, 11);
  const octBaix = clamp(spec.baixOctava | 0, 0, 6);
  const swing0 = clamp((spec.swing ?? 0) / 100, 0, .34);
  const potX = spec.pots?.x || 'Tempo', potY = spec.pots?.y || 'Patró', potZ = spec.pots?.z || 'Capes (breakdown)';

  // Pistes de percussió: nota MIDI, nivell de breakdown i dinàmica pròpies
  const pistes = (spec.pistes && spec.pistes.length ? spec.pistes : [{ id: 'bombo', nota: 36, capa: 0, vel: 105 }]);
  const notes = pistes.map(p => clamp(p.nota | 0, 0, 127));
  const capesPista = pistes.map(p => clamp(p.capa | 0, 0, 3));
  const velsPista = pistes.map(p => clamp(p.vel | 0, 1, 127));
  const capaMax = Math.max(0, ...capesPista);

  const patrons = (spec.patrons && spec.patrons.length ? spec.patrons : [{ graella: {}, baix: [] }]);
  // Una fila de bytes per pista i patró: 1 = sona. És com ho desen els modes
  // de la casa (bytes en lloc de llistes) per no cruixir la RAM de la Pico.
  const graelles = patrons.map(pat => pistes.map(p => {
    const fila = (pat.graella && pat.graella[p.id]) || [];
    return Array.from({ length: n }, (_, c) => (fila[c] ? 1 : 0));
  }));
  const baixos = patrons.map(pat => Array.from({ length: n }, (_, c) => ((pat.baix && pat.baix[c] != null ? pat.baix[c] : -1) | 0)));
  const teBaix = !!spec.baixOn && baixos.some(b => b.some(g => g >= 0));

  const bpm0 = Math.round((clamp(spec.bpmMin, 40, 240) + clamp(spec.bpmMax, 40, 240)) / 2);
  const spec4json = JSON.stringify({ ...spec, cat: 'ritmic' });

  const filesBytes = graelles.map(g =>
    `    (\n${g.map(f => `        bytes(${py.tuple(f)}),`).join('\n')}\n    ),`).join('\n');

  return `"""${nom} — mode rítmic fet amb el constructor de TECLA.
X: ${potX}  Y: ${potY}  Z: ${potZ}
${n} passos · ${pistes.length} pistes de percussió${teBaix ? ' · línia de baix' : ''}
"""
# TECLA-SPEC ${spec4json}
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_ESCALA = ${py.tuple(escala)}
_NOTES = ${py.tuple(notes)}          # nota MIDI de cada pista
_CAPES = ${py.tuple(capesPista)}     # a quin nivell de breakdown entra cada pista
_VELS = ${py.tuple(velsPista)}       # dinàmica de cada pista
_GRAELLES = (
${filesBytes}
)
_BAIX = ${py.tuples(baixos)}
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_OCT_BAIX = ${octBaix}
_SWING = ${py.f(swing0)}
_PERC_CH = 9        # canal 10 (percussió General MIDI)
_BAIX_CH = 0
_GATE = 0.055       # què dura un cop de percussió
_GATE_BAIX = 0.45   # el baix dura una fracció del pas


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.bpm = ${py.f(bpm0)}
        self.step = 0
        self.pat = 0
        self.capa = ${capaMax}
        self.swing = _SWING
        self.dens = 0.0        # quins cops es queden muts
        self.accent = 0.0      # contrast entre el temps fort i la resta
        self.repic = 0.0       # probabilitat de redoblar un cop
        self.llarg = 0         # 0 = el compàs sencer
        self.human = 0.0       # quant balla el pols
        self._llavor = 31337
        self.key = ${key}
        self.oct_baix = _OCT_BAIX
        self.step_dur = 0.0
        self.next_step = 0.0
        self.pend = []          # note-offs pendents: [nota, canal, quan]
        self._cc_cache = {}

    def setup(self):
        self.initialized = True
        self.step = 0
        self._calc()
        self.next_step = time.monotonic()
        self.pend = []
        self._cc_cache = {}
        self._panic()
        print("${nom}: %d BPM (capa %d/${capaMax})" % (int(self.bpm), self.capa))

    def _calc(self):
        self.step_dur = 60.0 / self.bpm / 4.0      # una semicorxera

    def _cc_once(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _panic(self):
        for ch in (_PERC_CH, _BAIX_CH):
            try:
                m = ControlChange(123, 0)
                m.channel = ch
                self.midi_out.send(m)
            except Exception:
                pass

    def _allibera(self, now, totes=False):
        """Tanca els cops que ja han fet el seu temps."""
        if not self.pend:
            return
        queden = []
        for p in self.pend:
            if totes or now >= p[2]:
                self.send_note_off(p[0], 0, p[1])
            else:
                queden.append(p)
        self.pend = queden

    def _cop(self, nota, vel, canal, dura, now):
        self.send_note_on(nota, vel, canal)
        self.pend.append([nota, canal, now + dura])

    def _atzar(self, n):
        """Congruencial lineal: sense el mòdul random, que a la Pico pesa."""
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _fire(self, now):
        graella = _GRAELLES[self.pat]
        i = self.step
        # Accent: el temps fort es queda i la resta es va fonent. Els passos
        # múltiples de 4 són els forts (cada negra d'un compàs de 4/4).
        k_ac = 1.0
        if self.accent > 0.0 and (i % 4) != 0:
            k_ac = 1.0 - self.accent
        for t in range(len(_NOTES)):
            if _CAPES[t] > self.capa:      # capa retirada: aquesta pista calla
                continue
            if graella[t][i]:
                # Densitat: el cop hi és, però aquesta volta pot no sonar
                if self.dens > 0.0 and self._atzar(1000) < int(self.dens * 1000):
                    continue
                vel = int(_VELS[t] * k_ac)
                vel = 1 if vel < 1 else (127 if vel > 127 else vel)
                self._cop(_NOTES[t], vel, _PERC_CH, _GATE, now)
                # Repicons: un redoblament dins del mateix pas
                if self.repic > 0.0 and self._atzar(1000) < int(self.repic * 1000):
                    self.pend.append([_NOTES[t], _PERC_CH, now + self.step_dur * 0.24])
                    self._cop(_NOTES[t], max(1, vel - 18), _PERC_CH, _GATE,
                              now + self.step_dur * 0.5)
${teBaix ? `        g = _BAIX[self.pat][i]
        if g >= 0:
            ln = len(_ESCALA)
            nota = self.oct_baix * 12 + self.key + _ESCALA[g % ln] + 12 * (g // ln)
            if 0 <= nota <= 127:
                self._cop(nota, 96, _BAIX_CH, self.step_dur * _GATE_BAIX, now)
` : ''}
    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()

        self._allibera(now)

        # ── Els tres potes, tal com s'han assignat ──
        v = px
${potCodeRitmic(potX, spec, capaMax)}
        v = py_
${potCodeRitmic(potY, spec, capaMax)}
        v = pz
${potCodeRitmic(potZ, spec, capaMax)}

        if now >= self.next_step:
            self._fire(now)
            # Swing: els passos parells s'allarguen i els senars s'escurcen, i
            # el compàs continua durant el mateix
            k = 1.0 + (self.swing if (self.step % 2) == 0 else -self.swing)
            # Longitud: en repòs el compàs sencer; girant el pot, més curt
            n_pas = ${n}
            if 0 < self.llarg < n_pas:
                n_pas = self.llarg
            self.step = (self.step + 1) % n_pas
            d = 0.0
            if self.human > 0.0:
                d = (self._atzar(2000) / 1000.0 - 1.0) * self.human * self.step_dur * 0.3
            self.next_step = now + self.step_dur * k + d

        return {'bpm': int(self.bpm), 'pat': self.pat + 1, 'capa': self.capa,
                'key': _KEYS[self.key]}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
        self._panic()
`;
}

// ── Família DRONE ─────────────────────────────────────────────────────────
// Els nou drones del firmware fan tots el mateix: mantenen un acord i li posen
// MOVIMENT amb un CC. El que canvia és la forma d'aquest moviment — el gate de
// ToDrone és una ona quadrada i l'ale d'arquet de ToArc és un triangle — i per
// això aquí és una sola cosa amb la forma triable.

/** Formes de moviment que el drone sap fer. */
export const DRONE_FORMES = ['Cap', 'Gate', 'Arc', 'Respiració'];

/**
 * Les nou QUALITATS d'acord: el mateix catàleg que els botons del formulari, i
 * el que recorre el pot de 'Qualitat' en nou trams de 0 a 127.
 */
export const DRONE_QUALITATS = [
  ['Quinta', [0, 7]], ['Major', [0, 4, 7]], ['Menor', [0, 3, 7]],
  ['Dom7', [0, 4, 7, 10]], ['Maj7', [0, 4, 7, 11]], ['Sus2', [0, 2, 7]],
  ['Sus4', [0, 5, 7]], ['Dim', [0, 3, 6]], ['Obert', [0, 7, 12, 19]],
];

/** Els potes que la família drone sap fer servir. */
export const DRONE_POT_FNS = ['Moviment (velocitat)', 'Tipus d\'acord', 'Qualitat', 'Octava',
  'Brillantor', 'Profunditat', 'Respiració de les veus', 'Dispersió de les veus',
  'Velocitat de la respiració', 'Modulació (CC1)', 'Tonalitat', '—'];

function potCodeDrone(fn, spec, nAcords, indent = '        ') {
  const i = indent;
  switch (fn) {
    case 'Moviment (velocitat)': {
      const lo = clamp(spec.movPeriode ?? 2, .05, 12);
      return `${i}# Del període que has posat cap a més ràpid (fins a 0.06 s)\n`
           + `${i}self.mov_per = _PER - (v / 127.0) * ${py.f(Math.max(.01, lo - .06))}`;
    }
    case "Tipus d'acord":
      return `${i}a = min(${nAcords - 1}, int((v / 128.0) * ${nAcords}))\n`
           + `${i}if self._tram('acord', a, v):\n${i}    self.acord = a\n${i}    self._arrenca()`;
    case 'Qualitat':
      // El recorregut del pot en NOU trams, un per qualitat. Comença per la que
      // coincideix amb el teu primer banc (per defecte la quinta), o sigui que
      // en repòs sona el que has muntat i girant-lo recorre les altres vuit.
      return `${i}q = (_QUAL0 + min(8, int((v / 128.0) * 9))) % 9\n`
           + `${i}if self._tram('qual', q, v):\n${i}    self.qual = q\n`
           + `${i}    print("${'%'}s: ${'%'}s" % (self.name, _QUAL_NOMS[q]))\n`
           + `${i}    self._arrenca()`;
    case 'Octava':
      return `${i}o = _OCT + int((v / 127.0) * 2.99)\n`
           + `${i}if self._tram('oct', o, v):\n${i}    self.octave = o\n${i}    self._arrenca()`;
    case 'Brillantor':
      return `${i}b = _VEL + int((v / 127.0) * (127 - _VEL))\n`
           + `${i}if b < self.vel - 4 or b > self.vel + 4:\n`
           + `${i}    self.vel = b\n${i}    self._arrenca()`;
    case 'Profunditat':
      return `${i}self.baix = _BAIX - int((v / 127.0) * _BAIX)`;
    case 'Respiració de les veus':
      return `${i}self.resp_prof = _RESP_PROF + (v / 127.0) * (1.0 - _RESP_PROF)`;
    case 'Dispersió de les veus':
      // Com de diferents són els períodes de cada veu. A zero respiren totes
      // juntes (un trèmolo); obrint-lo es desfasen i allò batega sol.
      return `${i}d = _RESP_DISP + (v / 127.0) * (1.0 - _RESP_DISP)\n`
           + `${i}if d < self.resp_disp - 0.02 or d > self.resp_disp + 0.02:\n`
           + `${i}    self.resp_disp = d\n${i}    self._reparteix()`;
    case 'Velocitat de la respiració':
      return `${i}self.resp_per = _RESP_PER - (v / 127.0) * ${py.f(Math.max(.05, (clamp(spec.respiraPer ?? 6, .2, 40)) - 0.4))}\n`
           + `${i}self._reparteix()`;
    case 'Modulació (CC1)':
      return `${i}self._cc_once(1, v)`;
    case 'Tonalitat':
      return `${i}k = int((v / 127.0) * 11.99)\n`
           + `${i}if self._tram('to', k, v):\n${i}    self.key = k\n${i}    self._arrenca()`;
    default:
      return `${i}pass`;
  }
}

function generateDrone(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  const key = clamp(spec.tonalitat | 0, 0, 11);
  const oct = clamp(spec.octava | 0, 0, 7);
  const vel = clamp(spec.brillantor ?? 80, 1, 127);
  const forma = DRONE_FORMES.includes(spec.moviment) ? spec.moviment : 'Cap';
  const cc = clamp(spec.movCC ?? 11, 0, 127);
  const per = clamp(spec.movPeriode ?? 2, .05, 12);
  const prof = clamp(spec.movProfunditat ?? 100, 0, 100);
  const duty = clamp(spec.movDuty ?? 50, 5, 95) / 100;
  // Respiració PER VEU: el que separa un acord sostingut d'una atmosfera. És el
  // mecanisme del mode Dinamo de la casa — cada veu té el seu propi cicle i la
  // seva pròpia fase, i es RE-ATACA quan el volum s'ha mogut prou. Amb totes les
  // veus juntes seria un trèmolo; desfasades, allò no es queda mai quiet.
  const respOn = !!spec.respiraVeus;
  const respPer = clamp(spec.respiraPer ?? 6, .2, 40);
  const respDisp = clamp(spec.respiraDisp ?? 45, 0, 100) / 100;
  const respProf = clamp(spec.respiraProf ?? 65, 0, 100) / 100;
  const potX = spec.pots?.x || 'Moviment (velocitat)';
  const potY = spec.pots?.y || "Tipus d'acord";
  const potZ = spec.pots?.z || 'Octava';

  // Acords: cada banc és una llista d'intervals en semitons des de la
  // fonamental. Sense cap veu, un drone no és res: cau a la fonamental.
  let acords = (spec.acords && spec.acords.length ? spec.acords : [[0, 7]])
    .map(a => {
      const ivs = [...new Set((a || []).map(x => clamp(x | 0, 0, 36)))].sort((p, q) => p - q);
      return ivs.length ? ivs : [0];
    });
  // Quina qualitat és el teu primer banc, si n'és cap: el pot de 'Qualitat'
  // arrenca d'aquí perquè en repòs soni el que has muntat.
  const qual0 = Math.max(0, DRONE_QUALITATS.findIndex(([, iv]) =>
    iv.length === acords[0].length && iv.every((x, k) => x === acords[0][k])));
  const spec4json = JSON.stringify({ ...spec, cat: 'drone' });

  // El valor del CC segons la forma. Es fa sense math: el triangle surt de la
  // fase i la respiració n'és el suavitzat (smoothstep), que en una Pico
  // costa molt menys que un cosinus.
  const formaCode = {
    'Cap': '        return -1',
    'Gate': `        return _ALT if self.fase < ${py.f(duty)} else self.baix`,
    'Arc': `        t = 1.0 - abs(2.0 * self.fase - 1.0)
        return self.baix + int((_ALT - self.baix) * t)`,
    'Respiració': `        t = 1.0 - abs(2.0 * self.fase - 1.0)
        t = t * t * (3.0 - 2.0 * t)
        return self.baix + int((_ALT - self.baix) * t)`,
  }[forma];

  return `"""${nom} — drone fet amb el constructor de TECLA.
X: ${potX}  Y: ${potY}  Z: ${potZ}
Moviment: ${forma}${forma === 'Cap' ? '' : ` sobre CC${cc}`}
Doble clic a qualsevol tecla: canvi de tonalitat.
Mantenir premut el botó 16: harmonia negativa.
"""
# TECLA-SPEC ${spec4json}
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_ACORDS = ${py.tuples(acords)}
_QUALS = ${py.tuples(DRONE_QUALITATS.map(([, iv]) => iv))}
_QUAL_NOMS = ${py.tuple(DRONE_QUALITATS.map(([n]) => `'${n}'`))}
_QUAL0 = ${qual0}       # la qualitat que coincideix amb el teu primer banc
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_OCT = ${oct}
_MOV_CC = ${cc}
_VEL = ${vel}
_PER = ${py.f(per)}
_BAIX = ${127 - Math.round(127 * prof / 100)}
_ALT = 127          # cim del moviment
_RESP = ${respOn ? 'True' : 'False'}
_RESP_PER = ${py.f(respPer)}
_RESP_DISP = ${py.f(respDisp)}
_RESP_PROF = ${py.f(respProf)}
_RESP_PAS = 6       # quant s'ha de moure el volum d'una veu per re-atacar-la
_HIST = 3           # histèresi del pot, en unitats de 0-127 (vegeu _tram)
_MIN_NOTA = 12
_MAX_NOTA = 108


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.key = ${key}
        self.octave = _OCT
        self.acord = 0
        self.qual = -1          # −1 = manen els bancs; 0..8 = una qualitat
        self.vel = _VEL
        self.vel_son = _VEL     # amb quin volum s'han atacat les notes que sonen
        self._trams = {}        # histèresi dels potes que trien per trams
        # Moviment: el període NO es diu 'speed' a propòsit — un drone no té
        # pols de notes i la pantalla no li ha de treure cap BPM.
        self.mov_per = _PER
        self.baix = _BAIX
        self.fase = 0.0
        self.ultim_cc = -1
        self.sonant = []
        self.resp_per = _RESP_PER
        self.resp_disp = _RESP_DISP
        self.resp_prof = _RESP_PROF
        self.veu_fase = []      # fase de la respiració de cada veu
        self.veu_per = []       # i el seu període propi
        self.veu_vel = []       # últim volum enviat
        self.veu_on = []        # sona ara mateix?
        self.expr = 127
        self.t = 0.0
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        self._cc_cache = {}

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.fase = 0.0
        self.ultim_cc = -1
        self.last_rel = [0.0] * 16
        self.last_btn = [False] * 16
        self._cc_cache = {}
        self._arrenca()

    def _cc_once(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _calla(self):
        for n in self.sonant:
            self.send_note_off(n, 0)
        self.sonant = []

    def _tram(self, k, i, v):
        """L'índex de tram 'i' (de la clau 'k') és nou, amb HISTÈRESI del pot?

        Un pot que tria per trams —quin acord, quina qualitat, quina octava—
        té un límit entre tram i tram, i just a sobre el valor tremola (±1 al
        conversor del dispositiu, i també amb el ratolí). Sense histèresi
        l'acord salta endavant i enrere a cada volta del bucle: cent re-atacs
        per segon apilats, que és exactament el que se sentia com un retall.
        Cal haver-se mogut _HIST unitats des de l'últim canvi per tornar-ne a
        fer un."""
        vell, vell_v = self._trams.get(k, (-1, -999))
        if i == vell or abs(v - vell_v) < _HIST:
            return False
        self._trams[k] = (i, v)
        return True

    def _reparteix(self, fases=None):
        """Dona a cada veu el seu període i la seva fase.

        Les fases es reparteixen amb el nombre auri (0,618…): és la manera de
        deixar-les el més separades possible passi el que passi amb el nombre de
        veus, i com que no fa servir l'atzar, el mode sona igual cada vegada.

        'fases' hi porta les fases que s'han de conservar (−1 = reparteix-la):
        una veu que ja sonava no ha de tornar a començar a respirar de zero."""
        n = len(self.sonant)
        if fases is None and len(self.veu_fase) == n:
            fases = self.veu_fase
        self.veu_per = []
        noves = []
        for k in range(n):
            # De resp_per fins a resp_per·(1+disp): períodes irracionals entre
            # ells, així el conjunt no torna a coincidir mai del tot.
            self.veu_per.append(self.resp_per * (1.0 + self.resp_disp * (k / float(n if n > 1 else 1))))
            f = fases[k] if (fases is not None and k < len(fases)) else -1.0
            noves.append(f if f >= 0.0 else (k * 0.6180339887) % 1.0)
        self.veu_fase = noves

    def _arrenca(self):
        """Torna a muntar l'acord sostingut (en canviar octava, acord o to).

        NOMÉS toca el que canvia: una nota que ja sonava i que l'acord nou
        també té es queda sonant tal com està, sense note_off ni re-atac. Abans
        es callava tot i s'atacava tot de nou, i cada canvi d'acord sumava el
        release de l'acord vell amb l'atac del nou —el doble de veus a l'hora, i
        totes en fase— que és el que feia el cop. Així el canvi és conducció de
        veus: només se sent el que de debò s'ha mogut."""
        arrel = self.octave * 12 + self.key
        veus = _QUALS[self.qual] if self.qual >= 0 else _ACORDS[self.acord]
        noves = []
        for iv in veus:
            n = self.negharm(arrel + iv, arrel % 12)
            if _MIN_NOTA <= n <= _MAX_NOTA and n not in noves:
                noves.append(n)
        if not noves:
            return
        # Un canvi de volum sí que s'ha de sentir: llavors re-ataca tothom.
        reatac = abs(self.vel - self.vel_son) > 3
        for n in self.sonant:
            if reatac or n not in noves:
                self.send_note_off(n, 0)
        fases, vels, ons = [], [], []
        for n in noves:
            k = self.sonant.index(n) if n in self.sonant else -1
            if k >= 0 and not reatac:
                fases.append(self.veu_fase[k] if k < len(self.veu_fase) else -1.0)
                vels.append(self.veu_vel[k] if k < len(self.veu_vel) else self.vel)
                ons.append(self.veu_on[k] if k < len(self.veu_on) else True)
            else:
                self.send_note_on(n, self.vel)
                fases.append(-1.0)
                vels.append(self.vel)
                ons.append(True)
        self.sonant = noves
        self.veu_vel = vels
        self.veu_on = ons
        self.vel_son = self.vel
        self._reparteix(fases)
        print("${nom}: %s%d (%d veus)" % (_KEYS[self.key], self.octave, len(self.sonant)))

    def _respira(self, dt):
        """Cada veu puja i baixa al seu ritme, i es RE-ATACA quan el volum s'ha
        mogut prou. El re-atac és el que fa que això no sigui un acord quiet amb
        un CC per sobre sinó una atmosfera que batega: és el que fa el Dinamo."""
        for k in range(len(self.sonant)):
            self.veu_fase[k] = (self.veu_fase[k] + dt / self.veu_per[k]) % 1.0
            t = 1.0 - abs(2.0 * self.veu_fase[k] - 1.0)
            t = t * t * (3.0 - 2.0 * t)                  # smoothstep: sense math
            v = int(self.vel * (1.0 - self.resp_prof + self.resp_prof * t))
            n = self.sonant[k]
            if v < 8:
                if self.veu_on[k]:
                    self.send_note_off(n, 0)
                    self.veu_on[k] = False
            elif (not self.veu_on[k]) or abs(v - self.veu_vel[k]) > _RESP_PAS:
                # Apagar-la abans de tornar-la a atacar: un NoteOn repetit sense
                # NoteOff pel mig el sintetitzador el pot apilar i deixar la nota
                # penjada. (El Dinamo de la casa fa exactament això.)
                if self.veu_on[k]:
                    self.send_note_off(n, 0)
                self.send_note_on(n, v)
                self.veu_on[k] = True
                self.veu_vel[k] = v

    def _valor_mov(self):
${formaCode}

    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()
        dt = now - self.t
        self.t = now
        neg_abans = self.neg_active
        self.poll_negharm(button_states, pz)
        if self.neg_active != neg_abans:
            self._arrenca()          # el reflex canvia les alçades de l'acord

        # ── Els tres potes, tal com s'han assignat ──
        v = px
${potCodeDrone(potX, spec, acords.length)}
        v = py_
${potCodeDrone(potY, spec, acords.length)}
        if not self.neg_active:      # Z congelada mentre tria l'eix d'harmonia
            v = pz
${potCodeDrone(potZ, spec, acords.length, '            ')}

        # ── Respiració de cada veu (l'atmosfera) ──
        if _RESP and self.sonant:
            self._respira(dt)

        # ── Moviment sobre el CC ──
        if self.mov_per > 0.01:
            self.fase = (self.fase + dt / self.mov_per) % 1.0
        val = self._valor_mov()
        if val >= 0 and (val < self.ultim_cc - 1 or val > self.ultim_cc + 1):
            self.ultim_cc = val
            self.expr = val
            try:
                self.midi_out.send(ControlChange(_MOV_CC, val))
            except Exception:
                pass

        # Doble clic a qualsevol tecla: tonalitat següent
        for i in range(min(len(button_states), 16)):
            if i == 15:
                continue
            cur = bool(button_states[i])
            if self.last_btn[i] and not cur:
                if 0.05 < (now - self.last_rel[i]) < 0.4:
                    self.last_rel[i] = 0.0
                    self.key = (self.key + 1) % 12
                    self._arrenca()
                else:
                    self.last_rel[i] = now
            self.last_btn[i] = cur

        return {'key': _KEYS[self.key], 'oct': self.octave,
                'acord': self.acord + 1, 'veus': len(self.sonant),
                'expr': self.expr, 'vives': sum(1 for o in self.veu_on if o)}

    def cleanup(self):
        self._calla()
        self.stop_tracked_notes()
        for c, val in ${(() => {
          // Els CC que es restauren en marxar, sense repeticions: l'expressió i
          // el volum tornen a ple i la resta a zero.
          const vist = new Set();
          const parells = [];
          for (const c of [cc, 1, 11, 64, 123, 120]) {
            if (vist.has(c)) continue;
            vist.add(c);
            parells.push(`(${c}, ${c === 11 || c === 7 ? 127 : 0})`);
          }
          return `(${parells.join(', ')})`;
        })()}:
            try:
                self.midi_out.send(ControlChange(c, val))
            except Exception:
                pass
`;
}

// ── Família TEXTURA ───────────────────────────────────────────────────────
// Els onze modes de soroll i textura del firmware són tots la mateixa recepta:
// esdeveniments curts que salten a l'atzar dins d'una zona de notes, amb una
// densitat que mana, opcionalment un fons greu sostingut a sota i un filtre
// que escombra. El que els distingeix és on cauen els números.

/** Els potes que la família textura sap fer servir. */
export const TEXTURA_POT_FNS = ['Densitat', 'Zona de notes', 'Dispersió', 'Atenuació',
  'Durada del gra', 'Irregularitat', 'Deriva de la zona', 'Ràfegues',
  'Filtre (velocitat)', 'Fons greu', 'Modulació (CC1)', '—'];

function potCodeTextura(fn, spec, indent = '        ') {
  const i = indent;
  switch (fn) {
    case 'Densitat': {
      const d = clamp(spec.densitat ?? 8, .2, 40);
      return `${i}# De la densitat que has posat cap amunt (fins a ${py.f(d * 3, 1)}/s)\n`
           + `${i}self.dens = _DENS + (v / 127.0) * ${py.f(Math.max(.1, d * 3 - d))}`;
    }
    case 'Zona de notes':
      return `${i}self.centre = _CENTRE + int((v / 127.0) * 36)`;
    case 'Dispersió':
      return `${i}self.disp = _DISP + int((v / 127.0) * 24)`;
    case 'Atenuació':
      return `${i}self.vol = 1.0 - (v / 127.0) * 0.75`;
    case 'Durada del gra':
      // De la durada que has posat fins a vuit vegades més llarga: el mateix
      // núvol passa de ser espurnes a ser un teixit sostingut.
      return `${i}self.dur_k = 1.0 + (v / 127.0) * 7.0`;
    case 'Irregularitat':
      // El que separa una textura d'un metrònom. En repòs, la que has posat.
      return `${i}self.jit = _JITTER + (v / 127.0) * (1.0 - _JITTER)`;
    case 'Deriva de la zona':
      // La zona de notes es passeja sola amunt i avall: la textura no es queda
      // mai al mateix registre i deixa de sonar estàtica.
      return `${i}self.deriva = (v / 127.0) * 24.0`;
    case 'Ràfegues':
      // Quants esdeveniments es disparen de cop. A 1 és degoteig; amunt, grumolls.
      return `${i}self.raf = 1 + int((v / 127.0) * 7.99)`;
    case 'Filtre (velocitat)':
      return `${i}self.mov_per = _PER - (v / 127.0) * (_PER - 0.1)`;
    case 'Fons greu':
      return `${i}f = _FONS_VEL + int((v / 127.0) * (127 - _FONS_VEL))\n`
           + `${i}if f < self.fons_vel - 4 or f > self.fons_vel + 4:\n`
           + `${i}    self.fons_vel = f\n${i}    self._fons()`;
    case 'Modulació (CC1)':
      return `${i}self._cc_once(1, v)`;
    default:
      return `${i}pass`;
  }
}

function generateTexture(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  const dens = clamp(spec.densitat ?? 8, .2, 40);
  const jitter = clamp((spec.jitter ?? 70) / 100, 0, 1);
  const centre = clamp(spec.notaCentre ?? 78, 12, 108);
  const disp = clamp(spec.notaDispersio ?? 18, 0, 48);
  const velMin = clamp(spec.velMin ?? 40, 1, 127);
  const velMax = Math.max(velMin, clamp(spec.velMax ?? 100, 1, 127));
  const durMin = clamp(spec.duradaMin ?? 20, 5, 4000);
  const durMax = Math.max(durMin, clamp(spec.duradaMax ?? 120, 5, 4000));
  const raf = !!spec.rafegues;
  const rafN = clamp(spec.rafegaNotes ?? 4, 2, 12);
  const rafPausa = clamp(spec.rafegaPausa ?? 4, 1, 20);
  const fonsOn = !!spec.fonsOn;
  const fonsNota = clamp(spec.fonsNota ?? 28, 0, 96);
  const fonsIvs = (spec.fonsIntervals && spec.fonsIntervals.length ? spec.fonsIntervals : [0, 7]).map(x => clamp(x | 0, 0, 36));
  const fonsVel = clamp(spec.fonsVel ?? 45, 0, 127);
  const forma = DRONE_FORMES.includes(spec.moviment) ? spec.moviment : 'Cap';
  const cc = clamp(spec.movCC ?? 74, 0, 127);
  const per = clamp(spec.movPeriode ?? 4, .05, 20);
  const prof = clamp(spec.movProfunditat ?? 100, 0, 100);
  const potX = spec.pots?.x || 'Densitat';
  const potY = spec.pots?.y || 'Zona de notes';
  const potZ = spec.pots?.z || 'Filtre (velocitat)';

  const spec4json = JSON.stringify({ ...spec, cat: 'textura' });
  const formaCode = {
    'Cap': '        return -1',
    'Gate': `        return _ALT if self.fase < 0.5 else self.baix`,
    'Arc': `        t = 1.0 - abs(2.0 * self.fase - 1.0)
        return self.baix + int((_ALT - self.baix) * t)`,
    'Respiració': `        t = 1.0 - abs(2.0 * self.fase - 1.0)
        t = t * t * (3.0 - 2.0 * t)
        return self.baix + int((_ALT - self.baix) * t)`,
  }[forma];

  return `"""${nom} — textura feta amb el constructor de TECLA.
X: ${potX}  Y: ${potY}  Z: ${potZ}
${raf ? `Ràfegues de ${rafN}` : 'Continu'}${fonsOn ? ' · amb fons greu' : ''}${forma === 'Cap' ? '' : ` · filtre ${forma.toLowerCase()} sobre CC${cc}`}
"""
# TECLA-SPEC ${spec4json}
import time
import random
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_VEL_MIN = ${velMin}
_VEL_MAX = ${velMax}
_DUR_MIN = ${py.f(durMin / 1000)}
_DUR_MAX = ${py.f(durMax / 1000)}
_JITTER = ${py.f(jitter)}
_DENS = ${py.f(dens)}
_CENTRE = ${centre}
_DISP = ${disp}
_FONS_IVS = ${py.tuple(fonsIvs)}
_FONS_VEL = ${fonsOn ? fonsVel : 0}
_PER = ${py.f(per)}
_MOV_CC = ${cc}
_ALT = 127
_MIN_NOTA = 0
_MAX_NOTA = 127


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.dens = ${py.f(dens)}       # esdeveniments per segon
        self.centre = ${centre}
        self.disp = ${disp}
        self.vol = 1.0
        self.mov_per = _PER
        self.dur_k = 1.0        # multiplicador de la durada del gra
        self.jit = _JITTER      # irregularitat de l'espera
        self.deriva = 0.0       # quant es passeja la zona de notes
        self.fase_der = 0.0     # -1..1, on és la deriva ara mateix
        self.dir_der = 1.0      # cap on va el vaivé
        self.raf = 1            # esdeveniments per disparada
        self.baix = ${127 - Math.round(127 * prof / 100)}
        self.fase = 0.0
        self.ultim_cc = -1
        self.fons_vel = _FONS_VEL
        self.fons_notes = []
        self.pend = []          # note-offs pendents: [nota, quan]
        self.seguent = 0.0
        self.t = 0.0
        self._cc_cache = {}

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.seguent = self.t
        self.fase = 0.0
        self.ultim_cc = -1
        self.pend = []
        self._cc_cache = {}
${fonsOn ? '        self._fons()\n' : ''}        print("${nom}: %.1f/s" % self.dens)

    def _cc_once(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _fons(self):
        """Fons greu sostingut: es torna a muntar quan en canvia el volum."""
        for n in self.fons_notes:
            self.send_note_off(n, 0)
        self.fons_notes = []
        if self.fons_vel <= 0:
            return
        for iv in _FONS_IVS:
            n = ${fonsNota} + iv
            if _MIN_NOTA <= n <= _MAX_NOTA:
                self.send_note_on(n, self.fons_vel)
                self.fons_notes.append(n)

    def _allibera(self, now, totes=False):
        if not self.pend:
            return
        queden = []
        for p in self.pend:
            if totes or now >= p[1]:
                self.send_note_off(p[0], 0)
            else:
                queden.append(p)
        self.pend = queden

    def _gra(self, now):
        """Un esdeveniment: nota a l'atzar dins la zona, curta i amb la seva
        pròpia força."""
        d = self.disp
        # Deriva: el centre es passeja sol, així la zona no es queda quieta
        centre = self.centre
        if self.deriva > 0.0:
            centre = int(centre + self.deriva * self.fase_der)
        n = centre + (random.randint(-d, d) if d else 0)
        if n < _MIN_NOTA or n > _MAX_NOTA:
            return
        vel = random.randint(_VEL_MIN, _VEL_MAX)
        vel = int(vel * self.vol)
        vel = 1 if vel < 1 else (127 if vel > 127 else vel)
        dur = (_DUR_MIN + random.random() * (_DUR_MAX - _DUR_MIN)) * self.dur_k
        self.send_note_on(n, vel)
        self.pend.append([n, now + dur])

    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()
        dt = now - self.t
        self.t = now

        self._allibera(now)

        # ── Els tres potes, tal com s'han assignat ──
        v = px
${potCodeTextura(potX, spec)}
        v = py_
${potCodeTextura(potY, spec)}
        v = pz
${potCodeTextura(potZ, spec)}

        # ── Esdeveniments ──
        if now >= self.seguent and self.dens > 0.01:
            interval = 1.0 / self.dens
${raf ? `            for _ in range(${rafN} + self.raf - 1):
                self._gra(now)
            espera = interval * ${py.f(rafPausa)}` : `            for _ in range(self.raf):
                self._gra(now)
            espera = interval`}
            # Atzar sobre l'espera: sense això, una textura sona a màquina
            if self.jit > 0:
                espera = espera * (1.0 - self.jit * 0.5 + random.random() * self.jit)
            self.seguent = now + espera

        # ── Deriva de la zona: un vaivé lent entre -1 i 1 ──
        if self.deriva > 0.0:
            self.fase_der += dt * 0.08 * self.dir_der
            if self.fase_der >= 1.0:
                self.fase_der = 1.0
                self.dir_der = -1.0
            elif self.fase_der <= -1.0:
                self.fase_der = -1.0
                self.dir_der = 1.0
        # ── Filtre en moviment ──
        if self.mov_per > 0.01:
            self.fase = (self.fase + dt / self.mov_per) % 1.0
        val = self._valor_mov()
        if val >= 0 and (val < self.ultim_cc - 1 or val > self.ultim_cc + 1):
            self.ultim_cc = val
            try:
                self.midi_out.send(ControlChange(_MOV_CC, val))
            except Exception:
                pass

        return {'dens': round(self.dens, 1), 'centre': self.centre, 'disp': self.disp}

    def _valor_mov(self):
${formaCode}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        for n in self.fons_notes:
            self.send_note_off(n, 0)
        self.fons_notes = []
        self.stop_tracked_notes()
        for c, val in ${(() => {
          const vist = new Set();
          const parells = [];
          for (const c of [cc, 1, 11, 123, 120]) {
            if (vist.has(c)) continue;
            vist.add(c);
            parells.push(`(${c}, ${c === 11 || c === 7 ? 127 : 0})`);
          }
          return `(${parells.join(', ')})`;
        })()}:
            try:
                self.midi_out.send(ControlChange(c, val))
            except Exception:
                pass
`;
}

// ── Família ONA ───────────────────────────────────────────────────────────
// Els vuit modes ona_* del firmware són un valor que evoluciona amb el temps i
// que es mapeja a una nota (o a un CC). Sinus, quadrada, triangle i serra el
// fan amb una fase; el random walk i el mapa logístic, amb una regla. Aquí
// són la mateixa cosa amb la forma triable — i amb una cosa que als originals
// els faltava: la QUANTITZACIÓ A ESCALA, que és el que els fa musicals.

export const ONA_FORMES = ['Sinus', 'Quadrada', 'Triangle', 'Serra', 'Respiració', 'Atzar', 'Caos'];

/** Els potes que la família ona sap fer servir. */
export const ONA_POT_FNS = ['Freqüència', 'Nota base', 'Amplitud', 'Duty',
  'Força', 'Paràmetre del caos', 'Octava', 'Durada', 'Suavitzat', 'Deriva',
  'Modulació (CC1)', '—'];

function potCodeOna(fn, spec, indent = '        ') {
  const i = indent;
  switch (fn) {
    case 'Freqüència': {
      const f = clamp(spec.freq ?? 2, .02, 20);
      return `${i}# De la freqüència que has posat cap amunt (fins a ${py.f(f * 5, 1)} Hz)\n`
           + `${i}self.freq = _FREQ + (v / 127.0) * ${py.f(Math.max(.01, f * 5 - f))}`;
    }
    case 'Nota base':
      return `${i}b = _BASE + int((v / 127.0) * 36)\n`
           + `${i}if b != self.base:\n${i}    self.base = b`;
    case 'Amplitud':
      return `${i}self.amp = 1.0 + (v / 127.0) * 0.6`;
    case 'Duty':
      return `${i}self.duty = _DUTY + (v / 127.0) * (0.95 - _DUTY)`;
    case 'Força':
      return `${i}self.vel = _VEL + int((v / 127.0) * (127 - _VEL))`;
    case 'Octava':
      // Desplaça l'ona sencera en octaves sense tocar-ne l'amplitud.
      return `${i}o = int((v / 127.0) * 3.99)\n`
           + `${i}if o != self.oct_desp:\n${i}    self.oct_desp = o`;
    case 'Durada':
      // De la durada que has posat fins a vuit vegades més: de picada a lligat.
      return `${i}self.dur_k = 1.0 + (v / 127.0) * 7.0`;
    case 'Suavitzat':
      // Glissando entre valors: l'ona deixa de saltar de nota en nota i llisca.
      // És el que separa un arpegi d'una sirena.
      return `${i}self.suau = (v / 127.0) * 0.92`;
    case 'Deriva':
      // La nota base es passeja sola: l'ona no es queda mai al mateix registre.
      return `${i}self.deriva = (v / 127.0) * 18.0`;
    case 'Paràmetre del caos':
      return `${i}self.r = _R + (v / 127.0) * (4.0 - _R)`;
    case 'Modulació (CC1)':
      return `${i}self._cc_once(1, v)`;
    default:
      return `${i}pass`;
  }
}

function generateWave(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  const forma = ONA_FORMES.includes(spec.forma) ? spec.forma : 'Sinus';
  const freq = clamp(spec.freq ?? 2, .02, 20);
  const duty = clamp((spec.duty ?? 50) / 100, .05, .95);
  const base = clamp(spec.notaBase ?? 48, 0, 120);
  const amplitud = clamp(spec.amplitud ?? 12, 1, 48);
  const desti = spec.desti === 'CC' ? 'CC' : 'Nota';
  const cc = clamp(spec.cc ?? 74, 0, 127);
  const vel = clamp(spec.vel ?? 80, 1, 127);
  const lligat = spec.lligat !== false;
  const durada = clamp(spec.durada ?? 150, 10, 4000);
  const rCaos = clamp(spec.rCaos ?? 3.7, 2.5, 4);
  const pas = clamp(spec.pasAtzar ?? 3, 1, 12);
  const potX = spec.pots?.x || 'Freqüència';
  const potY = spec.pots?.y || 'Nota base';
  const potZ = spec.pots?.z || 'Amplitud';

  // Quantització: per a cada classe d'altura, quants semitons cal baixar per
  // caure sobre un grau de l'escala. És una taula de 12 i es consulta amb la
  // nota final, no amb el desplaçament: així segueix sent correcta encara que
  // el pot canviï la nota base en marxa (calculant-la des de la base, la
  // quantització es trencava en silenci a la primera girada del pot).
  const quant = !!spec.quantitza;
  const escala = (spec.escalaIntervals && spec.escalaIntervals.length ? spec.escalaIntervals : [0, 2, 4, 5, 7, 9, 11]).map(x => x | 0);
  const ton = clamp(spec.tonalitat | 0, 0, 11);
  const pcs = new Set(escala.map(x => ((x + ton) % 12 + 12) % 12));
  const snap = [];
  for (let pc = 0; pc < 12; pc++) {
    let d = 0;
    while (d < 12 && !pcs.has(((pc - d) % 12 + 12) % 12)) d++;
    snap.push(d % 12);
  }

  const spec4json = JSON.stringify({ ...spec, cat: 'ona' });

  // Cada forma dona un valor de 0 a 1. Les de fase avancen amb el temps; les
  // generatives (atzar i caos) treuen un valor nou cada cicle complet.
  const perFase = !['Atzar', 'Caos'].includes(forma);
  const formaCode = {
    'Sinus': '        return 0.5 - 0.5 * cos(6.283185 * self.fase)',
    'Quadrada': '        return 1.0 if self.fase < self.duty else 0.0',
    'Triangle': '        return 1.0 - abs(2.0 * self.fase - 1.0)',
    'Serra': '        return self.fase',
    'Respiració': `        t = 1.0 - abs(2.0 * self.fase - 1.0)
        return t * t * (3.0 - 2.0 * t)`,
    'Atzar': '        return self.val',
    'Caos': '        return self.val',
  }[forma];

  // El pas d'un cicle: només les formes generatives hi fan res
  const cicleCode = {
    'Atzar': `            # Random walk: un pas a l'atzar, amb rebot als extrems
            self.val = self.val + (random.random() - 0.5) * ${py.f(pas / 12)}
            if self.val < 0.0:
                self.val = -self.val
            elif self.val > 1.0:
                self.val = 2.0 - self.val`,
    'Caos': `            # Mapa logístic: x = r·x·(1−x). Amb r entre 3.5 i 4 és caos
            self.val = self.r * self.val * (1.0 - self.val)
            if self.val < 0.0 or self.val > 1.0:
                self.val = 0.5`,
  }[forma] || '            pass';

  return `"""${nom} — ona feta amb el constructor de TECLA.
X: ${potX}  Y: ${potY}  Z: ${potZ}
Forma: ${forma} → ${desti === 'CC' ? `CC${cc}` : `nota${quant ? ' (quantitzada a escala)' : ''}`}
"""
# TECLA-SPEC ${spec4json}
import time
${forma === 'Sinus' ? 'from math import cos\n' : ''}${perFase ? '' : 'import random\n'}from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_BASE = ${base}
_AMPLITUD = ${amplitud}
_FREQ = ${py.f(freq)}
_DUTY = ${py.f(duty)}
_VEL = ${vel}
_R = ${py.f(rCaos)}
${quant ? `_SNAP = ${py.tuple(snap)}   # semitons a baixar per caure a l'escala\n` : ''}_DESTI_CC = ${cc}
_DURADA = ${py.f(durada / 1000)}


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.freq = _FREQ
        self.duty = _DUTY
        self.base = _BASE
        self.amp = 1.0
        self.vel = _VEL
        self.oct_desp = 0       # octaves de desplaçament
        self.dur_k = 1.0        # multiplicador de la durada
        self.suau = 0.0         # quant llisca el valor cap al nou
        self.deriva = 0.0       # quant es passeja la nota base
        self.fase_der = 0.0
        self.dir_der = 1.0
        self.val_suau = 0.5     # el valor ja suavitzat
        self.r = _R
        self.fase = 0.0
        self.val = 0.5
        self.sonant = -1
        self.off_t = 0.0
        self.ultim_cc = -1
        self.t = 0.0
        self._cc_cache = {}

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.fase = 0.0
        self.val = 0.5
        self.sonant = -1
        self.ultim_cc = -1
        self._cc_cache = {}
        print("${nom}: ${forma} %.2f Hz" % self.freq)

    def _cc_once(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _valor(self):
${formaCode}

    def _nota_de(self, v):
        """Valor 0–1 → alçada. Amb quantització, l'ona salta d'un grau de
        l'escala al següent en lloc de passar per tots els semitons."""
        base = self.base + self.oct_desp * 12 + int(self.deriva * self.fase_der)
${quant ? `        n = base + int(v * self.amp * _AMPLITUD)
        return n - _SNAP[n % 12]` : `        return base + int(v * self.amp * _AMPLITUD)`}

    def _calla(self):
        if self.sonant >= 0:
            self.send_note_off(self.sonant, 0)
            self.sonant = -1

    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()
        dt = now - self.t
        self.t = now

        # ── Els tres potes, tal com s'han assignat ──
        v = px
${potCodeOna(potX, spec)}
        v = py_
${potCodeOna(potY, spec)}
        v = pz
${potCodeOna(potZ, spec)}

        # ── Avança l'ona ──
        abans = self.fase
        self.fase = (self.fase + dt * self.freq) % 1.0
        if self.fase < abans:            # ha completat un cicle
${cicleCode}

        val = self._valor()
        val = 0.0 if val < 0.0 else (1.0 if val > 1.0 else val)
        # Suavitzat: el valor no salta al nou, hi llisca. Amb la destinació a
        # nota, això converteix els salts en un glissando.
        if self.suau > 0.0:
            self.val_suau += (val - self.val_suau) * (1.0 - self.suau)
            val = self.val_suau
        else:
            self.val_suau = val
        # Deriva: un vaivé lent de la nota base
        if self.deriva > 0.0:
            self.fase_der += dt * 0.09 * self.dir_der
            if self.fase_der >= 1.0:
                self.fase_der = 1.0
                self.dir_der = -1.0
            elif self.fase_der <= -1.0:
                self.fase_der = -1.0
                self.dir_der = 1.0

${desti === 'CC' ? `        # Destinació: CC
        c = int(val * 127)
        if c < self.ultim_cc - 1 or c > self.ultim_cc + 1:
            self.ultim_cc = c
            try:
                self.midi_out.send(ControlChange(_DESTI_CC, c))
            except Exception:
                pass
` : `        # Destinació: nota. Només es toca quan l'alçada canvia de debò,
        # si no seria una allau de note-ons a cada volta del bucle.
        nota = self._nota_de(val)
        nota = 0 if nota < 0 else (127 if nota > 127 else nota)
        if nota != self.sonant:
            self._calla()
            self.send_note_on(nota, self.vel)
            self.sonant = nota
            self.off_t = now + _DURADA * self.dur_k
${lligat ? '' : `        elif self.sonant >= 0 and now >= self.off_t:
            self._calla()
`}`}
        return {'forma': '${forma}', 'hz': round(self.freq, 2), 'nota': self.sonant}

    def cleanup(self):
        self._calla()
        self.stop_tracked_notes()
        for c, val in ${(() => {
          const vist = new Set();
          const parells = [];
          for (const c of [desti === 'CC' ? cc : 1, 1, 11, 123, 120]) {
            if (vist.has(c)) continue;
            vist.add(c);
            parells.push(`(${c}, ${c === 11 || c === 7 ? 127 : 0})`);
          }
          return `(${parells.join(', ')})`;
        })()}:
            try:
                self.midi_out.send(ControlChange(c, val))
            except Exception:
                pass
`;
}

// ── Família ALGORÍSMICA ───────────────────────────────────────────────────
// Aquí no s'hi escriu un patró: s'hi escriu una REGLA, i el patró en surt. És
// la diferència entre copiar un ritme i entendre d'on ve. A diferència de les
// altres famílies, el que viatja al mode generat no és el resultat de
// l'algorisme sinó l'algorisme mateix, així els potes el fan mutar en directe.
//
//   · Euclidià       — K pulsacions repartides el més uniformement possible
//                      sobre S passos (Bjorklund). Amb S diferents per veu en
//                      surten polirítmies que triguen compassos a tornar a
//                      coincidir.
//   · Autòmat        — les 256 regles elementals de Wolfram. La 90 fa el
//                      triangle de Sierpinski; la 30, caos; la 110 és
//                      Turing-completa.
//   · Markov         — una matriu de probabilitats entre graus de l'escala.
//   · Joc de la vida — Conway sobre una graella toroidal.
//   · Fractal        — l'òrbita d'un punt del pla complex, amb sis mapes
//                      diferents (Mandelbrot, Julia, Burning Ship, Tricorn,
//                      Multibrot³ i Phoenix).

export const ALG_NOMS = ['Euclidià', 'Autòmat', 'Markov', 'Joc de la vida', 'Fractal'];

// ── Els sis mapes del pla complex ─────────────────────────────────────────
// Tots iteren la mateixa idea —agafa un punt, aplica-hi una fórmula, torna-hi—
// però cadascun deforma el pla a la seva manera, i això se sent: el Mandelbrot
// fa òrbites arrodonides, el Burning Ship fa angles, el Phoenix té memòria del
// pas anterior i no es repeteix mai igual.
//
//   punt: què tria el clic sobre la imatge.
//   par:  si el mapa té un segon paràmetre (c de Julia, p de Phoenix).
export const FRACTALS = {
  'Mandelbrot':   { punt: 'c',  par: null,  sub: 'z² + c des de zero' },
  'Julia':        { punt: 'z₀', par: 'c',   sub: 'z² + c des del punt' },
  'Burning Ship': { punt: 'c',  par: null,  sub: '(|x|+i|y|)² + c' },
  'Tricorn':      { punt: 'c',  par: null,  sub: 'conjugat de z, al quadrat' },
  'Multibrot³':   { punt: 'c',  par: null,  sub: 'z³ + c' },
  'Phoenix':      { punt: 'c',  par: 'p',   sub: 'z² + c + p·z anterior' },
};
export const FRACTAL_NOMS = Object.keys(FRACTALS);

/**
 * Un pas d'iteració del mapa. Mirall EXACTE del Python que es genera, perquè el
 * dibuix de l'editor sigui el patró que sonarà i no una il·lustració.
 * @returns {[number,number,number,number]} [zx, zy, zx anterior, zy anterior]
 */
export function fractalPas(tipus, zx, zy, cx, cy, px, py, jx, jy) {
  switch (tipus) {
    case 'Burning Ship': {
      const ax = Math.abs(zx), ay = Math.abs(zy);
      return [ax * ax - ay * ay + cx, 2 * ax * ay + cy, zx, zy];
    }
    case 'Tricorn':
      // El conjugat capgira el signe de la part imaginària a cada volta.
      return [zx * zx - zy * zy + cx, -2 * zx * zy + cy, zx, zy];
    case 'Multibrot³':
      return [zx * zx * zx - 3 * zx * zy * zy + cx, 3 * zx * zx * zy - zy * zy * zy + cy, zx, zy];
    case 'Phoenix':
      // p multiplica el valor ANTERIOR: el mapa recorda d'on ve.
      return [zx * zx - zy * zy + cx + jx * px, 2 * zx * zy + jx * py, zx, zy];
    case 'Julia':
      return [zx * zx - zy * zy + jx, 2 * zx * zy + jy, zx, zy];
    default: // Mandelbrot
      return [zx * zx - zy * zy + cx, 2 * zx * zy + cy, zx, zy];
  }
}

/** Punt de partida de l'òrbita: el Julia arrenca del punt triat; la resta, de zero. */
export function fractalZ0(tipus, cx, cy) {
  return tipus === 'Julia' ? [cx, cy] : [0, 0];
}

// Cinc variables que valen per a QUALSEVOL algorisme: no toquen la regla,
// toquen com sona el que la regla treu. Així els cinc editors guanyen control
// sense haver d'inventar-ne un de propi per a cada un.
const ALG_COMUNS = ['Força', 'Gate', 'Silencis', 'Humanització', 'Transposició'];

const ALG_POT_FNS = {
  'Euclidià': ['Tempo', 'Densitat', 'Rotació', 'Octava', ...ALG_COMUNS, 'Brillantor (CC74)', '—'],
  'Autòmat': ['Tempo', 'Regla', 'Octava', 'Torna a sembrar', ...ALG_COMUNS, 'Brillantor (CC74)', '—'],
  'Markov': ['Tempo', 'Atzar', 'Octava', 'Registre', ...ALG_COMUNS, 'Brillantor (CC74)', '—'],
  'Joc de la vida': ['Tempo', 'Filtre de veus', 'Octava', 'Torna a sembrar', ...ALG_COMUNS,
                     'Brillantor (CC74)', '—'],
  'Fractal': ['Tempo', 'Part real de c', 'Part imaginària de c', 'Paràmetre del mapa',
              'Zoom de l\'òrbita', 'Passos de l\'òrbita', 'Recorregut del pla', 'Octava',
              ...ALG_COMUNS, 'Brillantor (CC74)', '—'],
};

/** Funcions de pot d'una família (l'algorísmica depèn de l'algorisme triat). */
export function potFnsFor(cat, alg) {
  if (cat === 'algoritmic') return ALG_POT_FNS[alg] || ALG_POT_FNS['Euclidià'];
  return POT_FNS[cat] || [];
}

// ── Els algorismes, també en JS ───────────────────────────────────────────
// Mirall exacte del que s'escriu al Python. El formulari els fa servir per
// ensenyar EL QUE SONARÀ mentre mous els controls: el dibuix no és una
// il·lustració, és el patró de debò.

/** Reparteix k pulsacions sobre n passos, el més uniformement possible. */
export function euclid(k, n) {
  n = Math.max(1, n | 0);
  k = Math.max(0, Math.min(n, k | 0));
  if (k === 0) return new Array(n).fill(0);
  if (k === n) return new Array(n).fill(1);
  const pat = [];
  let cub = 0;
  for (let i = 0; i < n; i++) {
    cub += k;
    if (cub >= n) { cub -= n; pat.push(1); } else pat.push(0);
  }
  return pat;
}

/** Gira un patró r posicions cap a la dreta. */
export function rota(pat, r) {
  const n = pat.length;
  if (!n) return pat;
  r = ((r % n) + n) % n;
  return r ? pat.slice(n - r).concat(pat.slice(0, n - r)) : pat.slice();
}

/** Una generació de l'autòmat elemental de Wolfram (vora toroidal). */
export function wolfram(fila, regla) {
  const n = fila.length;
  const out = new Array(n);
  for (let i = 0; i < n; i++) {
    const idx = (fila[(i - 1 + n) % n] << 2) | (fila[i] << 1) | fila[(i + 1) % n];
    out[i] = (regla >> idx) & 1;
  }
  return out;
}

/** Una generació del joc de la vida sobre una graella toroidal. */
export function vida(g) {
  const h = g.length, w = g[0].length;
  const out = g.map(f => f.slice());
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      let n = 0;
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          if (dx || dy) n += g[(y + dy + h) % h][(x + dx + w) % w];
        }
      }
      out[y][x] = g[y][x] ? (n === 2 || n === 3 ? 1 : 0) : (n === 3 ? 1 : 0);
    }
  }
  return out;
}

function potCodeAlg(fn, spec, indent = '        ') {
  const i = indent;
  switch (fn) {
    case 'Tempo': {
      const lo = clamp(spec.bpmMin ?? 80, 20, 300), hi = clamp(spec.bpmMax ?? 160, 20, 300);
      const min = Math.min(lo, hi), max = Math.max(lo, hi);
      return `${i}b = ${py.f(min)} + (v / 127.0) * ${py.f(max - min)}\n`
           + `${i}if b < self.bpm - 0.3 or b > self.bpm + 0.3:\n`
           + `${i}    self.bpm = b\n${i}    self._calc()`;
    }
    case 'Densitat':
      return `${i}d = (v / 127.0)\n${i}if d < self.dens - 0.02 or d > self.dens + 0.02:\n`
           + `${i}    self.dens = d\n${i}    self._recalc()`;
    case 'Filtre de veus':
      return `${i}self.llindar = 1 + int((v / 127.0) * 2.99)`;
    case 'Rotació':
      return `${i}r = int((v / 127.0) * 15.99)\n${i}if r != self.rot:\n`
           + `${i}    self.rot = r\n${i}    self._recalc()`;
    case 'Regla':
      // La primera de _REGLES és la que has triat: amb el pot al mínim sona
      // el mode tal com el vas configurar, i girant-lo n'explores d'altres.
      // (Amb el mapatge cru 0–255, el pot a zero et posava la regla 0, que no
      // fa res, i la teva configuració es perdia només d'engegar.)
      return `${i}r = _REGLES[min(len(_REGLES) - 1, int((v / 128.0) * len(_REGLES)))]\n`
           + `${i}if r != self.regla:\n${i}    self.regla = r\n`
           + `${i}    print("${'%'}s: regla ${'%'}d" % (self.name, r))`;
    case 'Octava':
      return `${i}o = _OCT + int((v / 127.0) * 2.99)\n${i}if o != self.octave:\n${i}    self.octave = o`;
    case 'Registre':
      return `${i}self.abast = _ABAST + int((v / 127.0) * 2.99)`;
    case 'Atzar':
      return `${i}self.atzar = (v / 127.0)`;
    case 'Torna a sembrar':
      return `${i}s = int((v / 127.0) * 7.99)\n${i}if s != self.llavor:\n`
           + `${i}    self.llavor = s\n${i}    self._sembra()`;
    // ── Les cinc compartides: no toquen la REGLA, toquen com sona el que en
    //    surt. Per això valen igual per als cinc algorismes.
    case 'Força':
      return `${i}self.vel_k = 0.35 + (v / 127.0) * 1.4`;
    case 'Gate':
      // De picada a lligat: la mateixa regla canvia de caràcter del tot.
      return `${i}self.gate_k = 0.25 + (v / 127.0) * 3.5`;
    case 'Silencis':
      // Aprima el que la regla treu, sense tocar la regla.
      return `${i}self.silenci = (v / 127.0) * 0.85`;
    case 'Humanització':
      return `${i}self.human = v / 127.0`;
    case 'Transposició':
      // Cromàtica, no diatònica: en repòs sona on l'has deixat.
      return `${i}self.transp = int((v / 127.0) * 12.99)`;
    // El pot en repòs deixa el fractal EXACTAMENT on el vas deixar tu, i
    // girant-lo el desplaça pel pla: així el mode arrenca sonant com l'has fet.
    case 'Part real de c':
      return `${i}self.cx = self.cx + (v / 127.0) * 0.6`;
    case 'Part imaginària de c':
      return `${i}self.cy = self.cy + (v / 127.0) * 0.6`;
    case 'Paràmetre del mapa':
      return `${i}self.jx = _JX + (v / 127.0) * 0.5`;
    case 'Zoom de l\'òrbita':
      // Quina part del pla es reparteix entre els graus. En repòs, el zoom que
      // has posat al formulari; girant-lo, s'estreny cap al centre i la melodia
      // s'obre. (Abans arrencava sempre a 1.0 i el teu valor es perdia.)
      return `${i}self.zoom = _ZOOM + (v / 127.0) * (6.0 - _ZOOM)`;
    case 'Passos de l\'òrbita':
      // Quantes iteracions s'avancen a cada nota: amb 1 la melodia recorre
      // l'òrbita pas a pas i amb 8 hi salta, i el mateix punt sona molt diferent.
      return `${i}self.iters = _ITERS + int((v / 127.0) * (8 - _ITERS))`;
    case 'Recorregut del pla':
      // Passeja el punt c en DIAGONAL (les dues parts alhora): un sol pot per
      // travessar el fractal, que és el gest que de debò es fa servir tocant.
      return `${i}d = (v / 127.0) * 0.55\n${i}self.cx = self.cx + d\n${i}self.cy = self.cy + d * 0.6`;
    case 'Brillantor (CC74)':
      return `${i}self._cc_once(74, v)`;
    default:
      return `${i}pass`;
  }
}

function generateAlgorithmic(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  // Els modes fets abans de la família de fractals duien algoritme:'Mandelbrot';
  // ara 'Mandelbrot' és un dels sis mapes de dins de 'Fractal'.
  const algDemanat = spec.algoritme === 'Mandelbrot' ? 'Fractal' : spec.algoritme;
  const alg = ALG_NOMS.includes(algDemanat) ? algDemanat : 'Euclidià';
  const escala = (spec.escalaIntervals && spec.escalaIntervals.length ? spec.escalaIntervals : [0, 2, 4, 7, 9]).map(x => x | 0);
  const key = clamp(spec.tonalitat | 0, 0, 11);
  const oct = clamp(spec.octava ?? 4, 0, 7);
  const vel = clamp(spec.vel ?? 92, 1, 127);
  const gate = clamp((spec.gate ?? 60) / 100, .05, 1);
  const bpm0 = Math.round((clamp(spec.bpmMin ?? 80, 20, 300) + clamp(spec.bpmMax ?? 160, 20, 300)) / 2);
  const potX = spec.pots?.x || 'Tempo';
  const potY = spec.pots?.y || (ALG_POT_FNS[alg][1] || '—');
  const potZ = spec.pots?.z || 'Octava';
  const spec4json = JSON.stringify({ ...spec, cat: 'algoritmic' });

  // ── Les peces que canvien segons l'algorisme ──
  let consts = '', estat = '', metodes = '', pas = '', recalc = '        pass', sembra = '        pass';
  let calRandom = false;

  if (alg === 'Euclidià') {
    const veus = (spec.veus && spec.veus.length ? spec.veus : [{ k: 4, n: 16, rot: 0, perc: true, nota: 36, grau: 0, vel: 105 }])
      .slice(0, 4)
      .map(v => ({
        n: clamp(v.n | 0, 2, 32),
        k: clamp(v.k | 0, 0, 32),
        rot: clamp(v.rot | 0, 0, 31),
        perc: v.perc !== false,
        nota: clamp(v.nota ?? 36, 0, 127),
        grau: clamp(v.grau | 0, 0, 14),
        vel: clamp(v.vel ?? 100, 1, 127),
      }));
    consts = `_VEUS = ${py.tuples(veus.map(v => [v.n, v.k, v.rot, v.perc ? 1 : 0, v.perc ? v.nota : v.grau, v.vel]))}
# per veu: (passos, pulsacions, rotació, és percussió, nota o grau, força)`;
    estat = `        self.dens = 0.0
        self.rot = 0
        self.pas_veu = [0] * len(_VEUS)
        self.patrons = []
        self._recalc()`;
    metodes = `    def _euclid(self, k, n):
        """Reparteix k pulsacions sobre n passos el més uniformement possible.
        És l'algorisme de Bjorklund escrit com un Bresenham: el mateix
        repartiment que fan servir els ritmes tradicionals de mig món."""
        if k <= 0:
            return bytes(n)
        if k >= n:
            return bytes(b'\\x01' * n)
        pat = bytearray(n)
        cub = 0
        for i in range(n):
            cub += k
            if cub >= n:
                cub -= n
                pat[i] = 1
        return bytes(pat)

    def _recalc(self):
        """Els patrons només es tornen a calcular quan un pot els mou."""
        self.patrons = []
        for (n, k0, r0, es_perc, nota, vel) in _VEUS:
            # Del que has configurat cap amunt: amb el pot al mínim sona el
            # teu K, i girant-lo s'omple fins a totes les pulsacions.
            k = int(k0 + (n - k0) * self.dens + 0.5)
            k = 0 if k < 0 else (n if k > n else k)
            self.patrons.append(self._euclid(k, n))
`;
    recalc = null;
    pas = `        for i in range(len(_VEUS)):
            n, k0, r0, es_perc, nota, vel = _VEUS[i]
            pat = self.patrons[i]
            p = self.pas_veu[i]
            if pat[(p - r0 - self.rot) % n]:
                if es_perc:
                    self._cop(nota, vel, _DRUM_CH, _GATE_PERC, now)
                else:
                    self._cop(self._nota(nota), vel, 0, self.step_dur * _GATE, now)
            # Cada veu té la seva llargada: per això en surten polirítmies
            self.pas_veu[i] = (p + 1) % n`;
  }

  if (alg === 'Autòmat') {
    const n = clamp(spec.autN ?? 16, 4, 24);
    const regla = clamp(spec.regla ?? 90, 0, 255);
    const maxVeus = clamp(spec.maxVeus ?? 5, 1, 8);
    const llavor = (spec.llavorAut && spec.llavorAut.length === n)
      ? spec.llavorAut.map(x => (x ? 1 : 0))
      : Array.from({ length: n }, (_, i) => (i === n >> 1 ? 1 : 0));
    const reglesInteressants = [90, 30, 110, 150, 54, 60, 126, 22, 182, 105];
    const llistaRegles = [regla, ...reglesInteressants.filter(r => r !== regla)].slice(0, 10);
    consts = `_N = ${n}
_LLAVOR = ${py.tuple(llavor)}
_MAX_VEUS = ${maxVeus}
_REGLES = ${py.tuple(llistaRegles)}   # la primera és la que has triat`;
    estat = `        self.regla = ${regla}
        self.llavor = 0
        self.fila = list(_LLAVOR)`;
    metodes = `    def _sembra(self):
        if self.llavor == 0:
            self.fila = list(_LLAVOR)
        else:
            # Llavors alternatives: una cel·la desplaçada cap a la dreta
            self.fila = [0] * _N
            self.fila[(self.llavor * 3) % _N] = 1

    def _generacio(self):
        """Una generació de l'autòmat elemental: cada cel·la mira el seu veí
        esquerre, ella mateixa i el dret, i la regla (0–255) diu què en surt.
        La 90 dibuixa el triangle de Sierpinski; la 30 fa caos; la 110 és
        Turing-completa."""
        r = self.fila
        out = [0] * _N
        viu = 0
        for i in range(_N):
            idx = (r[i - 1] << 2) | (r[i] << 1) | r[(i + 1) % _N]
            c = (self.regla >> idx) & 1
            out[i] = c
            viu += c
        # Moltes regles s'extingeixen sobre un anell (la 90 amb una amplada
        # potència de dos, per exemple): si passa, es torna a sembrar en lloc
        # de quedar-se mut per sempre.
        if viu == 0:
            self._sembra()
        else:
            self.fila = out
`;
    sembra = null;
    pas = `        self._generacio()
        veus = 0
        for i in range(_N):
            if self.fila[i] and veus < _MAX_VEUS:
                veus += 1
                self._cop(self._nota(i), _VEL, 0, self.step_dur * _GATE, now)`;
  }

  if (alg === 'Markov') {
    const g = clamp(spec.mkGraus ?? 7, 2, 8);
    const m = (spec.matriu && spec.matriu.length === g)
      ? spec.matriu.map(f => Array.from({ length: g }, (_, j) => clamp((f[j] ?? 0) | 0, 0, 3)))
      : Array.from({ length: g }, (_, i) => Array.from({ length: g }, (_, j) => (Math.abs(i - j) <= 1 ? 2 : 1)));
    consts = `_GRAUS = ${g}
_ABAST = ${clamp(spec.mkAbast ?? 2, 1, 4)}
_MATRIU = ${py.tuples(m)}
# de la fila (grau actual) a la columna (grau següent): pes 0-3`;
    estat = `        self.grau = 0
        self.atzar = 0.0
        self.abast = _ABAST`;
    metodes = `    def _tria(self):
        """Cadena de Markov: la fila del grau actual dona els pesos d'anar a
        cada grau. Amb 'atzar' al màxim, la matriu es dilueix cap a l'atzar
        pur — així se sent què hi aporta, la matriu."""
        fila = _MATRIU[self.grau]
        total = 0
        for w in fila:
            total += w + self.atzar * 3.0
        if total <= 0:
            return int(random.random() * _GRAUS)
        r = random.random() * total
        acum = 0.0
        for j in range(_GRAUS):
            acum += fila[j] + self.atzar * 3.0
            if r <= acum:
                return j
        return _GRAUS - 1
`;
    calRandom = true;
    pas = `        self.grau = self._tria()
        # El registre reparteix els graus per unes quantes octaves
        salt = int(random.random() * self.abast) * len(_ESCALA)
        self._cop(self._nota(self.grau + salt), _VEL, 0, self.step_dur * _GATE, now)`;
  }

  if (alg === 'Joc de la vida') {
    const w = clamp(spec.vidaW ?? 12, 4, 16);
    const h = clamp(spec.vidaH ?? 8, 4, 16);
    const llavor = (spec.llavorVida && spec.llavorVida.length === h && spec.llavorVida[0]?.length === w)
      ? spec.llavorVida.map(f => f.map(x => (x ? 1 : 0)))
      : Array.from({ length: h }, (_, y) => Array.from({ length: w }, (_, x) =>
          ((y === 1 && x === 2) || (y === 2 && x === 3) || (y === 3 && x >= 1 && x <= 3) ? 1 : 0)));   // glider
    consts = `_W = ${w}
_H = ${h}
_LLAVOR = ${py.tuples(llavor.map(f => f))}`;
    estat = `        self.llindar = 1
        self.llavor = 0
        self.g = [list(f) for f in _LLAVOR]
        self._sembra()          # garanteix que la graella no arrenqui buida`;
    metodes = `    def _aleatoria(self, llavor):
        """Sembra pseudoaleatòria i reproduïble (un LCG curt: no cal random)."""
        s = (llavor + 1) * 7919
        self.g = []
        for y in range(_H):
            fila = []
            for x in range(_W):
                s = (s * 1103515245 + 12345) & 0x7FFFFFFF
                fila.append(1 if (s >> 16) % 100 < 30 else 0)
            self.g.append(fila)

    def _sembra(self):
        if self.llavor == 0:
            self.g = [list(f) for f in _LLAVOR]
        else:
            self._aleatoria(self.llavor)
        if self._viva() == 0:
            # Una llavor buida deixaria el mode mut per sempre: se'n posa una
            # d'aleatòria, i si encara així no en surt res, una cèl·lula al mig.
            self._aleatoria(self.llavor + 1)
            if self._viva() == 0:
                self.g[_H // 2][_W // 2] = 1

    def _generacio(self):
        """Conway sobre una graella TOROIDAL (les vores s'enganxen): una
        cèl·lula viva segueix viva amb 2 o 3 veïnes, i una de morta neix amb
        exactament 3."""
        g = self.g
        nou = []
        for y in range(_H):
            fila = []
            dalt = g[y - 1]
            mig = g[y]
            baix = g[(y + 1) % _H]
            for x in range(_W):
                e = x - 1
                d = (x + 1) % _W
                n = (dalt[e] + dalt[x] + dalt[d] + mig[e] + mig[d]
                     + baix[e] + baix[x] + baix[d])
                if mig[x]:
                    fila.append(1 if (n == 2 or n == 3) else 0)
                else:
                    fila.append(1 if n == 3 else 0)
            nou.append(fila)
        self.g = nou

    def _viva(self):
        t = 0
        for f in self.g:
            for c in f:
                t += c
        return t
`;
    sembra = null;
    pas = `        self._generacio()
        # Cada COLUMNA és un grau; com més poblada, més forta sona
        for x in range(_W):
            n = 0
            for y in range(_H):
                n += self.g[y][x]
            if n >= self.llindar:
                v = _VEL - 30 + n * 12
                v = 1 if v < 1 else (127 if v > 127 else v)
                self._cop(self._nota(x), v, 0, self.step_dur * _GATE, now)
        if self._viva() == 0:
            self._sembra()          # si s'extingeix, torna a començar`;
  }

  if (alg === 'Fractal') {
    const tipus = FRACTAL_NOMS.includes(spec.fractal) ? spec.fractal : 'Mandelbrot';
    const cx = spec.cx ?? -0.4;
    const cy = spec.cy ?? 0.6;
    const jx = spec.jx ?? (tipus === 'Julia' ? -0.8 : 0.5);
    const jy = spec.jy ?? (tipus === 'Julia' ? 0.156 : 0);
    const iters = clamp(spec.iters ?? 1, 1, 8);
    const zoom = clamp(spec.zoom ?? 1, 1, 6);
    // El cos del bucle, un per mapa. És el mateix que fa fractalPas() en JS:
    // el que dibuixa l'editor és, literalment, el que sonarà.
    const COS = {
      'Mandelbrot': `            zx = x * x - y * y + self.cx
            zy = 2.0 * x * y + self.cy`,
      'Julia': `            zx = x * x - y * y + self.jx
            zy = 2.0 * x * y + _JY`,
      'Burning Ship': `            ax = x if x >= 0.0 else -x
            ay = y if y >= 0.0 else -y
            zx = ax * ax - ay * ay + self.cx
            zy = 2.0 * ax * ay + self.cy`,
      'Tricorn': `            zx = x * x - y * y + self.cx
            zy = -2.0 * x * y + self.cy`,
      'Multibrot³': `            zx = x * x * x - 3.0 * x * y * y + self.cx
            zy = 3.0 * x * x * y - y * y * y + self.cy`,
      'Phoenix': `            zx = x * x - y * y + self.cx + self.jx * self.px
            zy = 2.0 * x * y + self.jx * self.py`,
    }[tipus];
    const z0 = tipus === 'Julia'
      ? `        self.zx = self.cx
        self.zy = self.cy`
      : `        self.zx = 0.0
        self.zy = 0.0`;

    consts = `_ITERS = ${iters}
_CX = ${py.f(cx, 4)}
_CY = ${py.f(cy, 4)}
_JX = ${py.f(jx, 4)}
_JY = ${py.f(jy, 4)}
_ZOOM = ${py.f(zoom, 2)}
_MAPA = "${tipus}"`;
    estat = `        self.cx = _CX
        self.cy = _CY
        self.jx = _JX
        self.zoom = _ZOOM
        self.iters = _ITERS
${z0}
        self.px = 0.0
        self.py = 0.0`;
    metodes = `    def _reinicia(self):
        """L'òrbita ha marxat a l'infinit: torna-la al punt de sortida."""
${z0}
        self.px = 0.0
        self.py = 0.0

    def _orbita(self):
        """Un pas de ${tipus}. Torna on ha anat a parar la part real de z,
        normalitzada a 0..1. Els punts que NO s'escapen donen seqüències
        quasi-periòdiques: ni es repeteixen ni són aleatòries, que és
        exactament el terreny on la música es fa interessant."""
        for _ in range(self.iters):
            x = self.zx
            y = self.zy
${COS}
            self.px = x
            self.py = y
            self.zx = zx
            self.zy = zy
            if zx * zx + zy * zy > 4.0:     # s'ha escapat
                self._reinicia()
                return 0.5
        # El zoom reparteix menys pla entre els graus: la melodia s'obre.
        v = 0.5 + (self.zx / 4.0) * self.zoom
        return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)
`;
    pas = `        v = self._orbita()
        grau = int(v * (len(_ESCALA) * 2 - 1))
        self._cop(self._nota(grau), _VEL, 0, self.step_dur * _GATE, now)`;
  }

  return `"""${nom} — mode algorísmic (${alg}) fet amb el constructor de TECLA.
X: ${potX}  Y: ${potY}  Z: ${potZ}
El patró no està escrit enlloc: el genera la regla, i els potes la fan mutar.
"""
# TECLA-SPEC ${spec4json}
import time
${calRandom ? 'import random\n' : ''}from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_ESCALA = ${py.tuple(escala)}
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_OCT = ${oct}
_VEL = ${vel}
_GATE = ${py.f(gate)}
_GATE_PERC = 0.055
_DRUM_CH = 9
${consts}


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.bpm = ${py.f(bpm0)}
        self.key = ${key}
        self.octave = _OCT
        self.step = 0
        self.step_dur = 0.0
        self.next_t = 0.0
        self.pend = []
        self._cc_cache = {}
        self.vel_k = 1.0        # multiplicador de força
        self.gate_k = 1.0       # multiplicador de durada
        self.silenci = 0.0      # quina part del que surt es queda muda
        self.human = 0.0        # quant balla el pols
        self.transp = 0         # semitons de transposició
        self._llavor_h = 7777
${estat}

    def setup(self):
        self.initialized = True
        self.step = 0
        self._calc()
        self.next_t = time.monotonic()
        self.pend = []
        self._cc_cache = {}
        print("${nom}: ${alg} %d BPM" % int(self.bpm))

    def _calc(self):
        self.step_dur = 60.0 / self.bpm / 4.0

    def _cc_once(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _nota(self, grau):
        """Grau de l'escala → nota MIDI (els graus que en passen, pugen d'octava)."""
        n = len(_ESCALA)
        return self.octave * 12 + self.key + _ESCALA[grau % n] + 12 * (grau // n)

    def _allibera(self, now, totes=False):
        if not self.pend:
            return
        queden = []
        for p in self.pend:
            if totes or now >= p[2]:
                self.send_note_off(p[0], 0, p[1])
            else:
                queden.append(p)
        self.pend = queden

    def _atzar_h(self, n):
        """Congruencial lineal per als potes compartits (silencis, pols)."""
        self._llavor_h = (self._llavor_h * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor_h >> 8) % (n if n > 0 else 1)

    def _cop(self, nota, vel, canal, dura, now):
        # Silencis: el que la regla treu pot no arribar a sonar
        if self.silenci > 0.0 and self._atzar_h(1000) < int(self.silenci * 1000):
            return
        # La transposició no toca la percussió: allà l'alçada ÉS l'instrument
        if canal != _DRUM_CH:
            nota += self.transp
        if nota < 0 or nota > 127:
            return
        vel = int(vel * self.vel_k)
        vel = 1 if vel < 1 else (127 if vel > 127 else vel)
        self.send_note_on(nota, vel, canal)
        self.pend.append([nota, canal, now + dura * self.gate_k])

${metodes ? metodes + '\n' : ''}${recalc === null ? '' : `    def _recalc(self):
${recalc}

`}${sembra === null ? '' : `    def _sembra(self):
${sembra}

`}    def _pas(self, now):
${pas}

    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()

        self._allibera(now)

${alg === 'Fractal' ? `        # El punt torna a la base abans de llegir els potes: així els que el
        # mouen (part real, part imaginària, recorregut) se SUMEN en comptes de
        # trepitjar-se l'un a l'altre segons l'ordre en què estiguin assignats.
        self.cx = _CX
        self.cy = _CY
` : ''}        # ── Els tres potes, tal com s'han assignat ──
        v = px
${potCodeAlg(potX, spec)}
        v = py_
${potCodeAlg(potY, spec)}
        v = pz
${potCodeAlg(potZ, spec)}

        if now >= self.next_t:
            self._pas(now)
            self.step += 1
            d = 0.0
            if self.human > 0.0:
                d = (self._atzar_h(2000) / 1000.0 - 1.0) * self.human * self.step_dur * 0.3
            self.next_t = now + self.step_dur + d

        return {'alg': '${alg}', 'bpm': int(self.bpm), 'pas': self.step,
                ${alg === 'Fractal' ? `'cx': self.cx, 'cy': self.cy, 'zoom': self.zoom,
                'iters': self.iters, 'jx': self.jx, 'zx': self.zx, 'zy': self.zy,` : ''}
                'nom': self.name}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
        for c, val in ((74, 0), (1, 0), (11, 127), (123, 0), (120, 0)):
            try:
                self.midi_out.send(ControlChange(c, val))
            except Exception:
                pass
`;
}

// ── Família SOROLL ────────────────────────────────────────────────────────
// El TECLA no té generador de soroll: té setze tecles i un port MIDI. El soroll
// s'hi fa com se n'ha fet sempre abans dels sintetitzadors digitals — amb massa
// esdeveniments alhora. Quan la densitat puja prou i les altures deixen de
// tenir centre, l'oïda ja no sent notes: sent textura, i després paret.
//
// El COLOR és literal, no una metàfora: és el pendent espectral de la seqüència
// d'altures. El blanc és pla (cada nota independent), el marró és un passeig
// aleatori (integrar el blanc → −6 dB/octava, greu i lent), el rosa hi queda al
// mig, i el blau i el violeta són la primera i la segona DIFERÈNCIA del blanc
// (derivar → +6 i +12 dB/octava, agut i nerviós). Les mateixes operacions que
// als generadors analògics.
//
// I cinc motors, del silenci a la violència:
//   · Núvol      — el soroll pur, del degoteig a la paret.
//   · Saturació  — clústers de semitons adjacents a força màxima: el batec de
//                  freqüències que se sent com a distorsió.
//   · FM         — una nota que salta a velocitat d'àudio; el que a un synth
//                  seria modulació de freqüència, aquí és el pas de nota.
//   · Dial       — soroll i fragments tonals alternats, com buscar emissora.
//   · Impulsos   — espurnes esparses i curtes: pluja, vinil, brasa.

export const SOROLL_MOTORS = ['Núvol', 'Saturació', 'FM', 'Dial', 'Impulsos'];
export const SOROLL_COLORS = ['Blanc', 'Rosa', 'Marró', 'Blau', 'Violeta'];

export const SOROLL_POT_FNS = ['Densitat', 'Cruixent', 'Amplada', 'Intensitat',
  'Gruix del clúster', 'Espectre (α)', 'Centre', 'Velocitat de la FM', 'Profunditat de la FM',
  'Dial (emissora)', 'Xiulet del dial', 'Brillantor (CC74)', 'Ressonància (CC71)', '—'];

/**
 * Els cinc sorolls purs, com a valors d'α a la llei S(f) ∝ 1/f^α.
 * No són cinc casos especials: són cinc punts d'una sola recta contínua, i entre
 * ells (i més enllà) hi ha tot l'espectre.
 */
export const SOROLL_ALFES = {
  'Violeta': -2, 'Blau': -1, 'Blanc': 0, 'Rosa': 1, 'Marró': 2,
};
export const SOROLL_COLORS_ORDRE = ['Violeta', 'Blau', 'Blanc', 'Rosa', 'Marró'];

/** El nom del soroll que li correspon a un α (el més proper). */
export function nomPerAlfa(alfa) {
  let millor = 'Blanc', dist = 1e9;
  for (const [nom, a] of Object.entries(SOROLL_ALFES)) {
    const d = Math.abs(a - alfa);
    if (d < dist) { dist = d; millor = nom; }
  }
  return dist <= 0.25 ? millor : `α ${alfa >= 0 ? '' : '−'}${Math.abs(alfa).toFixed(2)}`;
}

/**
 * Coeficients del filtre d'espectre, en JS: el mateix que fa _coefs() al Python.
 * Serveixen per dibuixar la resposta a l'editor i per als tests.
 */
export function coefsEspectre(alfa, M = 32) {
  const d = alfa * 0.5;
  const b = new Array(M).fill(1);
  for (let j = 1; j < M; j++) b[j] = b[j - 1] * (j - 1 + d) / j;
  const e = b.reduce((s, x) => s + x * x, 0);
  return { b, norm: e > 0 ? SOROLL_GUANY / Math.sqrt(e) : 1 };
}

/**
 * Guany de sortida del filtre d'espectre.
 *
 * Deixa l'amplitud RMS al voltant de 0,42, o sigui que el retall a ±1 queda a
 * més de dues desviacions i amb prou feines actua. Amb un guany més alt el
 * senyal es retallava tant que el retall mateix aplanava l'espectre i el
 * violeta deixava de ser violeta.
 */
export const SOROLL_GUANY = 0.72;

/** El recorregut real de cada pot, per ensenyar-lo al costat del selector. */
export const SOROLL_POT_RANGS = {
  'Densitat': (s) => `${(s.densMin ?? .5).toFixed(1)} → ${Math.round(s.densMax ?? 300)} /s`,
  'Cruixent': () => 'gra → espurna',
  'Amplada': (s) => `0 → ±${s.ample ?? 24} st`,
  'Intensitat': () => 'silenci → 127',
  'Gruix del clúster': (s) => `1 → ${s.gruix ?? 3} notes`,
  'Color': () => 'blanc → violeta',
  'Centre': (s) => `${Math.max(12, (s.centre ?? 60) - 24)} → ${Math.min(120, (s.centre ?? 60) + 24)}`,
  'Velocitat de la FM': (s) => `${(s.fmHz ?? 12).toFixed(1)} → ${((s.fmHz ?? 12) + 60).toFixed(0)} Hz`,
  'Profunditat de la FM': (s) => `0 → ±${s.fmProf ?? 12} st`,
  'Dial (emissora)': () => 'quiet → escombrant',
  'Brillantor (CC74)': () => 'CC74 0 → 127',
  'Ressonància (CC71)': () => 'CC71 0 → 127',
};

// REGLA DE TOTS ELS POTES (i d'aquesta família en particular, que la incomplia
// sencera): amb el pot EN REPÒS ha de sonar el mode tal com el vas construir, i
// girant-lo s'estira cap a l'extrem que interessa. Abans el repòs volia dir
// densitat mínima, intensitat zero i amplada zero — o sigui que un soroll fet a
// consciència arrencava mut i semblava que els potes no fessin res.
function potCodeSoroll(fn, spec, indent = '        ') {
  const i = indent;
  switch (fn) {
    case 'Densitat':
      // Al quadrat: el tram de baix és on hi ha el detall i necessita recorregut.
      return `${i}self.dens = _DENS + (v / 127.0) * (v / 127.0) * (_DENS_MAX - _DENS)`;
    case 'Cruixent':
      return `${i}self.cruix = _CRUIX + (v / 127.0) * (1.0 - _CRUIX)`;
    case 'Amplada':
      return `${i}self.ample = _AMPLE + int((v / 127.0) * (_AMPLE_MAX - _AMPLE))`;
    case 'Intensitat':
      return `${i}self.inten = _INTEN + (v / 127.0) * (1.0 - _INTEN)`;
    case 'Gruix del clúster':
      return `${i}self.gruix = _GRUIX + int((v / 127.0) * (_GRUIX_MAX - _GRUIX))`;
    case 'Espectre (α)':
      // Recalcula els coeficients només quan α s'ha mogut de debò: són _M
      // multiplicacions i no cal fer-les a cada volta del bucle.
      return `${i}a = _ALFA + (v / 127.0) * (_ALFA_POT - _ALFA)\n`
           + `${i}if a < self.alfa - 0.04 or a > self.alfa + 0.04:\n`
           + `${i}    self.alfa = a\n${i}    self._coefs(a)`;
    case 'Centre':
      // Dues octaves amunt des d'on l'has posat.
      return `${i}self.centre = _CENTRE + int((v / 127.0) * 24.0)`;
    case 'Velocitat de la FM':
      return `${i}self.fm_hz = _FM_HZ + (v / 127.0) * 60.0`;
    case 'Profunditat de la FM':
      return `${i}self.fm_prof = _FM_PROF + (v / 127.0) * (48.0 - _FM_PROF)`;
    case 'Dial (emissora)':
      // Aquest és EL pot de la ràdio: girant-lo travesses el dial sencer i les
      // emissores hi entren i en surten amb el seu xiulet.
      return `${i}self.dial = _DIAL + (v / 127.0)`;
    case 'Xiulet del dial':
      return `${i}self.xiulet = _XIULET + (v / 127.0) * (1.0 - _XIULET)`;
    case 'Brillantor (CC74)':
      return `${i}self._cc_once(74, v)`;
    case 'Ressonància (CC71)':
      return `${i}self._cc_once(71, v)`;
    default:
      return `${i}pass`;
  }
}

function generateNoise(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  const motor = SOROLL_MOTORS.includes(spec.motor) ? spec.motor : 'Núvol';
  // α és la font de veritat de l'espectre; el nom del color n'és només una
  // etiqueta. Els modes fets abans que α existís només duien el nom.
  const alfa = clamp(spec.alfa != null ? spec.alfa
                     : (SOROLL_ALFES[spec.color] ?? 0), -3, 3);
  const alfaPot = clamp(spec.alfaPot != null ? spec.alfaPot : -2, -3, 3);
  // Taps del filtre. El blanc i el violeta en necessiten dos o tres; el rosa i
  // el marró, molts (els coeficients cauen com j^(−0.5)). Es retallen els que
  // no aporten res: al dispositiu cada tap és una multiplicació per nota.
  const nTaps = (() => {
    const llarg = 48;
    // El α més alt del recorregut és el que necessita més memòria (el marró
    // integra i els seus coeficients no cauen mai; el violeta amb dos ja hi és).
    const { b } = coefsEspectre(Math.max(alfa, alfaPot), llarg);
    let n = llarg;
    while (n > 4 && Math.abs(b[n - 1]) < 0.004) n--;
    return n;
  })();
  const dens = clamp(spec.densitat ?? 12, .2, 400);
  const densMin = clamp(spec.densMin ?? 0.5, .1, 400);
  const densMax = clamp(spec.densMax ?? 300, .2, 400);
  const centre = clamp(spec.centre ?? 60, 0, 127);
  const ample = clamp(spec.ample ?? 24, 0, 60);
  const gruix = clamp(spec.gruix ?? 1, 1, 12);
  const inten = clamp(spec.intensitat ?? 70, 0, 100) / 100;
  const cruix = clamp(spec.cruix ?? 60, 0, 100) / 100;
  const maxVeus = clamp(spec.maxVeus ?? 20, 2, 48);
  const graMin = clamp(spec.graMin ?? 40, 1, 3000);
  const graMax = clamp(spec.graMax ?? 180, 1, 4000);
  const fmHz = clamp(spec.fmHz ?? 12, .2, 80);
  const fmProf = clamp(spec.fmProf ?? 12, 0, 48);
  const dial = clamp(spec.dial ?? 50, 0, 100) / 100;
  const estacions = clamp(spec.estacions ?? 4, 1, 12);
  const xiulet = clamp(spec.xiulet ?? 70, 0, 100) / 100;
  const ccBrill = !!spec.ccBrill;
  const ccRes = !!spec.ccRes;
  const potX = spec.pots?.x || 'Densitat';
  const potY = spec.pots?.y || 'Amplada';
  const potZ = spec.pots?.z || 'Intensitat';
  const spec4json = JSON.stringify({ ...spec, cat: 'soroll' });

  // ── El cos de cada motor ──
  // Van DINS de l'if del planificador: 12 espais d'indentació.
  const MOTORS = {
    'Núvol': `            # Un esdeveniment: una altura del soroll, gruixuda si cal.
            self._cluster(self._nota(), now)`,
    'Saturació': `            # Semitons adjacents alhora i a tota força: el batec entre
            # freqüències properes és el que l'oïda sent com a distorsió.
            base = self._nota()
            n = self.gruix if self.gruix > 2 else 3
            dur = self._dur()
            for k in range(n):
                self._cop(base + k, 118 + int(self.inten * 9), now, dur)`,
    'FM': `            # La portadora salta amunt i avall seguint una fase que corre a
            # self.fm_hz. A poca velocitat és un trèmolo; a molta, els salts
            # entre esdeveniments consecutius són tan grans que ja no se senten
            # notes sinó timbre — que és el que fa la modulació de freqüència.
            self.fase = (now * self.fm_hz) % 1.0
            despl = int((self.fase * 2.0 - 1.0) * self.fm_prof)
            self._cop(self.centre + despl, self._vel(), now, self._dur())`,
    'Dial': `            # Buscar emissora. Al dial hi ha _ESTACIONS emissores repartides;
            # self.dial diu on ets i la deriva l'arrossega sol.
            self.deriva = (now * _DERIVA) % 1.0
            d = (self.dial + self.deriva) % 1.0
            pos = d * _ESTACIONS
            k = int(pos + 0.5)                   # l'emissora més propera
            des = pos - k                        # desintonització: −0.5 … 0.5
            prop = 1.0 - abs(des) * 2.0          # 1 = clavat, 0 = just entremig
            if prop > 0.86:
                # Sintonitzada: l'emissora surt neta, amb la seva quinta, i el
                # xiulet ha desaparegut del tot.
                self.xn = -1
                base = self.emissora + k * 5
                self._cop(base, self._vel(), now, _DUR_MAX)
                if self.gruix > 1:
                    self._cop(base + 7, self._vel() - 18, now, _DUR_MAX)
            else:
                # Entre emissores. Dues coses passen alhora, i són les que fan
                # que això soni a ràdio i no a soroll qualsevol:
                #
                #  · el XIULET d'heterodí: el batec entre la portadora i el
                #    receptor. Com més desintonitzat, més agut; sintonitzant,
                #    el xiulet BAIXA fins a desaparèixer. És el so que reconeix
                #    tothom que hagi buscat una emissora d'ona mitjana.
                #  · el soroll de fons puja com més lluny ets de l'emissora,
                #    perquè el control automàtic de guany obre al no trobar
                #    senyal. Just entremig, la ràdio bufa a tot drap.
                self.xn = self.centre + 12 + int(abs(des) * 2.0 * 30.0)
                if self.xiulet > 0.02 and random.random() < self.xiulet:
                    self._cop(self.xn, int(40 + prop * 50.0), now, _DUR_MAX * 0.7)
                if random.random() < 0.05:
                    self.emissora = self.centre + random.randint(-9, 9)
                # El fons és més fort al mig de dues emissores (1 − prop).
                antic = self.inten
                self.inten = antic * (0.35 + 0.65 * (1.0 - prop))
                self._cluster(self._nota(), now)
                self.inten = antic`,
    'Impulsos': `            # Espurnes: molt curtes i fluixes. El silenci entremig és el
            # que fa que això sigui pluja i no una paret.
            self._cop(self._nota(), 20 + int(self.inten * 60), now, self._dur())`,
  };

  // Els motors que no fan servir la fase o la deriva no en necessiten l'estat,
  // però tenir-lo sempre surt més barat que sis variants de la classe.
  return `"""${nom} — soroll fet amb el constructor de TECLA.
X: ${potX}  Y: ${potY}  Z: ${potZ}
Motor: ${motor} · espectre: ${nomPerAlfa(alfa)} (α = ${py.f(alfa, 2)})
L'espectre segueix la llei S(f) ∝ 1/f^α: 0 blanc, 1 rosa, 2 marró, −1 blau,
−2 violeta, i tot el que hi ha entremig.
"""
# TECLA-SPEC ${spec4json}
import time
import random
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

_MOTOR = "${motor}"
# Espectre: S(f) ∝ 1/f^α. 0 blanc · 1 rosa · 2 marró · −1 blau · −2 violeta.
_ALFA = ${py.f(alfa, 2)}
_ALFA_POT = ${py.f(alfaPot, 2)}         # on arriba el pot d'espectre
_M = ${nTaps}                           # taps del filtre: fins on baixa el 1/f
_GUANY = ${py.f(SOROLL_GUANY)}          # RMS ≈ 0.42: el retall a ±1 quasi no actua
_DENS = ${py.f(dens)}                  # el que has posat: el repòs dels potes
_DENS_MAX = ${py.f(Math.max(densMax, dens))}
_CENTRE = ${centre}
_AMPLE = ${ample}
_AMPLE_MAX = ${Math.max(ample, 48)}
_GRUIX = ${gruix}
_GRUIX_MAX = ${Math.max(gruix, 12)}
_INTEN = ${py.f(inten)}
_CRUIX = ${py.f(cruix)}
_DIAL = ${py.f(dial)}
_DUR_MIN = ${py.f(Math.min(graMin, graMax) / 1000, 4)}
_DUR_MAX = ${py.f(Math.max(graMin, graMax) / 1000, 4)}
_FM_HZ = ${py.f(fmHz)}
_FM_PROF = ${fmProf}
_DERIVA = ${py.f(dial * 0.35)}
_ESTACIONS = ${estacions}
_XIULET = ${py.f(xiulet)}
_MAX_VEUS = ${maxVeus}
_MAX_PER_TICK = 10          # notes per volta del bucle (a 100 Hz: 1000/s)
_MIN_NOTA = 12
_MAX_NOTA = 120


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.alfa = _ALFA
        self.b = [1.0] * _M        # coeficients del filtre d'espectre
        self.norm = 1.0
        self.hist = [0.0] * _M     # historial circular de soroll blanc
        self.hp = 0
        self.dens = _DENS          # esdeveniments per segon
        self.centre = _CENTRE
        self.ample = _AMPLE
        self.gruix = _GRUIX
        self.inten = _INTEN
        self.cruix = _CRUIX        # 0 = grans amb durada · 1 = espurnes
        self.deute = 0.0        # esdeveniments que toquen i encara no s'han fet
        self.pressupost = _MAX_PER_TICK
        self.fm_hz = _FM_HZ
        self.fm_prof = _FM_PROF
        self.dial = _DIAL
        self.xiulet = _XIULET
        self.xn = -1            # nota del xiulet d'heterodí (−1 = sintonitzat)
        self.deriva = 0.0
        self.emissora = _CENTRE
        self.fase = 0.0
        self.pend = []          # note-offs pendents: [nota, quan]
        self.t_ant = 0.0
        self._cc_cache = {}

    def setup(self):
        self.initialized = True
        now = time.monotonic()
        self.t_ant = now
        self.deute = 0.0
        self.pend = []
        self._cc_cache = {}
        self.hist = [0.0] * _M
        self.hp = 0
        self._coefs(self.alfa)
        print("${nom}: ${motor} alfa=%.2f %.1f/s" % (self.alfa, self.dens))

    def _cc_once(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _coefs(self, alfa):
        """Els coeficients del filtre que dona espectre S(f) ∝ 1/f^α.

        Generar soroll de qualsevol pendent és fer una INTEGRACIÓ FRACCIONÀRIA
        d'ordre d = α/2 sobre soroll blanc. Els coeficients són els de la sèrie
        binomial de (1 − B)^(−d), que surten d'una recurrència d'una línia:

            b[0] = 1        b[j] = b[j−1] · (j − 1 + d) / j

        i ja hi són tots els colors, sense casos especials:

            α = 0  → d = 0    → b = (1, 0, 0…)      blanc     PSD ∝ 1
            α = 1  → d = 0.5  → b[j] ~ j^(−0.5)     rosa      PSD ∝ 1/f
            α = 2  → d = 1    → b = (1, 1, 1…)      marró     PSD ∝ 1/f²
            α = −1 → d = −0.5                       blau      PSD ∝ f
            α = −2 → d = −1   → b = (1, −1, 0…)     violeta   PSD ∝ f²

        Amb d = 1 el filtre és una suma acumulada (integrar) i amb d = −1 una
        diferència (derivar): els casos que abans estaven escrits a mà ara en
        surten sols, i els valors d'entremig —α = 1.5, α = −0.3…— també.

        La normalització per l'energia dels coeficients deixa TOTS els colors
        amb la mateixa amplitud: el que canvia entre un i altre és el caràcter,
        no el volum.

        Truncar la sèrie a _M taps limita fins on baixa la llei: per sota de
        f ≈ 1/_M la resposta s'aplana. Amb α alt (marró) això no és un defecte
        sinó el que el fa ESTABLE — una integral pura derivaria sense aturador.
        """
        d = alfa * 0.5
        b = [1.0] * _M
        for j in range(1, _M):
            b[j] = b[j - 1] * (j - 1 + d) / j
        e = 0.0
        for x in b:
            e += x * x
        self.b = b
        self.norm = (_GUANY / (e ** 0.5)) if e > 0.0 else 1.0

    def _soroll(self):
        """Una mostra de soroll de l'espectre triat, entre −1 i 1."""
        # Historial circular de soroll blanc: hp és la mostra d'ara i hp+j la de
        # fa j passos. Truncar a _M taps limita fins on baixa el 1/f, i de retruc
        # estabilitza el marró — una integral pura derivaria sense aturador.
        self.hp = self.hp - 1
        if self.hp < 0:
            self.hp = _M - 1
        self.hist[self.hp] = random.random() * 2.0 - 1.0
        s = 0.0
        p = self.hp
        for j in range(_M):
            s += self.b[j] * self.hist[p]
            p += 1
            if p >= _M:
                p = 0
        v = s * self.norm
        return -1.0 if v < -1.0 else (1.0 if v > 1.0 else v)

    def _nota(self):
        n = self.centre + int(self._soroll() * self.ample)
        return _MIN_NOTA if n < _MIN_NOTA else (_MAX_NOTA if n > _MAX_NOTA else n)

    def _vel(self):
        v = int(28 + self.inten * 99)
        return 1 if v < 1 else (127 if v > 127 else v)

    def _dur(self):
        """Durada d'un esdeveniment. El CRUIXENT l'escurça fins a fer-la zero:
        aleshores el note_off surt tot seguit del note_on i el que se sent no és
        una nota sinó un CLIC. Un clic no és res; milers de clics per segon són
        soroll — és així com es fa soroll amb notes MIDI."""
        d = _DUR_MIN + random.random() * (_DUR_MAX - _DUR_MIN)
        return d * (1.0 - self.cruix)

    def _cop(self, nota, vel, now, dur):
        if nota < _MIN_NOTA or nota > _MAX_NOTA:
            return
        # Pressupost de notes per volta del bucle. Amb clústers gruixuts i
        # densitat alta se'n dispararien milers per segon: el bus MIDI ho
        # aguantaria, però cap sintetitzador —ni el del navegador ni el del
        # dispositiu— no aguanta mil oscil·ladors oberts. Per damunt d'aquest
        # sostre el so ja no es densifica més, només es trenca.
        if self.pressupost <= 0:
            return
        self.pressupost = self.pressupost - 1
        vel = 1 if vel < 1 else (127 if vel > 127 else int(vel))
        self.send_note_on(nota, vel)
        if dur <= 0.003:
            # Espurna: atac i caiguda a la mateixa volta del bucle.
            self.send_note_off(nota, 0)
            return
        self.pend.append([nota, now + dur])
        # Sostre de veus: sense això, a densitat alta el mode acaba amb centenars
        # de notes obertes i el sintetitzador es rendeix.
        if len(self.pend) > _MAX_VEUS:
            vella = self.pend.pop(0)
            self.send_note_off(vella[0], 0)

    def _cluster(self, base, now):
        """Un esdeveniment de gruix notes: una de sola és un gra, dotze són paret."""
        dur = self._dur()
        self._cop(base, self._vel(), now, dur)
        for _ in range(self.gruix - 1):
            # Cada veu del clúster té la seva pròpia altura i força: si totes
            # fossin iguals no seria soroll, seria una nota gruixuda.
            self._cop(base + random.randint(-3, 3),
                      self._vel() - random.randint(0, 30), now, dur)

    def _allibera(self, now, totes=False):
        if not self.pend:
            return
        queden = []
        for p in self.pend:
            if totes or now >= p[1]:
                self.send_note_off(p[0], 0)
            else:
                queden.append(p)
        self.pend = queden

    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()
        self.pressupost = _MAX_PER_TICK

        self._allibera(now)

        # ── Els tres potes, tal com s'han assignat ──
        v = px
${potCodeSoroll(potX, spec)}
        v = py_
${potCodeSoroll(potY, spec)}
        v = pz
${potCodeSoroll(potZ, spec)}
${ccBrill ? `
        # La intensitat obre el filtre: com més violent, més brillant.
        self._cc_once(74, int(self.inten * 127))` : ''}${ccRes ? `
        self._cc_once(71, int(self.inten * 127))` : ''}

        # ── Esdeveniments ──
        # Comptador de DEUTE en comptes d'un rellotge de "quan toca el següent":
        # si la densitat és més alta que la freqüència del bucle, en un sol pas
        # se'n disparen uns quants. Sense això la densitat quedava topada pel
        # bucle (20/s al simulador) i el soroll no arribava mai a ser soroll —
        # eren notes ràpides. Els modes de la casa que sonen a soroll de debò
        # (mode_mandelbrot, mode_tormenta) fan justament això: emeten a cada
        # volta del bucle, sense esperar.
        dt = now - self.t_ant
        if dt > 0.25:                    # una pausa llarga no ha de fer allau
            dt = 0.25
        self.deute = self.deute + self.dens * dt
        n = int(self.deute)
        if n > 0:
            self.deute = self.deute - n
            if n > _MAX_PER_TICK:
                n = _MAX_PER_TICK
            for _ in range(n):
${MOTORS[motor].split('\n').map(l => l ? '    ' + l : l).join('\n')}

        self.t_ant = now
        return {'motor': _MOTOR, 'alfa': round(self.alfa, 2),
                'dens': round(self.dens, 1), 'ample': self.ample,
                'dial': round(self.dial % 1.0, 3), 'xn': self.xn}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
        for c, val in ((74, 0), (71, 0), (1, 0), (11, 127), (123, 0), (120, 0)):
            try:
                self.midi_out.send(ControlChange(c, val))
            except Exception:
                pass
`;
}

// ── ACORDS ────────────────────────────────────────────────────────────────
// La família que aplega tot el que sap l'app d'harmonia: una progressió teva,
// amb la qualitat de cada acord treta de la FUNCIÓ harmònica (diatònica,
// dominants secundàries, napolità, sisenes augmentades…), conduïda amb voice
// leading de debò i amb l'harmonia negativa i l'arpegiador a sobre.
//
// El que la fa diferent de la família drone: allà un acord es queda quiet;
// aquí el que importa és el CAMÍ d'un acord al següent, i per això la
// conducció de veus no és un adorn sinó el motor.

/** Els acords, per nom. Mateixa taula que CHORDS_JS de tecla-music-data.js. */
export const ACORDS_TIPUS = {
  'Major': [0, 4, 7], 'm': [0, 3, 7], '7': [0, 4, 7, 10], 'maj7': [0, 4, 7, 11],
  'm7': [0, 3, 7, 10], 'dim': [0, 3, 6], 'aug': [0, 4, 8], 'sus4': [0, 5, 7],
  'sus2': [0, 2, 7], 'm7b5': [0, 3, 6, 10], '6': [0, 4, 7, 9], 'add9': [0, 4, 7, 14],
  '9': [0, 4, 7, 10, 14], 'm9': [0, 3, 7, 10, 14], '69': [0, 4, 7, 9, 14],
  '7sus4': [0, 5, 7, 10], '7b9': [0, 4, 7, 10, 13], '13': [0, 4, 7, 10, 14, 21],
};

/** Les dotze formes de conducció de veus (mateix ordre que VL_TYPES). */
export const ACORDS_VL = ['proximitat', 'comu', 'baix', 'ascendent', 'descendent',
  'obert', 'tancat', 'fonamental', 'inv1', 'inv2', 'drop2', 'pendol'];

/** Els vuit eixos d'harmonia negativa (mateix ordre que NEG_HARM_AXES). */
export const ACORDS_EIXOS = ['Quinta', 'Unisonant', 'Tercera M', 'Tercera m',
  'Tritó', 'Quarta', 'Sexta M', 'Sèptima m'];

/** Patrons d'arpegi que el mode sap fer. */
export const ACORDS_ARPS = ['Bloc', 'Amunt', 'Avall', 'Ping-pong', 'Alberti', 'Aleatori'];

/**
 * TAULES D'ACORDS — una taula és una llista de POSICIONS, i cada posició és un
 * grapat de veus. La idea ve del Plaits Palette (rubato.audio), on el
 * comandament recorre una taula de posicions en comptes d'avançar una
 * progressió en el temps. Les dues coses són complementàries i aquí conviuen:
 * la progressió avança sola i el pot escombra la taula.
 *
 * Cada veu és un INTERVAL EN SEMITONS des de la fonamental, que és el que un
 * músic llegeix i el que es pot arrossegar amb el dit. Opcionalment hi pot
 * haver una desviació en CENTS per a les afinacions que no cauen a la graella
 * temperada: ara el mode les arrodoneix, però queden desades perquè el dia que
 * enviem pitch-bend per veu no calgui migrar cap taula.
 *
 *   [0, 4, 7]                      → tríada major
 *   [[0, 0], [4, -14], [7, 2]]     → la mateixa amb la tercera justa (5/4)
 */
/**
 * Les tres transformacions neo-riemannianes sobre una tríada. Cadascuna mou
 * EXACTAMENT una veu, un semitò o un to — per això el Tonnetz és el mapa
 * canònic de la conducció de veus mínima.
 *
 *   P (paral·lela) · major↔menor: la tercera puja o baixa un semitò
 *   L (sensible)   · Do major → Mi menor: la fonamental baixa un semitò
 *   R (relativa)   · Do major → La menor: la quinta puja un to
 *
 * @param {string} passos  seqüència de lletres, p. ex. 'PLPLPL'
 * @returns {Array<[string, number[]]>} posicions [nom, intervals]
 */
export function tonnetzWalk(passos) {
  const NOMS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  // Estat: fonamental (semitons des de Do) i si és major
  let arrel = 0, major = true;
  const triada = () => (major ? [arrel, arrel + 4, arrel + 7] : [arrel, arrel + 3, arrel + 7]);
  const nom = () => NOMS[((arrel % 12) + 12) % 12] + (major ? '' : 'm');
  const out = [[nom(), triada()]];
  for (const p of String(passos || '').toUpperCase()) {
    if (p === 'P') { major = !major; }
    else if (p === 'L') { if (major) { arrel += 4; major = false; } else { arrel -= 4; major = true; } }
    else if (p === 'R') { if (major) { arrel += 9; major = false; } else { arrel += 3; major = true; } }
    else continue;
    // Es replega a l'octava de Do perquè la taula no se'n vagi cap amunt
    while (arrel > 6) arrel -= 12;
    while (arrel < -6) arrel += 12;
    out.push([`${nom()}  (${p})`, triada()]);
  }
  return out;
}

export const ACORDS_TAULES = [
  {
    id: 'original', nom: 'Original', autor: 'Mutable Instruments', cat: 'Paletes',
    desc: 'Les onze posicions del Plaits, de l’octava nua a la tríada major.',
    pos: [
      ['Octava', [0, 12]], ['Quinta', [0, 7, 12]], ['Sus4', [0, 5, 7]],
      ['Menor', [0, 3, 7]], ['Menor 7a', [0, 3, 7, 10]], ['Menor 9a', [0, 3, 10, 14]],
      ['Menor 11a', [0, 3, 10, 17]], ['6/9', [0, 4, 9, 14]],
      ['Major 9a', [0, 4, 11, 14]], ['Major 7a', [0, 4, 7, 11]], ['Major', [0, 4, 7]],
    ],
  },
  {
    id: 'tonnetz', nom: 'Passeig pel Tonnetz', autor: 'neo-riemannià', cat: 'Progressions',
    desc: 'Les tres transformacions del reticle: P (paral·lela, major↔menor), '
        + 'L (sensible) i R (relativa). Cada pas mou UNA sola veu un semitò o un '
        + 'to — és la conducció de veus mínima portada a l’extrem.',
    pos: tonnetzWalk('PLPLPLRPLPLPLR'),
  },
  {
    id: 'coltrane', nom: 'Coltrane', autor: 'cicle de terceres majors', cat: 'Progressions',
    desc: 'El cicle de Giant Steps: la tònica baixa una tercera major a cada '
        + 'volta i divideix l’octava en tres parts iguals.',
    pos: [
      ['Bmaj7', [0, 4, 7, 11]], ['D7', [3, 7, 10, 13]], ['Gmaj7', [-4, 0, 3, 7]],
      ['Bb7', [-1, 3, 6, 9]], ['Ebmaj7', [-8, -4, -1, 3]], ['F#7', [-5, -1, 2, 5]],
    ],
  },
  {
    id: 'blues', nom: 'Blues de dotze', autor: 'tradicional', cat: 'Progressions',
    desc: 'I7–IV7–V7 amb les setenes de dominant que li donen el color.',
    pos: [
      ['I7', [0, 4, 7, 10]], ['IV7', [5, 9, 12, 15]], ['V7', [7, 11, 14, 17]],
      ['bVII7', [10, 14, 17, 20]], ['I7 (tanca)', [0, 4, 7, 10]],
    ],
  },
  {
    id: 'quartal', nom: 'Quartals', autor: 'McCoy Tyner', cat: 'Paletes',
    desc: 'Acords per quartes en comptes de per terceres: sonen oberts i sense '
        + 'mode definit, el color del jazz modal.',
    pos: [
      ['Quartal 3', [0, 5, 10]], ['Quartal 4', [0, 5, 10, 15]],
      ['Quartal 5', [0, 5, 10, 15, 20]], ['So What', [0, 5, 10, 15, 19]],
      ['Quintal', [0, 7, 14]], ['Quintal 4', [0, 7, 14, 21]],
    ],
  },
  {
    id: 'campanes', nom: 'Campanes', autor: 'espectre inharmònic', cat: 'Microtonals',
    desc: 'Els parcials d’una campana no són harmònics: hi ha una tercera menor '
        + 'i un tritó que fan aquell so metàl·lic. Amb les desviacions de debò.',
    pos: [
      ['Campana', [[0, 0], [3, -14], [7, 2], [12, 0], [16, -14]]],
      ['Gong', [[0, 0], [2, 4], [7, 2], [11, -12], [14, 4]]],
      ['Tubular', [[0, 0], [9, -16], [16, 2], [21, -31], [24, 0]]],
    ],
  },
  {
    id: 'harmonica', nom: 'Sèrie harmònica', autor: 'entonació justa', cat: 'Microtonals',
    desc: 'Els primers parcials tal com sonen de debò: la tercera hi és 14 cents '
        + 'més baixa que al piano i la setena, 31.',
    pos: [
      ['1–3–5', [[0, 0], [7, 2], [16, -14]]],
      ['1–3–5–7', [[0, 0], [7, 2], [16, -14], [22, -31]]],
      ['1–3–5–7–9', [[0, 0], [7, 2], [16, -14], [22, -31], [26, 4]]],
      ['Sèptima justa', [[0, 0], [4, -14], [7, 2], [10, -31]]],
    ],
  },
];

/** Els potes que la família acords sap fer servir. */
export const ACORDS_POT_FNS = ['Tempo', 'Conducció de veus', 'Harmonia negativa',
  'Reflex gradual', 'Taula d\'acords', 'Extensió de l\'acord', 'Arpegiador', 'Velocitat de l\'arpegi',
  'Octava', 'Obertura', 'Gate', 'Tonalitat', 'Brillantor (CC74)', 'Modulació (CC1)', '—'];

/** Les veus d'una posició, en semitons (arrodonint els cents si n'hi ha). */
export function veusDePosicio(pos) {
  return (pos || []).map(v => (Array.isArray(v) ? Math.round(v[0] + (v[1] || 0) / 100) : v));
}

/** La desviació en cents d'una posició (0 si la veu és un semitò net). */
export function centsDePosicio(pos) {
  return (pos || []).map(v => (Array.isArray(v) ? (v[1] || 0) : 0));
}

function potCodeAcords(fn, spec, nPassos, indent = '        ') {
  const i = indent;
  const bpmMin = clamp(spec.bpmMin ?? 60, 20, 300);
  const bpmMax = clamp(spec.bpmMax ?? 120, 20, 300);
  switch (fn) {
    case 'Tempo':
      return `${i}self.bpm = ${py.f(Math.min(bpmMin, bpmMax))} + (v / 127.0) * ${py.f(Math.abs(bpmMax - bpmMin))}`;
    case 'Conducció de veus':
      // Les dotze formes, en dotze trams. Comença per la que has triat: en
      // repòs la progressió es condueix tal com l'has feta.
      return `${i}k = (_VL0 + min(11, int((v / 128.0) * 12))) % 12\n`
           + `${i}if self._tram('vl', k, v):\n${i}    self.vl = _VL_NOMS[k]`;
    case 'Harmonia negativa':
      // Repòs = com l'has fet. A partir d'un terç, s'encén i els vuit eixos es
      // reparteixen la resta del recorregut: un sol pot fa les dues coses.
      return `${i}if v < 42:\n${i}    self.neg = _NEG0\n${i}    self.neg_eix = _EIX0\n`
           + `${i}else:\n${i}    self.neg = True\n`
           + `${i}    self.neg_eix = min(7, int(((v - 42) / 86.0) * 8))`;
    case 'Reflex gradual':
      // L'harmonia negativa deixa de ser un interruptor: el pot decideix
      // QUANTES veus es reflecteixen, de dalt cap avall. A mig camí, la meitat
      // de l'acord és negativa i l'altra meitat no — un color que no és ni
      // l'un ni l'altre i que no es pot fer de cap altra manera.
      return `${i}self.neg_morph = v / 127.0`;
    case 'Taula d\'acords':
      // El pot deixa d'avançar la progressió i ESCOMBRA la taula: la
      // fonamental la posa el pas on ets, i la taula en dona la forma. En
      // repòs (posició 0) sona el que has muntat al formulari.
      return `${i}t = min(_N_TAULA - 1, int((v / 128.0) * _N_TAULA))\n`
           + `${i}if self._tram('taula', t, v):\n${i}    self.taula = t\n`
           + `${i}    self._toca_acord()`;
    case 'Extensió de l\'acord':
      // De la tríada nua a les tensions: afegeix 7a, 9a i 13a per trams.
      return `${i}self.extensio = min(3, int((v / 128.0) * 4))`;
    case 'Arpegiador':
      return `${i}k = min(${ACORDS_ARPS.length - 1}, int((v / 128.0) * ${ACORDS_ARPS.length}))\n`
           + `${i}if self._tram('arp', k, v):\n${i}    self.arp = k`;
    case 'Velocitat de l\'arpegi':
      return `${i}self.arp_div = (1, 2, 3, 4, 6, 8)[min(5, int((v / 128.0) * 6))]`;
    case 'Octava':
      return `${i}o = _OCT + int((v / 127.0) * 2.99)\n`
           + `${i}if self._tram('oct', o, v):\n${i}    self.octave = o`;
    case 'Obertura':
      // Separa les veus estirant-les cap amunt d'octava en octava.
      return `${i}self.obertura = (v / 127.0) * 12.0`;
    case 'Gate':
      return `${i}self.gate = ${py.f(clamp(spec.gate ?? 80, 5, 100) / 100)} + (v / 127.0) * ${py.f(1.0 - clamp(spec.gate ?? 80, 5, 100) / 100)}`;
    case 'Tonalitat':
      return `${i}k = int((v / 127.0) * 11.99)\n`
           + `${i}if self._tram('to', k, v):\n${i}    self.key = k`;
    case 'Brillantor (CC74)':
      return `${i}self._cc_once(74, v)`;
    case 'Modulació (CC1)':
      return `${i}self._cc_once(1, v)`;
    default:
      return `${i}pass`;
  }
}

function generateChords(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  const escala = (spec.escalaIntervals && spec.escalaIntervals.length
    ? spec.escalaIntervals : [0, 2, 4, 5, 7, 9, 11]).map(x => clamp(x | 0, 0, 24));
  const key = clamp(spec.tonalitat | 0, 0, 11);
  const oct = clamp(spec.octava ?? 3, 0, 7);
  const vel = clamp(spec.vel ?? 90, 1, 127);
  const gate = clamp(spec.gate ?? 80, 5, 100) / 100;
  const bpmMin = clamp(spec.bpmMin ?? 60, 20, 300);
  const bpmMax = clamp(spec.bpmMax ?? 120, 20, 300);
  const vl0 = Math.max(0, ACORDS_VL.indexOf(spec.vl || 'proximitat'));
  const vlOn = spec.vlOn !== false;
  const negOn = !!spec.negOn;
  const eix0 = clamp(spec.negEix | 0, 0, 7);
  const arp0 = Math.max(0, ACORDS_ARPS.indexOf(spec.arp || 'Bloc'));
  const arpDiv = clamp(spec.arpDiv ?? 4, 1, 8);
  const baixOn = !!spec.baixOn;
  const baixOct = clamp(spec.baixOctava ?? 2, 0, 6);

  // La progressió. Cada pas: grau de l'escala, funció harmònica i durada en
  // pulsacions. El tipus d'acord surt de la FUNCIÓ (com a la capa teclat), o
  // el forces tu si has triat un tipus concret.
  const passos = (spec.passos && spec.passos.length ? spec.passos : [{ grau: 0, fn: 'diatonic', dur: 4 }])
    .map(p => [clamp(p.grau | 0, 0, 13), String(p.fn || 'diatonic'), clamp(p.dur ?? 4, 1, 32)]);

  // Les qualitats es resolen AQUÍ, en JS, amb la mateixa taula que la capa
  // teclat: el mode generat ja rep la llista d'intervals resolta i no ha de
  // portar-se tota la teoria a la Pico.
  const resolts = passos.map(([grau, fn]) => {
    const [offset, tipus] = applyHarmonicFn(escala, grau, fn);
    const ivs = Array.isArray(tipus) ? tipus : (ACORDS_TIPUS[tipus] || [0, 4, 7]);
    const arrel = escala[grau % escala.length] + 12 * Math.floor(grau / escala.length) + offset;
    return [arrel, ivs];
  });

  // La TAULA que el pot escombra. La posició 0 és sempre "com l'has fet": el
  // pot en repòs no ha de canviar res del que sents al formulari.
  const taula = ACORDS_TAULES.find(t => t.id === spec.taula) || null;
  const posicions = taula
    ? [[null, null], ...taula.pos.map(([n, p]) => [n, veusDePosicio(p)])]
    : [[null, null]];

  const spec4json = JSON.stringify({ ...spec, cat: 'acords' });

  return `"""${nom} — progressió d'acords feta amb el Laboratori de TECLA.
X: ${spec.pots?.x || 'Tempo'}  Y: ${spec.pots?.y || 'Conducció de veus'}  Z: ${spec.pots?.z || 'Harmonia negativa'}
${passos.length} acords · conducció ${spec.vl || 'proximitat'}${negOn ? ` · harmonia negativa (${ACORDS_EIXOS[eix0]})` : ''}
Mantenir premut el botó 16: harmonia negativa.
"""
# TECLA-SPEC ${spec4json}
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# Cada pas: (arrel en semitons des de la tònica, intervals de l'acord, durada)
_PROG = (
${resolts.map(([arrel, ivs], k) => `    (${arrel}, ${py.tuple(ivs)}, ${passos[k][2]}),`).join('\n')}
)
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
# Taula d'acords: la posició 0 és la de la progressió (com l'has fet) i la
# resta són les formes de la taula, que el pot escombra sobre la MATEIXA arrel.
_TAULA = (
${posicions.map(([n, v]) => `    ${v ? py.tuple(v) : 'None'},   # ${n || 'com el has fet'}`).join('\n')}
)
_N_TAULA = ${posicions.length}
_VL_NOMS = ${py.tuple(ACORDS_VL.map(v => `'${v}'`))}
_VL0 = ${vl0}
_NEG0 = ${negOn ? 'True' : 'False'}
_EIX0 = ${eix0}
_OCT = ${oct}
_VEL = ${vel}
_GATE = ${py.f(gate)}
_BPM = ${py.f((bpmMin + bpmMax) / 2)}
_ARP_DIV = ${arpDiv}
_BAIX = ${baixOn ? 'True' : 'False'}
_BAIX_OCT = ${baixOct}
_HIST = 3
_MIN_NOTA = 12
_MAX_NOTA = 108


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.key = ${key}
        self.octave = _OCT
        self.bpm = _BPM
        self.vl = _VL_NOMS[_VL0]
        self.vl_on = ${vlOn ? 'True' : 'False'}
        self.neg = _NEG0
        self.neg_eix = _EIX0
        # Quina PART de l'acord es reflecteix (0 = cap · 1 = tot l'acord)
        self.neg_morph = 1.0 if _NEG0 else 0.0
        self.taula = 0           # 0 = la forma de la progressió; 1.. = la taula
        self.extensio = 0        # 0 = tal com l'has fet; 1..3 hi afegeix tensions
        self.obertura = 0.0
        self.gate = _GATE
        self.arp = ${arp0}
        self.arp_div = _ARP_DIV
        self.pas = 0             # quin acord de la progressió
        self.puls = 0            # quantes pulsacions porta aquest acord
        self.t = 0.0
        self.t_puls = 0.0
        self.sonant = []         # notes de l'acord que sonen ara
        self.veus = []           # el voicing sencer (per a la pantalla)
        self.arp_i = 0
        self.arp_t = 0.0
        self.baix_nota = -1
        self.vl_prev = None      # voicing anterior: el que fa la conducció
        self.pendol_amunt = False
        self._trams = {}
        self._cc_cache = {}
        self._llavor = 12345

    def setup(self):
        self.initialized = True
        self.t = time.monotonic()
        self.t_puls = self.t
        self.arp_t = self.t
        self.pas = 0
        self.puls = 0
        self.vl_prev = None
        self._trams = {}
        self._cc_cache = {}
        # L'harmonia negativa ha d'estar posada ABANS de muntar el primer
        # acord: base_mode reflecteix segons neg_active, i si esperéssim al
        # primer update() la primera volta de la progressió sortiria sense
        # reflectir.
        self.neg_active = bool(self.neg)
        if self.neg:
            self.neg_axis = self.neg_eix
        self._toca_acord()

    # ── Utilitats ────────────────────────────────────────────────────────
    def _tram(self, k, i, v):
        """Índex de tram amb histèresi: al límit entre dos trams el pot
        tremola, i sense això la forma de conducció saltaria a cada volta."""
        vell, vell_v = self._trams.get(k, (-1, -999))
        if i == vell or abs(v - vell_v) < _HIST:
            return False
        self._trams[k] = (i, v)
        return True

    def _cc_once(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _atzar(self, n):
        """Congruencial lineal: sense el mòdul random, que a la Pico pesa."""
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % max(1, n)

    # ── Conducció de veus ────────────────────────────────────────────────
    # Port compacte de modes/kbd_voicelead.py: mateixes formes i mateix cost,
    # perquè la progressió soni igual aquí que a la capa teclat.
    def _cost(self, cand, prev, bass_pc, es_drop2):
        total = 0
        for n in cand:
            millor = 128
            for p in prev:
                d = n - p
                if d < 0:
                    d = -d
                if d < millor:
                    millor = d
            total += millor
        lo = min(cand)
        baix = abs(lo - min(prev))
        vl = self.vl
        if vl == 'comu':
            comuns = 0
            for n in cand:
                if n in prev:
                    comuns += 1
            return -4 * comuns + total
        if vl == 'baix':
            return 3 * baix + total
        if vl == 'ascendent':
            return (60 if lo < min(prev) else 0) + total
        if vl == 'descendent':
            return (60 if lo > min(prev) else 0) + total
        if vl == 'obert':
            return -(max(cand) - lo) + total
        if vl == 'tancat':
            return (max(cand) - lo) * 2 + total
        if vl in ('fonamental', 'inv1', 'inv2'):
            return (0 if lo % 12 == bass_pc else 80) + total + baix // 2
        if vl == 'drop2':
            return (0 if es_drop2 else 80) + total
        if vl == 'pendol':
            if self.pendol_amunt:
                return (60 if lo < min(prev) else 0) + total
            return (60 if lo > min(prev) else 0) + total
        return total + baix // 2

    def _candidats(self, notes):
        obert = (self.vl == 'obert')
        drop2 = (self.vl == 'drop2')
        base = sorted(notes)
        n = len(base)
        out = []
        for inv in range(n):
            v = sorted(base[inv:] + [x + 12 for x in base[:inv]])
            variants = [(v, False)]
            if obert and n >= 3:
                variants.append((sorted([(x + 12) if (i % 2 == 1) else x
                                         for i, x in enumerate(v)]), False))
            if drop2 and n >= 3:
                d2 = list(v)
                d2[-2] -= 12
                variants.append((sorted(d2), True))
            for vv, isd2 in variants:
                for despl in (-12, 0, 12):
                    cand = [x + despl for x in vv]
                    if all(_MIN_NOTA <= x <= _MAX_NOTA for x in cand):
                        out.append((cand, isd2))
        return out or [(base, False)]

    def _condueix(self, notes):
        """El voicing de 'notes' segons la forma activa. 'notes' arriba en
        ordre d'intervals (fonamental, 3a, 5a…): les inversions en depenen."""
        if not notes or not self.vl_on:
            return notes
        if self.vl == 'pendol':
            self.pendol_amunt = not self.pendol_amunt
        if not self.vl_prev:
            self.vl_prev = sorted(notes)
            return notes
        if self.vl == 'inv1' and len(notes) > 1:
            bass_pc = notes[1] % 12
        elif self.vl == 'inv2' and len(notes) > 2:
            bass_pc = notes[2] % 12
        else:
            bass_pc = notes[0] % 12
        millor = None
        millor_cost = 1 << 30
        for cand, isd2 in self._candidats(notes):
            c = self._cost(cand, self.vl_prev, bass_pc, isd2)
            if c < millor_cost:
                millor_cost = c
                millor = cand
        self.vl_prev = millor
        return millor

    # ── L'acord ──────────────────────────────────────────────────────────
    def _notes_del_pas(self, k):
        """Les notes MIDI de l'acord k, amb extensió, obertura i harmonia
        negativa aplicades."""
        arrel_rel, ivs, _ = _PROG[k % len(_PROG)]
        arrel = self.octave * 12 + self.key + arrel_rel
        # La taula, si el pot l'ha mogut: mateixa arrel, forma de la taula
        forma = _TAULA[self.taula] if 0 <= self.taula < _N_TAULA else None
        ivs = list(forma) if forma else list(ivs)
        # Extensió: la tríada s'omple de tensions sense repetir el que ja hi és
        if self.extensio >= 1 and 10 not in ivs and 11 not in ivs:
            ivs.append(11 if (0 in ivs and 4 in ivs and 7 in ivs) else 10)
        if self.extensio >= 2 and 14 not in ivs:
            ivs.append(14)
        if self.extensio >= 3 and 21 not in ivs:
            ivs.append(21)
        notes = []
        for j, iv in enumerate(ivs):
            n = arrel + iv + int(self.obertura) * (1 if j % 2 else 0)
            if _MIN_NOTA <= n <= _MAX_NOTA and n not in notes:
                notes.append(n)
        # ── Reflex GRADUAL ──────────────────────────────────────────────
        # L'harmonia negativa no és un interruptor: es reflecteixen les veus
        # de DALT cap avall segons neg_morph. Amb mitja volta, la meitat de
        # l'acord és negativa i l'altra no, i en surt un color ambigu que no
        # és ni el positiu ni el negatiu.
        # Manen els dos controls sense trepitjar-se: el pot gradual si l'has
        # mogut, i si no, l'interruptor (formulari o botó 16) reflecteix tot.
        morph = self.neg_morph if self.neg_morph > 0.0 else (1.0 if self.neg else 0.0)
        if morph > 0.0 and notes:
            k = int(morph * len(notes) + 0.5)
            if k > 0:
                ordre = sorted(range(len(notes)), key=lambda i: notes[i], reverse=True)
                for i in ordre[:k]:
                    notes[i] = self.negharm(notes[i], self.key)
                # El reflex pot fer xocar dues veus a la mateixa altura
                vistes, netes = [], []
                for n in notes:
                    if _MIN_NOTA <= n <= _MAX_NOTA and n not in vistes:
                        vistes.append(n)
                        netes.append(n)
                notes = netes
        return notes

    def _calla(self):
        for n in self.sonant:
            self.send_note_off(n, 0)
        self.sonant = []
        if self.baix_nota >= 0:
            self.send_note_off(self.baix_nota, 0)
            self.baix_nota = -1

    def _toca_acord(self):
        """Munta l'acord del pas actual i el fa sonar (o el deixa a punt per a
        l'arpegi)."""
        self._calla()
        notes = self._notes_del_pas(self.pas)
        if not notes:
            return
        self.veus = self._condueix(notes)
        self.arp_i = 0
        if _BAIX:
            b = _BAIX_OCT * 12 + (self.veus[0] % 12)
            if _MIN_NOTA <= b <= _MAX_NOTA:
                self.send_note_on(b, max(1, _VEL - 12))
                self.baix_nota = b
        if self.arp == 0:                      # Bloc: tot alhora
            for n in self.veus:
                self.send_note_on(n, _VEL)
                self.sonant.append(n)

    def _ordre_arp(self):
        """L'ordre en què l'arpegi recorre les veus."""
        n = len(self.veus)
        if n == 0:
            return []
        if self.arp == 1:                      # Amunt
            return list(range(n))
        if self.arp == 2:                      # Avall
            return list(range(n - 1, -1, -1))
        if self.arp == 3:                      # Ping-pong
            return list(range(n)) + list(range(n - 2, 0, -1))
        if self.arp == 4:                      # Alberti: greu-agut-mig-agut
            if n >= 3:
                return [0, n - 1, 1, n - 1]
            return list(range(n))
        return None                            # Aleatori: es tria a cada pas

    def _pas_arp(self):
        """Una nota de l'arpegi."""
        if not self.veus:
            return
        for n in self.sonant:
            self.send_note_off(n, 0)
        self.sonant = []
        ordre = self._ordre_arp()
        if ordre is None:
            idx = self._atzar(len(self.veus))
        else:
            idx = ordre[self.arp_i % len(ordre)]
            self.arp_i += 1
        n = self.veus[idx]
        self.send_note_on(n, _VEL)
        self.sonant.append(n)

    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()
        neg_abans = (self.neg, self.neg_eix, round(self.neg_morph, 2))

        # ── Els tres potes, tal com s'han assignat ──
        v = px
${potCodeAcords(spec.pots?.x || 'Tempo', spec, passos.length)}
        v = py_
${potCodeAcords(spec.pots?.y || 'Conducció de veus', spec, passos.length)}
        v = pz
${potCodeAcords(spec.pots?.z || 'Harmonia negativa', spec, passos.length)}

        # ── Harmonia negativa ──
        # Aquí NO és només el gest del botó 16: és un paràmetre del mode, que
        # ve del formulari i del pot. base_mode només reflecteix quan
        # neg_active és cert i poll_negharm el reescriu des del botó a cada
        # volta, o sigui que el conduïm nosaltres i el botó hi SUMA.
        boto = self.poll_negharm(button_states)
        if boto:
            self.neg_morph = 1.0        # el botó 16 reflecteix l'acord sencer
        self.neg_active = bool(self.neg or boto or self.neg_morph > 0.0)
        if self.neg_active:
            self.neg_axis = self.neg_eix
        if (self.neg, self.neg_eix, round(self.neg_morph, 2)) != neg_abans and self.veus:
            self._toca_acord()       # el reflex canvia les altures de l'acord

        # ── El pols: una pulsació és una negra ──
        interval = 60.0 / max(20.0, self.bpm)
        if now - self.t_puls >= interval:
            self.t_puls = now
            self.puls += 1
            dur = _PROG[self.pas % len(_PROG)][2]
            if self.puls >= dur:
                self.puls = 0
                self.pas = (self.pas + 1) % len(_PROG)
                self._toca_acord()

        # ── L'arpegi ──
        if self.arp != 0 and self.veus:
            pas_arp = interval / max(1, self.arp_div)
            if now - self.arp_t >= pas_arp:
                self.arp_t = now
                self._pas_arp()
        # Gate del bloc: talla l'acord abans del pas següent
        elif self.arp == 0 and self.sonant and self.gate < 0.99:
            dur = _PROG[self.pas % len(_PROG)][2] * interval
            if (now - self.t_puls) + self.puls * interval > dur * self.gate:
                for n in self.sonant:
                    self.send_note_off(n, 0)
                self.sonant = []

        self.t = now
        arrel_rel = _PROG[self.pas % len(_PROG)][0]
        return {'key': _KEYS[(self.key + arrel_rel) % 12], 'oct': self.octave,
                'bpm': int(self.bpm), 'pas': self.pas + 1, 'passos': len(_PROG),
                'vl': self.vl, 'neg': 1 if self.neg else 0,
                'eix': self.neg_eix, 'taula': self.taula,
                'morph': int(self.neg_morph * 100),
                'veus': list(self.veus)}

    def cleanup(self):
        self._calla()
        self.stop_tracked_notes()
        for c in (1, 74):
            try:
                self.midi_out.send(ControlChange(c, 0))
            except Exception:
                pass
`;
}

// ── SONIFICACIÓ ───────────────────────────────────────────────────────────
// La família on el que viatja al mode NO és l'algorisme sinó el RESULTAT —
// l'inversa exacta de l'algorísmica. Un vídeo no cap a una Pico i mai hi
// cabrà: l'anàlisi es fa al navegador (js/tecla-sonify.js) i aquí només
// s'incrusta la corba de característiques que n'ha sortit.

export const SONIFY_POT_FNS = ['Velocitat', 'Transposició', 'Registre', 'Densitat',
  'Amplada de l\'acord', 'Gate', 'Sentit', 'Longitud del bucle', 'Força',
  'Quantització', 'Brillantor (CC74)', 'Modulació (CC1)', '—'];

function potCodeSonify(fn, spec, indent = '        ') {
  const i = indent;
  switch (fn) {
    case 'Velocitat':
      // Del que dura de debò fins a vuit vegades més ràpid. En repòs, el tempo
      // real del vídeo: el mode sona com el que has vist.
      return `${i}self.vel_k = 1.0 + (v / 127.0) * 7.0`;
    case 'Transposició':
      return `${i}self.transp = int((v / 127.0) * 24.99) - 0`;
    case 'Registre':
      // Estreny o eixampla el recorregut d'alçades sense moure'n el centre.
      return `${i}self.abast = 0.15 + (v / 127.0) * 1.85`;
    case 'Densitat':
      return `${i}self.silenci = (v / 127.0) * 0.85`;
    case 'Amplada de l\'acord':
      // L'amplada que va mesurar l'anàlisi es converteix en veus de debò.
      return `${i}self.ample_k = (v / 127.0) * 2.0`;
    case 'Gate':
      return `${i}self.gate = 0.15 + (v / 127.0) * 1.6`;
    case 'Sentit':
      return `${i}s = min(2, int((v / 128.0) * 3))\n${i}if s != self.sentit:\n${i}    self.sentit = s`;
    case 'Longitud del bucle':
      return `${i}self.llarg = _N - int((v / 127.0) * (_N - 2))`;
    case 'Força':
      return `${i}self.forca_k = 0.35 + (v / 127.0) * 1.5`;
    case 'Quantització':
      return `${i}self.quant = v > 63`;
    case 'Brillantor (CC74)':
      return `${i}self._cc_once(74, v)`;
    case 'Modulació (CC1)':
      return `${i}self._cc_once(1, v)`;
    default:
      return `${i}pass`;
  }
}

function generateSonify(spec) {
  const cls = className(spec.nom);
  const nom = modeName(spec.nom);
  const escala = (spec.escalaIntervals && spec.escalaIntervals.length
    ? spec.escalaIntervals : [0, 2, 4, 5, 7, 9, 11]).map(x => clamp(x | 0, 0, 24));
  const key = clamp(spec.tonalitat | 0, 0, 11);
  const notaMin = clamp(spec.notaMin ?? 36, 0, 120);
  const notaMax = clamp(spec.notaMax ?? 84, 1, 127);
  const quant = spec.quantitza !== false;
  const gate = clamp(spec.gate ?? 70, 5, 200) / 100;
  const corba = (spec.corba && spec.corba.length ? spec.corba : [[500, 64, 90, 6]])
    .map(p => [Math.max(1, p[0] | 0), clamp(p[1] | 0, 0, 127), clamp(p[2] | 0, 0, 127), clamp(p[3] | 0, 0, 36)]);
  const potX = spec.pots?.x || 'Velocitat';
  const potY = spec.pots?.y || 'Densitat';
  const potZ = spec.pots?.z || 'Amplada de l\'acord';
  const spec4json = JSON.stringify({ ...spec, cat: 'sonify' });

  return `"""${nom} — sonificació feta amb el Laboratori de TECLA.
X: ${potX}  Y: ${potY}  Z: ${potZ}
Font: ${spec.fontNom || 'imatge/vídeo'} · ${corba.length} punts · ${(corba.reduce((s, p) => s + p[0], 0) / 1000).toFixed(1)} s
El que hi ha aquí NO és el vídeo: és la corba que en va sortir. L'anàlisi es
va fer al navegador i aquí només hi viatja el resultat.
"""
# TECLA-SPEC ${spec4json}
import time
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange

# [dt en ms, alçada 0-127, força 0-127, amplada 0-36]
_CORBA = (
${corba.map(p => `    ${py.tuple(p)},`).join('\n')}
)
_N = ${corba.length}
_ESCALA = ${py.tuple(escala)}
_KEYS = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_KEY = ${key}
_MIN = ${Math.min(notaMin, notaMax)}
_MAX = ${Math.max(notaMin, notaMax)}
_QUANT = ${quant ? 'True' : 'False'}
_GATE = ${py.f(gate)}
_MIN_NOTA = 12
_MAX_NOTA = 108


class ${cls}(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "${nom}"
        self.i = 0
        self.t_seg = 0.0
        self.sonant = []
        self.off_t = 0.0
        self.vel_k = 1.0        # multiplicador de velocitat de lectura
        self.transp = 0
        self.abast = 1.0        # com d'estret és el recorregut d'alçades
        self.silenci = 0.0
        self.ample_k = 0.0      # quantes veus surten de l'amplada mesurada
        self.gate = _GATE
        self.sentit = 0         # 0 endavant · 1 enrere · 2 ping-pong
        self.llarg = 0          # 0 = la corba sencera
        self.forca_k = 1.0
        self.quant = _QUANT
        self.amunt = True
        self._llavor = 4242
        self._cc_cache = {}

    def setup(self):
        self.initialized = True
        self.i = 0
        self.t_seg = time.monotonic()
        self._cc_cache = {}

    def _atzar(self, n):
        self._llavor = (self._llavor * 1103515245 + 12345) & 0x7FFFFFFF
        return (self._llavor >> 8) % (n if n > 0 else 1)

    def _cc_once(self, cc, v):
        v = 0 if v < 0 else (127 if v > 127 else int(v))
        if self._cc_cache.get(cc) == v:
            return
        self._cc_cache[cc] = v
        try:
            self.midi_out.send(ControlChange(cc, v))
        except Exception:
            pass

    def _nota(self, alcada):
        """0-127 de la corba → alçada MIDI, dins del registre i, si toca,
        arrapada a l'escala perquè allò sigui música i no una sirena."""
        centre = (_MIN + _MAX) * 0.5
        n = centre + (alcada / 127.0 - 0.5) * (_MAX - _MIN) * self.abast
        n = int(n) + self.transp
        if self.quant and _ESCALA:
            pc = (n - _KEY) % 12
            millor, dist = 0, 99
            for iv in _ESCALA:
                d = abs((iv % 12) - pc)
                d = min(d, 12 - d)
                if d < dist:
                    dist, millor = d, iv % 12
            n = n - pc + millor
        return _MIN_NOTA if n < _MIN_NOTA else (_MAX_NOTA if n > _MAX_NOTA else n)

    def _calla(self):
        for n in self.sonant:
            self.send_note_off(n, 0)
        self.sonant = []

    def _toca(self, punt, now):
        _, alcada, forca, ample = punt
        if forca <= 0:
            return
        if self.silenci > 0.0 and self._atzar(1000) < int(self.silenci * 1000):
            return
        vel = int(forca * self.forca_k)
        vel = 1 if vel < 1 else (127 if vel > 127 else vel)
        base = self._nota(alcada)
        self._calla()
        self.send_note_on(base, vel)
        self.sonant.append(base)
        # L'AMPLADA que va mesurar l'anàlisi es fa sentir: com més escampat
        # estava el moviment, més obert és l'acord que en surt.
        if self.ample_k > 0.0 and ample > 0:
            obertura = int(ample * self.ample_k)
            for d in (obertura, -obertura):
                n = base + d
                if _MIN_NOTA <= n <= _MAX_NOTA and n not in self.sonant:
                    if self.quant and _ESCALA:
                        n = self._nota(int((n - (_MIN + _MAX) * 0.5) / max(1, (_MAX - _MIN)) * 127 + 64))
                    if n not in self.sonant:
                        self.send_note_on(n, max(1, vel - 20))
                        self.sonant.append(n)

    def update(self, pot_values, button_states):
        # Potes FÍSICS: X=pot_values[1], Y=pot_values[0], Z=pot_values[2]
        py_, px, pz = pot_values
        now = time.monotonic()
        self.poll_negharm(button_states, pz)

        v = px
${potCodeSonify(potX, spec)}
        v = py_
${potCodeSonify(potY, spec)}
        v = pz
${potCodeSonify(potZ, spec)}

        if self.sonant and now >= self.off_t:
            self._calla()

        n_punts = _N
        if 1 < self.llarg < n_punts:
            n_punts = self.llarg
        if now >= self.t_seg:
            punt = _CORBA[self.i % _N]
            self._toca(punt, now)
            espera = (punt[0] / 1000.0) / self.vel_k
            self.off_t = now + espera * self.gate
            self.t_seg = now + espera
            # El sentit de lectura
            if self.sentit == 1:
                self.i = (self.i - 1) % n_punts
            elif self.sentit == 2:
                if self.amunt:
                    self.i += 1
                    if self.i >= n_punts - 1:
                        self.amunt = False
                else:
                    self.i -= 1
                    if self.i <= 0:
                        self.amunt = True
            else:
                self.i = (self.i + 1) % n_punts

        return {'punt': self.i + 1, 'punts': _N, 'veus': list(self.sonant),
                'nota': self.sonant[0] if self.sonant else -1,
                'key': _KEYS[(self.sonant[0] % 12) if self.sonant else 0]}

    def cleanup(self):
        self._calla()
        self.stop_tracked_notes()
        for c in (1, 74):
            try:
                self.midi_out.send(ControlChange(c, 0))
            except Exception:
                pass
`;
}

// ── Punt d'entrada ────────────────────────────────────────────────────────

const GENERADORS = {
  melodic: generateMelodic, ritmic: generateRhythmic,
  drone: generateDrone, textura: generateTexture, ona: generateWave,
  algoritmic: generateAlgorithmic, soroll: generateNoise, acords: generateChords, sonify: generateSonify,
};

/**
 * Genera un mode a partir de l'especificació.
 * @returns {{nom:string, file:string, cls:string, source:string}}
 */
export function generateMode(spec) {
  const gen = GENERADORS[spec?.cat];
  if (!gen) throw new Error(`Família encara no implementada: ${spec?.cat}`);
  return {
    nom: modeName(spec.nom),
    file: fileName(spec.nom),
    cls: className(spec.nom),
    source: gen(spec),
  };
}

/** Recupera l'especificació incrustada a un mode generat (o null). */
export function specFromSource(source) {
  const m = /^#\s*TECLA-SPEC\s+(\{.*\})\s*$/m.exec(String(source || ''));
  if (!m) return null;
  try { return JSON.parse(m[1]); } catch { return null; }
}

/** Les famílies que ja saben generar codi. */
export function famíliesImplementades() {
  return Object.keys(GENERADORS);
}

/**
 * Funcions de pot de cada família. ÚNICA font de veritat: el formulari les
 * llegeix d'aquí, perquè un nom que el generador no sàpiga fer no pugui
 * arribar a aparèixer al desplegable.
 */
export const POT_FNS = {
  melodic: MELODIC_POT_FNS,
  ritmic: RITMIC_POT_FNS,
  drone: DRONE_POT_FNS,
  textura: TEXTURA_POT_FNS,
  ona: ONA_POT_FNS,
  algoritmic: ALG_POT_FNS['Euclidià'],
  soroll: SOROLL_POT_FNS,
  acords: ACORDS_POT_FNS,
  sonify: SONIFY_POT_FNS,
};

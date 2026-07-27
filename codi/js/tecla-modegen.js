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
      return `${i}o = _OCT - 1 + int((v / 127.0) * 2.99)\n`
           + `${i}if o != self.octave:\n${i}    self.octave = o`;
    case 'Dinàmica':
      return `${i}self.vel_k = 0.45 + (v / 127.0) * 0.9`;
    case 'Articulació':
      return `${i}self.artic = 0.15 + (v / 127.0) * 0.85`;
    case 'Tonalitat':
      return `${i}k = int((v / 127.0) * 11.99)\n`
           + `${i}if k != self.key:\n${i}    self.key = k\n`
           + `${i}    print("${'%'}s: ${'%'}s" % (self.name, _KEYS[k]))`;
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
        self.artic = ${py.f(artic)}
        self.vel_k = 1.0
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

    def _toca(self, now):
        graus = _GRAUS[self.pat]
        vels = _VELS[self.pat]
        i = self.step % len(graus)
        self.step = (self.step + 1) % len(graus)
        g = graus[i]
        if g < 0:                       # silenci: el buit també és música
            return
        nota = self._nota(g)
        nota = self.negharm(nota, self._arrel() % 12)
        nota = 24 if nota < 24 else (108 if nota > 108 else nota)
        vel = int(vels[i] * self.vel_k)
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
            self.next_t = now + self.speed

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
      return `${i}c = min(${capes}, int((v / 127.0) * ${py.f(capes + .99, 2)}))\n`
           + `${i}if c != self.capa:\n${i}    self.capa = c\n`
           + `${i}    print("${'%'}s: capa ${'%'}d/${capes}" % (self.name, c))`;
    case 'Swing':
      return `${i}self.swing = (v / 127.0) * 0.34`;
    case 'Octava del baix':
      return `${i}o = _OCT_BAIX - 1 + int((v / 127.0) * 2.99)\n`
           + `${i}if o != self.oct_baix:\n${i}    self.oct_baix = o`;
    case 'Brillantor (CC74)':
      return `${i}self._cc_once(74, v)`;
    default:
      return `${i}pass`;
  }
}

/** Els potes que la família rítmica sap fer servir. */
export const RITMIC_POT_FNS = ['Tempo', 'Patró', 'Capes (breakdown)', 'Swing',
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
        self.swing = ${py.f(swing0)}
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

    def _fire(self, now):
        graella = _GRAELLES[self.pat]
        i = self.step
        for t in range(len(_NOTES)):
            if _CAPES[t] > self.capa:      # capa retirada: aquesta pista calla
                continue
            if graella[t][i]:
                self._cop(_NOTES[t], _VELS[t], _PERC_CH, _GATE, now)
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
            self.step = (self.step + 1) % ${n}
            self.next_step = now + self.step_dur * k

        return {'bpm': int(self.bpm), 'pat': self.pat + 1, 'capa': self.capa,
                'key': _KEYS[self.key]}

    def cleanup(self):
        self._allibera(0.0, totes=True)
        self.stop_tracked_notes()
        self._panic()
`;
}

// ── Punt d'entrada ────────────────────────────────────────────────────────

const GENERADORS = { melodic: generateMelodic, ritmic: generateRhythmic };

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

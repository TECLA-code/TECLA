"""Looper harmònic del Mode Teclat — pedal de loop.

Un sol botó 'looper' (timing LLIURE) que captura BÉ l'arpegiador de forma
automàtica: si durant la presa l'arp ha emès notes, en acabar de gravar el
loop s'auto-quantitza a la graella de l'arp (arp_speed) per eliminar el jitter
del bucle principal; si només s'han gravat acords/notes manuals, es conserva el
timing lliure exacte (es reprodueix tal com ho toques). Així no calen dues
funcions de loop separades.

El paràmetre `quantized=True` (funció legacy 'looper_q', si encara hi ha un botó
assignat) força la quantització encara que no s'hagi usat l'arp; per a un loop
quantitzat, el pot 'Arp Speed (BPM)' canvia el tempo en reprendre (pausa→represa).

Gest del botó (idèntic per a les dues variants):
  toc 1                 -> ARMAT (la gravació comença amb la primera nota/acord)
  toc 2                 -> fi de gravació i reproducció IMMEDIATA en bucle
  toc curt mentre sona  -> pausa (es conserva) / re-arrenca des del principi
  toc llarg (>=0.8s)    -> esborra el loop

Es graven les notes MIDI resultants (acord, inversió i harmonia negativa ja
aplicades). Canviar d'escala, tonalitat o capa després NO altera el loop:
està pensat per gravar una progressió i tocar notes soltes a sobre.

El loop sona pel SEU canal MIDI (modeloop.canals_auxiliars: el 2 amb el canal de
sortida per defecte), no pel del teclat. Dues coses en depenen:

  · El pitch bend en viu (pot 'Pitch Bend') va pel canal del teclat i NO torça
    el loop: es pot bendejar una nota a sobre d'una progressió que no es mou.
  · El pitch bend fet MENTRE es grava (o en overdub) queda dins del loop, com
    una nota més, i es repeteix amb ell pel seu canal. A cada volta el canal
    del loop torna al bend que hi havia en començar la presa.

I una de gratis: el looper i el teclat ja no es trepitgen les notes (un
NoteOff del loop no pot apagar la nota que el músic sosté, ni a l'inrevés),
perquè un NoteOff només apaga el seu canal.

Mòdul amb càrrega lazy: només s'importa si alguna funció looper s'usa.
"""
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.pitch_bend import PitchBend
from motor.modeloop import canals_auxiliars, BEND_CENTER
try:
    from core.pantalla import diu
except Exception:                       # simulador i proves sense core/
    def diu(text):
        print(text)
        return True

# Estats de kbd.loop_state (0 = IDLE definit a mode_keyboard sense importar res)
IDLE, ARMED, RECORDING, PLAYING, PAUSED = 0, 1, 2, 3, 4

LONG_PRESS = 0.8       # segons: esborrar loop (botó looper) / desfer UNA capa (botó overdub)
CLEAR_ALL_PRESS = 1.6  # segons (el doble): esborrar TOTES les capes d'overdub de cop
MAX_EVENTS = 64      # límit de seguretat de RAM (un loop normal en té 4-16)
MAX_BENDS = 48       # pressupost a part per als pitch bend (no mengen el de notes)
BEND_MIN_GAP = 0.03  # segons: dos bends més seguits es fusionen en un (escombrat de pot)
MIN_LOOP_LEN = 0.2   # segons mínims perquè un loop sigui vàlid
QUANT_STEPS_PER_BEAT = 4  # graella: l'offset es quantitza a passos d'arp

# Cada esdeveniment és [offset, durada, notes, velocitat]. Un pitch bend és un
# esdeveniment amb `notes` BUIT: [offset, 0, (), valor 0..16383]. Així el motor
# de reproducció, l'overdub i el desfer de capes els tracten com la resta.


def _ensure(kbd):
    """Crea les estructures del looper la primera vegada que s'usa."""
    if not hasattr(kbd, 'loop_events'):
        kbd.loop_events = []       # [offset, durada, (notes...), velocitat]
        kbd.loop_length = 0.0      # lliure: segons | quantitzat: PASSOS de graella
        kbd.loop_t0 = 0.0
        kbd.loop_pos_idx = 0
        kbd._loop_open = {}        # btn_idx -> esdeveniment pendent de release
        kbd._loop_note_offs = []   # [(temps_absolut, (notes...)), ...]
        kbd.loop_quantized = False # True quan el loop actual és en passos
        kbd.loop_grid = 0.15       # segons/pas del loop quantitzat (fixat en arrencar)
        kbd.loop_overdub = False   # Overdub: el que toques s'afegeix al loop
        kbd._dub_current = []      # esdeveniments de la capa d'overdub en curs
        kbd._dub_layers = []       # pila de capes tancades (per desfer-les una a una)
        kbd._loop_had_arp = False  # True si l'arp ha gravat notes en aquesta presa
                                   # (dispara l'auto-quantització en tancar la gravació)
        kbd._loop_had_sustain = False  # True si s'ha gravat amb sustain (CC64) actiu:
                                       # "fixa" el sustain a les durades (lligat) perquè el
                                       # loop NO depengui del pedal en directe en reproduir
        kbd._loop_bends = 0        # pitch bends gravats al loop (pressupost propi)
        kbd._loop_bend_last = None # últim bend gravat: els que vénen massa seguits s'hi fusionen
        kbd._loop_bend_last_t = 0.0
        kbd._loop_bend0 = BEND_CENTER  # bend viu en començar la presa: on torna cada volta
        kbd._loop_bend_out = None  # últim bend enviat pel canal del loop (per no repetir-lo)
        kbd._loop_ch = canals_auxiliars(kbd.midi)[1]  # el canal del loop, segons el de sortida


def _grid(kbd):
    """Durada d'un pas de graella en segons (segueix el tempo actual de l'arp)."""
    return max(0.02, getattr(kbd, 'arp_speed', 0.15))


def _sustain_on(kbd):
    """True si el sustain (pedal CC64) està actiu ara mateix."""
    return (getattr(kbd, 'sustain_hold_enabled', False)
            or getattr(kbd, 'sustain_level', 0) >= 64)


def _es_bend(ev):
    return not ev[2]


def _te_notes(evs):
    for ev in evs:
        if ev[2]:
            return True
    return False


def _ple(kbd):
    """El pressupost de NOTES és ple (els bends no hi compten)."""
    return len(kbd.loop_events) - kbd._loop_bends >= MAX_EVENTS


def _bend_viu(kbd):
    """El pitch bend que el teclat té enviat ara mateix (centre si cap)."""
    v = getattr(kbd, '_last_pitch_bend', None)
    return BEND_CENTER if v is None else v


def _bend_loop(kbd, value):
    """Pitch bend pel canal del loop, només si canvia."""
    value = max(0, min(16383, int(value)))
    if kbd._loop_bend_out == value:
        return
    kbd._loop_bend_out = value
    try:
        kbd.midi.send(PitchBend(value, channel=kbd._loop_ch))
    except Exception:
        pass


def _volta(kbd):
    """Comença una volta del loop: el seu canal torna al bend d'inici de presa."""
    if kbd._loop_bends:
        _bend_loop(kbd, kbd._loop_bend0)


def _comenca_presa(kbd, now):
    """ARMAT -> GRAVANT amb la primera nota. Es pren nota del bend viu: el loop
    hi tornarà a cada volta (el que passi durant la presa es grava a sobre)."""
    kbd.loop_state = RECORDING
    kbd.loop_t0 = now
    kbd._loop_bend0 = _bend_viu(kbd)
    kbd._loop_bend_last = None
    diu("🔴 Gravant...")


def _reset_presa(kbd):
    kbd.loop_events = []
    kbd._loop_open = {}
    kbd._loop_bends = 0
    kbd._loop_bend_last = None


def _bake_sustain(kbd):
    """Fixa el sustain a la gravació: cada esdeveniment se sosté fins que comença
    el següent (lligat). Així el loop sona sostingut PER SI MATEIX —les notes les
    aguanta el seu propi NoteOn/NoteOff, no el pedal en directe— i modificar el
    sustain després NO altera el loop. S'aplica en segons, ABANS de quantitzar.
    Es deixa un marge petit perquè el NoteOff surti abans del NoteOn següent i no
    talli notes comunes entre acords. Els bends no són "el següent": es lliga
    fins a la següent NOTA."""
    evs = kbd.loop_events
    n = len(evs)
    for i in range(n):
        if _es_bend(evs[i]):
            continue
        nxt = kbd.loop_length
        for j in range(i + 1, n):
            if not _es_bend(evs[j]):
                nxt = evs[j][0]
                break
        gap = nxt - evs[i][0]
        if gap <= 0:
            continue
        target = gap - 0.03 if gap > 0.08 else gap
        cur = evs[i][1] or 0.05
        if target > cur:
            evs[i][1] = target


def handle_button(kbd, held_time, now, quantized=False):
    """Gestiona un release del botó looper segons el temps premut i l'estat.
    quantized=True quan ve de la funció 'looper_q'."""
    _ensure(kbd)
    st = kbd.loop_state

    if held_time >= LONG_PRESS:
        _silence(kbd)
        kbd.loop_state = IDLE
        _reset_presa(kbd)
        kbd.loop_overdub = False
        kbd._dub_current = []
        kbd._dub_layers = []
        kbd._loop_had_arp = False
        kbd._loop_had_sustain = False
        diu("🔁 Looper ESBORRAT")
        return

    if st == IDLE:
        kbd.loop_state = ARMED
        _reset_presa(kbd)
        kbd.loop_quantized = False  # es decideix al toc que tanca la gravació
        kbd._loop_had_arp = False   # es marca si l'arp grava durant la presa
        kbd._loop_had_sustain = False
        diu("🔁 Looper ARMAT — toca per començar a gravar"
              + (" (quantitzat)" if quantized else ""))
    elif st == ARMED:
        kbd.loop_state = IDLE
        diu("🔁 Looper cancel·lat")
    elif st == RECORDING:
        kbd.loop_length = now - kbd.loop_t0
        # Tancar esdeveniments oberts (botons encara premuts en acabar)
        for ev in kbd._loop_open.values():
            ev[1] = max(0.05, kbd.loop_length - ev[0])
        kbd._loop_open = {}
        kbd._loop_bend_last = None
        if not _te_notes(kbd.loop_events) or kbd.loop_length < MIN_LOOP_LEN:
            # Un loop només de bends no és un loop: no hi ha res que sostingui
            kbd.loop_state = IDLE
            _reset_presa(kbd)
            diu("🔁 Looper: res a gravar")
        else:
            # Fixa el sustain a les durades si s'ha gravat amb el pedal actiu, perquè
            # el loop sigui INDEPENDENT del sustain en directe. En segons, abans de
            # quantitzar (que després converteix les durades a passos).
            if getattr(kbd, '_loop_had_sustain', False):
                _bake_sustain(kbd)
            # Auto-quantitza si l'arp ha intervingut en aquesta presa (captura fina
            # de l'arp sense jitter), o si s'ha forçat amb la funció legacy looper_q.
            if quantized or getattr(kbd, '_loop_had_arp', False):
                _quantize(kbd)
            kbd.loop_state = PLAYING
            kbd.loop_t0 = now
            kbd.loop_pos_idx = 0
            _volta(kbd)
            if kbd.loop_quantized:
                diu(f"🔁♩ Loop quantitzat: {len(kbd.loop_events) - kbd._loop_bends} acords, "
                      f"{int(kbd.loop_length)} passos (BPM viu amb el pot d'arp)")
            else:
                diu(f"🔁 Loop en marxa: {len(kbd.loop_events) - kbd._loop_bends} acords, "
                      f"{kbd.loop_length:.1f}s")
    elif st == PLAYING:
        if kbd.loop_overdub:
            _end_overdub(kbd)
        _silence(kbd)
        kbd.loop_state = PAUSED
        diu("🔁 Loop en pausa")
    elif st == PAUSED:
        kbd.loop_state = PLAYING
        kbd.loop_t0 = now
        kbd.loop_pos_idx = 0
        if kbd.loop_quantized:
            # Refrescar el tempo amb l'arp_speed actual: la represa és el
            # moment deliberat de canviar el tempo del loop
            kbd.loop_grid = _grid(kbd)
            diu(f"🔁 Loop reprès (pas de {kbd.loop_grid * 1000:.0f}ms)")
        else:
            diu("🔁 Loop reprès")
        _volta(kbd)


def record_press(kbd, btn_idx, now):
    """Captura un acord/nota acabat de generar (cridat des de kbd_buttons)."""
    _ensure(kbd)
    if kbd.loop_state == ARMED:
        _comenca_presa(kbd, now)
    if kbd.loop_state == RECORDING:
        notes = tuple(kbd.button_notes.get(btn_idx, ()))
        if not notes or _ple(kbd):
            return
        if _sustain_on(kbd):
            kbd._loop_had_sustain = True
        ev = [now - kbd.loop_t0, None, notes, kbd.velocity]
        kbd.loop_events.append(ev)
        kbd._loop_open[btn_idx] = ev
    elif kbd.loop_state == PLAYING and kbd.loop_overdub:
        notes = tuple(kbd.button_notes.get(btn_idx, ()))
        if not notes or _ple(kbd):
            return
        ev = [_dub_offset(kbd, now), None, notes, kbd.velocity]
        _insert_dub_event(kbd, ev)
        kbd._loop_open[btn_idx] = ev


def record_release(kbd, btn_idx, now):
    """Tanca la durada d'un esdeveniment quan s'allibera el botó."""
    if kbd.loop_state == RECORDING:
        ev = kbd._loop_open.pop(btn_idx, None)
        if ev is not None:
            ev[1] = max(0.05, (now - kbd.loop_t0) - ev[0])
    elif kbd.loop_state == PLAYING and getattr(kbd, 'loop_overdub', False):
        ev = kbd._loop_open.pop(btn_idx, None)
        if ev is not None and ev[1] is None:
            if kbd.loop_quantized:
                sl = kbd.loop_grid
                dur = round((now - kbd.loop_t0) / sl) - ev[0]
                ev[1] = max(1, min(int(dur), int(kbd.loop_length)))
            else:
                dur = (now - kbd.loop_t0) - ev[0]
                ev[1] = max(0.05, min(dur, kbd.loop_length))


def record_live_note(kbd, note, vel, now):
    """Captura una nota individual emesa pel motor de l'arpegiador.
    La durada és un pas d'arp (90%, amb un petit espai, com sona l'arp)."""
    _ensure(kbd)
    if kbd.loop_state == ARMED:
        _comenca_presa(kbd, now)
    if _ple(kbd):
        return
    if kbd.loop_state == RECORDING:
        kbd._loop_had_arp = True  # marca la presa per auto-quantitzar en tancar
        if _sustain_on(kbd):
            kbd._loop_had_sustain = True
        dur = max(0.05, getattr(kbd, 'arp_speed', 0.15) * 0.9)
        kbd.loop_events.append([now - kbd.loop_t0, dur, (note,), vel])
    elif kbd.loop_state == PLAYING and kbd.loop_overdub:
        if kbd.loop_quantized:
            dur = 1
        else:
            dur = max(0.05, getattr(kbd, 'arp_speed', 0.15) * 0.9)
        _insert_dub_event(kbd, [_dub_offset(kbd, now), dur, (note,), vel])


def record_bend(kbd, value, now):
    """Captura un pitch bend del teclat (valor MIDI 0..16383, 8192 = centre):
    durant la presa s'afegeix al loop, en overdub a la capa en curs. Fora
    d'això no fa res: un bend amb el loop ARMAT no comença la gravació (la
    comença la primera nota) però sí que queda com a bend d'inici de presa,
    via _bend_viu, quan arribi.

    Els bends que arriben a menys de BEND_MIN_GAP del darrer s'hi fusionen
    (un escombrat del pot en genera desenes per segon): el darrer bend acaba
    sempre amb el valor final, i el loop queda on el músic ha deixat el pot.
    Passat el pressupost MAX_BENDS, també: es conserva el moviment però no
    se n'afegeixen més punts."""
    _ensure(kbd)
    st = kbd.loop_state
    if st == RECORDING:
        off = now - kbd.loop_t0
    elif st == PLAYING and kbd.loop_overdub:
        off = _dub_offset(kbd, now, fi=True)
    else:
        return
    last = kbd._loop_bend_last
    if last is not None and ((now - kbd._loop_bend_last_t) < BEND_MIN_GAP
                             or kbd._loop_bends >= MAX_BENDS):
        last[3] = value
        return
    if kbd._loop_bends >= MAX_BENDS:
        return
    ev = [off, 0, (), value]
    if st == RECORDING:
        kbd.loop_events.append(ev)
    else:
        _insert_dub_event(kbd, ev)
    kbd._loop_bend_last = ev
    kbd._loop_bend_last_t = now
    kbd._loop_bends += 1


# ── Overdub ──────────────────────────────────────────────────────────────────

def _dub_offset(kbd, now, fi=False):
    """Posició actual dins del loop, en les unitats del loop (segons o passos).
    Amb `fi`, un loop quantitzat retorna passos FRACCIONARIS: els bends no es
    quantitzen (un escombrat aixafat a la graella sona a graons)."""
    if kbd.loop_quantized:
        if fi:
            return ((now - kbd.loop_t0) / kbd.loop_grid) % kbd.loop_length
        return int(round((now - kbd.loop_t0) / kbd.loop_grid)) % int(kbd.loop_length)
    return (now - kbd.loop_t0) % kbd.loop_length


def _insert_dub_event(kbd, ev):
    """Insereix mantenint l'ordre per offset (el motor de reproducció ho exigeix)
    i sense re-disparar en aquest mateix passi el que el músic acaba de tocar en viu."""
    evs = kbd.loop_events
    i = 0
    while i < len(evs) and evs[i][0] <= ev[0]:
        i += 1
    evs.insert(i, ev)
    if i < kbd.loop_pos_idx:
        kbd.loop_pos_idx += 1
    else:
        kbd.loop_pos_idx = i + 1  # ja ha sonat en viu; del loop sonarà al proper passi
    kbd._dub_current.append(ev)


def _end_overdub(kbd):
    """Tanca la capa d'overdub en curs."""
    kbd.loop_overdub = False
    kbd._loop_bend_last = None
    # Tancar durades de botons encara premuts
    for ev in list(kbd._loop_open.values()):
        if ev[1] is None:
            ev[1] = 1 if kbd.loop_quantized else 0.1
    kbd._loop_open = {}
    if kbd._dub_current:
        kbd._dub_layers.append(kbd._dub_current)
        diu(f"➕ Capa {len(kbd._dub_layers)} afegida: {len(kbd._dub_current)} esdeveniments "
              "(toc llarg: desfer-la | toc molt llarg: desfer-les totes)")
    else:
        diu("➕ Overdub tancat (sense canvis)")
    kbd._dub_current = []


def handle_dub_button(kbd, held_time, now):
    """Gest del botó 'looper_dub':
      toc curt amb loop sonant -> entra/surt del mode overdub
      toc curt amb loop en pausa -> reprèn el loop directament en overdub
      toc llarg (0.8s) -> desfà UNA capa (l'última); repetir per anar pelant
      toc molt llarg (1.6s) -> desfà TOTES les capes (el loop base es manté)"""
    _ensure(kbd)
    if held_time >= CLEAR_ALL_PRESS:
        clear_all_layers(kbd, now)
        return
    if held_time >= LONG_PRESS:
        undo_last_layer(kbd, now)
        return
    if kbd.loop_state == PLAYING:
        if not kbd.loop_overdub:
            kbd.loop_overdub = True
            kbd._dub_current = []
            kbd._loop_bend_last = None
            diu("➕ Overdub ACTIU — el que toquis s'afegeix al loop")
        else:
            _end_overdub(kbd)
    elif kbd.loop_state == PAUSED:
        kbd.loop_state = PLAYING
        kbd.loop_t0 = now
        kbd.loop_pos_idx = 0
        if kbd.loop_quantized:
            kbd.loop_grid = _grid(kbd)
        kbd.loop_overdub = True
        kbd._dub_current = []
        kbd._loop_bend_last = None
        _volta(kbd)
        diu("➕ Loop reprès amb Overdub actiu")
    else:
        diu("➕ Overdub: primer grava un loop amb el botó looper")


def _remove_events(kbd, events, now):
    """Treu esdeveniments del loop i recol·loca el punter de reproducció."""
    for ev in events:
        try:
            kbd.loop_events.remove(ev)
        except ValueError:
            pass
    n = 0
    for ev in kbd.loop_events:
        if _es_bend(ev):
            n += 1
    kbd._loop_bends = n
    kbd._loop_bend_last = None
    if kbd.loop_state == PLAYING:
        sl = kbd.loop_grid if kbd.loop_quantized else 1.0
        t = now - kbd.loop_t0
        idx = 0
        for ev in kbd.loop_events:
            if ev[0] * sl <= t:
                idx += 1
            else:
                break
        kbd.loop_pos_idx = idx


def undo_last_layer(kbd, now):
    """Desfà la capa d'overdub en curs (si n'hi ha) o l'última de la pila.
    Repetir el gest va pelant capes una a una."""
    if kbd.loop_overdub:
        kbd.loop_overdub = False
        kbd._loop_open = {}
    if kbd._dub_current:
        layer = kbd._dub_current
        kbd._dub_current = []
    elif kbd._dub_layers:
        layer = kbd._dub_layers.pop()
    else:
        diu("➕ Overdub: cap capa per desfer")
        return
    _remove_events(kbd, layer, now)
    diu(f"➖ Capa desfeta ({len(layer)} esdeveniments) | en queden {len(kbd._dub_layers)}")


def clear_all_layers(kbd, now):
    """Desfà TOTES les capes d'overdub de cop. El loop base es manté intacte."""
    if kbd.loop_overdub:
        kbd.loop_overdub = False
        kbd._loop_open = {}
    tots = list(kbd._dub_current)
    for layer in kbd._dub_layers:
        tots.extend(layer)
    if not tots:
        diu("➕ Overdub: cap capa per esborrar")
        return
    n_capes = len(kbd._dub_layers) + (1 if kbd._dub_current else 0)
    kbd._dub_current = []
    kbd._dub_layers = []
    _remove_events(kbd, tots, now)
    diu(f"🧹 {n_capes} capes esborrades ({len(tots)} esdeveniments) — només queda el loop base")


def _quantize(kbd):
    """Converteix offsets/durades de segons a PASSOS de graella (enters). Els
    bends passen a passos FRACCIONARIS: conserven la posició fina, perquè un
    escombrat aixafat a la graella sonaria a graons."""
    sl = _grid(kbd)
    for ev in kbd.loop_events:
        if _es_bend(ev):
            ev[0] = ev[0] / sl
            continue
        ev[0] = round(ev[0] / sl)                      # offset en passos
        ev[1] = max(1, round((ev[1] or 0.1) / sl))     # durada en passos
    kbd.loop_length = max(1.0, round(kbd.loop_length / sl))  # llargada en passos
    # Garantir que cap esdeveniment cau fora del loop
    for ev in kbd.loop_events:
        if ev[0] >= kbd.loop_length:
            ev[0] = (kbd.loop_length - 0.01) if _es_bend(ev) else int(kbd.loop_length) - 1
    # Arrodonir les notes pot avançar-les per davant d'un bend: l'ordre per
    # offset és el que el motor de reproducció exigeix (sort estable).
    kbd.loop_events.sort(key=lambda e: e[0])
    kbd.loop_quantized = True
    kbd.loop_grid = sl  # tempo del loop FIXAT en aquest moment


def tick(kbd, now):
    """Motor de reproducció: cridat a cada cicle d'update quan PLAYING.
    El tempo d'un loop quantitzat és kbd.loop_grid: es FIXA en arrencar o
    reprendre (no segueix el pot en viu — si no, activar la capa arp
    segrestaria el tempo del loop amb la posició física del pot de BPM).
    Per canviar el tempo: pausa -> ajusta el BPM -> represa.
    Tot surt pel canal del loop: notes, note-offs i bends."""
    if kbd.loop_state != PLAYING:
        return
    sl = getattr(kbd, 'loop_grid', 1.0) if kbd.loop_quantized else 1.0
    length_s = kbd.loop_length * sl

    t = now - kbd.loop_t0
    if t >= length_s:
        # Tornar a començar mantenint la fase exacta (sense deriva)
        kbd.loop_t0 += length_s
        kbd.loop_pos_idx = 0
        t = now - kbd.loop_t0
        _volta(kbd)

    evs = kbd.loop_events
    while kbd.loop_pos_idx < len(evs) and evs[kbd.loop_pos_idx][0] * sl <= t:
        offset, dur, notes, vel = evs[kbd.loop_pos_idx]
        kbd.loop_pos_idx += 1
        if not notes:
            _bend_loop(kbd, vel)
            continue
        for n in notes:
            try:
                kbd.midi.send(NoteOn(n, vel, channel=kbd._loop_ch))
            except Exception:
                pass
        kbd._loop_note_offs.append((kbd.loop_t0 + (offset + (dur or 0.1)) * sl, notes))

    if kbd._loop_note_offs:
        kept = []
        for end_t, notes in kbd._loop_note_offs:
            if now >= end_t:
                # Pel canal del loop: no pot tocar la nota que el músic sosté
                # pel del teclat, encara que sigui la mateixa altura.
                for n in notes:
                    try:
                        kbd.midi.send(NoteOff(n, 0, channel=kbd._loop_ch))
                    except Exception:
                        pass
            else:
                kept.append((end_t, notes))
        kbd._loop_note_offs = kept


def _silence(kbd):
    """Envia NoteOff de totes les notes del loop que sonen ara mateix, i deixa
    el canal del loop afinat si el loop l'havia bendejat."""
    for _end_t, notes in kbd._loop_note_offs:
        for n in notes:
            try:
                kbd.midi.send(NoteOff(n, 0, channel=kbd._loop_ch))
            except Exception:
                pass
    kbd._loop_note_offs = []
    if kbd._loop_bend_out not in (None, BEND_CENTER):
        _bend_loop(kbd, BEND_CENTER)


def pause_for_panic(kbd):
    """Cridat des de KeyboardMode.pause_looper() (STOP general / sortida de capa):
    silencia les notes del loop i el pausa (es conserva; toc curt per reprendre)."""
    _ensure(kbd)
    if kbd.loop_state == PLAYING:
        if kbd.loop_overdub:
            _end_overdub(kbd)
        _silence(kbd)
        kbd.loop_state = PAUSED
        diu("🔁 Loop en pausa (STOP)")
    elif kbd.loop_state in (ARMED, RECORDING):
        kbd.loop_state = IDLE
        _reset_presa(kbd)

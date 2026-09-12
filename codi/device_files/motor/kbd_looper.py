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

Mòdul amb càrrega lazy: només s'importa si alguna funció looper s'usa.
"""
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
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
MIN_LOOP_LEN = 0.2   # segons mínims perquè un loop sigui vàlid
QUANT_STEPS_PER_BEAT = 4  # graella: l'offset es quantitza a passos d'arp


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


def _grid(kbd):
    """Durada d'un pas de graella en segons (segueix el tempo actual de l'arp)."""
    return max(0.02, getattr(kbd, 'arp_speed', 0.15))


def _sustain_on(kbd):
    """True si el sustain (pedal CC64) està actiu ara mateix."""
    return (getattr(kbd, 'sustain_hold_enabled', False)
            or getattr(kbd, 'sustain_level', 0) >= 64)


def _bake_sustain(kbd):
    """Fixa el sustain a la gravació: cada esdeveniment se sosté fins que comença
    el següent (lligat). Així el loop sona sostingut PER SI MATEIX —les notes les
    aguanta el seu propi NoteOn/NoteOff, no el pedal en directe— i modificar el
    sustain després NO altera el loop. S'aplica en segons, ABANS de quantitzar.
    Es deixa un marge petit perquè el NoteOff surti abans del NoteOn següent i no
    talli notes comunes entre acords."""
    evs = kbd.loop_events
    n = len(evs)
    for i in range(n):
        nxt = evs[i + 1][0] if i + 1 < n else kbd.loop_length
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
        kbd.loop_events = []
        kbd._loop_open = {}
        kbd.loop_overdub = False
        kbd._dub_current = []
        kbd._dub_layers = []
        kbd._loop_had_arp = False
        kbd._loop_had_sustain = False
        diu("🔁 Looper ESBORRAT")
        return

    if st == IDLE:
        kbd.loop_state = ARMED
        kbd.loop_events = []
        kbd._loop_open = {}
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
        if not kbd.loop_events or kbd.loop_length < MIN_LOOP_LEN:
            kbd.loop_state = IDLE
            kbd.loop_events = []
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
            if kbd.loop_quantized:
                diu(f"🔁♩ Loop quantitzat: {len(kbd.loop_events)} acords, "
                      f"{int(kbd.loop_length)} passos (BPM viu amb el pot d'arp)")
            else:
                diu(f"🔁 Loop en marxa: {len(kbd.loop_events)} acords, {kbd.loop_length:.1f}s")
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


def record_press(kbd, btn_idx, now):
    """Captura un acord/nota acabat de generar (cridat des de kbd_buttons)."""
    _ensure(kbd)
    if kbd.loop_state == ARMED:
        kbd.loop_state = RECORDING
        kbd.loop_t0 = now
        diu("🔴 Gravant...")
    if kbd.loop_state == RECORDING:
        notes = tuple(kbd.button_notes.get(btn_idx, ()))
        if not notes or len(kbd.loop_events) >= MAX_EVENTS:
            return
        if _sustain_on(kbd):
            kbd._loop_had_sustain = True
        ev = [now - kbd.loop_t0, None, notes, kbd.velocity]
        kbd.loop_events.append(ev)
        kbd._loop_open[btn_idx] = ev
    elif kbd.loop_state == PLAYING and kbd.loop_overdub:
        notes = tuple(kbd.button_notes.get(btn_idx, ()))
        if not notes or len(kbd.loop_events) >= MAX_EVENTS:
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
        kbd.loop_state = RECORDING
        kbd.loop_t0 = now
        diu("🔴 Gravant...")
    if len(kbd.loop_events) >= MAX_EVENTS:
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


# ── Overdub ──────────────────────────────────────────────────────────────────

def _dub_offset(kbd, now):
    """Posició actual dins del loop, en les unitats del loop (segons o passos)."""
    if kbd.loop_quantized:
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
    """Converteix offsets/durades de segons a PASSOS de graella (enters)."""
    sl = _grid(kbd)
    for ev in kbd.loop_events:
        ev[0] = round(ev[0] / sl)                      # offset en passos
        ev[1] = max(1, round((ev[1] or 0.1) / sl))     # durada en passos
    kbd.loop_length = max(1.0, round(kbd.loop_length / sl))  # llargada en passos
    # Garantir que cap esdeveniment cau fora del loop
    for ev in kbd.loop_events:
        if ev[0] >= kbd.loop_length:
            ev[0] = int(kbd.loop_length) - 1
    kbd.loop_quantized = True
    kbd.loop_grid = sl  # tempo del loop FIXAT en aquest moment


def tick(kbd, now):
    """Motor de reproducció: cridat a cada cicle d'update quan PLAYING.
    El tempo d'un loop quantitzat és kbd.loop_grid: es FIXA en arrencar o
    reprendre (no segueix el pot en viu — si no, activar la capa arp
    segrestaria el tempo del loop amb la posició física del pot de BPM).
    Per canviar el tempo: pausa -> ajusta el BPM -> represa."""
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

    evs = kbd.loop_events
    while kbd.loop_pos_idx < len(evs) and evs[kbd.loop_pos_idx][0] * sl <= t:
        offset, dur, notes, vel = evs[kbd.loop_pos_idx]
        for n in notes:
            try:
                kbd.midi.send(NoteOn(n, vel))
            except Exception:
                pass
        kbd._loop_note_offs.append((kbd.loop_t0 + (offset + (dur or 0.1)) * sl, notes))
        kbd.loop_pos_idx += 1

    if kbd._loop_note_offs:
        kept = []
        vives = kbd.active_notes          # el que el músic té premut ARA
        for end_t, notes in kbd._loop_note_offs:
            if now >= end_t:
                for n in notes:
                    # Tocar A SOBRE del loop: si el músic sosté aquesta mateixa
                    # altura, el note-off del loop li mataria la SEVA nota —
                    # MIDI no compta propietaris, un NoteOff apaga i prou. Qui
                    # la va disparar l'últim és ell, i qui l'ha d'apagar també:
                    # se salta, i el seu release ja l'enviarà. L'entrada es
                    # CONSUMEIX igualment (no es torna a `kept`) o ho tornaríem
                    # a provar a cada volta mentre la tingués premuda.
                    if n in vives:
                        continue
                    try:
                        kbd.midi.send(NoteOff(n, 0))
                    except Exception:
                        pass
            else:
                kept.append((end_t, notes))
        kbd._loop_note_offs = kept


def loop_sostenint(kbd, note):
    """El loop té ara mateix aquesta altura sonant, amb el note-off pendent?

    És l'altra meitat de la col·lisió: deixar anar una tecla que el loop també
    està tocant li tallava la nota al loop. Aquí es diu que no l'apagui, i el
    note-off que el loop ja té programat la tancarà al seu moment — o sigui
    que sempre queda algú que l'apaga i cap nota no es penja.
    """
    if not getattr(kbd, 'loop_state', 0):
        return False
    for _end_t, notes in getattr(kbd, '_loop_note_offs', ()):
        if note in notes:
            return True
    return False


def _silence(kbd):
    """Envia NoteOff de totes les notes del loop que sonen ara mateix."""
    for _end_t, notes in kbd._loop_note_offs:
        for n in notes:
            try:
                kbd.midi.send(NoteOff(n, 0))
            except Exception:
                pass
    kbd._loop_note_offs = []


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
        kbd.loop_events = []
        kbd._loop_open = {}

"""Illes -- el comandament del mon que sona.

GENERAT per eines/firmware.py des de tecla/dispositiu.json. No editar a ma:
el taller d'illes el torna a escriure i els canvis es perdrien.

Aqui una tecla pot fer quatre coses, i les dues primeres no s'assemblen gens:

  control  un CONTROL MIDI. Amb el Logic obert, qualsevol NOTA que surti del
           TECLA la toca el Logic -- encara que el joc no hi tingui res a
           veure -- i el dispositiu sona en paral·lel a la peca. Un control,
           en canvi, no fa sonar res: el sinte l'ignora si no te res
           assignat, i el pont si que l'escolta. Aixi el dispositiu MANA
           sobre la musica sense TOCAR-LA.
  text     TECLES. Escriu «/filtre acid» com un teclat qualsevol. No passa
           per cap pont: funciona encara que no hi hagi res engegat, i per
           aixo es la mena que no es pot espatllar.
  drecera  una combinacio de tecles.
  capa     canvia quina taula es mira. NO es el canvi de banc del firmware:
           aquell descarrega el mode i atura el que sona; aquest no atura res.

Les tecles 1, 13, 14, 15, 16 son del firmware i aqui no s'hi toquen.

Capes: Música · Visuals
"""
import time

from adafruit_midi.control_change import ControlChange
from modes.base_mode import BaseMode

RANURES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)       # index de tecla de cada ranura
CONTROLS = (21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31)     # el CC de cada ranura (igual a totes les capes)
CC_CAPA = 19       # diu al pont en quina capa som

# Una entrada per capa. Cada tecla es una tupla, i el primer element diu que:
#   ('c', numero)              control MIDI
#   ('t', "text", entrar)      escriure
#   ('d', "TECLA", (mods,))    drecera
#   ('l', cap_a)               canviar de capa ('+', '-' o un numero)
#   ('x',)                     res
CAPES = ((('c', 21), ('c', 22), ('c', 23), ('c', 24), ('c', 25), ('c', 26), ('c', 27), ('c', 28), ('c', 29), ('c', 30), ('l', '+')), (('t', '/filtre cap', True), ('t', '/filtre nit', True), ('t', '/filtre gel', True), ('t', '/filtre foc', True), ('t', '/filtre acid', True), ('t', '/filtre pixel', True), ('t', '/filtre onada', True), ('t', '/auto', True), ('t', '/manual', True), ('t', '/deixa', True), ('l', '+')))

# Els potenciometres de cada capa: el CC que mou cadascun, o None.
POTS = ((74, 1, 7), (74, 1, 7))


class ModeIlles(BaseMode):
    # BaseMode nomes te ajudes per a NOTES (note_on, note_off): es el que fan
    # tots els altres modes. Aqui el missatge es construeix a ma, que son dues
    # linies, i aixi no cal tocar la classe base per un mode que justament es
    # l'unic que no toca cap nota.
    def _cc(self, numero, valor):
        self.midi_out.send(ControlChange(numero, max(0, min(127, int(valor)))))

    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Illes"
        self.capa = 0
        self.premuts = [False] * 16
        self.ultims_pots = [-1, -1, -1]
        self._kbd = None
        self._teclat = None
        self.t = time.monotonic()

    def setup(self):
        self.initialized = True
        self.capa = 0
        self.premuts = [False] * 16
        self.ultims_pots = [-1, -1, -1]
        self._cc(CC_CAPA, 0)

    # El teclat no es crea fins que alguna tecla l'hagi de fer servir:
    # importar-lo ocupa memoria, i en aquest xip la memoria es el que
    # s'acaba primer.
    def _obre_teclat(self):
        if self._kbd is None:
            import gc
            gc.collect()
            import usb_hid
            from adafruit_hid.keyboard import Keyboard
            from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
            self._kbd = Keyboard(usb_hid.devices)
            self._teclat = KeyboardLayoutUS(self._kbd)
        return self._kbd

    def _escriu(self, text, entrar):
        if not text:
            return
        self._obre_teclat()
        self._teclat.write(text)
        if entrar:
            from adafruit_hid.keycode import Keycode
            self._kbd.send(Keycode.ENTER)

    def _drecera(self, tecla, mods):
        from adafruit_hid.keycode import Keycode
        kbd = self._obre_teclat()
        codis = [getattr(Keycode, m) for m in mods if hasattr(Keycode, m)]
        if hasattr(Keycode, tecla):
            codis.append(getattr(Keycode, tecla))
            kbd.send(*codis)

    def _va_a(self, cap_a):
        if cap_a == '+':
            self.capa = (self.capa + 1) % len(CAPES)
        elif cap_a == '-':
            self.capa = (self.capa - 1) % len(CAPES)
        else:
            self.capa = int(cap_a) % len(CAPES)
        self._cc(CC_CAPA, self.capa)

    def _fes(self, ranura):
        feta = CAPES[self.capa][ranura]
        quina = feta[0]
        if quina == 'c':
            self._cc(feta[1], 127)
        elif quina == 't':
            self._escriu(feta[1], feta[2])
        elif quina == 'd':
            self._drecera(feta[1], feta[2])
        elif quina == 'l':
            self._va_a(feta[1])

    def update(self, pot_values, button_states):
        enviats = 0

        # Les tecles: nomes quan es premen, no mentre estan premudes. Si
        # s'enviessin a cada volta, un dit recolzat serien tres-centes
        # comandes per segon i el mon aniria boig.
        for ranura in range(len(RANURES)):
            i = RANURES[ranura]
            if i >= len(button_states):
                continue
            ara = bool(button_states[i])
            if ara and not self.premuts[i]:
                try:
                    self._fes(ranura)
                except Exception as e:
                    # Una tecla que peta no pot endur-se el mode: el mode es
                    # l'unic que fa que el dispositiu serveixi de res.
                    print("Illes: la tecla", i + 1, "no va:", e)
                enviats += 1
            self.premuts[i] = ara

        # Els pots, nomes quan es mouen de debo: un pot quiet balla un o dos
        # punts per soroll de l'ADC, i cada ball seria una comanda.
        pots = POTS[self.capa]
        for i in range(min(len(pots), len(pot_values))):
            valor = int(pot_values[i])
            if pots[i] is not None and abs(valor - self.ultims_pots[i]) >= 2:
                self.ultims_pots[i] = valor
                self._cc(pots[i], valor)
                enviats += 1

        return {'enviats': enviats, 'capa': self.capa}

    def cleanup(self):
        self._kbd = None
        self._teclat = None
        return []

"""Testimoni de potes per a la Pantalla de l'app: «Pot Nom: valor».

El fan servir els TRES llocs on un pot s'aplica —el teclat (kbd_pots), les
capes de Config Modes (potlayers) i els potes directes dels modes (mm_update)—
i la Pantalla ha de veure el mateix de tots tres. Abans cadascun tenia la seva
regla i cap no llegia bé:

- El teclat callava la «primera lectura» per sincronitzar la capa. Però amb
  la RECOLLIDA (un pot no mana fins que es mou 4 passos) la primera lectura
  JA és un gest de debò: el primer gir del pot no sortia mai per pantalla, i
  el segon només si s'allunyava 3 passos més. Reportat: «fa la sensació que
  a vegades no ho llegeix tot correctament».
- Les capes de Config Modes deien CADA valor: fins a 127 línies per gir,
  contra el sostre de 30 línies per segon de core/pantalla. S'hi perdien
  notes, passos d'arpegi i —el pitjor— el valor final del gir, que és el que
  es vol llegir. I el soroll de l'ADC (±1) les feia parlar amb el pot quiet:
  la pantalla no tornava mai al nom del mode.
- Els potes directes dels modes es deien amb el nom FÍSIC («Pot X: 64») i
  abans que el mode els recollís: el número de la pantalla no era el que el
  mode feia servir.

Ara la regla és una:

- es diu el valor que S'APLICA, des d'on s'aplica;
- el primer gest es diu;
- mentre gira, una línia cada INTERVAL per pot com a molt;
- mai es deixa l'últim valor: quan el pot s'atura es diu on ha quedat (tick);
- el soroll de l'ADC no es diu: LLINDAR de 2 passos.

Sense consola connectada no costa res que es noti: `diu` ho comprova abans
d'escriure, i aquí només hi ha un diccionari i una resta.
"""
import time

INTERVAL = 0.1      # segons entre línies d'un mateix pot mentre gira (≤10/s)
LLINDAR = 2         # passos: per sota és soroll de l'ADC, no un gest


class PotDit:
    def __init__(self):
        self._dit = {}      # nom → últim valor dit
        self._t = {}        # nom → quan es va dir
        self._pend = {}     # nom → (valor, fmt) que espera el seu torn

    def mou(self, nom, v, fmt=None, llindar=LLINDAR):
        """El pot `nom` s'ha aplicat amb `v`. Torna True si s'ha dit ara.
        `fmt`: format propi de la línia (una sola %d), per al tempo.
        `llindar`: 1 si qui crida ja ha filtrat el soroll (el tempo: el seu
        pot té histèresi pròpia i el número que es diu és en BPM, no en
        passos de pot)."""
        v = int(v)
        d = self._dit.get(nom)
        if d is not None and -llindar < v - d < llindar:
            self._pend.pop(nom, None)
            return False
        ara = time.monotonic()
        if ara - self._t.get(nom, -1e9) < INTERVAL:
            self._pend[nom] = (v, fmt)      # gira de pressa: es dirà al tick
            return False
        return self._diu(nom, v, fmt, ara)

    def tick(self):
        """Una volta del bucle: diu els valors que esperaven el seu torn
        (el pot que s'ha aturat després de girar de pressa)."""
        if not self._pend:
            return
        ara = time.monotonic()
        for nom in list(self._pend):
            if ara - self._t.get(nom, -1e9) >= INTERVAL:
                v, fmt = self._pend.pop(nom)
                self._diu(nom, v, fmt, ara)

    def llavor(self, nom, v):
        """On és el pot ara, sense dir-ho: en entrar en un mode els potes
        són on els vas deixar, no un gest. El primer gir sí que es dirà."""
        self._dit[nom] = int(v)
        self._pend.pop(nom, None)

    def oblida(self, nom=None):
        """Oblida un pot (el proper valor es dirà) o tots."""
        if nom is not None:
            self._dit.pop(nom, None)
            self._t.pop(nom, None)
            self._pend.pop(nom, None)
            return
        self._dit.clear()
        self._t.clear()
        self._pend.clear()

    def _diu(self, nom, v, fmt, ara):
        self._dit[nom] = v
        self._t[nom] = ara
        self._pend.pop(nom, None)
        try:
            from core.pantalla import diu
            return diu(fmt % v if fmt else "Pot %s: %d" % (nom, v))
        except Exception:
            return False

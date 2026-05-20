"""
Programa generat amb TECLA Blocks
Creat per programació visual amb blocs
"""

import time
import board
import usb_midi
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
import random

# Inicialitzar MIDI
midi = MIDI(midi_out=usb_midi.ports[1])

# Variables globals
current_octave = 4
bpm = 120
button_states = [False] * 16
last_button_states = [False] * 16
pot_values = [0, 0, 0]

# Funció principal
def main():
    """Programa principal"""
    print("Iniciant programa TECLA Blocks...")
    
    try:
        import math
        import time
        import random

        machine_bpm = None
        steam_pressure = None
        num_gears = None


        # Repetir per sempre
        while True:
          machine_bpm = (math.sin(time.monotonic() * 0.2 * 6.28) + 1) / 2 * (240 - 60) + 60
          steam_pressure = (math.sin(time.monotonic() * 0.15 * 6.28) + 1) / 2 * (100 - 0) + 0
          num_gears = (math.sin(time.monotonic() * 0.08 * 6.28) + 1) / 2 * (8 - 1) + 1
          # Tocar nota MIDI 36
          midi.send(NoteOn(36, 100))
          time.sleep(0.1)
          midi.send(NoteOff(36, 0))
          # Tocar nota MIDI 40
          midi.send(NoteOn(40, 80))
          time.sleep(0.1)
          midi.send(NoteOff(40, 0))
          # Tocar nota MIDI 48
          midi.send(NoteOn(48, 60))
          time.sleep(0.05)
          midi.send(NoteOff(48, 0))
          for count in range(int(num_gears)):
            # Tocar nota MIDI (random.randint(52, 76))
            midi.send(NoteOn((random.randint(52, 76)), 70))
            time.sleep(0.05)
            midi.send(NoteOff((random.randint(52, 76)), 0))
            time.sleep(0.03)
          time.sleep(0.05)  # Petit delay per evitar bloqueig

        if steam_pressure > 50:
          # Tocar nota MIDI (84 + steam_pressure / 8)
          midi.send(NoteOn((84 + steam_pressure / 8), (80 + steam_pressure / 3)))
          time.sleep(0.2)
          midi.send(NoteOff((84 + steam_pressure / 8), 0))
        time.sleep((15 / machine_bpm))

    except KeyboardInterrupt:
        print("\nPrograma aturat per l'usuari")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Aturar totes les notes
        for note in range(128):
            midi.send(NoteOff(note, 0))
        print("Programa finalitzat")

if __name__ == "__main__":
    main()

# ==========================================
# TECLA BLOCKS DATA (DO NOT EDIT BELOW)
# ==========================================
# TECLA_BLOCKS_EMBEDDED_JSON = '''{"blocks":{"languageVersion":0,"blocks":[{"type":"tecla_repeat_forever","id":"[yt(O+pVpwk!^!leq2NG","x":50,"y":50,"inputs":{"DO":{"block":{"type":"variables_set","id":"B|`?lBU${E/j(ryT!^kA","fields":{"VAR":{"id":"+U;9*QN4t=(lVSo`3s/0"}},"inputs":{"VALUE":{"block":{"type":"tecla_software_lfo","id":":P[+6e|N-Plt8jG,vYt/","inputs":{"RATE":{"shadow":{"type":"math_number","id":"-MjI2*yziFz%xWkPA4Q?","fields":{"NUM":0.2}}},"MIN":{"shadow":{"type":"math_number","id":"@^%07+xr*`*`Pl!*-,uM","fields":{"NUM":60}}},"MAX":{"shadow":{"type":"math_number","id":"BJZX*t)+RGw+S9481KR~","fields":{"NUM":240}}}}}}},"next":{"block":{"type":"variables_set","id":"7@kgu.p_5uCnF(_6Bt%_","fields":{"VAR":{"id":"a62]u1@%qFSCz)*ds(xx"}},"inputs":{"VALUE":{"block":{"type":"tecla_software_lfo","id":"/1lU|!r^p:Pkc!tcYI66","inputs":{"RATE":{"shadow":{"type":"math_number","id":"kM9l4p!3Yu-PCwd:-peT","fields":{"NUM":0.15}}},"MIN":{"shadow":{"type":"math_number","id":"]!Vo_Rnn[Whe^_j0ID%V","fields":{"NUM":0}}},"MAX":{"shadow":{"type":"math_number","id":"ggFh/jNPb}R.hyQ-glry","fields":{"NUM":100}}}}}}},"next":{"block":{"type":"variables_set","id":"N[hi)]rdi2zn*t4RG{]L","fields":{"VAR":{"id":"Ts70(z+TckJP[PRvUl)u"}},"inputs":{"VALUE":{"block":{"type":"tecla_software_lfo","id":"!dTWr{N3bYZ|!~]wCtiY","inputs":{"RATE":{"shadow":{"type":"math_number","id":"s^un;]fylT9IY-^uxRdP","fields":{"NUM":0.08}}},"MIN":{"shadow":{"type":"math_number","id":"ezTaPcZRT#+ofNl+=e*m","fields":{"NUM":1}}},"MAX":{"shadow":{"type":"math_number","id":"I4a5ettP;E*XRpG(3glI","fields":{"NUM":8}}}}}}},"next":{"block":{"type":"tecla_play_note","id":"J-pl#t.~OU:1mv!bnv;s","inputs":{"NOTE":{"shadow":{"type":"math_number","id":"gMG3T?.%iJbw}`D_aVzw","fields":{"NUM":36}}},"VELOCITY":{"shadow":{"type":"math_number","id":",,2Rf,T2Hv8yP3mFy+*N","fields":{"NUM":100}}},"DURATION":{"shadow":{"type":"math_number","id":"m,jYOqfD^a{8Du!-ie*%","fields":{"NUM":0.1}}}},"next":{"block":{"type":"tecla_play_note","id":"NZx?yinr/S9o{2z.qRq5","inputs":{"NOTE":{"shadow":{"type":"math_number","id":"cNBuaY;c/H8eUVY3/+Q0","fields":{"NUM":40}}},"VELOCITY":{"shadow":{"type":"math_number","id":"3PQUyGNd_P07W}a0:$Tt","fields":{"NUM":80}}},"DURATION":{"shadow":{"type":"math_number","id":"83u@]zkF!rzz(b)pH;3/","fields":{"NUM":0.1}}}},"next":{"block":{"type":"tecla_play_note","id":"^3u]3`$YHAJz=LJ5]+2t","inputs":{"NOTE":{"shadow":{"type":"math_number","id":"FxCr:-q*L.1}vun9m}1j","fields":{"NUM":48}}},"VELOCITY":{"shadow":{"type":"math_number","id":"S[%?EE$!J^pC=EdEvYOM","fields":{"NUM":60}}},"DURATION":{"shadow":{"type":"math_number","id":"]T`DG*^P=4A?0acibqPM","fields":{"NUM":0.05}}}},"next":{"block":{"type":"controls_repeat_ext","id":"!b=dBq^PwswJ;.|4p9Tm","inputs":{"TIMES":{"block":{"type":"variables_get","id":"Pfcn%.qCoNW]5N2;kSBA","fields":{"VAR":{"id":"Ts70(z+TckJP[PRvUl)u"}}}},"DO":{"block":{"type":"tecla_play_note","id":"J3m9!b?curMxkx7t(DBs","inputs":{"NOTE":{"block":{"type":"math_random_int","id":"F[|nTUD#k^).]WJlo.jK","inputs":{"FROM":{"shadow":{"type":"math_number","id":"W$So~:{Ez9Z!5*Lq}8@T","fields":{"NUM":52}}},"TO":{"shadow":{"type":"math_number","id":"aY4:{;9W_3fi*M@_yX60","fields":{"NUM":76}}}}}},"VELOCITY":{"shadow":{"type":"math_number","id":"kJ(!L:_(X~c8Q$E}T^r+","fields":{"NUM":70}}},"DURATION":{"shadow":{"type":"math_number","id":"u|OckSi}CZ`A]raK!msu","fields":{"NUM":0.05}}}},"next":{"block":{"type":"tecla_wait","id":"|a9`/+}P+-fwdKUtsi{m","inputs":{"TIME":{"shadow":{"type":"math_number","id":"K0P^T(2RI^tGz|Ft.iG5","fields":{"NUM":0.03}}}}}}}}}}}}}}}}}}}}}}}}},{"type":"controls_if","id":"UwdQ9;_ql3hF].?~3H`E","x":150,"y":530,"inputs":{"IF0":{"block":{"type":"logic_compare","id":"|U,)SnaMCvbiVV;o(/Ad","fields":{"OP":"GT"},"inputs":{"A":{"block":{"type":"variables_get","id":"eh@(3MB:,|A`hJ!6E,fW","fields":{"VAR":{"id":"a62]u1@%qFSCz)*ds(xx"}}}},"B":{"shadow":{"type":"math_number","id":"[NRA)4J{p5c)g`B6zylC","fields":{"NUM":50}}}}}},"DO0":{"block":{"type":"tecla_play_note","id":"ZeR?$,8`?_KUBAITS-q~","inputs":{"NOTE":{"block":{"type":"math_arithmetic","id":"y#8oH~uEFZYL6u0yn4;G","fields":{"OP":"ADD"},"inputs":{"A":{"shadow":{"type":"math_number","id":"c1y!1;e#F^l=r66+sGc@","fields":{"NUM":84}}},"B":{"block":{"type":"math_arithmetic","id":"+lDpMu5Pk,kRlLI_j/O`","fields":{"OP":"DIVIDE"},"inputs":{"A":{"block":{"type":"variables_get","id":"_K%,7hEsT%,.{C6vgizS","fields":{"VAR":{"id":"a62]u1@%qFSCz)*ds(xx"}}}},"B":{"shadow":{"type":"math_number","id":"]UhMYUR44(|00;n3Kj@j","fields":{"NUM":8}}}}}}}}},"VELOCITY":{"block":{"type":"math_arithmetic","id":"aP]mEvACkBZ}PVH:_2[S","fields":{"OP":"ADD"},"inputs":{"A":{"shadow":{"type":"math_number","id":"IiucS8Ae[mq*7C|=uSzA","fields":{"NUM":80}}},"B":{"block":{"type":"math_arithmetic","id":":xxZ0gr61NS0@8y?%{HY","fields":{"OP":"DIVIDE"},"inputs":{"A":{"block":{"type":"variables_get","id":"`p~8,oZ`*!cDJi51Xta^","fields":{"VAR":{"id":"a62]u1@%qFSCz)*ds(xx"}}}},"B":{"shadow":{"type":"math_number","id":"br*PfA_{H:@U(I@foNbN","fields":{"NUM":3}}}}}}}}},"DURATION":{"shadow":{"type":"math_number","id":"04#s(W,?K!wO[fN+/Zbg","fields":{"NUM":0.2}}}}}}},"next":{"block":{"type":"tecla_wait","id":"PFmU2l!,K}KbA/~#a!U+","inputs":{"TIME":{"block":{"type":"math_arithmetic","id":"!f^}8B+SOMuk6,(F3OEF","fields":{"OP":"DIVIDE"},"inputs":{"A":{"shadow":{"type":"math_number","id":"^*9T~WnHIGu_G-GnRASv","fields":{"NUM":15}}},"B":{"block":{"type":"variables_get","id":"%{MGm4g|Wl8?Ijo*eg([","fields":{"VAR":{"id":"+U;9*QN4t=(lVSo`3s/0"}}}}}}}}}}}]},"variables":[{"name":"machine_bpm","id":"+U;9*QN4t=(lVSo`3s/0"},{"name":"steam_pressure","id":"a62]u1@%qFSCz)*ds(xx"},{"name":"num_gears","id":"Ts70(z+TckJP[PRvUl)u"}]}'''
# ==========================================

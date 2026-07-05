/**
 * Generador de codi Python per blocs TECLA
 * Converteix blocs Blockly a codi CircuitPython executable al dispositiu TECLA
 */

// Converteix un nom lliure (p. ex. "la meva funció") en un identificador Python vàlid
function _teclaSafeName(name) {
  let n = String(name || 'funcio').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  n = n.replace(/[^a-zA-Z0-9_]/g, '_');
  if (/^[0-9]/.test(n)) n = '_' + n;
  return n || 'funcio';
}

// ==================== GENERADORS DE MÚSICA ====================

Blockly.Python.forBlock['tecla_play_note'] = function (block) {
  const note = Blockly.Python.valueToCode(block, 'NOTE', Blockly.Python.ORDER_ATOMIC) || '60';
  const velocity = Blockly.Python.valueToCode(block, 'VELOCITY', Blockly.Python.ORDER_ATOMIC) || '100';
  const duration = Blockly.Python.valueToCode(block, 'DURATION', Blockly.Python.ORDER_ATOMIC) || '0.5';

  const code = `# Tocar nota MIDI ${note}\n` +
    `midi.send(NoteOn((${note}) + _riff[0], ${velocity}))\n` +
    `tecla_sleep(${duration})\n` +
    `midi.send(NoteOff((${note}) + _riff[0], 0))\n`;
  return code;
};

Blockly.Python.forBlock['tecla_play_chord'] = function (block) {
  const chord = block.getFieldValue('CHORD');
  const duration = block.getFieldValue('DURATION');

  // Mapa d'acords a notes MIDI
  const chordMap = {
    'C': [60, 64, 67],   // Do Major
    'D': [62, 66, 69],   // Re Major
    'E': [64, 68, 71],   // Mi Major
    'F': [65, 69, 72],   // Fa Major
    'G': [67, 71, 74],   // Sol Major
    'A': [69, 73, 76],   // La Major
    'B': [71, 75, 78],   // Si Major
    'Cm': [60, 63, 67],  // Do menor
    'Dm': [62, 65, 69],  // Re menor
    'Em': [64, 67, 71],  // Mi menor
    'Fm': [65, 68, 72],  // Fa menor
    'Gm': [67, 70, 74],  // Sol menor
    'Am': [69, 72, 76],  // La menor
    'Bm': [71, 74, 78]   // Si menor
  };

  const notes = chordMap[chord] || [60, 64, 67];
  let code = `# Tocar acord ${chord}\n`;

  // Tocar totes les notes de l'acord
  notes.forEach(note => {
    code += `midi.send(NoteOn(${note} + (current_octave - 4) * 12, 100))\n`;
  });

  code += `tecla_sleep(${duration})\n`;

  // Aturar totes les notes
  notes.forEach(note => {
    code += `midi.send(NoteOff(${note} + (current_octave - 4) * 12, 0))\n`;
  });

  return code;
};

Blockly.Python.forBlock['tecla_play_arpeggio'] = function (block) {
  const chord = block.getFieldValue('CHORD');
  const speed = Blockly.Python.valueToCode(block, 'SPEED', Blockly.Python.ORDER_ATOMIC) || '0.1';

  // Mapa d'acords (duplicat del play_chord per simplicitat o moure a global si es pot)
  // Per ara el redefinim aquí
  const chordMap = {
    'C': [60, 64, 67], 'D': [62, 66, 69], 'E': [64, 68, 71],
    'F': [65, 69, 72], 'G': [67, 71, 74], 'A': [69, 73, 76], 'B': [71, 75, 78],
    'Cm': [60, 63, 67], 'Dm': [62, 65, 69], 'Em': [64, 67, 71],
    'Fm': [65, 68, 72], 'Gm': [67, 70, 74], 'Am': [69, 72, 76], 'Bm': [71, 74, 78]
  };

  const notes = chordMap[chord] || [60, 64, 67];
  let code = `# Arpegi ${chord}\n`;

  notes.forEach((note, index) => {
    code += `midi.send(NoteOn(${note} + (current_octave - 4) * 12, 100))\n`;
    code += `tecla_sleep(${speed})\n`;
    code += `midi.send(NoteOff(${note} + (current_octave - 4) * 12, 0))\n`;
  });

  return code;
};

Blockly.Python.forBlock['tecla_play_scale'] = function (block) {
  const scale = block.getFieldValue('SCALE');
  const root = block.getFieldValue('ROOT');

  // Mapa de notes arrel
  const rootNotes = {
    'C': 60, 'D': 62, 'E': 64, 'F': 65,
    'G': 67, 'A': 69, 'B': 71
  };

  // Intervals per escales
  const scaleIntervals = {
    'major': [0, 2, 4, 5, 7, 9, 11, 12],
    'minor': [0, 2, 3, 5, 7, 8, 10, 12],
    'pentatonic': [0, 2, 4, 7, 9, 12],
    'blues': [0, 3, 5, 6, 7, 10, 12],
    'dorian': [0, 2, 3, 5, 7, 9, 10, 12],
    'chromatic': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  };

  const baseNote = rootNotes[root] || 60;
  const intervals = scaleIntervals[scale] || scaleIntervals.major;

  let code = `# Tocar escala ${scale} des de ${root}\n`;

  intervals.forEach(interval => {
    const note = baseNote + interval;
    code += `midi.send(NoteOn(${note}, 100))\n`;
    code += `tecla_sleep(0.3)\n`;
    code += `midi.send(NoteOff(${note}, 0))\n`;
  });

  return code;
};

Blockly.Python.forBlock['tecla_set_octave'] = function (block) {
  const octave = block.getFieldValue('OCTAVE');
  const code = `global current_octave\n` +
    `# Canviar octava a ${octave}\n` +
    `current_octave = ${octave}\n`;
  return code;
};

// ==================== GENERADORS DE CONTROL ====================

Blockly.Python.forBlock['tecla_read_button'] = function (block) {
  const button = block.getFieldValue('BUTTON');
  const buttonIndex = parseInt(button) - 1;
  const code = `button_states[${buttonIndex}]`;
  return [code, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python.forBlock['tecla_read_pot'] = function (block) {
  const pot = block.getFieldValue('POT');
  const code = `pot_values[${pot}]`;
  return [code, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python.forBlock['tecla_on_button_press'] = function (block) {
  const button = block.getFieldValue('BUTTON');
  const buttonIndex = parseInt(button) - 1;
  const IND = Blockly.Python.INDENT || '  ';
  const statements = Blockly.Python.statementToCode(block, 'DO') || `${IND}pass\n`;

  const code = `# Quan es prem botó ${button}\n` +
    `if button_states[${buttonIndex}] and not last_button_states[${buttonIndex}]:\n` +
    statements +
    `\n`;
  return code;
};

// ==================== GENERADORS D'EFECTES ====================

Blockly.Python.forBlock['tecla_effect_delay'] = function (block) {
  const time = Blockly.Python.valueToCode(block, 'TIME', Blockly.Python.ORDER_ATOMIC) || '50';
  const feedback = Blockly.Python.valueToCode(block, 'FEEDBACK', Blockly.Python.ORDER_ATOMIC) || '60';

  const code = `# Activar efecte Delay\n` +
    `midi.send(ControlChange(12, ${time}))  # Delay time\n` +
    `midi.send(ControlChange(13, ${feedback}))  # Delay feedback\n`;
  return code;
};

Blockly.Python.forBlock['tecla_effect_reverb'] = function (block) {
  const amount = Blockly.Python.valueToCode(block, 'AMOUNT', Blockly.Python.ORDER_ATOMIC) || '70';

  const code = `# Activar efecte Reverb\n` +
    `midi.send(ControlChange(91, ${amount}))  # Reverb level\n`;
  return code;
};

Blockly.Python.forBlock['tecla_effect_filter'] = function (block) {
  const type = block.getFieldValue('TYPE');
  const frequency = Blockly.Python.valueToCode(block, 'FREQUENCY', Blockly.Python.ORDER_ATOMIC) || '64';

  const code = `# Aplicar filtre ${type}\n` +
    `midi.send(ControlChange(74, ${frequency}))  # Filter cutoff\n`;
  return code;
};

// ==================== GENERADORS DE TEMPS ====================

Blockly.Python.forBlock['tecla_wait'] = function (block) {
  const seconds = Blockly.Python.valueToCode(block, 'TIME', Blockly.Python.ORDER_ATOMIC) || '1';
  const code = `tecla_sleep(${seconds})\n`;
  return code;
};

Blockly.Python.forBlock['tecla_repeat_forever'] = function (block) {
  const statements = Blockly.Python.statementToCode(block, 'DO');

  const code = `# Repetir per sempre\n` +
    `while True:\n` +
    `  tecla_yield()  # Comprova si algun botó interromp el bucle\n` +
    statements +
    `  tecla_sleep(0.01)  # Petit delay per evitar bloqueig\n`;
  return code;
};

// ==================== HELPERS DE HARDWARE (Python compartit) ====================
// Bloc de codi Python inserit a la capçalera de l'export estàndard I al codi
// de dispositiu (_buildDeviceCode). Cada perifèric es configura un sol cop
// (memòria cau) per evitar errors "pin in use" quan un bloc s'executa repetidament.
window.TECLA_HW_HELPERS = `# --- Helpers de hardware (cada pin es configura només un cop) ---
_hw_cache = {}

def _gpio(n, out=False, up=False):
    """Pin digital GP<n>. out=True el fa de sortida; up=True llegeix amb pull-up"""
    _k = ("o" if out else ("u" if up else "i")) + str(n)
    if _k not in _hw_cache:
        import digitalio
        _p = digitalio.DigitalInOut(getattr(board, "GP%d" % n))
        if out:
            _p.direction = digitalio.Direction.OUTPUT
        else:
            _p.direction = digitalio.Direction.INPUT
            _p.pull = digitalio.Pull.UP if up else digitalio.Pull.DOWN
        _hw_cache[_k] = _p
    return _hw_cache[_k]

def _adc(n):
    """Entrada analògica A<n> (0-65535)"""
    _k = "a%d" % int(n)
    if _k not in _hw_cache:
        import analogio
        _hw_cache[_k] = analogio.AnalogIn(getattr(board, "A%d" % int(n)))
    return _hw_cache[_k]

def _adc_named(name):
    if name not in _hw_cache:
        import analogio
        _hw_cache[name] = analogio.AnalogIn(getattr(board, name))
    return _hw_cache[name]

def _pwm(n, freq=1000):
    _k = "p%d" % n
    if _k not in _hw_cache:
        import pwmio
        _hw_cache[_k] = pwmio.PWMOut(getattr(board, "GP%d" % n), frequency=freq, duty_cycle=0)
    return _hw_cache[_k]

def _servo(n):
    _k = "s%d" % n
    if _k not in _hw_cache:
        import pwmio
        from adafruit_motor import servo as _sv
        _hw_cache[_k] = _sv.Servo(pwmio.PWMOut(getattr(board, "GP%d" % n), frequency=50))
    return _hw_cache[_k]

def _neopix(n, count):
    _k = "n%d" % n
    if _k not in _hw_cache:
        import neopixel
        _hw_cache[_k] = neopixel.NeoPixel(getattr(board, "GP%d" % n), count, brightness=0.4, auto_write=False)
    return _hw_cache[_k]

def _npx_wheel(pos):
    pos = pos & 255
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    pos -= 170
    return (0, pos * 3, 255 - pos * 3)

def _npx_rainbow(px, offset):
    for _i in range(len(px)):
        px[_i] = _npx_wheel((_i * 256 // len(px)) + offset)
    px.show()

class _NoScreen:
    """Pantalla fantasma: si no hi ha OLED, els blocs de dibuix no fan res"""
    def __getattr__(self, _a):
        return lambda *args, **kw: None

def _display():
    """OLED SSD1306 128x64. Autodetecta els pins I2C del TECLA.
    Cal la llibreria adafruit_ssd1306 a CIRCUITPY/lib/"""
    if "oled" not in _hw_cache:
        _d = None
        try:
            import busio, adafruit_ssd1306
            for _sda, _scl in (("GP16", "GP17"), ("GP20", "GP21"), ("GP18", "GP19")):
                try:
                    _i2c = busio.I2C(getattr(board, _scl), getattr(board, _sda), frequency=400000)
                    _d = adafruit_ssd1306.SSD1306_I2C(128, 64, _i2c)
                    break
                except Exception:
                    pass
        except ImportError:
            pass
        _hw_cache["oled"] = _d if _d else _NoScreen()
    return _hw_cache["oled"]

def _distance_cm(trig_n, echo_n):
    """Sensor ultrasònic HC-SR04: distància en cm (-1 si no respon)"""
    _t = _gpio(trig_n, True)
    _e = _gpio(echo_n, False)
    _t.value = False
    time.sleep(0.000005)
    _t.value = True
    time.sleep(0.00001)
    _t.value = False
    _t0 = time.monotonic()
    while not _e.value:
        if time.monotonic() - _t0 > 0.05:
            return -1
    _t1 = time.monotonic()
    while _e.value:
        if time.monotonic() - _t1 > 0.05:
            return -1
    return (time.monotonic() - _t1) * 17150
`;

// ==================== FUNCIÓ PER GENERAR CODI COMPLET ====================

function generateCompletePythonCode(workspace) {
  // Generar codi dels blocs (workspaceToCode ja fa la init internament)
  const code = Blockly.Python.workspaceToCode(workspace);

  // Template de codi CircuitPython per TECLA
  const header = `"""
Programa generat amb TECLA Blocks
Creat per programació visual amb blocs
"""

import time
import board
import random

# MIDI (opcional - depèn del hardware i firmware del dispositiu)
try:
    import usb_midi
    from adafruit_midi import MIDI
    from adafruit_midi.note_on import NoteOn
    from adafruit_midi.note_off import NoteOff
    from adafruit_midi.control_change import ControlChange
    from adafruit_midi.program_change import ProgramChange
    from adafruit_midi.pitch_bend import PitchBend
    midi = MIDI(midi_out=usb_midi.ports[1])
    _has_midi = True
except ImportError:
    midi = None
    _has_midi = False

# HID Teclat/Ratolí (opcional - per enviar tecles i clics)
try:
    import usb_hid
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.keycode import Keycode
    from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
    _keyboard = Keyboard(usb_hid.devices)
    _keyboard_layout = KeyboardLayoutUS(_keyboard)
    _has_hid = True
except ImportError:
    _keyboard = None
    _keyboard_layout = None
    _has_hid = False
    class Keycode:
        A=4;B=5;C=6;D=7;E=8;F=9;G=10;H=11;I=12;J=13;K=14;L=15;M=16
        N=17;O=18;P=19;Q=20;R=21;S=22;T=23;U=24;V=25;W=26;X=27;Y=28;Z=29
        SPACE=44;ENTER=40;ESCAPE=41;BACKSPACE=42;TAB=43
        LEFT_CTRL=224;LEFT_SHIFT=225;LEFT_ALT=226;LEFT_GUI=227

# Botons i potenciòmetres del TECLA (opcional segons placa)
_btns = []
_pots = []
try:
    import digitalio
    for _i in range(16):
        _b = digitalio.DigitalInOut(getattr(board, "GP%d" % _i))
        _b.direction = digitalio.Direction.INPUT
        _b.pull = digitalio.Pull.DOWN
        _btns.append(_b)
except Exception:
    _btns = []
try:
    import analogio
    for _n in ("A1", "A0", "A2"):
        _pots.append(analogio.AnalogIn(getattr(board, _n)))
except Exception:
    _pots = []

${window.TECLA_HW_HELPERS}
# Els potenciòmetres ja ocupen A0-A2: reutilitzar-los com a entrades analògiques
for _i, _n in enumerate(("A1", "A0", "A2")):
    if _i < len(_pots):
        _hw_cache["a" + _n[1:]] = _pots[_i]

# Variables globals
current_octave = 4
bpm = 120
button_states = [False] * 16
last_button_states = [False] * 16
pot_values = [0, 0, 0]
_riff = [0]  # Offset de transposició (bloc "riff")

def _scan_inputs():
    """Llegeix botons i potenciòmetres cap a les variables globals"""
    for _i in range(len(_btns)):
        last_button_states[_i] = button_states[_i]
        button_states[_i] = _btns[_i].value
    for _i in range(len(_pots)):
        pot_values[_i] = _pots[_i].value >> 9  # 0-127

def tecla_sleep(duration):
    """Espera 'duration' segons"""
    _t_end = time.monotonic() + duration
    while time.monotonic() < _t_end:
        time.sleep(0.005)

def tecla_yield():
    """Refresca botons/pots dins dels bucles llargs"""
    _scan_inputs()

# Funció principal
def main():
    """Programa principal"""
    global current_octave, bpm
    print("Iniciant programa TECLA Blocks...")

    try:
        while True:
            _scan_inputs()
`;

  const footer = `
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\\nPrograma aturat per l'usuari")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Aturar totes les notes si MIDI disponible
        if _has_midi and midi:
            try:
                for note in range(128):
                    midi.send(NoteOff(note, 0))
            except:
                pass
        print("Programa finalitzat")

if __name__ == "__main__":
    main()
`;

  // Indentar el codi generat (sempre mínim 'pass' per evitar try: buit → SyntaxError)
  const _rawIndented = code.split('\n')
    .map(line => line ? '            ' + line : '')
    .join('\n');
  const indentedCode = _rawIndented.trim() ? _rawIndented : '            pass  # Afegeix blocs al workspace';

  // SERIALITZACIÓ INTEGADA (Bedded Blocks)
  // Guardem l'estat dels blocs dins el propi arxiu Python com a comentari
  // Això permetrà obrir l'arxiu .py i recuperar els blocs originals!
  const blockState = Blockly.serialization.workspaces.save(workspace);
  const jsonBlocks = JSON.stringify(blockState);

  const embeddedData = `
# ==========================================
# TECLA BLOCKS DATA (DO NOT EDIT BELOW)
# ==========================================
# TECLA_BLOCKS_EMBEDDED_JSON = '''${jsonBlocks}'''
# ==========================================
`;

  return header + indentedCode + footer + embeddedData;
}

// ==================== GENERADORS DE SÍNTESI AVANÇADA ====================

Blockly.Python.forBlock['tecla_oscillator'] = function (block) {
  const waveform = block.getFieldValue('WAVEFORM');
  // Map waveform to numeric value for MIDI: sine=0, square=1, saw=2, triangle=3
  let waveVal = 0;
  if (waveform === 'SQUARE') waveVal = 1;
  else if (waveform === 'SAWTOOTH') waveVal = 2;
  else if (waveform === 'TRIANGLE') waveVal = 3;

  const frequency = Blockly.Python.valueToCode(block, 'FREQUENCY', Blockly.Python.ORDER_ATOMIC) || '440';
  const amplitude = Blockly.Python.valueToCode(block, 'AMPLITUDE', Blockly.Python.ORDER_ATOMIC) || '100';

  const code = `# Configurar oscil·lador ${waveform}\n` +
    `midi.send(ControlChange(20, ${waveVal}))  # VSynth Waveform\n` +
    `midi.send(ControlChange(21, int(${frequency}))) # VSynth Frequency\n` +
    `midi.send(ControlChange(22, int(${amplitude}))) # VSynth Amplitude\n`;
  return code;
};

Blockly.Python.forBlock['tecla_lfo'] = function (block) {
  const rate = Blockly.Python.valueToCode(block, 'RATE', Blockly.Python.ORDER_ATOMIC) || '2';
  const depth = Blockly.Python.valueToCode(block, 'DEPTH', Blockly.Python.ORDER_ATOMIC) || '50';

  const code = `# Configurar LFO\n` +
    `midi.send(ControlChange(23, int(${rate})))   # LFO Rate\n` +
    `midi.send(ControlChange(24, int(${depth})))  # LFO Depth\n`;
  return code;
};

Blockly.Python.forBlock['tecla_envelope'] = function (block) {
  const attack = Blockly.Python.valueToCode(block, 'ATTACK', Blockly.Python.ORDER_ATOMIC) || '10';
  const decay = Blockly.Python.valueToCode(block, 'DECAY', Blockly.Python.ORDER_ATOMIC) || '50';
  const sustain = Blockly.Python.valueToCode(block, 'SUSTAIN', Blockly.Python.ORDER_ATOMIC) || '70';
  const release = Blockly.Python.valueToCode(block, 'RELEASE', Blockly.Python.ORDER_ATOMIC) || '100';

  const code = `# Envolvent ADSR\n` +
    `midi.send(ControlChange(25, int(${attack})))   # Attack\n` +
    `midi.send(ControlChange(26, int(${decay})))    # Decay\n` +
    `midi.send(ControlChange(27, int(${sustain})))  # Sustain\n` +
    `midi.send(ControlChange(28, int(${release})))  # Release\n`;
  return code;
};

Blockly.Python.forBlock['tecla_modulation'] = function (block) {
  const type = block.getFieldValue('TYPE');
  const carrier = Blockly.Python.valueToCode(block, 'CARRIER', Blockly.Python.ORDER_ATOMIC) || '440';
  const modulator = Blockly.Python.valueToCode(block, 'MODULATOR', Blockly.Python.ORDER_ATOMIC) || '220';
  const depth = Blockly.Python.valueToCode(block, 'DEPTH', Blockly.Python.ORDER_ATOMIC) || '50';

  const code = `# Modulació ${type}\n` +
    `mod_carrier = ${carrier}\n` +
    `mod_modulator = ${modulator}\n` +
    `mod_depth = ${depth}\n` +
    `# Aplicar modulació ${type}\n`;
  return code;
};

Blockly.Python.forBlock['tecla_waveshaper'] = function (block) {
  const type = block.getFieldValue('TYPE');
  const amount = Blockly.Python.valueToCode(block, 'AMOUNT', Blockly.Python.ORDER_ATOMIC) || '50';

  const code = `# Waveshaper ${type}\n` +
    `waveshape_type = "${type}"\n` +
    `waveshape_amount = ${amount}\n`;
  return code;
};

// ==================== GENERADORS D'ENTRADA/SORTIDA ====================

Blockly.Python.forBlock['tecla_digital_write'] = function (block) {
  const pin = block.getFieldValue('PIN');
  const value = block.getFieldValue('VALUE');

  const code = `# Escriure pin digital GP${pin}\n` +
    `_gpio(${pin}, True).value = ${value === '1' ? 'True' : 'False'}\n`;
  return code;
};

Blockly.Python.forBlock['tecla_digital_read'] = function (block) {
  const pin = block.getFieldValue('PIN');
  return [`_gpio(${pin}).value`, Blockly.Python.ORDER_MEMBER];
};

Blockly.Python.forBlock['tecla_analog_write'] = function (block) {
  const pin = block.getFieldValue('PIN');
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC) || '32768';

  const code = `# Escriure PWM pin GP${pin}\n` +
    `_pwm(${pin}).duty_cycle = max(0, min(65535, int(${value})))\n`;
  return code;
};

Blockly.Python.forBlock['tecla_analog_read'] = function (block) {
  const pin = block.getFieldValue('PIN');
  return [`_adc(${pin}).value`, Blockly.Python.ORDER_MEMBER];
};

// ==================== GENERADORS DE SENSORS ====================

Blockly.Python.forBlock['tecla_sensor_temperature'] = function (block) {
  Blockly.Python.definitions_['import_microcontroller'] = 'import microcontroller';
  const code = `microcontroller.cpu.temperature`;
  return [code, Blockly.Python.ORDER_MEMBER];
};

Blockly.Python.forBlock['tecla_sensor_accelerometer'] = function (block) {
  const axis = block.getFieldValue('AXIS');
  let code;
  if (axis === 'magnitude') {
    code = `(accel.acceleration[0]**2 + accel.acceleration[1]**2 + accel.acceleration[2]**2)**0.5`;
  } else {
    const axisIndex = { 'x': 0, 'y': 1, 'z': 2 }[axis];
    code = `accel.acceleration[${axisIndex}]`;
  }
  return [code, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python.forBlock['tecla_sensor_distance'] = function (block) {
  const trig = block.getFieldValue('TRIG');
  const echo = block.getFieldValue('ECHO');

  const code = `_distance_cm(${trig}, ${echo})`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

// ==================== GENERADORS DE TEXT ====================

Blockly.Python.forBlock['tecla_text_length'] = function (block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_ATOMIC) || '""';
  const code = `len(${text})`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_text_join'] = function (block) {
  const text1 = Blockly.Python.valueToCode(block, 'TEXT1', Blockly.Python.ORDER_ATOMIC) || '""';
  const text2 = Blockly.Python.valueToCode(block, 'TEXT2', Blockly.Python.ORDER_ATOMIC) || '""';
  const code = `str(${text1}) + str(${text2})`;
  return [code, Blockly.Python.ORDER_ADDITIVE];
};

Blockly.Python.forBlock['tecla_text_contains'] = function (block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_ATOMIC) || '""';
  const search = Blockly.Python.valueToCode(block, 'SEARCH', Blockly.Python.ORDER_ATOMIC) || '""';
  const code = `${search} in ${text}`;
  return [code, Blockly.Python.ORDER_RELATIONAL];
};

// ==================== GENERADORS DE LLISTES ====================

Blockly.Python.forBlock['tecla_list_create'] = function (block) {
  const code = `[]`;
  return [code, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python.forBlock['tecla_list_add'] = function (block) {
  const list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_ATOMIC) || '[]';
  const item = Blockly.Python.valueToCode(block, 'ITEM', Blockly.Python.ORDER_ATOMIC) || 'None';

  const code = `${list}.append(${item})\n`;
  return code;
};

Blockly.Python.forBlock['tecla_list_get'] = function (block) {
  const list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_ATOMIC) || '[]';
  const index = Blockly.Python.valueToCode(block, 'INDEX', Blockly.Python.ORDER_ATOMIC) || '0';
  const code = `${list}[${index}]`;
  return [code, Blockly.Python.ORDER_MEMBER];
};

Blockly.Python.forBlock['tecla_list_length'] = function (block) {
  const list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_ATOMIC) || '[]';
  const code = `len(${list})`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

// ==================== GENERADORS DE COMUNICACIÓ ====================

Blockly.Python.forBlock['tecla_serial_print'] = function (block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_ATOMIC) || '""';
  const code = `print(${text})\n`;
  return code;
};

Blockly.Python.forBlock['tecla_serial_read'] = function (block) {
  const code = `input()`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_i2c_write'] = function (block) {
  const address = Blockly.Python.valueToCode(block, 'ADDRESS', Blockly.Python.ORDER_ATOMIC) || '0x00';
  const data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || 'b"\\x00"';

  const code = `# Escriure I2C\n` +
    `i2c.writeto(${address}, ${data})\n`;
  return code;
};

Blockly.Python.forBlock['tecla_i2c_read'] = function (block) {
  const address = Blockly.Python.valueToCode(block, 'ADDRESS', Blockly.Python.ORDER_ATOMIC) || '0x00';
  const bytes = Blockly.Python.valueToCode(block, 'BYTES', Blockly.Python.ORDER_ATOMIC) || '1';

  const code = `i2c.readfrom(${address}, ${bytes})`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

// ==================== GENERADORS DE MATEMÀTIQUES AVANÇADES ====================

Blockly.Python.forBlock['tecla_math_random_int'] = function (block) {
  const from = Blockly.Python.valueToCode(block, 'FROM', Blockly.Python.ORDER_ATOMIC) || '0';
  const to = Blockly.Python.valueToCode(block, 'TO', Blockly.Python.ORDER_ATOMIC) || '100';
  const code = `random.randint(${from}, ${to})`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_map'] = function (block) {
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC) || '0';
  const fromMin = Blockly.Python.valueToCode(block, 'FROM_MIN', Blockly.Python.ORDER_ATOMIC) || '0';
  const fromMax = Blockly.Python.valueToCode(block, 'FROM_MAX', Blockly.Python.ORDER_ATOMIC) || '1023';
  const toMin = Blockly.Python.valueToCode(block, 'TO_MIN', Blockly.Python.ORDER_ATOMIC) || '0';
  const toMax = Blockly.Python.valueToCode(block, 'TO_MAX', Blockly.Python.ORDER_ATOMIC) || '127';

  const code = `int((${value} - ${fromMin}) * (${toMax} - ${toMin}) / (${fromMax} - ${fromMin}) + ${toMin})`;
  return [code, Blockly.Python.ORDER_MULTIPLICATIVE];
};

Blockly.Python.forBlock['tecla_math_constrain'] = function (block) {
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC) || '0';
  const min = Blockly.Python.valueToCode(block, 'MIN', Blockly.Python.ORDER_ATOMIC) || '0';
  const max = Blockly.Python.valueToCode(block, 'MAX', Blockly.Python.ORDER_ATOMIC) || '100';

  const code = `max(${min}, min(${max}, ${value}))`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_trig'] = function (block) {
  const op = block.getFieldValue('OP');
  const num = Blockly.Python.valueToCode(block, 'NUM', Blockly.Python.ORDER_ATOMIC) || '0';
  const code = `math.${op}(${num})`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

// ==================== GENERADORS DE FUNCIONS ====================

Blockly.Python.forBlock['tecla_function_define'] = function (block) {
  const name = _teclaSafeName(block.getFieldValue('NAME'));
  const statements = Blockly.Python.statementToCode(block, 'BODY');

  const IND = Blockly.Python.INDENT || '  ';
  // Com a definició: s'emet al principi del codi, abans de qualsevol crida
  Blockly.Python.definitions_['userfunc_' + name] =
    `def ${name}():\n` +
    `${IND}"""Funció definida per l'usuari"""\n` +
    (statements || `${IND}pass\n`);
  return '';
};

Blockly.Python.forBlock['tecla_function_call'] = function (block) {
  const name = _teclaSafeName(block.getFieldValue('NAME'));
  const code = `${name}()\n`;
  return code;
};





// ==================== GENERADORS DE RITME ====================

Blockly.Python.forBlock['tecla_set_bpm'] = function (block) {
  const bpm = Blockly.Python.valueToCode(block, 'BPM', Blockly.Python.ORDER_ATOMIC) || '120';
  const code = `global bpm\nbpm = ${bpm}\n`;
  return code;
};

Blockly.Python.forBlock['tecla_wait_beat'] = function (block) {
  const beats = block.getFieldValue('BEATS');
  const code = `time.sleep(${beats} * (60.0 / bpm))\n`;
  return code;
};

// ==================== GENERADORS CREATIUS ====================

Blockly.Python.forBlock['tecla_get_random_scale_note'] = function (block) {
  const scale = block.getFieldValue('SCALE');
  const root = block.getFieldValue('ROOT');
  const octave = Blockly.Python.valueToCode(block, 'OCTAVE', Blockly.Python.ORDER_ATOMIC) || '4';

  // Mapeig de notes arrel
  const rootNotes = {
    'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
  };

  // Intervals
  const scaleIntervals = {
    'major': [0, 2, 4, 5, 7, 9, 11, 12],
    'minor': [0, 2, 3, 5, 7, 8, 10, 12],
    'pentatonic': [0, 2, 4, 7, 9, 12],
    'blues': [0, 3, 5, 6, 7, 10, 12],
    'dorian': [0, 2, 3, 5, 7, 9, 10, 12],
    'chromatic': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  };

  const intervals = JSON.stringify(scaleIntervals[scale]);

  // Codi Python inline per calcular la nota
  const code = `((${rootNotes[root]} + random.choice(${intervals})) + ((${octave} + 1) * 12))`;

  return [code, Blockly.Python.ORDER_ATOMIC];
};

// ==================== GENERADORS D'INSTRUMENTS I CONTROL ====================

Blockly.Python.forBlock['tecla_set_instrument'] = function (block) {
  const instrument = block.getFieldValue('INSTRUMENT');
  const code = `# Canviar instrument a ${instrument}\n` +
    `midi.send(ProgramChange(${instrument}))\n`;
  return code;
};

Blockly.Python.forBlock['tecla_set_pan'] = function (block) {
  const pan = Blockly.Python.valueToCode(block, 'PAN', Blockly.Python.ORDER_ATOMIC) || '64';
  const code = `# Panning (0-127)\n` +
    `midi.send(ControlChange(10, ${pan}))\n`;
  return code;
};

Blockly.Python.forBlock['tecla_set_volume'] = function (block) {
  const volume = Blockly.Python.valueToCode(block, 'VOLUME', Blockly.Python.ORDER_ATOMIC) || '100';
  const code = `# Volum Global (0-127)\n` +
    `midi.send(ControlChange(7, ${volume}))\n`;
  return code;
};

// NOTA: els generadors de teclat/media (tecla_key_press, tecla_key_combo,
// tecla_type_text, tecla_media, tecla_open_app) viuen a tecla_python_hid.js

// Exportar la funció
window.generateCompletePythonCode = generateCompletePythonCode;
window._fullGenerateCode = generateCompletePythonCode;

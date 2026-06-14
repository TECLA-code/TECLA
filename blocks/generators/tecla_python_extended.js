// ==================== GENERADORS PYTHON AMPLIATS ====================
// Extensió de generadors per TECLA Blocks v2.1

// ==================== CONTROL AVANÇAT ====================

Blockly.Python.forBlock['tecla_switch'] = function(block) {
  const IND = Blockly.Python.INDENT || '  ';
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_RELATIONAL) || '0';
  const caseVal = block.getFieldValue('CASE0') || '0';
  const lit = isNaN(Number(caseVal)) ? JSON.stringify(caseVal) : caseVal;
  const caseCode = Blockly.Python.statementToCode(block, 'CASE0') || `${IND}pass\n`;
  const defCode  = Blockly.Python.statementToCode(block, 'DEFAULT') || `${IND}pass\n`;
  return `if ${value} == ${lit}:\n${caseCode}else:\n${defCode}`;
};

Blockly.Python.forBlock['tecla_break'] = function(block) {
  return 'break\n';
};

Blockly.Python.forBlock['tecla_continue'] = function(block) {
  return 'continue\n';
};

Blockly.Python.forBlock['tecla_try_except'] = function(block) {
  const IND = Blockly.Python.INDENT || '  ';
  const tryCode = Blockly.Python.statementToCode(block, 'TRY') || `${IND}pass\n`;
  const exceptCode = Blockly.Python.statementToCode(block, 'EXCEPT') || `${IND}pass\n`;
  return `try:\n${tryCode}except Exception as e:\n${exceptCode}\n`;
};

// ==================== TEMPS I TEMPORITZADORS ====================

Blockly.Python.forBlock['tecla_time_now'] = function(block) {
  Blockly.Python.definitions_['import_time'] = 'import time';
  return ['time.monotonic()', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_time_millis'] = function(block) {
  Blockly.Python.definitions_['import_time'] = 'import time';
  return ['int(time.monotonic() * 1000)', Blockly.Python.ORDER_FUNCTION_CALL];
};

function _teclaVarName(block, field, fallback) {
  const id = block.getFieldValue(field);
  return id ? Blockly.Python.nameDB_.getName(id, Blockly.Names.NameType.VARIABLE) : fallback;
}

Blockly.Python.forBlock['tecla_timer_start'] = function(block) {
  const varName = _teclaVarName(block, 'VAR', 'timer');
  Blockly.Python.definitions_['import_time'] = 'import time';
  return `${varName} = time.monotonic()\n`;
};

Blockly.Python.forBlock['tecla_timer_elapsed'] = function(block) {
  const varName = _teclaVarName(block, 'VAR', 'timer');
  Blockly.Python.definitions_['import_time'] = 'import time';
  return [`time.monotonic() - ${varName}`, Blockly.Python.ORDER_ADDITIVE];
};

Blockly.Python.forBlock['tecla_sleep_ms'] = function(block) {
  const time = Blockly.Python.valueToCode(block, 'TIME', Blockly.Python.ORDER_ATOMIC) || '0';
  Blockly.Python.definitions_['import_time'] = 'import time';
  return `time.sleep(${time} / 1000.0)\n`;
};

// ==================== STRING AVANÇAT ====================

Blockly.Python.forBlock['tecla_string_replace'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const old = Blockly.Python.valueToCode(block, 'OLD', Blockly.Python.ORDER_NONE) || '""';
  const newStr = Blockly.Python.valueToCode(block, 'NEW', Blockly.Python.ORDER_NONE) || '""';
  return [`${text}.replace(${old}, ${newStr})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_string_split'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const delimiter = Blockly.Python.valueToCode(block, 'DELIMITER', Blockly.Python.ORDER_NONE) || '""';
  return [`${text}.split(${delimiter})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_string_join'] = function(block) {
  const list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_NONE) || '[]';
  const separator = Blockly.Python.valueToCode(block, 'SEPARATOR', Blockly.Python.ORDER_MEMBER) || '""';
  return [`${separator}.join(str(x) for x in ${list})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_string_format'] = function(block) {
  const format = Blockly.Python.valueToCode(block, 'FORMAT', Blockly.Python.ORDER_MEMBER) || '""';
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return [`${format}.format(${value})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_string_contains'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const search = Blockly.Python.valueToCode(block, 'SEARCH', Blockly.Python.ORDER_NONE) || '""';
  return [`${search} in ${text}`, Blockly.Python.ORDER_RELATIONAL];
};

Blockly.Python.forBlock['tecla_string_startswith'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const prefix = Blockly.Python.valueToCode(block, 'PREFIX', Blockly.Python.ORDER_NONE) || '""';
  return [`${text}.startswith(${prefix})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_string_endswith'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const suffix = Blockly.Python.valueToCode(block, 'SUFFIX', Blockly.Python.ORDER_NONE) || '""';
  return [`${text}.endswith(${suffix})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

// ==================== MATEMÀTIQUES AVANÇADES ====================

Blockly.Python.forBlock['tecla_math_sin'] = function(block) {
  const angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.sin(${angle})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_cos'] = function(block) {
  const angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.cos(${angle})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_tan'] = function(block) {
  const angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.tan(${angle})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_log'] = function(block) {
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '1';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.log(${value})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_exp'] = function(block) {
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.exp(${value})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_degrees'] = function(block) {
  const radians = Blockly.Python.valueToCode(block, 'RADIANS', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.degrees(${radians})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_radians'] = function(block) {
  const degrees = Blockly.Python.valueToCode(block, 'DEGREES', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.radians(${degrees})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_math_bitwise'] = function(block) {
  const a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_BITWISE_AND) || '0';
  const b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_BITWISE_AND) || '0';
  const op = block.getFieldValue('OP');
  const operators = {
    'AND': '&',
    'OR': '|',
    'XOR': '^',
    'LSHIFT': '<<',
    'RSHIFT': '>>'
  };
  return [`${a} ${operators[op]} ${b}`, Blockly.Python.ORDER_BITWISE_AND];
};

// ==================== NEOPIXELS / RGB LEDS ====================

Blockly.Python.forBlock['tecla_neopixel_setup'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '16';
  const count = Blockly.Python.valueToCode(block, 'COUNT', Blockly.Python.ORDER_NONE) || '8';
  return `# Tira NeoPixel al pin GP${pin}\npixels = _neopix(int(${pin}), int(${count}))\n`;
};

Blockly.Python.forBlock['tecla_neopixel_set'] = function(block) {
  const index = Blockly.Python.valueToCode(block, 'INDEX', Blockly.Python.ORDER_NONE) || '0';
  const r = Blockly.Python.valueToCode(block, 'R', Blockly.Python.ORDER_NONE) || '0';
  const g = Blockly.Python.valueToCode(block, 'G', Blockly.Python.ORDER_NONE) || '0';
  const b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_NONE) || '0';
  return `pixels[${index}] = (${r}, ${g}, ${b})\n`;
};

Blockly.Python.forBlock['tecla_neopixel_show'] = function(block) {
  return 'pixels.show()\n';
};

Blockly.Python.forBlock['tecla_neopixel_clear'] = function(block) {
  return 'pixels.fill((0, 0, 0))\npixels.show()\n';
};

Blockly.Python.forBlock['tecla_neopixel_rainbow'] = function(block) {
  const offset = Blockly.Python.valueToCode(block, 'OFFSET', Blockly.Python.ORDER_NONE) || '0';
  return `_npx_rainbow(pixels, int(${offset}))\n`;
};

// ==================== DISPLAY OLED/LCD ====================

// La pantalla és el SSD1306 del TECLA: _display() l'autodetecta i, si no hi és,
// retorna una pantalla fantasma perquè el programa no peti.
Blockly.Python.forBlock['tecla_display_setup'] = function(block) {
  return `# Inicialitzar pantalla OLED (cal adafruit_ssd1306 a CIRCUITPY/lib/)\n_display()\n`;
};

Blockly.Python.forBlock['tecla_display_text'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || '""';
  const x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '0';
  const y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '0';
  return `_display().text(str(${text}), int(${x}), int(${y}), 1)\n_display().show()\n`;
};

Blockly.Python.forBlock['tecla_display_clear'] = function(block) {
  return '_display().fill(0)\n_display().show()\n';
};

Blockly.Python.forBlock['tecla_display_pixel'] = function(block) {
  const x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '0';
  const y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '0';
  const state = block.getFieldValue('STATE') === 'ON' ? '1' : '0';
  return `_display().pixel(int(${x}), int(${y}), ${state})\n_display().show()\n`;
};

Blockly.Python.forBlock['tecla_display_line'] = function(block) {
  const x1 = Blockly.Python.valueToCode(block, 'X1', Blockly.Python.ORDER_NONE) || '0';
  const y1 = Blockly.Python.valueToCode(block, 'Y1', Blockly.Python.ORDER_NONE) || '0';
  const x2 = Blockly.Python.valueToCode(block, 'X2', Blockly.Python.ORDER_NONE) || '0';
  const y2 = Blockly.Python.valueToCode(block, 'Y2', Blockly.Python.ORDER_NONE) || '0';
  return `_display().line(int(${x1}), int(${y1}), int(${x2}), int(${y2}), 1)\n_display().show()\n`;
};

Blockly.Python.forBlock['tecla_display_rect'] = function(block) {
  const x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '0';
  const y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '0';
  const width = Blockly.Python.valueToCode(block, 'WIDTH', Blockly.Python.ORDER_NONE) || '10';
  const height = Blockly.Python.valueToCode(block, 'HEIGHT', Blockly.Python.ORDER_NONE) || '10';
  const fill = block.getFieldValue('FILL') === 'FILLED' ? 'fill_rect' : 'rect';
  return `_display().${fill}(int(${x}), int(${y}), int(${width}), int(${height}), 1)\n_display().show()\n`;
};

// ==================== MOTORS I SERVOS ====================

Blockly.Python.forBlock['tecla_servo_setup'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '16';
  return `# Servo al pin GP${pin} (cal adafruit_motor a CIRCUITPY/lib/)\n_servo(int(${pin}))\n`;
};

Blockly.Python.forBlock['tecla_servo_angle'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '16';
  const angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '90';
  return `_servo(int(${pin})).angle = max(0, min(180, int(${angle})))\n`;
};

Blockly.Python.forBlock['tecla_motor_setup'] = function(block) {
  const pin1 = Blockly.Python.valueToCode(block, 'PIN1', Blockly.Python.ORDER_NONE) || '16';
  const pin2 = Blockly.Python.valueToCode(block, 'PIN2', Blockly.Python.ORDER_NONE) || '17';
  return `# Motor DC als pins GP${pin1}/GP${pin2}\nmotor_pin1 = _gpio(int(${pin1}), True)\nmotor_pin2 = _gpio(int(${pin2}), True)\n`;
};

Blockly.Python.forBlock['tecla_motor_speed'] = function(block) {
  const speed = Blockly.Python.valueToCode(block, 'SPEED', Blockly.Python.ORDER_NONE) || '0';
  const direction = block.getFieldValue('DIRECTION');
  if (direction === 'FORWARD') {
    return `motor_pin1.value = True\nmotor_pin2.value = False\n`;
  } else if (direction === 'BACKWARD') {
    return `motor_pin1.value = False\nmotor_pin2.value = True\n`;
  } else {
    return `motor_pin1.value = False\nmotor_pin2.value = False\n`;
  }
};

// ==================== SENSORS ADICIONALS ====================

Blockly.Python.forBlock['tecla_sensor_light'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  return [`int(_adc(${pin}).value / 65535 * 100)`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_sensor_sound'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  return [`int(_adc(${pin}).value / 65535 * 100)`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_sensor_moisture'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  return [`int(_adc(${pin}).value / 65535 * 100)`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_sensor_pir'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '16';
  return [`_gpio(int(${pin})).value`, Blockly.Python.ORDER_MEMBER];
};

Blockly.Python.forBlock['tecla_sensor_button_external'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '16';
  const pull = block.getFieldValue('PULL');
  if (pull === 'PULLUP') {
    // Amb pull-up, el botó premut posa el pin a 0: invertim la lectura
    return [`(not _gpio(int(${pin}), False, True).value)`, Blockly.Python.ORDER_LOGICAL_NOT];
  }
  return [`_gpio(int(${pin})).value`, Blockly.Python.ORDER_MEMBER];
};

// ==================== PWM AVANÇAT ====================

Blockly.Python.forBlock['tecla_pwm_setup'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '16';
  const freq = Blockly.Python.valueToCode(block, 'FREQ', Blockly.Python.ORDER_NONE) || '1000';
  return `# PWM al pin GP${pin} a ${freq} Hz\n_pwm(int(${pin}), int(${freq}))\n`;
};

Blockly.Python.forBlock['tecla_pwm_duty'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '16';
  const duty = Blockly.Python.valueToCode(block, 'DUTY', Blockly.Python.ORDER_NONE) || '50';
  return `_pwm(int(${pin})).duty_cycle = int(max(0, min(100, ${duty})) / 100 * 65535)\n`;
};

// ==================== EMMAGATZEMATGE ====================

// Magatzem simple clau-valor en memòria (es perd en reiniciar el dispositiu)
Blockly.Python.forBlock['tecla_storage_write'] = function(block) {
  const key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '""';
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['tecla_storage'] = '_storage = {}  # magatzem clau-valor en memòria';
  return `_storage[${key}] = ${value}\n`;
};

Blockly.Python.forBlock['tecla_storage_read'] = function(block) {
  const key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '""';
  Blockly.Python.definitions_['tecla_storage'] = '_storage = {}  # magatzem clau-valor en memòria';
  return [`_storage.get(${key}, 0)`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_storage_exists'] = function(block) {
  const key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '""';
  Blockly.Python.definitions_['tecla_storage'] = '_storage = {}  # magatzem clau-valor en memòria';
  return [`(${key} in _storage)`, Blockly.Python.ORDER_RELATIONAL];
};

Blockly.Python.forBlock['tecla_storage_delete'] = function(block) {
  const key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '""';
  Blockly.Python.definitions_['tecla_storage'] = '_storage = {}  # magatzem clau-valor en memòria';
  return `_storage.pop(${key}, None)\n`;
};

// ==================== SISTEMA ====================

Blockly.Python.forBlock['tecla_system_reset'] = function(block) {
  Blockly.Python.definitions_['import_microcontroller'] = 'import microcontroller';
  return 'microcontroller.reset()\n';
};

Blockly.Python.forBlock['tecla_system_memory'] = function(block) {
  Blockly.Python.definitions_['import_gc'] = 'import gc';
  return ['gc.mem_free()', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_system_cpu_temp'] = function(block) {
  Blockly.Python.definitions_['import_microcontroller'] = 'import microcontroller';
  return ['microcontroller.cpu.temperature', Blockly.Python.ORDER_MEMBER];
};

Blockly.Python.forBlock['tecla_system_voltage'] = function(block) {
  return ['(_adc_named("VOLTAGE_MONITOR").value * 3.3 * 3 / 65536)', Blockly.Python.ORDER_MULTIPLICATIVE];
};

// ==================== GENERADORS MODULARS / GENERATIUS ====================

Blockly.Python.forBlock['tecla_probability'] = function (block) {
    const percent = Blockly.Python.valueToCode(block, 'PERCENT', Blockly.Python.ORDER_MEMBER) || '50';
    const IND = Blockly.Python.INDENT || '  ';
    const statements = Blockly.Python.statementToCode(block, 'DO') || `${IND}pass\n`;

    Blockly.Python.definitions_['import_random'] = 'import random';

    const code = `# Probabilitat ${percent}%\n` +
        `if random.random() < (${percent} / 100.0):\n` +
        statements +
        `\n`;
    return code;
};

Blockly.Python.forBlock['tecla_software_lfo'] = function (block) {
    const rate = Blockly.Python.valueToCode(block, 'RATE', Blockly.Python.ORDER_MEMBER) || '1';
    const min = Blockly.Python.valueToCode(block, 'MIN', Blockly.Python.ORDER_MEMBER) || '0';
    const max = Blockly.Python.valueToCode(block, 'MAX', Blockly.Python.ORDER_MEMBER) || '100';

    Blockly.Python.definitions_['import_math'] = 'import math';
    Blockly.Python.definitions_['import_time'] = 'import time';

    // Fórmula: (sin(t * rate) + 1) / 2 * (max - min) + min
    // Basic sine calculation mapped to range
    // time.monotonic() * rate * 2 * pi gives cycles

    const code = `(math.sin(time.monotonic() * ${rate} * 6.28) + 1) / 2 * (${max} - ${min}) + ${min}`;
    return [code, Blockly.Python.ORDER_MULTIPLICATIVE];
};

Blockly.Python.forBlock['tecla_scale_quantize'] = function (block) {
    const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_MEMBER) || '60';
    const scale = block.getFieldValue('SCALE');
    const root = block.getFieldValue('ROOT');

    // Definim intervals i notes arrel (repetim lògica de python però inline o funcions helper)
    // Per eficiència generarem una funció helper Python

    Blockly.Python.definitions_['func_quantize'] = `
def quantize_note(value, scale_name, root_name):
    root_notes = {'C':0, 'D':2, 'E':4, 'F':5, 'G':7, 'A':9, 'B':11}
    scale_intervals = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'pentatonic': [0, 2, 4, 7, 9],
        'blues': [0, 3, 5, 6, 7, 10],
        'chromatic': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    }
    
    root_val = root_notes.get(root_name, 0)
    intervals = scale_intervals.get(scale_name, [0])
    
    # Normalitzar a octava 0-11
    note_in_octave = (value - root_val) % 12
    octave_base = value - note_in_octave
    
    # Trobar interval més proper
    closest = min(intervals, key=lambda x: abs(x - note_in_octave))
    
    return octave_base + closest
`;

    const code = `quantize_note(${value}, '${scale}', '${root}')`;
    return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_euclidean_rhythm'] = function (block) {
    const step = Blockly.Python.valueToCode(block, 'STEP', Blockly.Python.ORDER_MEMBER) || '0';
    const pulses = Blockly.Python.valueToCode(block, 'PULSES', Blockly.Python.ORDER_MEMBER) || '4';
    const steps = Blockly.Python.valueToCode(block, 'STEPS', Blockly.Python.ORDER_MEMBER) || '16';

    // Algorisme Euclidià Simple: (step * pulses) % steps < pulses
    // És una aproximació molt eficient que genera distribució uniforme

    const code = `((${step} * ${pulses}) % ${steps}) < ${pulses}`;
    return [code, Blockly.Python.ORDER_RELATIONAL];
};

// ==================== MIDI AVANÇAT ====================

Blockly.Python.forBlock['tecla_midi_cc'] = function (block) {
  const ccType = block.getFieldValue('CC_TYPE');
  const ccNum  = Blockly.Python.valueToCode(block, 'CC_NUM',  Blockly.Python.ORDER_ATOMIC) || '1';
  const ccVal  = Blockly.Python.valueToCode(block, 'CC_VAL',  Blockly.Python.ORDER_ATOMIC) || '64';
  const num    = ccType === 'custom' ? ccNum : ccType;
  return `midi.send(ControlChange(${num}, max(0, min(127, int(${ccVal})))))\n`;
};

Blockly.Python.forBlock['tecla_midi_pitch_bend'] = function (block) {
  const amount = Blockly.Python.valueToCode(block, 'AMOUNT', Blockly.Python.ORDER_ATOMIC) || '0';
  return `# Pitch Bend: escala -63..+63 → 0..16383\n` +
    `midi.send(PitchBend(max(0, min(16383, int((${amount} + 63) * 130)))))\n`;
};

Blockly.Python.forBlock['tecla_midi_all_notes_off'] = function (_block) {
  return `# Panic: apagar totes les notes\n` +
    `for _ch in range(16):\n` +
    `    midi.send(ControlChange(123, 0, channel=_ch))\n`;
};

Blockly.Python.forBlock['tecla_midi_sustain'] = function (block) {
  const state = block.getFieldValue('STATE');
  return `midi.send(ControlChange(64, ${state}))  # Sustain pedal\n`;
};

Blockly.Python.forBlock['tecla_midi_expression'] = function (block) {
  const val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC) || '127';
  return `midi.send(ControlChange(11, max(0, min(127, int(${val})))))  # CC11 Expressió\n`;
};

// ==================== LIVE CODING ====================

Blockly.Python.forBlock['tecla_note_on_only'] = function (block) {
  const note = Blockly.Python.valueToCode(block, 'NOTE',     Blockly.Python.ORDER_ATOMIC) || '60';
  const vel  = Blockly.Python.valueToCode(block, 'VELOCITY', Blockly.Python.ORDER_ATOMIC) || '100';
  return `midi.send(NoteOn((${note}) + _riff[0], ${vel}))  # NoteOn sense NoteOff\n`;
};

Blockly.Python.forBlock['tecla_note_off_only'] = function (block) {
  const note = Blockly.Python.valueToCode(block, 'NOTE', Blockly.Python.ORDER_ATOMIC) || '60';
  return `midi.send(NoteOff((${note}) + _riff[0], 0))  # NoteOff explícit\n`;
};

Blockly.Python.forBlock['tecla_transpose'] = function (block) {
  const note = Blockly.Python.valueToCode(block, 'NOTE',      Blockly.Python.ORDER_ADDITIVE) || '60';
  const semi = Blockly.Python.valueToCode(block, 'SEMITONES', Blockly.Python.ORDER_ADDITIVE) || '0';
  return [`max(0, min(127, (${note}) + (${semi})))`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_humanize_vel'] = function (block) {
  const base   = Blockly.Python.valueToCode(block, 'BASE_VEL', Blockly.Python.ORDER_ADDITIVE) || '100';
  const spread = Blockly.Python.valueToCode(block, 'SPREAD',   Blockly.Python.ORDER_ATOMIC)   || '10';
  Blockly.Python.definitions_['import_random'] = 'import random';
  return [`max(1, min(127, (${base}) + random.randint(-${spread}, ${spread})))`,
          Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python.forBlock['tecla_crescendo'] = function (block) {
  const from = Blockly.Python.valueToCode(block, 'FROM_VAL', Blockly.Python.ORDER_ATOMIC) || '0';
  const to   = Blockly.Python.valueToCode(block, 'TO_VAL',   Blockly.Python.ORDER_ATOMIC) || '127';
  const dur  = Blockly.Python.valueToCode(block, 'DURATION', Blockly.Python.ORDER_ATOMIC) || '2.0';
  const cc   = block.getFieldValue('CC');
  return `# Crescendo CC${cc} de ${from} a ${to} en ${dur}s\n` +
    `_steps = 20\n` +
    `_step_t = (${dur}) / _steps\n` +
    `for _i in range(_steps + 1):\n` +
    `    _v = int((${from}) + (_i / _steps) * ((${to}) - (${from})))\n` +
    `    midi.send(ControlChange(${cc}, max(0, min(127, _v))))\n` +
    `    time.sleep(_step_t)\n`;
};

Blockly.Python.forBlock['tecla_riff_repeat'] = function (block) {
  const IND    = Blockly.Python.INDENT || '  ';
  const times  = block.getFieldValue('TIMES') || '4';
  const transp = parseInt(block.getFieldValue('EACH_TRANSPOSE') || '0', 10) || 0;
  const riff   = Blockly.Python.statementToCode(block, 'RIFF') || `${IND}pass\n`;
  if (!transp) {
    return `# Riff × ${times}\nfor _rep in range(${times}):\n${riff}`;
  }
  // _riff[0] és l'offset global que els blocs de nota sumen a cada NoteOn/NoteOff
  return `# Riff × ${times} (${transp > 0 ? '+' : ''}${transp} semitons per repetició)\n` +
    `_riff[0] = 0\n` +
    `for _rep in range(${times}):\n` +
    riff +
    `${IND}_riff[0] += ${transp}\n` +
    `_riff[0] = 0\n`;
};

// ==================== SEQÜENCIADOR ====================

Blockly.Python.forBlock['tecla_seq_play_steps'] = function (block) {
  const notes    = block.getFieldValue('NOTES') || '60,62,64,67';
  const velocity = Blockly.Python.valueToCode(block, 'VELOCITY', Blockly.Python.ORDER_ATOMIC) || '100';
  const stepDur  = Blockly.Python.valueToCode(block, 'STEP_DUR', Blockly.Python.ORDER_ATOMIC) || '0.25';
  return `# Seqüència MIDI\n` +
    `for _seq_note in [${notes}]:\n` +
    `    midi.send(NoteOn(_seq_note, ${velocity}))\n` +
    `    time.sleep(${stepDur})\n` +
    `    midi.send(NoteOff(_seq_note, 0))\n`;
};

Blockly.Python.forBlock['tecla_arpeggio_dir'] = function (block) {
  const chord = block.getFieldValue('CHORD');
  const dir   = block.getFieldValue('DIR');
  const speed = Blockly.Python.valueToCode(block, 'SPEED', Blockly.Python.ORDER_ATOMIC) || '0.12';

  const chordMap = {
    'C':  [48,52,55,60], 'D':  [50,54,57,62], 'E':  [52,56,59,64],
    'F':  [53,57,60,65], 'G':  [55,59,62,67], 'A':  [57,61,64,69], 'B':  [59,63,66,71],
    'Cm': [48,51,55,60], 'Dm': [50,53,57,62], 'Em': [52,55,59,64],
    'Fm': [53,56,60,65], 'Gm': [55,58,62,67], 'Am': [57,60,64,69], 'Bm': [59,62,66,71]
  };
  const notes = chordMap[chord] || [48,52,55,60];

  let seq;
  if (dir === 'up')     seq = notes;
  else if (dir === 'down') seq = [...notes].reverse();
  else if (dir === 'updown') seq = [...notes, ...[...notes].reverse().slice(1,-1)];
  else seq = notes; // random handled at runtime below

  if (dir === 'random') {
    return `# Arpegi ${chord} aleatori\n` +
      `import random as _rnd\n` +
      `_arp = [${notes.join(',')}]\n` +
      `_rnd.shuffle(_arp)\n` +
      `for _n in _arp:\n` +
      `    midi.send(NoteOn(_n, 100))\n` +
      `    time.sleep(${speed})\n` +
      `    midi.send(NoteOff(_n, 0))\n`;
  }

  let code = `# Arpegi ${chord} ${dir}\n`;
  seq.forEach(n => {
    code += `midi.send(NoteOn(${n}, 100))\n`;
    code += `time.sleep(${speed})\n`;
    code += `midi.send(NoteOff(${n}, 0))\n`;
  });
  return code;
};

Blockly.Python.forBlock['tecla_seq_grid'] = function (block) {
  const _N = {'C':0,'Cs':1,'D':2,'Ds':3,'E':4,'F':5,'Fs':6,'G':7,'Gs':8,'A':9,'As':10,'B':11};
  const vel = block.getFieldValue('VEL') || '100';
  const dur = block.getFieldValue('DUR') || '0.25';
  const steps = [];
  for (let i = 1; i <= 8; i++) {
    const n = block.getFieldValue('N' + i);
    const o = block.getFieldValue('O' + i);
    if (!n || n === 'REST') steps.push(-1);
    else steps.push((parseInt(o) + 1) * 12 + (_N[n] || 0));
  }
  let code = `# Seqüenciador grid (8 passos)\n`;
  code += `for _sn in [${steps.join(', ')}]:\n`;
  code += `    if _sn >= 0:\n`;
  code += `        midi.send(NoteOn(_sn, ${vel}))\n`;
  code += `        time.sleep(${dur})\n`;
  code += `        midi.send(NoteOff(_sn, 0))\n`;
  code += `    else:\n`;
  code += `        time.sleep(${dur})\n`;
  return code;
};

Blockly.Python.forBlock['tecla_drum_hit'] = function (block) {
  const drum     = block.getFieldValue('DRUM');
  const velocity = Blockly.Python.valueToCode(block, 'VELOCITY', Blockly.Python.ORDER_ATOMIC) || '100';
  return `# Percussió MIDI GM (canal 10)\n` +
    `midi.send(NoteOn(${drum}, ${velocity}, channel=9))\n` +
    `time.sleep(0.05)\n` +
    `midi.send(NoteOff(${drum}, 0, channel=9))\n`;
};

Blockly.Python.forBlock['tecla_drum_pattern'] = function (block) {
  const drum    = block.getFieldValue('DRUM');
  const pattern = block.getFieldValue('PATTERN') || '1000100010001000';
  const stepDur = Blockly.Python.valueToCode(block, 'STEP_DUR', Blockly.Python.ORDER_ATOMIC) || '0.125';
  return `# Patró rítmic: ${pattern}\n` +
    `for _step in "${pattern}":\n` +
    `    if _step == '1':\n` +
    `        midi.send(NoteOn(${drum}, 100, channel=9))\n` +
    `        time.sleep(0.04)\n` +
    `        midi.send(NoteOff(${drum}, 0, channel=9))\n` +
    `    time.sleep(${stepDur})\n`;
};

Blockly.Python.forBlock['tecla_note_name'] = function (block) {
  const note = block.getFieldValue('NOTE') || '60';
  return [note, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python.forBlock['tecla_chord_progression'] = function (block) {
  const prog     = block.getFieldValue('PROG');
  const keyOff   = parseInt(block.getFieldValue('KEY') || '0', 10);
  const beatsDur = Blockly.Python.valueToCode(block, 'BEATS_DUR', Blockly.Python.ORDER_ATOMIC) || '1.0';

  // Progressions en C (offset 0), transposades pel key
  const progressions = {
    pop:     [[48,52,55],[53,57,60],[55,59,62],[48,52,55]],       // I-IV-V-I
    modern:  [[48,52,55],[55,59,62],[57,60,64],[53,57,60]],       // I-V-vi-IV
    jazz:    [[50,53,57],[55,59,62],[48,52,55]],                   // ii-V-I
    fifties: [[48,52,55],[57,60,64],[53,57,60],[55,59,62]],       // I-vi-IV-V
    blues:   [[48,52,55],[53,57,60],[48,52,55],[55,59,62]],       // I-IV-I-V
    rock:    [[48,51,55],[46,50,53],[45,48,52],[46,50,53]]        // i-VII-VI-VII
  };

  const chords = (progressions[prog] || progressions.pop)
    .map(ch => ch.map(n => n + keyOff));

  const keyNames = {0:'C',2:'D',4:'E',5:'F',7:'G',9:'A',11:'B'};
  const keyName  = keyNames[keyOff] || 'C';

  let code = `# Progressió ${prog} en ${keyName}\n`;
  chords.forEach((ch, i) => {
    code += `# Acord ${i+1}\n`;
    ch.forEach(n => code += `midi.send(NoteOn(${n}, 90))\n`);
    code += `time.sleep(${beatsDur})\n`;
    ch.forEach(n => code += `midi.send(NoteOff(${n}, 0))\n`);
  });
  return code;
};

// ==================== GENERADORS PYTHON AMPLIATS ====================
// Extensió de generadors per TECLA Blocks v2.1

// ==================== CONTROL AVANÇAT ====================

Blockly.Python['tecla_switch'] = function(block) {
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC);
  // Implementació simplificada amb if/elif
  return `# Switch statement (simplificat amb if/elif)\n`;
};

Blockly.Python['tecla_break'] = function(block) {
  return 'break\n';
};

Blockly.Python['tecla_continue'] = function(block) {
  return 'continue\n';
};

Blockly.Python['tecla_try_except'] = function(block) {
  const tryCode = Blockly.Python.statementToCode(block, 'TRY');
  const exceptCode = Blockly.Python.statementToCode(block, 'EXCEPT');
  return `try:\n${tryCode}except Exception as e:\n${exceptCode}\n`;
};

// ==================== TEMPS I TEMPORITZADORS ====================

Blockly.Python['tecla_time_now'] = function(block) {
  Blockly.Python.definitions_['import_time'] = 'import time';
  return ['time.monotonic()', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_time_millis'] = function(block) {
  Blockly.Python.definitions_['import_time'] = 'import time';
  return ['int(time.monotonic() * 1000)', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_timer_start'] = function(block) {
  const varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.Variables.NAME_TYPE);
  Blockly.Python.definitions_['import_time'] = 'import time';
  return `${varName} = time.monotonic()\n`;
};

Blockly.Python['tecla_timer_elapsed'] = function(block) {
  const varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.Variables.NAME_TYPE);
  Blockly.Python.definitions_['import_time'] = 'import time';
  return [`time.monotonic() - ${varName}`, Blockly.Python.ORDER_ADDITIVE];
};

Blockly.Python['tecla_sleep_ms'] = function(block) {
  const time = Blockly.Python.valueToCode(block, 'TIME', Blockly.Python.ORDER_ATOMIC) || '0';
  Blockly.Python.definitions_['import_time'] = 'import time';
  return `time.sleep(${time} / 1000.0)\n`;
};

// ==================== STRING AVANÇAT ====================

Blockly.Python['tecla_string_replace'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const old = Blockly.Python.valueToCode(block, 'OLD', Blockly.Python.ORDER_NONE) || '""';
  const newStr = Blockly.Python.valueToCode(block, 'NEW', Blockly.Python.ORDER_NONE) || '""';
  return [`${text}.replace(${old}, ${newStr})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_string_split'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const delimiter = Blockly.Python.valueToCode(block, 'DELIMITER', Blockly.Python.ORDER_NONE) || '""';
  return [`${text}.split(${delimiter})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_string_join'] = function(block) {
  const list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_NONE) || '[]';
  const separator = Blockly.Python.valueToCode(block, 'SEPARATOR', Blockly.Python.ORDER_MEMBER) || '""';
  return [`${separator}.join(str(x) for x in ${list})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_string_format'] = function(block) {
  const format = Blockly.Python.valueToCode(block, 'FORMAT', Blockly.Python.ORDER_MEMBER) || '""';
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return [`${format}.format(${value})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_string_contains'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const search = Blockly.Python.valueToCode(block, 'SEARCH', Blockly.Python.ORDER_NONE) || '""';
  return [`${search} in ${text}`, Blockly.Python.ORDER_RELATIONAL];
};

Blockly.Python['tecla_string_startswith'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const prefix = Blockly.Python.valueToCode(block, 'PREFIX', Blockly.Python.ORDER_NONE) || '""';
  return [`${text}.startswith(${prefix})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_string_endswith'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_MEMBER) || '""';
  const suffix = Blockly.Python.valueToCode(block, 'SUFFIX', Blockly.Python.ORDER_NONE) || '""';
  return [`${text}.endswith(${suffix})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

// ==================== MATEMÀTIQUES AVANÇADES ====================

Blockly.Python['tecla_math_sin'] = function(block) {
  const angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.sin(${angle})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_math_cos'] = function(block) {
  const angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.cos(${angle})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_math_tan'] = function(block) {
  const angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.tan(${angle})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_math_log'] = function(block) {
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '1';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.log(${value})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_math_exp'] = function(block) {
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.exp(${value})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_math_degrees'] = function(block) {
  const radians = Blockly.Python.valueToCode(block, 'RADIANS', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.degrees(${radians})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_math_radians'] = function(block) {
  const degrees = Blockly.Python.valueToCode(block, 'DEGREES', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  return [`math.radians(${degrees})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_math_bitwise'] = function(block) {
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

Blockly.Python['tecla_neopixel_setup'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  const count = Blockly.Python.valueToCode(block, 'COUNT', Blockly.Python.ORDER_NONE) || '10';
  Blockly.Python.definitions_['import_neopixel'] = 'import neopixel\nimport board';
  Blockly.Python.definitions_['neopixel_strip'] = `pixels = neopixel.NeoPixel(board.GP${pin}, ${count}, brightness=0.5, auto_write=False)`;
  return '';
};

Blockly.Python['tecla_neopixel_set'] = function(block) {
  const index = Blockly.Python.valueToCode(block, 'INDEX', Blockly.Python.ORDER_NONE) || '0';
  const r = Blockly.Python.valueToCode(block, 'R', Blockly.Python.ORDER_NONE) || '0';
  const g = Blockly.Python.valueToCode(block, 'G', Blockly.Python.ORDER_NONE) || '0';
  const b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_NONE) || '0';
  return `pixels[${index}] = (${r}, ${g}, ${b})\n`;
};

Blockly.Python['tecla_neopixel_show'] = function(block) {
  return 'pixels.show()\n';
};

Blockly.Python['tecla_neopixel_clear'] = function(block) {
  return 'pixels.fill((0, 0, 0))\npixels.show()\n';
};

Blockly.Python['tecla_neopixel_rainbow'] = function(block) {
  const offset = Blockly.Python.valueToCode(block, 'OFFSET', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['neopixel_rainbow'] = `def rainbow_cycle(offset):
    for i in range(len(pixels)):
        pixel_index = (i * 256 // len(pixels)) + offset
        pixels[i] = wheel(pixel_index & 255)
    pixels.show()

def wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)`;
  return `rainbow_cycle(${offset})\n`;
};

// ==================== DISPLAY OLED/LCD ====================

Blockly.Python['tecla_display_setup'] = function(block) {
  const type = block.getFieldValue('TYPE');
  if (type === 'OLED') {
    Blockly.Python.definitions_['import_display'] = 'import board\nimport displayio\nimport busio\nimport adafruit_displayio_ssd1306';
    Blockly.Python.definitions_['display_setup'] = `i2c = busio.I2C(board.SCL, board.SDA)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)`;
  } else {
    Blockly.Python.definitions_['import_display'] = 'import board\nimport busio\nfrom adafruit_character_lcd.character_lcd_i2c import Character_LCD_I2C';
    Blockly.Python.definitions_['display_setup'] = `i2c = busio.I2C(board.SCL, board.SDA)
lcd = Character_LCD_I2C(i2c, 16, 2)`;
  }
  return '';
};

Blockly.Python['tecla_display_text'] = function(block) {
  const text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || '""';
  const x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '0';
  const y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '0';
  return `display.text(${text}, ${x}, ${y}, 1)\n`;
};

Blockly.Python['tecla_display_clear'] = function(block) {
  return 'display.fill(0)\ndisplay.show()\n';
};

Blockly.Python['tecla_display_pixel'] = function(block) {
  const x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '0';
  const y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '0';
  const state = block.getFieldValue('STATE') === 'ON' ? '1' : '0';
  return `display.pixel(${x}, ${y}, ${state})\n`;
};

Blockly.Python['tecla_display_line'] = function(block) {
  const x1 = Blockly.Python.valueToCode(block, 'X1', Blockly.Python.ORDER_NONE) || '0';
  const y1 = Blockly.Python.valueToCode(block, 'Y1', Blockly.Python.ORDER_NONE) || '0';
  const x2 = Blockly.Python.valueToCode(block, 'X2', Blockly.Python.ORDER_NONE) || '0';
  const y2 = Blockly.Python.valueToCode(block, 'Y2', Blockly.Python.ORDER_NONE) || '0';
  return `display.line(${x1}, ${y1}, ${x2}, ${y2}, 1)\n`;
};

Blockly.Python['tecla_display_rect'] = function(block) {
  const x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '0';
  const y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '0';
  const width = Blockly.Python.valueToCode(block, 'WIDTH', Blockly.Python.ORDER_NONE) || '10';
  const height = Blockly.Python.valueToCode(block, 'HEIGHT', Blockly.Python.ORDER_NONE) || '10';
  const fill = block.getFieldValue('FILL') === 'FILLED' ? 'fill_rect' : 'rect';
  return `display.${fill}(${x}, ${y}, ${width}, ${height}, 1)\n`;
};

// ==================== MOTORS I SERVOS ====================

Blockly.Python['tecla_servo_setup'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_servo'] = 'import board\nimport pwmio\nfrom adafruit_motor import servo';
  Blockly.Python.definitions_[`servo_${pin}`] = `pwm_${pin} = pwmio.PWMOut(board.GP${pin}, frequency=50)
servo_${pin} = servo.Servo(pwm_${pin})`;
  return '';
};

Blockly.Python['tecla_servo_angle'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  const angle = Blockly.Python.valueToCode(block, 'ANGLE', Blockly.Python.ORDER_NONE) || '90';
  return `servo_${pin}.angle = ${angle}\n`;
};

Blockly.Python['tecla_motor_setup'] = function(block) {
  const pin1 = Blockly.Python.valueToCode(block, 'PIN1', Blockly.Python.ORDER_NONE) || '0';
  const pin2 = Blockly.Python.valueToCode(block, 'PIN2', Blockly.Python.ORDER_NONE) || '1';
  Blockly.Python.definitions_['import_motor'] = 'import board\nimport pwmio\nimport digitalio';
  Blockly.Python.definitions_['motor_setup'] = `motor_pin1 = digitalio.DigitalInOut(board.GP${pin1})
motor_pin2 = digitalio.DigitalInOut(board.GP${pin2})
motor_pin1.direction = digitalio.Direction.OUTPUT
motor_pin2.direction = digitalio.Direction.OUTPUT`;
  return '';
};

Blockly.Python['tecla_motor_speed'] = function(block) {
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

Blockly.Python['tecla_sensor_light'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_analogio'] = 'import board\nimport analogio';
  Blockly.Python.definitions_[`light_sensor_${pin}`] = `light_sensor = analogio.AnalogIn(board.A${pin})`;
  return [`int(light_sensor.value / 65535 * 100)`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_sensor_sound'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_analogio'] = 'import board\nimport analogio';
  Blockly.Python.definitions_[`sound_sensor_${pin}`] = `sound_sensor = analogio.AnalogIn(board.A${pin})`;
  return [`int(sound_sensor.value / 65535 * 100)`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_sensor_moisture'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_analogio'] = 'import board\nimport analogio';
  Blockly.Python.definitions_[`moisture_sensor_${pin}`] = `moisture_sensor = analogio.AnalogIn(board.A${pin})`;
  return [`int(moisture_sensor.value / 65535 * 100)`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_sensor_pir'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_digitalio'] = 'import board\nimport digitalio';
  Blockly.Python.definitions_[`pir_sensor_${pin}`] = `pir_sensor = digitalio.DigitalInOut(board.GP${pin})
pir_sensor.direction = digitalio.Direction.INPUT`;
  return [`pir_sensor.value`, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['tecla_sensor_button_external'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  const pull = block.getFieldValue('PULL');
  Blockly.Python.definitions_['import_digitalio'] = 'import board\nimport digitalio';
  const pullType = pull === 'PULLUP' ? 'digitalio.Pull.UP' : 'digitalio.Pull.DOWN';
  Blockly.Python.definitions_[`button_${pin}`] = `button_${pin} = digitalio.DigitalInOut(board.GP${pin})
button_${pin}.direction = digitalio.Direction.INPUT
button_${pin}.pull = ${pullType}`;
  return [`button_${pin}.value`, Blockly.Python.ORDER_ATOMIC];
};

// ==================== PWM AVANÇAT ====================

Blockly.Python['tecla_pwm_setup'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  const freq = Blockly.Python.valueToCode(block, 'FREQ', Blockly.Python.ORDER_NONE) || '1000';
  Blockly.Python.definitions_['import_pwmio'] = 'import board\nimport pwmio';
  Blockly.Python.definitions_[`pwm_${pin}`] = `pwm_${pin} = pwmio.PWMOut(board.GP${pin}, frequency=${freq}, duty_cycle=0)`;
  return '';
};

Blockly.Python['tecla_pwm_duty'] = function(block) {
  const pin = Blockly.Python.valueToCode(block, 'PIN', Blockly.Python.ORDER_NONE) || '0';
  const duty = Blockly.Python.valueToCode(block, 'DUTY', Blockly.Python.ORDER_NONE) || '50';
  return `pwm_${pin}.duty_cycle = int(${duty} / 100 * 65535)\n`;
};

// ==================== EMMAGATZEMATGE ====================

Blockly.Python['tecla_storage_write'] = function(block) {
  const key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '""';
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_storage'] = 'import json';
  return `# Save to storage: ${key} = ${value}\n`;
};

Blockly.Python['tecla_storage_read'] = function(block) {
  const key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '""';
  return [`# Read from storage: ${key}`, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['tecla_storage_exists'] = function(block) {
  const key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '""';
  return [`# Check if exists: ${key}`, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['tecla_storage_delete'] = function(block) {
  const key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '""';
  return `# Delete from storage: ${key}\n`;
};

// ==================== SISTEMA ====================

Blockly.Python['tecla_system_reset'] = function(block) {
  Blockly.Python.definitions_['import_microcontroller'] = 'import microcontroller';
  return 'microcontroller.reset()\n';
};

Blockly.Python['tecla_system_memory'] = function(block) {
  Blockly.Python.definitions_['import_gc'] = 'import gc';
  return ['gc.mem_free()', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['tecla_system_cpu_temp'] = function(block) {
  Blockly.Python.definitions_['import_microcontroller'] = 'import microcontroller';
  return ['microcontroller.cpu.temperature', Blockly.Python.ORDER_MEMBER];
};

Blockly.Python['tecla_system_voltage'] = function(block) {
  Blockly.Python.definitions_['import_analogio'] = 'import board\nimport analogio';
  Blockly.Python.definitions_['voltage_sensor'] = `voltage_sense = analogio.AnalogIn(board.VOLTAGE_MONITOR)`;
  return ['voltage_sense.value * 3.3 / 65536', Blockly.Python.ORDER_MULTIPLICATIVE];
};

// ==================== GENERADORS MODULARS / GENERATIUS ====================

Blockly.Python['tecla_probability'] = function (block) {
    const percent = Blockly.Python.valueToCode(block, 'PERCENT', Blockly.Python.ORDER_MEMBER) || '50';
    const statements = Blockly.Python.statementToCode(block, 'DO');

    Blockly.Python.definitions_['import_random'] = 'import random';

    const code = `# Probabilitat ${percent}%\n` +
        `if random.random() < (${percent} / 100.0):\n` +
        statements +
        `\n`;
    return code;
};

Blockly.Python['tecla_software_lfo'] = function (block) {
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

Blockly.Python['tecla_scale_quantize'] = function (block) {
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

Blockly.Python['tecla_euclidean_rhythm'] = function (block) {
    const step = Blockly.Python.valueToCode(block, 'STEP', Blockly.Python.ORDER_MEMBER) || '0';
    const pulses = Blockly.Python.valueToCode(block, 'PULSES', Blockly.Python.ORDER_MEMBER) || '4';
    const steps = Blockly.Python.valueToCode(block, 'STEPS', Blockly.Python.ORDER_MEMBER) || '16';

    // Algorisme Euclidià Simple: (step * pulses) % steps < pulses
    // És una aproximació molt eficient que genera distribució uniforme

    const code = `((${step} * ${pulses}) % ${steps}) < ${pulses}`;
    return [code, Blockly.Python.ORDER_RELATIONAL];
};

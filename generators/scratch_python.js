// ==================== GENERADORS PYTHON PER BLOCS SCRATCH ====================

// ==================== EVENTS ====================

Blockly.Python['scratch_when_flag_clicked'] = function(block) {
  // Aquest bloc marca l'inici del programa
  return '# Programa iniciat (bandera verda)\n';
};

Blockly.Python['scratch_when_key_pressed'] = function(block) {
  const key = block.getFieldValue('KEY');
  Blockly.Python.definitions_['import_usb_hid'] = 'try:\n    import usb_hid\n    from adafruit_hid.keyboard import Keyboard\n    kbd = Keyboard(usb_hid.devices)\nexcept:\n    kbd = None';
  return `# Event: Quan es premi tecla ${key}\n`;
};

Blockly.Python['scratch_broadcast'] = function(block) {
  const message = block.getFieldValue('MESSAGE');
  Blockly.Python.definitions_['broadcast_system'] = `broadcast_messages = {}\n\ndef broadcast(msg):\n    broadcast_messages[msg] = True\n\ndef check_broadcast(msg):\n    return broadcast_messages.get(msg, False)\n\ndef clear_broadcast(msg):\n    broadcast_messages[msg] = False`;
  return `broadcast("${message}")\n`;
};

Blockly.Python['scratch_when_receive'] = function(block) {
  const message = block.getFieldValue('MESSAGE');
  return `# Event: Quan rebi "${message}"\nif check_broadcast("${message}"):\n    clear_broadcast("${message}")\n`;
};

Blockly.Python['scratch_when_button_pressed'] = function(block) {
  const button = Blockly.Python.valueToCode(block, 'BUTTON', Blockly.Python.ORDER_ATOMIC) || '1';
  return `# Event: Quan es premi botó ${button}\n`;
};

// ==================== LOOKS ====================

Blockly.Python['scratch_say'] = function(block) {
  const message = Blockly.Python.valueToCode(block, 'MESSAGE', Blockly.Python.ORDER_NONE) || '""';
  const seconds = Blockly.Python.valueToCode(block, 'SECONDS', Blockly.Python.ORDER_NONE) || '2';
  Blockly.Python.definitions_['import_time'] = 'import time';
  return `print(${message})\ntime.sleep(${seconds})\n`;
};

Blockly.Python['scratch_think'] = function(block) {
  const message = Blockly.Python.valueToCode(block, 'MESSAGE', Blockly.Python.ORDER_NONE) || '""';
  const seconds = Blockly.Python.valueToCode(block, 'SECONDS', Blockly.Python.ORDER_NONE) || '2';
  Blockly.Python.definitions_['import_time'] = 'import time';
  return `print(f"(Pensant: {${message}})")\ntime.sleep(${seconds})\n`;
};

Blockly.Python['scratch_show'] = function(block) {
  return '# Activar sortida/display\n';
};

Blockly.Python['scratch_hide'] = function(block) {
  return '# Desactivar sortida/display\n';
};

Blockly.Python['scratch_change_size'] = function(block) {
  const change = Blockly.Python.valueToCode(block, 'CHANGE', Blockly.Python.ORDER_NONE) || '10';
  return `# Canviar mida per ${change}\n`;
};

Blockly.Python['scratch_set_size'] = function(block) {
  const size = Blockly.Python.valueToCode(block, 'SIZE', Blockly.Python.ORDER_NONE) || '100';
  return `# Establir mida a ${size}%\n`;
};

// ==================== SOUND ====================

Blockly.Python['scratch_play_sound'] = function(block) {
  const sound = block.getFieldValue('SOUND');
  const noteMap = {
    'C': 60, 'D': 62, 'E': 64, 'F': 65, 'G': 67, 'A': 69, 'B': 71,
    'BEEP': 440, 'MEOW': 880
  };
  const note = noteMap[sound] || 60;
  Blockly.Python.definitions_['import_midi'] = 'import usb_midi\nimport adafruit_midi\nfrom adafruit_midi.note_on import NoteOn\nfrom adafruit_midi.note_off import NoteOff\nmidi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)';
  return `midi.send(NoteOn(${note}, 100))\ntime.sleep(0.2)\nmidi.send(NoteOff(${note}, 0))\n`;
};

Blockly.Python['scratch_play_sound_until_done'] = function(block) {
  const sound = block.getFieldValue('SOUND');
  const noteMap = {'C': 60, 'D': 62, 'E': 64, 'BEEP': 440};
  const note = noteMap[sound] || 60;
  Blockly.Python.definitions_['import_midi'] = 'import usb_midi\nimport adafruit_midi\nfrom adafruit_midi.note_on import NoteOn\nfrom adafruit_midi.note_off import NoteOff\nmidi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)';
  Blockly.Python.definitions_['import_time'] = 'import time';
  return `midi.send(NoteOn(${note}, 100))\ntime.sleep(0.5)\nmidi.send(NoteOff(${note}, 0))\n`;
};

Blockly.Python['scratch_stop_all_sounds'] = function(block) {
  return '# Aturar tots els sons\nfor i in range(128):\n    midi.send(NoteOff(i, 0))\n';
};

Blockly.Python['scratch_change_volume'] = function(block) {
  const change = Blockly.Python.valueToCode(block, 'CHANGE', Blockly.Python.ORDER_NONE) || '10';
  Blockly.Python.definitions_['volume_var'] = 'global_volume = 100';
  return `global_volume = max(0, min(100, global_volume + ${change}))\n`;
};

Blockly.Python['scratch_set_volume'] = function(block) {
  const volume = Blockly.Python.valueToCode(block, 'VOLUME', Blockly.Python.ORDER_NONE) || '100';
  Blockly.Python.definitions_['volume_var'] = 'global_volume = 100';
  return `global_volume = max(0, min(100, ${volume}))\n`;
};

// ==================== SENSING ====================

Blockly.Python['scratch_touching'] = function(block) {
  const object = block.getFieldValue('OBJECT');
  if (object === 'BUTTON1') {
    return ['button_1.value', Blockly.Python.ORDER_MEMBER];
  } else if (object === 'BUTTON2') {
    return ['button_2.value', Blockly.Python.ORDER_MEMBER];
  }
  return ['False', Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['scratch_key_pressed'] = function(block) {
  const key = block.getFieldValue('KEY');
  return [`False  # Tecla ${key} (requereix connexió PC)`, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['scratch_mouse_x'] = function(block) {
  return ['0  # Mouse X (requereix connexió PC)', Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['scratch_mouse_y'] = function(block) {
  return ['0  # Mouse Y (requereix connexió PC)', Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['scratch_loudness'] = function(block) {
  Blockly.Python.definitions_['import_analogio'] = 'import board\nimport analogio\nmicrophone = analogio.AnalogIn(board.A0)';
  return ['int(microphone.value / 65535 * 100)', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['scratch_timer'] = function(block) {
  Blockly.Python.definitions_['import_time'] = 'import time';
  Blockly.Python.definitions_['start_time'] = 'start_time = time.monotonic()';
  return ['time.monotonic() - start_time', Blockly.Python.ORDER_ADDITIVE];
};

Blockly.Python['scratch_reset_timer'] = function(block) {
  Blockly.Python.definitions_['import_time'] = 'import time';
  return 'start_time = time.monotonic()\n';
};

Blockly.Python['scratch_current_time'] = function(block) {
  const timeunit = block.getFieldValue('TIMEUNIT');
  Blockly.Python.definitions_['import_rtc'] = 'try:\n    import rtc\n    import time\nexcept:\n    pass';
  const unitMap = {
    'YEAR': 'time.localtime().tm_year',
    'MONTH': 'time.localtime().tm_mon',
    'DAY': 'time.localtime().tm_mday',
    'HOUR': 'time.localtime().tm_hour',
    'MINUTE': 'time.localtime().tm_min',
    'SECOND': 'time.localtime().tm_sec'
  };
  return [unitMap[timeunit] || '0', Blockly.Python.ORDER_MEMBER];
};

Blockly.Python['scratch_days_since_2000'] = function(block) {
  Blockly.Python.definitions_['import_time'] = 'import time';
  return ['int((time.time() - 946684800) / 86400)', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ==================== OPERATORS ====================

Blockly.Python['scratch_join'] = function(block) {
  const string1 = Blockly.Python.valueToCode(block, 'STRING1', Blockly.Python.ORDER_NONE) || '""';
  const string2 = Blockly.Python.valueToCode(block, 'STRING2', Blockly.Python.ORDER_NONE) || '""';
  return [`str(${string1}) + str(${string2})`, Blockly.Python.ORDER_ADDITIVE];
};

Blockly.Python['scratch_letter_of'] = function(block) {
  const letter = Blockly.Python.valueToCode(block, 'LETTER', Blockly.Python.ORDER_NONE) || '1';
  const string = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_MEMBER) || '""';
  return [`${string}[${letter} - 1] if 0 < ${letter} <= len(${string}) else ""`, Blockly.Python.ORDER_CONDITIONAL];
};

Blockly.Python['scratch_length_of'] = function(block) {
  const string = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_MEMBER) || '""';
  return [`len(str(${string}))`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['scratch_contains'] = function(block) {
  const string1 = Blockly.Python.valueToCode(block, 'STRING1', Blockly.Python.ORDER_MEMBER) || '""';
  const string2 = Blockly.Python.valueToCode(block, 'STRING2', Blockly.Python.ORDER_NONE) || '""';
  return [`str(${string2}) in str(${string1})`, Blockly.Python.ORDER_RELATIONAL];
};

Blockly.Python['scratch_mod'] = function(block) {
  const num1 = Blockly.Python.valueToCode(block, 'NUM1', Blockly.Python.ORDER_MULTIPLICATIVE) || '0';
  const num2 = Blockly.Python.valueToCode(block, 'NUM2', Blockly.Python.ORDER_MULTIPLICATIVE) || '1';
  return [`${num1} % ${num2}`, Blockly.Python.ORDER_MULTIPLICATIVE];
};

Blockly.Python['scratch_round'] = function(block) {
  const num = Blockly.Python.valueToCode(block, 'NUM', Blockly.Python.ORDER_NONE) || '0';
  return [`round(${num})`, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Python['scratch_mathop'] = function(block) {
  const operator = block.getFieldValue('OPERATOR');
  const num = Blockly.Python.valueToCode(block, 'NUM', Blockly.Python.ORDER_NONE) || '0';
  Blockly.Python.definitions_['import_math'] = 'import math';
  
  const opMap = {
    'ABS': `abs(${num})`,
    'SQRT': `math.sqrt(${num})`,
    'SIN': `math.sin(${num})`,
    'COS': `math.cos(${num})`,
    'TAN': `math.tan(${num})`,
    'LN': `math.log(${num})`,
    'LOG': `math.log10(${num})`,
    'EXP': `math.exp(${num})`,
    'POW10': `10 ** ${num}`
  };
  
  return [opMap[operator] || `${num}`, Blockly.Python.ORDER_FUNCTION_CALL];
};

// ==================== MY BLOCKS ====================

Blockly.Python['scratch_custom_block'] = function(block) {
  const name = block.getFieldValue('NAME');
  return `${name}()\n`;
};

Blockly.Python['scratch_define_custom'] = function(block) {
  const name = block.getFieldValue('NAME');
  const body = Blockly.Python.statementToCode(block, 'BODY') || '    pass\n';
  Blockly.Python.definitions_[`custom_${name}`] = `def ${name}():\n${body}`;
  return '';
};

// ==================== VARIABLES ====================

Blockly.Python['scratch_change_var'] = function(block) {
  const variable = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.Variables.NAME_TYPE);
  const value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '1';
  return `${variable} = ${variable} + ${value}\n`;
};

Blockly.Python['scratch_show_variable'] = function(block) {
  const variable = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.Variables.NAME_TYPE);
  return `print(f"${variable} = {${variable}}")\n`;
};

Blockly.Python['scratch_hide_variable'] = function(block) {
  return '# Amagar variable del display\n';
};

// ==================== CONTROL ====================

Blockly.Python['scratch_stop'] = function(block) {
  const stopOption = block.getFieldValue('STOP_OPTION');
  if (stopOption === 'ALL') {
    Blockly.Python.definitions_['import_sys'] = 'import sys';
    return 'sys.exit()\n';
  } else if (stopOption === 'THIS') {
    return 'return\n';
  }
  return '# Aturar altres scripts\n';
};

Blockly.Python['scratch_when_start_as_clone'] = function(block) {
  return '# Event: Quan comenci com a clon\n';
};

Blockly.Python['scratch_create_clone'] = function(block) {
  Blockly.Python.definitions_['import_threading'] = 'import _thread';
  return '# Crear clon (thread paral·lel)\n_thread.start_new_thread(main_program, ())\n';
};

Blockly.Python['scratch_delete_clone'] = function(block) {
  return '# Eliminar aquest clon\nreturn\n';
};

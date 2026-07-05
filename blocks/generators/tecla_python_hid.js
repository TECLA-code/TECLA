// ==================== GENERADORS PYTHON – HID (Teclat / Media) ====================
// Genera codi CircuitPython per a blocs d'accions de teclat i media (adafruit_hid)

const _HID_MOD_MAP = {
  'CONTROL':       'Keycode.CONTROL',
  'ALT':           'Keycode.ALT',
  'SHIFT':         'Keycode.SHIFT',
  'CTRL_SHIFT':    'Keycode.CONTROL, Keycode.SHIFT',
  'CTRL_ALT':      'Keycode.CONTROL, Keycode.ALT',
  'CTRL_SHIFT_ALT':'Keycode.CONTROL, Keycode.SHIFT, Keycode.ALT',
  'GUI':           'Keycode.GUI'
};

Blockly.Python.forBlock['tecla_key_press'] = function(block) {
  const key = block.getFieldValue('KEY');
  return `_keyboard.send(Keycode.${key})\n`;
};

Blockly.Python.forBlock['tecla_key_combo'] = function(block) {
  const modifier = block.getFieldValue('MODIFIER');
  const key      = block.getFieldValue('KEY');
  const mods     = _HID_MOD_MAP[modifier] || 'Keycode.CONTROL';
  return `_keyboard.send(${mods}, Keycode.${key})\n`;
};

Blockly.Python.forBlock['tecla_type_text'] = function(block) {
  const text = block.getFieldValue('TEXT')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"');
  return `_layout.write("${text}")\n`;
};

Blockly.Python.forBlock['tecla_media'] = function(block) {
  const action = block.getFieldValue('ACTION');
  // Map actions that changed name between adafruit_hid versions
  const safeMap = {
    'SCAN_NEXT_TRACK':     '_SCAN_NEXT',
    'SCAN_PREVIOUS_TRACK': '_SCAN_PREV'
  };
  const code = safeMap[action] ? `ConsumerControlCode.${action} if hasattr(ConsumerControlCode, '${action}') else _SCAN_${action.includes('NEXT') ? 'NEXT' : 'PREV'}` : `ConsumerControlCode.${action}`;
  // Simpler: use pre-computed compat vars set at boot
  const useVar = safeMap[action] || `ConsumerControlCode.${action}`;
  return `_cc.send(${useVar})\n`;
};

Blockly.Python.forBlock['tecla_open_app'] = function(block) {
  const app  = (block.getFieldValue('APP_NAME') || 'Spotify').replace(/"/g, '\\"');
  const plat = block.getFieldValue('PLATFORM');
  let code = `# Obrir app: ${app}\n`;
  if (plat === 'mac') {
    code += `_keyboard.press(Keycode.COMMAND, Keycode.SPACE)\n`;
    code += `_keyboard.release_all()\n`;
    code += `time.sleep(0.5)\n`;
    code += `_layout.write("${app}")\n`;
    code += `time.sleep(0.3)\n`;
    code += `_keyboard.send(Keycode.ENTER)\n`;
  } else {
    code += `_keyboard.press(Keycode.WINDOWS, Keycode.R)\n`;
    code += `_keyboard.release_all()\n`;
    code += `time.sleep(0.4)\n`;
    code += `_layout.write("${app}")\n`;
    code += `time.sleep(0.2)\n`;
    code += `_keyboard.send(Keycode.ENTER)\n`;
  }
  return code;
};

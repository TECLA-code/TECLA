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

Blockly.Python['tecla_key_press'] = function(block) {
  const key = block.getFieldValue('KEY');
  return `_keyboard.send(Keycode.${key})\n`;
};

Blockly.Python['tecla_key_combo'] = function(block) {
  const modifier = block.getFieldValue('MODIFIER');
  const key      = block.getFieldValue('KEY');
  const mods     = _HID_MOD_MAP[modifier] || 'Keycode.CONTROL';
  return `_keyboard.send(${mods}, Keycode.${key})\n`;
};

Blockly.Python['tecla_type_text'] = function(block) {
  const text = block.getFieldValue('TEXT')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"');
  return `_layout.write("${text}")\n`;
};

Blockly.Python['tecla_media'] = function(block) {
  const action = block.getFieldValue('ACTION');
  return `_cc.send(ConsumerControlCode.${action})\n`;
};

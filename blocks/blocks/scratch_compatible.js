// ==================== BLOCS COMPATIBLES AMB SCRATCH ====================
// Blocs inspirats en Scratch per fer TECLA Blocks més familiar

// ==================== EVENTS (SCRATCH) ====================

Blockly.Blocks['scratch_when_flag_clicked'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🚩 Quan es premi bandera verda");
    this.setNextStatement(true, null);
    this.setColour('#FFBF00');
    this.setTooltip("Executa quan s'inicia el programa");
  }
};

Blockly.Blocks['scratch_when_key_pressed'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("⌨️ Quan es premi tecla")
        .appendField(new Blockly.FieldDropdown([
          ["espai", "SPACE"],
          ["fletxa amunt", "UP"],
          ["fletxa avall", "DOWN"],
          ["fletxa esquerra", "LEFT"],
          ["fletxa dreta", "RIGHT"],
          ["a", "A"],
          ["b", "B"],
          ["c", "C"]
        ]), "KEY");
    this.setNextStatement(true, null);
    this.setColour('#FFBF00');
    this.setTooltip("Executa quan es prem una tecla (requereix PC connectat)");
  }
};

Blockly.Blocks['scratch_broadcast'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("📢 Enviar missatge")
        .appendField(new Blockly.FieldTextInput("missatge1"), "MESSAGE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#FFBF00');
    this.setTooltip("Envia un missatge a altres parts del programa");
  }
};

Blockly.Blocks['scratch_when_receive'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("📻 Quan rebi")
        .appendField(new Blockly.FieldTextInput("missatge1"), "MESSAGE");
    this.setNextStatement(true, null);
    this.setColour('#FFBF00');
    this.setTooltip("Executa quan es rep un missatge");
  }
};

Blockly.Blocks['scratch_when_button_pressed'] = {
  init: function() {
    this.appendValueInput("BUTTON")
        .setCheck("Number")
        .appendField("🎮 Quan es premi botó");
    this.setNextStatement(true, null);
    this.setColour('#FFBF00');
    this.setTooltip("Executa quan es prem un botó de TECLA");
  }
};

// ==================== LOOKS (APARENCES) ====================

Blockly.Blocks['scratch_say'] = {
  init: function() {
    this.appendValueInput("MESSAGE")
        .setCheck("String")
        .appendField("💬 Dir");
    this.appendValueInput("SECONDS")
        .setCheck("Number")
        .appendField("durant");
    this.appendDummyInput()
        .appendField("segons");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#9966FF');
    this.setTooltip("Mostra un missatge (al display o serial)");
  }
};

Blockly.Blocks['scratch_think'] = {
  init: function() {
    this.appendValueInput("MESSAGE")
        .setCheck("String")
        .appendField("💭 Pensar");
    this.appendValueInput("SECONDS")
        .setCheck("Number")
        .appendField("durant");
    this.appendDummyInput()
        .appendField("segons");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#9966FF');
    this.setTooltip("Mostra un pensament");
  }
};

Blockly.Blocks['scratch_show'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("👁️ Mostrar");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#9966FF');
    this.setTooltip("Activa sortida/display");
  }
};

Blockly.Blocks['scratch_hide'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🙈 Amagar");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#9966FF');
    this.setTooltip("Desactiva sortida/display");
  }
};

Blockly.Blocks['scratch_change_size'] = {
  init: function() {
    this.appendValueInput("CHANGE")
        .setCheck("Number")
        .appendField("📏 Canviar mida per");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#9966FF');
    this.setTooltip("Canvia la intensitat/escala");
  }
};

Blockly.Blocks['scratch_set_size'] = {
  init: function() {
    this.appendValueInput("SIZE")
        .setCheck("Number")
        .appendField("📏 Establir mida a");
    this.appendDummyInput()
        .appendField("%");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#9966FF');
    this.setTooltip("Estableix la mida/intensitat (100% = normal)");
  }
};

// ==================== SOUND (SO SCRATCH) ====================

Blockly.Blocks['scratch_play_sound'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🔊 Tocar so")
        .appendField(new Blockly.FieldDropdown([
          ["Do", "C"],
          ["Re", "D"],
          ["Mi", "E"],
          ["Fa", "F"],
          ["Sol", "G"],
          ["La", "A"],
          ["Si", "B"],
          ["Beep", "BEEP"],
          ["Meow", "MEOW"]
        ]), "SOUND");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#D65CD6');
    this.setTooltip("Reprodueix un so predefinit");
  }
};

Blockly.Blocks['scratch_play_sound_until_done'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🔊 Tocar so")
        .appendField(new Blockly.FieldDropdown([
          ["Do", "C"],
          ["Re", "D"],
          ["Mi", "E"],
          ["Beep", "BEEP"]
        ]), "SOUND")
        .appendField("fins que acabi");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#D65CD6');
    this.setTooltip("Reprodueix so i espera");
  }
};

Blockly.Blocks['scratch_stop_all_sounds'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🔇 Aturar tots els sons");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#D65CD6');
    this.setTooltip("Atura tota la reproducció");
  }
};

Blockly.Blocks['scratch_change_volume'] = {
  init: function() {
    this.appendValueInput("CHANGE")
        .setCheck("Number")
        .appendField("🔉 Canviar volum per");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#D65CD6');
    this.setTooltip("Augmenta o disminueix el volum");
  }
};

Blockly.Blocks['scratch_set_volume'] = {
  init: function() {
    this.appendValueInput("VOLUME")
        .setCheck("Number")
        .appendField("🔊 Establir volum a");
    this.appendDummyInput()
        .appendField("%");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#D65CD6');
    this.setTooltip("Estableix el volum (0-100%)");
  }
};

// ==================== SENSING (DETECCIÓ) ====================

Blockly.Blocks['scratch_touching'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("👆 Tocant")
        .appendField(new Blockly.FieldDropdown([
          ["botó 1", "BUTTON1"],
          ["botó 2", "BUTTON2"],
          ["sensor", "SENSOR"]
        ]), "OBJECT");
    this.setOutput(true, "Boolean");
    this.setColour('#4CBFE6');
    this.setTooltip("Detecta si s'està tocant");
  }
};

Blockly.Blocks['scratch_key_pressed'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("⌨️ Tecla")
        .appendField(new Blockly.FieldDropdown([
          ["espai", "SPACE"],
          ["fletxa amunt", "UP"],
          ["a", "A"]
        ]), "KEY")
        .appendField("premuda?");
    this.setOutput(true, "Boolean");
    this.setColour('#4CBFE6');
    this.setTooltip("Comprova si una tecla està premuda");
  }
};

Blockly.Blocks['scratch_mouse_x'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🖱️ Ratolí X");
    this.setOutput(true, "Number");
    this.setColour('#4CBFE6');
    this.setTooltip("Posició X del ratolí (requereix connexió PC)");
  }
};

Blockly.Blocks['scratch_mouse_y'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🖱️ Ratolí Y");
    this.setOutput(true, "Number");
    this.setColour('#4CBFE6');
    this.setTooltip("Posició Y del ratolí");
  }
};

Blockly.Blocks['scratch_loudness'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🔊 Volum ambient");
    this.setOutput(true, "Number");
    this.setColour('#4CBFE6');
    this.setTooltip("Nivell de so detectat pel micròfon (0-100)");
  }
};

Blockly.Blocks['scratch_timer'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("⏱️ Cronòmetre");
    this.setOutput(true, "Number");
    this.setColour('#4CBFE6');
    this.setTooltip("Temps en segons des de l'inici");
  }
};

Blockly.Blocks['scratch_reset_timer'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("⏱️ Reiniciar cronòmetre");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#4CBFE6');
    this.setTooltip("Posa el cronòmetre a 0");
  }
};

Blockly.Blocks['scratch_current_time'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("📅")
        .appendField(new Blockly.FieldDropdown([
          ["any", "YEAR"],
          ["mes", "MONTH"],
          ["dia", "DAY"],
          ["hora", "HOUR"],
          ["minut", "MINUTE"],
          ["segon", "SECOND"]
        ]), "TIMEUNIT")
        .appendField("actual");
    this.setOutput(true, "Number");
    this.setColour('#4CBFE6');
    this.setTooltip("Obté la data/hora actual");
  }
};

Blockly.Blocks['scratch_days_since_2000'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("📆 Dies des de 2000");
    this.setOutput(true, "Number");
    this.setColour('#4CBFE6');
    this.setTooltip("Dies transcorreguts des de l'1 de gener de 2000");
  }
};

// ==================== OPERATORS SCRATCH ====================

Blockly.Blocks['scratch_join'] = {
  init: function() {
    this.appendValueInput("STRING1")
        .setCheck("String")
        .appendField("🔗 Unir");
    this.appendValueInput("STRING2")
        .setCheck("String")
        .appendField("i");
    this.setOutput(true, "String");
    this.setColour('#40BF4A');
    this.setTooltip("Uneix dos textos");
  }
};

Blockly.Blocks['scratch_letter_of'] = {
  init: function() {
    this.appendValueInput("LETTER")
        .setCheck("Number")
        .appendField("🔤 Lletra");
    this.appendValueInput("STRING")
        .setCheck("String")
        .appendField("de");
    this.setOutput(true, "String");
    this.setColour('#40BF4A');
    this.setTooltip("Obté una lletra d'un text (1=primera)");
  }
};

Blockly.Blocks['scratch_length_of'] = {
  init: function() {
    this.appendValueInput("STRING")
        .setCheck("String")
        .appendField("📏 Longitud de");
    this.setOutput(true, "Number");
    this.setColour('#40BF4A');
    this.setTooltip("Nombre de caràcters del text");
  }
};

Blockly.Blocks['scratch_contains'] = {
  init: function() {
    this.appendValueInput("STRING1")
        .setCheck("String");
    this.appendValueInput("STRING2")
        .setCheck("String")
        .appendField("conté");
    this.setOutput(true, "Boolean");
    this.setColour('#40BF4A');
    this.setTooltip("Comprova si un text conté un altre");
  }
};

Blockly.Blocks['scratch_mod'] = {
  init: function() {
    this.appendValueInput("NUM1")
        .setCheck("Number");
    this.appendValueInput("NUM2")
        .setCheck("Number")
        .appendField("mod");
    this.setOutput(true, "Number");
    this.setColour('#40BF4A');
    this.setTooltip("Residu de la divisió");
  }
};

Blockly.Blocks['scratch_round'] = {
  init: function() {
    this.appendValueInput("NUM")
        .setCheck("Number")
        .appendField("🔄 Arrodonir");
    this.setOutput(true, "Number");
    this.setColour('#40BF4A');
    this.setTooltip("Arrodoneix al número enter més proper");
  }
};

Blockly.Blocks['scratch_mathop'] = {
  init: function() {
    this.appendValueInput("NUM")
        .setCheck("Number")
        .appendField(new Blockly.FieldDropdown([
          ["abs", "ABS"],
          ["arrel", "SQRT"],
          ["sin", "SIN"],
          ["cos", "COS"],
          ["tan", "TAN"],
          ["ln", "LN"],
          ["log", "LOG"],
          ["e^", "EXP"],
          ["10^", "POW10"]
        ]), "OPERATOR")
        .appendField("de");
    this.setOutput(true, "Number");
    this.setColour('#40BF4A');
    this.setTooltip("Operació matemàtica");
  }
};

// ==================== MY BLOCKS (PERSONALITZATS) ====================

Blockly.Blocks['scratch_custom_block'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🧩 Bloc personalitzat")
        .appendField(new Blockly.FieldTextInput("el_meu_bloc"), "NAME");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#FF6680');
    this.setTooltip("Crea un bloc personalitzat reutilitzable");
  }
};

Blockly.Blocks['scratch_define_custom'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🔧 Definir")
        .appendField(new Blockly.FieldTextInput("el_meu_bloc"), "NAME");
    this.appendStatementInput("BODY")
        .setCheck(null);
    this.setColour('#FF6680');
    this.setTooltip("Defineix què fa el bloc personalitzat");
  }
};

// ==================== VARIABLES SCRATCH ====================

Blockly.Blocks['scratch_change_var'] = {
  init: function() {
    this.appendValueInput("VALUE")
        .setCheck("Number")
        .appendField("📊 Canviar")
        .appendField(new Blockly.FieldVariable("variable"), "VAR")
        .appendField("per");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#FF8C1A');
    this.setTooltip("Suma un valor a la variable");
  }
};

Blockly.Blocks['scratch_show_variable'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("👁️ Mostrar variable")
        .appendField(new Blockly.FieldVariable("variable"), "VAR");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#FF8C1A');
    this.setTooltip("Fa visible la variable al display");
  }
};

Blockly.Blocks['scratch_hide_variable'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🙈 Amagar variable")
        .appendField(new Blockly.FieldVariable("variable"), "VAR");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#FF8C1A');
    this.setTooltip("Amaga la variable del display");
  }
};

// ==================== CONTROL SCRATCH ====================

Blockly.Blocks['scratch_stop'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🛑 Aturar")
        .appendField(new Blockly.FieldDropdown([
          ["tot", "ALL"],
          ["aquest script", "THIS"],
          ["altres scripts", "OTHER"]
        ]), "STOP_OPTION");
    this.setPreviousStatement(true, null);
    this.setColour('#FFAB19');
    this.setTooltip("Atura l'execució");
  }
};

Blockly.Blocks['scratch_when_start_as_clone'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("👥 Quan comenci com a clon");
    this.setNextStatement(true, null);
    this.setColour('#FFAB19');
    this.setTooltip("Event per instàncies paral·leles");
  }
};

Blockly.Blocks['scratch_create_clone'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("👥 Crear clon de mi mateix");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#FFAB19');
    this.setTooltip("Crea una còpia paral·lela del programa");
  }
};

Blockly.Blocks['scratch_delete_clone'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("🗑️ Eliminar aquest clon");
    this.setPreviousStatement(true, null);
    this.setColour('#FFAB19');
    this.setTooltip("Elimina aquesta instància");
  }
};

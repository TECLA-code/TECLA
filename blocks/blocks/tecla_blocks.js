/**
 * Blocs personalitzats per TECLA
 * Defineix els blocs visuals específics per programar TECLA
 */

// ==================== BLOCS DE MÚSICA ====================

Blockly.Blocks['tecla_play_note'] = {
  init: function () {
    this.appendValueInput("NOTE")
      .setCheck("Number")
      .appendField("🎵 Tocar nota");
    this.appendValueInput("VELOCITY")
      .setCheck("Number")
      .appendField("velocitat");
    this.appendValueInput("DURATION")
      .setCheck("Number")
      .appendField("durada");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Toca una nota musical (número MIDI) durant un temps determinat");
    this.setHelpUrl("");
    // Inputs inline per estalviar espai
    this.setInputsInline(true);
  }
};

Blockly.Blocks['tecla_play_chord'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎸 Tocar acord")
      .appendField(new Blockly.FieldDropdown([
        ["Do Major (C)", "C"], ["Re Major (D)", "D"], ["Mi Major (E)", "E"],
        ["Fa Major (F)", "F"], ["Sol Major (G)", "G"], ["La Major (A)", "A"],
        ["Si Major (B)", "B"], ["Do menor (Cm)", "Cm"], ["Re menor (Dm)", "Dm"],
        ["Mi menor (Em)", "Em"], ["Fa menor (Fm)", "Fm"], ["Sol menor (Gm)", "Gm"],
        ["La menor (Am)", "Am"], ["Si menor (Bm)", "Bm"]
      ]), "CHORD");
    this.appendDummyInput()
      .appendField("durada (segons)")
      .appendField(new Blockly.FieldNumber(1.0, 0.1, 10, 0.1), "DURATION");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Toca un acord (vàries notes al mateix temps)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_play_scale'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎼 Tocar escala")
      .appendField(new Blockly.FieldDropdown([
        ["Major", "major"], ["Menor natural", "minor"],
        ["Pentatònica", "pentatonic"], ["Blues", "blues"],
        ["Dòrica", "dorian"], ["Cromàtica", "chromatic"]
      ]), "SCALE")
      .appendField("des de")
      .appendField(new Blockly.FieldDropdown([
        ["Do", "C"], ["Re", "D"], ["Mi", "E"], ["Fa", "F"],
        ["Sol", "G"], ["La", "A"], ["Si", "B"]
      ]), "ROOT");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Toca una escala musical completa");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_get_random_scale_note'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎲 Nota Random")
      .appendField(new Blockly.FieldDropdown([
        ["Major", "major"], ["Menor", "minor"],
        ["Pentatònica", "pentatonic"], ["Blues", "blues"],
        ["Dòrica", "dorian"]
      ]), "SCALE");
    this.appendDummyInput()
      .appendField("Key")
      .appendField(new Blockly.FieldDropdown([
        ["C", "C"], ["D", "D"], ["E", "E"], ["F", "F"],
        ["G", "G"], ["A", "A"], ["B", "B"]
      ]), "ROOT");
    this.appendValueInput("OCTAVE")
      .setCheck("Number")
      .appendField("Octava");
    this.setOutput(true, "Number");
    this.setColour('#ff1a6c');
    this.setTooltip("Retorna una nota MIDI aleatòria dins de l'escala triada");
    this.setInputsInline(true);
  }
};

Blockly.Blocks['tecla_set_octave'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎹 Canviar octava a")
      .appendField(new Blockly.FieldNumber(4, 1, 7), "OCTAVE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Canvia l'octava per les següents notes");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE CONTROL ====================

Blockly.Blocks['tecla_read_button'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🔘 Botó")
      .appendField(new Blockly.FieldNumber(1, 1, 16), "BUTTON")
      .appendField("premut?");
    this.setOutput(true, "Boolean");
    this.setColour('#2979ff');
    this.setTooltip("Comprova si un botó està premut");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_read_pot'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎛️ Potenciòmetre")
      .appendField(new Blockly.FieldDropdown([
        ["X (ADC0)", "0"], ["Y (ADC1)", "1"], ["Z (ADC2)", "2"]
      ]), "POT");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Llegeix el valor d'un potenciòmetre (0-127)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_on_button_press'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("⚡ Quan es prem botó")
      .appendField(new Blockly.FieldNumber(1, 1, 16), "BUTTON");
    this.appendStatementInput("DO")
      .setCheck(null)
      .appendField("fer");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#2979ff');
    this.setTooltip("Executa accions quan es prem un botó");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS D'EFECTES ====================

Blockly.Blocks['tecla_set_instrument'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎷 Canviar Instrument a")
      .appendField(new Blockly.FieldDropdown([
        ["🎹 Piano Cua", "0"],
        ["🎹 Piano Elèctric", "4"],
        ["🎹 Orgue", "16"],
        ["🎸 Guitarra Acústica", "25"],
        ["🎸 Guitarra Elèctrica", "29"],
        ["🎻 Violí", "40"],
        ["🎻 Strings", "48"],
        ["🎺 Trompeta", "56"],
        ["🎷 Saxo", "65"],
        ["🎹 Synth Lead", "80"],
        ["🎹 Synth Pad", "88"],
        ["🌌 FX Sci-Fi", "96"]
      ]), "INSTRUMENT");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#e040fb');
    this.setTooltip("Canvia el so de l'instrument (Program Change)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_set_pan'] = {
  init: function () {
    this.appendValueInput("PAN")
      .setCheck("Number")
      .appendField("🎧 Panning (L-R)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#e040fb');
    this.setTooltip("Controla el balanç esquerra/dreta (0-127, 64 = Centre)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_set_volume'] = {
  init: function () {
    this.appendValueInput("VOLUME")
      .setCheck("Number")
      .appendField("🔊 Volum");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#e040fb');
    this.setTooltip("Controla el volum del canal MIDI (CC 7)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_effect_delay'] = {
  init: function () {
    this.appendValueInput("TIME")
      .setCheck("Number")
      .appendField("🔊 Activar Delay")
      .appendField("temps");
    this.appendValueInput("FEEDBACK")
      .setCheck("Number")
      .appendField("feedback");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#e040fb');
    this.setTooltip("Afegeix efecte de delay (eco) amb paràmetres dinàmics");
    this.setHelpUrl("");
    this.setInputsInline(true);
  }
};

Blockly.Blocks['tecla_effect_reverb'] = {
  init: function () {
    this.appendValueInput("AMOUNT")
      .setCheck("Number")
      .appendField("🌊 Activar Reverb")
      .appendField("quantitat");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#e040fb');
    this.setTooltip("Afegeix efecte de reverberació (dinàmic)");
    this.setHelpUrl("");
    this.setInputsInline(true);
  }
};

Blockly.Blocks['tecla_effect_filter'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎚️ Filtre")
      .appendField(new Blockly.FieldDropdown([
        ["Passa-baix", "lowpass"],
        ["Passa-alt", "highpass"],
        ["Passa-banda", "bandpass"]
      ]), "TYPE");
    this.appendValueInput("FREQUENCY")
      .setCheck("Number")
      .appendField("freqüència");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#e040fb');
    this.setTooltip("Aplica un filtre de freqüència controlable");
    this.setHelpUrl("");
    this.setInputsInline(true);
  }
};

// ==================== BLOCS DE TEMPS / RITME ====================

Blockly.Blocks['tecla_set_bpm'] = {
  init: function () {
    this.appendValueInput("BPM")
      .setCheck("Number")
      .appendField("⏱️ Fixar BPM (Ritme)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff9100');
    this.setTooltip("Defineix la velocitat global del programa (Beats Per Minute)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_wait_beat'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🥁 Esperar")
      .appendField(new Blockly.FieldDropdown([
        ["1/4 Beat (Semicorxera)", "0.25"],
        ["1/2 Beat (Corxera)", "0.5"],
        ["1 Beat (Negra)", "1"],
        ["2 Beats (Blanca)", "2"],
        ["4 Beats (Rodona)", "4"]
      ]), "BEATS");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff9100');
    this.setTooltip("Espera un temps musical basat en el BPM");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_wait'] = {
  init: function () {
    this.appendValueInput("TIME")
      .setCheck("Number")
      .appendField("⏱️ Esperar");
    this.appendDummyInput()
      .appendField("segons");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff9100');
    this.setTooltip("Espera un temps determinat (pot ser variable) abans de continuar");
    this.setHelpUrl("");
    this.setInputsInline(true);
  }
};

Blockly.Blocks['tecla_repeat_forever'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🔁 Repetir per sempre");
    this.appendStatementInput("DO")
      .setCheck(null)
      .appendField("fer");
    this.setPreviousStatement(true, null);
    this.setColour('#ff9100');
    this.setTooltip("Repeteix les accions indefinidament");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE SÍNTESI AVANÇADA ====================

Blockly.Blocks['tecla_oscillator'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🌊 Oscil·lador")
      .appendField(new Blockly.FieldDropdown([
        ["Sinusoidal", "sine"],
        ["Quadrada", "square"],
        ["Triangular", "triangle"],
        ["Dent de serra", "sawtooth"],
        ["Pols", "pulse"],
        ["Soroll", "noise"]
      ]), "WAVEFORM");
    this.appendValueInput("FREQUENCY")
      .setCheck("Number")
      .appendField("freqüència");
    this.appendValueInput("AMPLITUDE")
      .setCheck("Number")
      .appendField("amplitud");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#d500f9');
    this.setTooltip("Configura un oscil·lador amb forma d'ona, freqüència i amplitud");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_lfo'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("〰️ LFO (Oscil·lador de baixa freq.)")
      .appendField(new Blockly.FieldDropdown([
        ["Sinusoidal", "sine"],
        ["Triangular", "triangle"],
        ["Quadrada", "square"],
        ["Aleatòria", "random"]
      ]), "WAVEFORM");
    this.appendValueInput("RATE")
      .setCheck("Number")
      .appendField("velocitat (Hz)");
    this.appendDummyInput()
      .appendField("controla")
      .appendField(new Blockly.FieldDropdown([
        ["Pitch", "pitch"],
        ["Amplitud", "amplitude"],
        ["Filtre", "filter"],
        ["Pan", "pan"]
      ]), "TARGET");
    this.appendValueInput("DEPTH")
      .setCheck("Number")
      .appendField("profunditat");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#d500f9');
    this.setTooltip("LFO per modular paràmetres automàticament");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_envelope'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("📈 Envolvent ADSR");
    this.appendValueInput("ATTACK")
      .setCheck("Number")
      .appendField("Attack (ms)");
    this.appendValueInput("DECAY")
      .setCheck("Number")
      .appendField("Decay (ms)");
    this.appendValueInput("SUSTAIN")
      .setCheck("Number")
      .appendField("Sustain (%)");
    this.appendValueInput("RELEASE")
      .setCheck("Number")
      .appendField("Release (ms)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#d500f9');
    this.setTooltip("Configura envolvent ADSR per controlar l'evolució del so");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_modulation'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎚️ Modulació")
      .appendField(new Blockly.FieldDropdown([
        ["FM (Freqüència)", "fm"],
        ["AM (Amplitud)", "am"],
        ["PM (Fase)", "pm"],
        ["Ring Mod", "ring"]
      ]), "TYPE");
    this.appendValueInput("CARRIER")
      .setCheck("Number")
      .appendField("Portadora");
    this.appendValueInput("MODULATOR")
      .setCheck("Number")
      .appendField("Moduladora");
    this.appendValueInput("DEPTH")
      .setCheck("Number")
      .appendField("Profunditat");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#d500f9');
    this.setTooltip("Síntesi per modulació (FM, AM, PM, Ring)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_waveshaper'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🔥 Waveshaper (distorsió)")
      .appendField(new Blockly.FieldDropdown([
        ["Suau", "soft"],
        ["Mitjà", "medium"],
        ["Dur", "hard"],
        ["Fuzz", "fuzz"],
        ["Bitcrusher", "bitcrush"]
      ]), "TYPE");
    this.appendValueInput("AMOUNT")
      .setCheck("Number")
      .appendField("quantitat");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#d500f9');
    this.setTooltip("Afegeix distorsió o waveshaping al senyal");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS D'ENTRADA/SORTIDA ====================

Blockly.Blocks['tecla_digital_write'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("💡 Pin digital")
      .appendField(new Blockly.FieldNumber(0, 0, 29), "PIN")
      .appendField("escriure")
      .appendField(new Blockly.FieldDropdown([
        ["HIGH (1)", "1"],
        ["LOW (0)", "0"]
      ]), "VALUE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00f0ff');
    this.setTooltip("Escriu un valor digital a un pin GPIO");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_digital_read'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("📥 Llegir pin digital")
      .appendField(new Blockly.FieldNumber(0, 0, 29), "PIN");
    this.setOutput(true, "Boolean");
    this.setColour('#00f0ff');
    this.setTooltip("Llegeix el valor d'un pin digital");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_analog_write'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("📊 Pin analògic")
      .appendField(new Blockly.FieldNumber(0, 0, 2), "PIN");
    this.appendValueInput("VALUE")
      .setCheck("Number")
      .appendField("escriure PWM");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00f0ff');
    this.setTooltip("Escriu un valor PWM (0-65535) a un pin");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_analog_read'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("📈 Llegir analògic")
      .appendField(new Blockly.FieldDropdown([
        ["A0", "0"], ["A1", "1"], ["A2", "2"]
      ]), "PIN");
    this.setOutput(true, "Number");
    this.setColour('#00f0ff');
    this.setTooltip("Llegeix valor analògic (0-65535)");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE SENSORS ====================

Blockly.Blocks['tecla_sensor_temperature'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🌡️ Temperatura interna (CPU)");
    this.setOutput(true, "Number");
    this.setColour('#40c8ff');
    this.setTooltip("Llegeix la temperatura del microcontrolador");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_sensor_accelerometer'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("📐 Acceleròmetre")
      .appendField(new Blockly.FieldDropdown([
        ["X", "x"], ["Y", "y"], ["Z", "z"],
        ["Magnitud", "magnitude"]
      ]), "AXIS");
    this.setOutput(true, "Number");
    this.setColour('#40c8ff');
    this.setTooltip("Llegeix valors d'acceleròmetre (si està connectat)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_sensor_distance'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("📏 Sensor de distància")
      .appendField("Trigger")
      .appendField(new Blockly.FieldNumber(16, 0, 29), "TRIG")
      .appendField("Echo")
      .appendField(new Blockly.FieldNumber(17, 0, 29), "ECHO");
    this.setOutput(true, "Number");
    this.setColour('#40c8ff');
    this.setTooltip("Mesura distància amb sensor ultrasònic HC-SR04");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE TEXT/STRINGS ====================

Blockly.Blocks['tecla_text_length'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck("String")
      .appendField("📏 longitud de");
    this.setOutput(true, "Number");
    this.setColour('#ffe500');
    this.setTooltip("Retorna la longitud d'un text");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_text_join'] = {
  init: function () {
    this.appendValueInput("TEXT1")
      .setCheck("String")
      .appendField("🔗 unir");
    this.appendValueInput("TEXT2")
      .setCheck("String")
      .appendField("amb");
    this.setOutput(true, "String");
    this.setColour('#ffe500');
    this.setTooltip("Uneix dos textos");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_text_contains'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck("String")
      .appendField("🔍");
    this.appendValueInput("SEARCH")
      .setCheck("String")
      .appendField("conté");
    this.setOutput(true, "Boolean");
    this.setColour('#ffe500');
    this.setTooltip("Comprova si un text conté un altre");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE LLISTES/ARRAYS ====================

Blockly.Blocks['tecla_list_create'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("📋 Crear llista buida");
    this.setOutput(true, "Array");
    this.setColour('#ff6e40');
    this.setTooltip("Crea una llista buida");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_list_add'] = {
  init: function () {
    this.appendValueInput("LIST")
      .setCheck("Array")
      .appendField("➕ Afegir a llista");
    this.appendValueInput("ITEM")
      .setCheck(null)
      .appendField("element");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff6e40');
    this.setTooltip("Afegeix un element al final de la llista");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_list_get'] = {
  init: function () {
    this.appendValueInput("LIST")
      .setCheck("Array")
      .appendField("📌 Obtenir de llista");
    this.appendValueInput("INDEX")
      .setCheck("Number")
      .appendField("posició");
    this.setOutput(true, null);
    this.setColour('#ff6e40');
    this.setTooltip("Obté un element d'una posició de la llista");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_list_length'] = {
  init: function () {
    this.appendValueInput("LIST")
      .setCheck("Array")
      .appendField("📏 longitud de llista");
    this.setOutput(true, "Number");
    this.setColour('#ff6e40');
    this.setTooltip("Retorna el nombre d'elements de la llista");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE COMUNICACIÓ ====================

Blockly.Blocks['tecla_serial_print'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck(null)
      .appendField("📡 Serial print");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00ffc8');
    this.setTooltip("Envia dades pel port sèrie");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_serial_read'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("📨 Serial llegir");
    this.setOutput(true, "String");
    this.setColour('#00ffc8');
    this.setTooltip("Llegeix dades del port sèrie");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_i2c_write'] = {
  init: function () {
    this.appendValueInput("ADDRESS")
      .setCheck("Number")
      .appendField("🔌 I2C escriure a adreça");
    this.appendValueInput("DATA")
      .setCheck(null)
      .appendField("dades");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00ffc8');
    this.setTooltip("Envia dades per I2C a un dispositiu");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_i2c_read'] = {
  init: function () {
    this.appendValueInput("ADDRESS")
      .setCheck("Number")
      .appendField("🔌 I2C llegir de adreça");
    this.appendValueInput("BYTES")
      .setCheck("Number")
      .appendField("bytes");
    this.setOutput(true, "Array");
    this.setColour('#00ffc8');
    this.setTooltip("Llegeix dades per I2C d'un dispositiu");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE MATEMÀTIQUES AVANÇADES ====================

Blockly.Blocks['tecla_math_random_int'] = {
  init: function () {
    this.appendValueInput("FROM")
      .setCheck("Number")
      .appendField("🎲 Número aleatori entre");
    this.appendValueInput("TO")
      .setCheck("Number")
      .appendField("i");
    this.setOutput(true, "Number");
    this.setColour('#00e676');
    this.setTooltip("Genera un número enter aleatori entre dos valors");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_math_map'] = {
  init: function () {
    this.appendValueInput("VALUE")
      .setCheck("Number")
      .appendField("🔄 Escalar valor");
    this.appendValueInput("FROM_MIN")
      .setCheck("Number")
      .appendField("de");
    this.appendValueInput("FROM_MAX")
      .setCheck("Number")
      .appendField("-");
    this.appendValueInput("TO_MIN")
      .setCheck("Number")
      .appendField("a");
    this.appendValueInput("TO_MAX")
      .setCheck("Number")
      .appendField("-");
    this.setOutput(true, "Number");
    this.setColour('#00e676');
    this.setTooltip("Escala un valor d'un rang a un altre (com map() d'Arduino)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_math_constrain'] = {
  init: function () {
    this.appendValueInput("VALUE")
      .setCheck("Number")
      .appendField("🔒 Limitar");
    this.appendValueInput("MIN")
      .setCheck("Number")
      .appendField("mínim");
    this.appendValueInput("MAX")
      .setCheck("Number")
      .appendField("màxim");
    this.setOutput(true, "Number");
    this.setColour('#00e676');
    this.setTooltip("Limita un valor entre un mínim i màxim");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_math_trig'] = {
  init: function () {
    this.appendValueInput("NUM")
      .setCheck("Number")
      .appendField(new Blockly.FieldDropdown([
        ["sin", "sin"], ["cos", "cos"], ["tan", "tan"],
        ["asin", "asin"], ["acos", "acos"], ["atan", "atan"]
      ]), "OP");
    this.setOutput(true, "Number");
    this.setColour('#00e676');
    this.setTooltip("Funcions trigonomètriques");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE FUNCIONS/PROCEDIMENTS ====================

Blockly.Blocks['tecla_function_define'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🔧 Definir funció")
      .appendField(new Blockly.FieldTextInput("la_meva_funcio"), "NAME");
    this.appendStatementInput("BODY")
      .setCheck(null)
      .appendField("fer");
    this.setColour('#76ff03');
    this.setTooltip("Defineix una funció reutilitzable");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_function_call'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🔧 Cridar funció")
      .appendField(new Blockly.FieldTextInput("la_meva_funcio"), "NAME");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#76ff03');
    this.setTooltip("Crida una funció definida");
    this.setHelpUrl("");
  }
};

// ==================== CONTROL AVANÇAT ====================

Blockly.Blocks['tecla_switch'] = {
  init: function () {
    this.appendValueInput("VALUE")
      .appendField("⚙️ Switch");
    this.appendStatementInput("CASE0")
      .appendField("Cas")
      .appendField(new Blockly.FieldTextInput("1"), "CASE0");
    this.appendStatementInput("DEFAULT")
      .appendField("Per defecte");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff9100');
    this.setTooltip("Estructura switch/case per múltiples condicions");
    this.setMutator(new Blockly.Mutator(['tecla_switch_case']));
    this.caseCount_ = 1;
  }
};

Blockly.Blocks['tecla_break'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🛑 Break");
    this.setPreviousStatement(true, null);
    this.setColour('#ff9100');
    this.setTooltip("Surt del bucle actual");
  }
};

Blockly.Blocks['tecla_continue'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("⏭️ Continue");
    this.setPreviousStatement(true, null);
    this.setColour('#ff9100');
    this.setTooltip("Salta a la següent iteració del bucle");
  }
};

Blockly.Blocks['tecla_try_except'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🛡️ Prova:");
    this.appendStatementInput("TRY")
      .setCheck(null);
    this.appendDummyInput()
      .appendField("❌ Si error:");
    this.appendStatementInput("EXCEPT")
      .setCheck(null);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff9100');
    this.setTooltip("Gestió d'errors try/except");
  }
};

// ==================== TEMPS I TEMPORITZADORS ====================

Blockly.Blocks['tecla_time_now'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("⏰ Temps actual (s)");
    this.setOutput(true, "Number");
    this.setColour('#78909c');
    this.setTooltip("Retorna el temps en segons des de l'inici");
  }
};

Blockly.Blocks['tecla_time_millis'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("⏱️ Mil·lisegons");
    this.setOutput(true, "Number");
    this.setColour('#78909c');
    this.setTooltip("Temps en mil·lisegons des de l'inici");
  }
};

Blockly.Blocks['tecla_timer_start'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("⏲️ Iniciar temporitzador")
      .appendField(new Blockly.FieldVariable("timer"), "VAR");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#78909c');
    this.setTooltip("Inicia un temporitzador");
  }
};

Blockly.Blocks['tecla_timer_elapsed'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("⏲️ Temps transcorregut")
      .appendField(new Blockly.FieldVariable("timer"), "VAR");
    this.setOutput(true, "Number");
    this.setColour('#78909c');
    this.setTooltip("Temps transcorregut des de l'inici del temporitzador");
  }
};

Blockly.Blocks['tecla_sleep_ms'] = {
  init: function () {
    this.appendValueInput("TIME")
      .setCheck("Number")
      .appendField("💤 Dormir (ms)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#78909c');
    this.setTooltip("Pausa en mil·lisegons");
  }
};

// ==================== STRING AVANÇAT ====================

Blockly.Blocks['tecla_string_replace'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck("String")
      .appendField("🔄 Reemplaçar a");
    this.appendValueInput("OLD")
      .setCheck("String")
      .appendField("cerca");
    this.appendValueInput("NEW")
      .setCheck("String")
      .appendField("per");
    this.setOutput(true, "String");
    this.setColour('#00e676');
    this.setTooltip("Reemplaça text dins un string");
  }
};

Blockly.Blocks['tecla_string_split'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck("String")
      .appendField("✂️ Dividir");
    this.appendValueInput("DELIMITER")
      .setCheck("String")
      .appendField("per");
    this.setOutput(true, "Array");
    this.setColour('#00e676');
    this.setTooltip("Divideix un string en una llista");
  }
};

Blockly.Blocks['tecla_string_join'] = {
  init: function () {
    this.appendValueInput("LIST")
      .setCheck("Array")
      .appendField("🔗 Unir llista");
    this.appendValueInput("SEPARATOR")
      .setCheck("String")
      .appendField("amb");
    this.setOutput(true, "String");
    this.setColour('#00e676');
    this.setTooltip("Uneix elements d'una llista amb un separador");
  }
};

Blockly.Blocks['tecla_string_format'] = {
  init: function () {
    this.appendValueInput("FORMAT")
      .setCheck("String")
      .appendField("📝 Format");
    this.appendValueInput("VALUE")
      .setCheck(null)
      .appendField("valor");
    this.setOutput(true, "String");
    this.setColour('#00e676');
    this.setTooltip("Formata un string amb valors");
  }
};

Blockly.Blocks['tecla_string_contains'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck("String")
      .appendField("🔍 Conté");
    this.appendValueInput("SEARCH")
      .setCheck("String")
      .appendField("el text");
    this.setOutput(true, "Boolean");
    this.setColour('#00e676');
    this.setTooltip("Comprova si un string conté un text");
  }
};

Blockly.Blocks['tecla_string_startswith'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck("String")
      .appendField("▶️ Comença amb");
    this.appendValueInput("PREFIX")
      .setCheck("String");
    this.setOutput(true, "Boolean");
    this.setColour('#00e676');
    this.setTooltip("Comprova si comença amb un prefix");
  }
};

Blockly.Blocks['tecla_string_endswith'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck("String")
      .appendField("◀️ Acaba amb");
    this.appendValueInput("SUFFIX")
      .setCheck("String");
    this.setOutput(true, "Boolean");
    this.setColour('#00e676');
    this.setTooltip("Comprova si acaba amb un sufix");
  }
};

// ==================== MATEMÀTIQUES AVANÇADES ====================

Blockly.Blocks['tecla_math_sin'] = {
  init: function () {
    this.appendValueInput("ANGLE")
      .setCheck("Number")
      .appendField("📐 sin");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Sinus d'un angle (en radians)");
  }
};

Blockly.Blocks['tecla_math_cos'] = {
  init: function () {
    this.appendValueInput("ANGLE")
      .setCheck("Number")
      .appendField("📐 cos");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Cosinus d'un angle (en radians)");
  }
};

Blockly.Blocks['tecla_math_tan'] = {
  init: function () {
    this.appendValueInput("ANGLE")
      .setCheck("Number")
      .appendField("📐 tan");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Tangent d'un angle (en radians)");
  }
};

Blockly.Blocks['tecla_math_log'] = {
  init: function () {
    this.appendValueInput("VALUE")
      .setCheck("Number")
      .appendField("📊 log");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Logaritme natural");
  }
};

Blockly.Blocks['tecla_math_exp'] = {
  init: function () {
    this.appendValueInput("VALUE")
      .setCheck("Number")
      .appendField("📈 exp");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Exponencial (e^x)");
  }
};

Blockly.Blocks['tecla_math_degrees'] = {
  init: function () {
    this.appendValueInput("RADIANS")
      .setCheck("Number")
      .appendField("🔄 Radians a graus");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Converteix radians a graus");
  }
};

Blockly.Blocks['tecla_math_radians'] = {
  init: function () {
    this.appendValueInput("DEGREES")
      .setCheck("Number")
      .appendField("🔄 Graus a radians");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Converteix graus a radians");
  }
};

Blockly.Blocks['tecla_math_bitwise'] = {
  init: function () {
    this.appendValueInput("A")
      .setCheck("Number")
      .appendField("🔢 Bitwise");
    this.appendValueInput("B")
      .setCheck("Number")
      .appendField(new Blockly.FieldDropdown([
        ["AND &", "AND"],
        ["OR |", "OR"],
        ["XOR ^", "XOR"],
        ["LEFT SHIFT <<", "LSHIFT"],
        ["RIGHT SHIFT >>", "RSHIFT"]
      ]), "OP");
    this.setOutput(true, "Number");
    this.setColour('#2979ff');
    this.setTooltip("Operacions bitwise");
  }
};

// ==================== NEOPIXELS / RGB LEDS ====================

Blockly.Blocks['tecla_neopixel_setup'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("💡 Configurar NeoPixels pin");
    this.appendValueInput("COUNT")
      .setCheck("Number")
      .appendField("quantitat");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Configura tira de LEDs NeoPixel");
  }
};

Blockly.Blocks['tecla_neopixel_set'] = {
  init: function () {
    this.appendValueInput("INDEX")
      .setCheck("Number")
      .appendField("💡 NeoPixel");
    this.appendValueInput("R")
      .setCheck("Number")
      .appendField("R");
    this.appendValueInput("G")
      .setCheck("Number")
      .appendField("G");
    this.appendValueInput("B")
      .setCheck("Number")
      .appendField("B");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Estableix color d'un LED NeoPixel (RGB 0-255)");
  }
};

Blockly.Blocks['tecla_neopixel_show'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("💡 Actualitzar NeoPixels");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Actualitza els LEDs amb els colors establerts");
  }
};

Blockly.Blocks['tecla_neopixel_clear'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("💡 Apagar NeoPixels");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Apaga tots els LEDs");
  }
};

Blockly.Blocks['tecla_neopixel_rainbow'] = {
  init: function () {
    this.appendValueInput("OFFSET")
      .setCheck("Number")
      .appendField("🌈 Arc de Sant Martí offset");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff1a6c');
    this.setTooltip("Efecte arc de Sant Martí");
  }
};

// ==================== DISPLAY OLED/LCD ====================

Blockly.Blocks['tecla_display_setup'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🖥️ Configurar Display")
      .appendField(new Blockly.FieldDropdown([
        ["OLED 128x64", "OLED"],
        ["LCD 16x2", "LCD"]
      ]), "TYPE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00f0ff');
    this.setTooltip("Configura display OLED o LCD");
  }
};

Blockly.Blocks['tecla_display_text'] = {
  init: function () {
    this.appendValueInput("TEXT")
      .setCheck("String")
      .appendField("🖥️ Mostrar text");
    this.appendValueInput("X")
      .setCheck("Number")
      .appendField("X");
    this.appendValueInput("Y")
      .setCheck("Number")
      .appendField("Y");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00f0ff');
    this.setTooltip("Mostra text a posició X,Y");
  }
};

Blockly.Blocks['tecla_display_clear'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🖥️ Netejar display");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00f0ff');
    this.setTooltip("Neteja la pantalla");
  }
};

Blockly.Blocks['tecla_display_pixel'] = {
  init: function () {
    this.appendValueInput("X")
      .setCheck("Number")
      .appendField("🖥️ Pixel X");
    this.appendValueInput("Y")
      .setCheck("Number")
      .appendField("Y");
    this.appendDummyInput()
      .appendField(new Blockly.FieldDropdown([
        ["Encès", "ON"],
        ["Apagat", "OFF"]
      ]), "STATE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00f0ff');
    this.setTooltip("Dibuixa un pixel");
  }
};

Blockly.Blocks['tecla_display_line'] = {
  init: function () {
    this.appendValueInput("X1")
      .setCheck("Number")
      .appendField("🖥️ Línia de X1");
    this.appendValueInput("Y1")
      .setCheck("Number")
      .appendField("Y1");
    this.appendValueInput("X2")
      .setCheck("Number")
      .appendField("a X2");
    this.appendValueInput("Y2")
      .setCheck("Number")
      .appendField("Y2");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00f0ff');
    this.setTooltip("Dibuixa una línia");
  }
};

Blockly.Blocks['tecla_display_rect'] = {
  init: function () {
    this.appendValueInput("X")
      .setCheck("Number")
      .appendField("🖥️ Rectangle X");
    this.appendValueInput("Y")
      .setCheck("Number")
      .appendField("Y");
    this.appendValueInput("WIDTH")
      .setCheck("Number")
      .appendField("amplada");
    this.appendValueInput("HEIGHT")
      .setCheck("Number")
      .appendField("alçada");
    this.appendDummyInput()
      .appendField(new Blockly.FieldDropdown([
        ["Contorn", "OUTLINE"],
        ["Omplert", "FILLED"]
      ]), "FILL");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00f0ff');
    this.setTooltip("Dibuixa un rectangle");
  }
};

// ==================== MOTORS I SERVOS ====================

Blockly.Blocks['tecla_servo_setup'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("🎛️ Configurar Servo pin");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff6e40');
    this.setTooltip("Configura un servomotor");
  }
};

Blockly.Blocks['tecla_servo_angle'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("🎛️ Servo pin");
    this.appendValueInput("ANGLE")
      .setCheck("Number")
      .appendField("angle");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff6e40');
    this.setTooltip("Mou el servo a un angle (0-180 graus)");
  }
};

Blockly.Blocks['tecla_motor_setup'] = {
  init: function () {
    this.appendValueInput("PIN1")
      .setCheck("Number")
      .appendField("⚙️ Configurar Motor DC pins");
    this.appendValueInput("PIN2")
      .setCheck("Number")
      .appendField(",");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff6e40');
    this.setTooltip("Configura un motor DC");
  }
};

Blockly.Blocks['tecla_motor_speed'] = {
  init: function () {
    this.appendValueInput("SPEED")
      .setCheck("Number")
      .appendField("⚙️ Motor velocitat");
    this.appendDummyInput()
      .appendField(new Blockly.FieldDropdown([
        ["Endavant", "FORWARD"],
        ["Enrere", "BACKWARD"],
        ["Aturar", "STOP"]
      ]), "DIRECTION");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff6e40');
    this.setTooltip("Controla velocitat i direcció del motor (-100 a 100)");
  }
};

// ==================== SENSORS ADICIONALS ====================

Blockly.Blocks['tecla_sensor_light'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("☀️ Sensor de llum pin");
    this.setOutput(true, "Number");
    this.setColour('#e040fb');
    this.setTooltip("Llegeix sensor de llum (0-100)");
  }
};

Blockly.Blocks['tecla_sensor_sound'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("🔊 Sensor de so pin");
    this.setOutput(true, "Number");
    this.setColour('#e040fb');
    this.setTooltip("Llegeix nivell de so (0-100)");
  }
};

Blockly.Blocks['tecla_sensor_moisture'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("💧 Sensor humitat pin");
    this.setOutput(true, "Number");
    this.setColour('#e040fb');
    this.setTooltip("Llegeix humitat (0-100)");
  }
};

Blockly.Blocks['tecla_sensor_pir'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("👁️ Sensor PIR (moviment) pin");
    this.setOutput(true, "Boolean");
    this.setColour('#e040fb');
    this.setTooltip("Detecta moviment (True/False)");
  }
};

Blockly.Blocks['tecla_sensor_button_external'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("🔘 Botó extern pin");
    this.appendDummyInput()
      .appendField(new Blockly.FieldDropdown([
        ["Pull Up", "PULLUP"],
        ["Pull Down", "PULLDOWN"]
      ]), "PULL");
    this.setOutput(true, "Boolean");
    this.setColour('#e040fb');
    this.setTooltip("Llegeix botó extern");
  }
};

// ==================== PWM AVANÇAT ====================

Blockly.Blocks['tecla_pwm_setup'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("📶 PWM Configurar pin");
    this.appendValueInput("FREQ")
      .setCheck("Number")
      .appendField("freqüència");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff3d00');
    this.setTooltip("Configura sortida PWM amb freqüència");
  }
};

Blockly.Blocks['tecla_pwm_duty'] = {
  init: function () {
    this.appendValueInput("PIN")
      .setCheck("Number")
      .appendField("📶 PWM pin");
    this.appendValueInput("DUTY")
      .setCheck("Number")
      .appendField("duty cycle");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff3d00');
    this.setTooltip("Estableix duty cycle (0-100%)");
  }
};

// ==================== EMMAGATZEMATGE ====================

Blockly.Blocks['tecla_storage_write'] = {
  init: function () {
    this.appendValueInput("KEY")
      .setCheck("String")
      .appendField("💾 Guardar clau");
    this.appendValueInput("VALUE")
      .setCheck(null)
      .appendField("valor");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#90a4ae');
    this.setTooltip("Guarda un valor a memòria persistent");
  }
};

Blockly.Blocks['tecla_storage_read'] = {
  init: function () {
    this.appendValueInput("KEY")
      .setCheck("String")
      .appendField("💾 Llegir clau");
    this.setOutput(true, null);
    this.setColour('#90a4ae');
    this.setTooltip("Llegeix un valor de memòria");
  }
};

Blockly.Blocks['tecla_storage_exists'] = {
  init: function () {
    this.appendValueInput("KEY")
      .setCheck("String")
      .appendField("💾 Existeix clau");
    this.setOutput(true, "Boolean");
    this.setColour('#90a4ae');
    this.setTooltip("Comprova si existeix una clau");
  }
};

Blockly.Blocks['tecla_storage_delete'] = {
  init: function () {
    this.appendValueInput("KEY")
      .setCheck("String")
      .appendField("💾 Eliminar clau");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#90a4ae');
    this.setTooltip("Elimina una clau de memòria");
  }
};

// ==================== SISTEMA ====================

Blockly.Blocks['tecla_system_reset'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🔄 Reiniciar sistema");
    this.setPreviousStatement(true, null);
    this.setColour('#37474f');
    this.setTooltip("Reinicia el dispositiu");
  }
};

Blockly.Blocks['tecla_system_memory'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🧠 Memòria lliure");
    this.setOutput(true, "Number");
    this.setColour('#37474f');
    this.setTooltip("Retorna memòria lliure en bytes");
  }
};

Blockly.Blocks['tecla_system_cpu_temp'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🌡️ Temperatura CPU");
    this.setOutput(true, "Number");
    this.setColour('#37474f');
    this.setTooltip("Temperatura del processador");
  }
};

Blockly.Blocks['tecla_system_voltage'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("⚡ Voltatge bateria");
    this.setOutput(true, "Number");
    this.setColour('#37474f');
    this.setTooltip("Voltatge d'alimentació");
  }
};

// ==================== BLOCS GENERATIUS / MODULARS ====================

Blockly.Blocks['tecla_probability'] = {
    init: function () {
        this.appendValueInput("PERCENT")
            .setCheck("Number")
            .appendField("🎲 Amb probabilitat");
        this.appendDummyInput()
            .appendField("%");
        this.appendStatementInput("DO")
            .setCheck(null)
            .appendField("fer");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour('#ff1a6c');
        this.setTooltip("Executa els blocs interiors només un % de les vegades");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['tecla_software_lfo'] = {
    init: function () {
        this.appendDummyInput()
            .appendField("〰️ LFO (Software)");
        this.appendValueInput("RATE")
            .setCheck("Number")
            .appendField("freq (Hz)");
        this.appendValueInput("MIN")
            .setCheck("Number")
            .appendField("min");
        this.appendValueInput("MAX")
            .setCheck("Number")
            .appendField("max");
        this.setOutput(true, "Number");
        this.setColour('#d500f9');
        this.setTooltip("Oscil·lador sinusoidal que retorna un valor entre min i max");
        this.setHelpUrl("");
        this.setInputsInline(true);
    }
};

Blockly.Blocks['tecla_scale_quantize'] = {
    init: function () {
        this.appendValueInput("VALUE")
            .setCheck("Number")
            .appendField("📏 Quantitzar valor");
        this.appendDummyInput()
            .appendField("a escala")
            .appendField(new Blockly.FieldDropdown([
                ["Major", "major"], ["Menor", "minor"],
                ["Pentatònica", "pentatonic"], ["Blues", "blues"],
                ["Cromàtica", "chromatic"]
            ]), "SCALE")
            .appendField("Clau")
            .appendField(new Blockly.FieldDropdown([
                ["C", "C"], ["D", "D"], ["E", "E"], ["F", "F"],
                ["G", "G"], ["A", "A"], ["B", "B"]
            ]), "ROOT");
        this.setOutput(true, "Number");
        this.setColour('#ff1a6c');
        this.setTooltip("Ajusta un número a la nota més propera de l'escala triada");
        this.setHelpUrl("");
    }
};

Blockly.Blocks['tecla_euclidean_rhythm'] = {
    init: function () {
        this.appendDummyInput()
            .appendField("🥁 Ritme Euclidià");
        this.appendValueInput("STEP")
            .setCheck("Number")
            .appendField("pas actual");
        this.appendValueInput("PULSES")
            .setCheck("Number")
            .appendField("cops (hits)");
        this.appendValueInput("STEPS")
            .setCheck("Number")
            .appendField("total passos");
        this.setOutput(true, "Boolean");
        this.setColour('#ff9100');
        this.setTooltip("Retorna cert si toca un cop en el pas actual (generador de ritmes)");
        this.setHelpUrl("");
        this.setInputsInline(true);
    }
};

// ==================== BLOCS DE MIDI AVANÇAT ====================

Blockly.Blocks['tecla_midi_cc'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎛️ Enviar CC")
      .appendField(new Blockly.FieldDropdown([
        ["1 – Modulació", "1"], ["7 – Volum", "7"], ["10 – Pan", "10"],
        ["11 – Expressió", "11"], ["64 – Sustain", "64"],
        ["71 – Resonància (Q)", "71"], ["74 – Brillantor (Cutoff)", "74"],
        ["91 – Reverb Send", "91"], ["93 – Chorus Send", "93"],
        ["Personalitzat…", "custom"]
      ]), "CC_TYPE");
    this.appendValueInput("CC_NUM")
      .setCheck("Number")
      .appendField("num");
    this.appendValueInput("CC_VAL")
      .setCheck("Number")
      .appendField("valor (0–127)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#40c8ff');
    this.setInputsInline(true);
    this.setTooltip("Envia un missatge MIDI Control Change (CC) al DAW");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_midi_pitch_bend'] = {
  init: function () {
    this.appendValueInput("AMOUNT")
      .setCheck("Number")
      .appendField("🎵 Pitch Bend");
    this.appendDummyInput()
      .appendField("(-63 = avall, 0 = centre, +63 = amunt)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#40c8ff');
    this.setInputsInline(true);
    this.setTooltip("Desafia l'afinació de totes les notes del canal (-63 a +63)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_midi_all_notes_off'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🚨 Panic – Apagar totes les notes");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#40c8ff');
    this.setTooltip("Envia NoteOff a totes les notes de tots els canals (CC 123)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_midi_sustain'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🦶 Pedal Sustain")
      .appendField(new Blockly.FieldDropdown([
        ["ON (premut)", "127"],
        ["OFF (alliberat)", "0"]
      ]), "STATE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#40c8ff');
    this.setInputsInline(true);
    this.setTooltip("Activa o desactiva el pedal de sustain (CC 64)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_midi_expression'] = {
  init: function () {
    this.appendValueInput("VALUE")
      .setCheck("Number")
      .appendField("🎭 Expressió (dinàmica)");
    this.appendDummyInput()
      .appendField("(0=silenci, 127=màxim)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#40c8ff');
    this.setInputsInline(true);
    this.setTooltip("Controla la dinàmica expressiva en temps real (CC 11)");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE LIVE CODING ====================

Blockly.Blocks['tecla_note_on_only'] = {
  init: function () {
    this.appendValueInput("NOTE")
      .setCheck("Number")
      .appendField("▶ NoteOn nota");
    this.appendValueInput("VELOCITY")
      .setCheck("Number")
      .appendField("vel");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff3d00');
    this.setInputsInline(true);
    this.setTooltip("Inicia una nota sense aturar-la (útil per drones i pads)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_note_off_only'] = {
  init: function () {
    this.appendValueInput("NOTE")
      .setCheck("Number")
      .appendField("■ NoteOff nota");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff3d00');
    this.setInputsInline(true);
    this.setTooltip("Atura una nota que estava sonant (NoteOff explícit)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_transpose'] = {
  init: function () {
    this.appendValueInput("NOTE")
      .setCheck("Number")
      .appendField("🔀 Transportar nota");
    this.appendValueInput("SEMITONES")
      .setCheck("Number")
      .appendField("+ semitons");
    this.setOutput(true, "Number");
    this.setColour('#ff3d00');
    this.setInputsInline(true);
    this.setTooltip("Puja o baixa una nota N semitons (positiu = amunt, negatiu = avall)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_humanize_vel'] = {
  init: function () {
    this.appendValueInput("BASE_VEL")
      .setCheck("Number")
      .appendField("🎭 Humanitzar vel");
    this.appendValueInput("SPREAD")
      .setCheck("Number")
      .appendField("± variació");
    this.setOutput(true, "Number");
    this.setColour('#ff3d00');
    this.setInputsInline(true);
    this.setTooltip("Retorna una velocitat aleatòria dins del rang base ± variació");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_crescendo'] = {
  init: function () {
    this.appendValueInput("FROM_VAL")
      .setCheck("Number")
      .appendField("📈 Crescendo de");
    this.appendValueInput("TO_VAL")
      .setCheck("Number")
      .appendField("a");
    this.appendValueInput("DURATION")
      .setCheck("Number")
      .appendField("en (s)");
    this.appendDummyInput()
      .appendField(new Blockly.FieldDropdown([
        ["Volum (CC7)", "7"],
        ["Expressió (CC11)", "11"],
        ["Modulació (CC1)", "1"],
        ["Brillantor (CC74)", "74"]
      ]), "CC");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff3d00');
    this.setInputsInline(true);
    this.setTooltip("Augmenta o disminueix gradualment un paràmetre MIDI al llarg del temps");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_riff_repeat'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🔄 Repetir Riff")
      .appendField(new Blockly.FieldNumber(4, 1, 64), "TIMES")
      .appendField("vegades, transport")
      .appendField(new Blockly.FieldNumber(0, -12, 12), "EACH_TRANSPOSE")
      .appendField("semitons/rep");
    this.appendStatementInput("RIFF")
      .setCheck(null)
      .appendField("riff");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#ff3d00');
    this.setTooltip("Repeteix el contingut N vegades, transposant X semitons cada repetició");
    this.setHelpUrl("");
  }
};

// ==================== BLOCS DE SEQÜENCIADOR ====================

Blockly.Blocks['tecla_seq_play_steps'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎵 Seqüència MIDI")
      .appendField(new Blockly.FieldTextInput("60,62,64,67,69"), "NOTES");
    this.appendValueInput("VELOCITY")
      .setCheck("Number")
      .appendField("vel");
    this.appendValueInput("STEP_DUR")
      .setCheck("Number")
      .appendField("durada/pas (s)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00ffc8');
    this.setInputsInline(true);
    this.setTooltip("Toca una seqüència de notes MIDI separades per comes (ex: 60,62,64,67)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_arpeggio_dir'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎶 Arpegi")
      .appendField(new Blockly.FieldDropdown([
        ["Do Major (C)", "C"], ["Re Major (D)", "D"], ["Mi Major (E)", "E"],
        ["Fa Major (F)", "F"], ["Sol Major (G)", "G"], ["La Major (A)", "A"],
        ["Si Major (B)", "B"], ["Do menor (Cm)", "Cm"], ["Re menor (Dm)", "Dm"],
        ["Mi menor (Em)", "Em"], ["Fa menor (Fm)", "Fm"], ["Sol menor (Gm)", "Gm"],
        ["La menor (Am)", "Am"], ["Si menor (Bm)", "Bm"]
      ]), "CHORD")
      .appendField(new Blockly.FieldDropdown([
        ["↑ Amunt", "up"],
        ["↓ Avall", "down"],
        ["↕ Amunt-Avall", "updown"],
        ["🎲 Aleatori", "random"]
      ]), "DIR");
    this.appendValueInput("SPEED")
      .setCheck("Number")
      .appendField("temps/nota (s)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00ffc8');
    this.setInputsInline(true);
    this.setTooltip("Toca les notes d'un acord en seqüència amb la direcció triada");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_drum_hit'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🥁 Colpir")
      .appendField(new Blockly.FieldDropdown([
        ["Kick (Bombo)", "36"],
        ["Snare (Caixa)", "38"],
        ["Hi-Hat Tancat", "42"],
        ["Hi-Hat Obert", "46"],
        ["Crash", "49"],
        ["Ride", "51"],
        ["Tom Alt", "50"],
        ["Tom Mig", "47"],
        ["Tom Baix", "45"],
        ["Clap", "39"],
        ["Cowbell", "56"]
      ]), "DRUM");
    this.appendValueInput("VELOCITY")
      .setCheck("Number")
      .appendField("vel");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00ffc8');
    this.setInputsInline(true);
    this.setTooltip("Toca un instrument de percussió MIDI GM (canal 10)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_drum_pattern'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🥁 Patró (16 passos)")
      .appendField(new Blockly.FieldDropdown([
        ["Kick (Bombo)", "36"],
        ["Snare (Caixa)", "38"],
        ["Hi-Hat Tancat", "42"],
        ["Hi-Hat Obert", "46"],
        ["Crash", "49"]
      ]), "DRUM");
    this.appendDummyInput()
      .appendField("pasos")
      .appendField(new Blockly.FieldTextInput("1000100010001000"), "PATTERN");
    this.appendValueInput("STEP_DUR")
      .setCheck("Number")
      .appendField("durada/pas (s)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00ffc8');
    this.setTooltip("Patró rítmic de fins a 16 passos: 1=cop, 0=silenci (ex: 1000100010001000)");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_note_name'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎵 Nota")
      .appendField(new Blockly.FieldDropdown([
        ["C2 (Do 2)", "36"], ["D2 (Re 2)", "38"], ["E2 (Mi 2)", "40"],
        ["F2 (Fa 2)", "41"], ["G2 (Sol 2)", "43"], ["A2 (La 2)", "45"], ["B2 (Si 2)", "47"],
        ["C3 (Do 3)", "48"], ["D3 (Re 3)", "50"], ["E3 (Mi 3)", "52"],
        ["F3 (Fa 3)", "53"], ["G3 (Sol 3)", "55"], ["A3 (La 3)", "57"], ["B3 (Si 3)", "59"],
        ["C4 (Do 4 – central)", "60"], ["C#4 / Db4", "61"],
        ["D4 (Re 4)", "62"], ["D#4 / Eb4", "63"],
        ["E4 (Mi 4)", "64"], ["F4 (Fa 4)", "65"], ["F#4 / Gb4", "66"],
        ["G4 (Sol 4)", "67"], ["G#4 / Ab4", "68"],
        ["A4 (La 4 – 440Hz)", "69"], ["A#4 / Bb4", "70"], ["B4 (Si 4)", "71"],
        ["C5 (Do 5)", "72"], ["D5 (Re 5)", "74"], ["E5 (Mi 5)", "76"],
        ["F5 (Fa 5)", "77"], ["G5 (Sol 5)", "79"], ["A5 (La 5)", "81"], ["B5 (Si 5)", "83"],
        ["C6 (Do 6)", "84"], ["D6 (Re 6)", "86"], ["E6 (Mi 6)", "88"]
      ]), "NOTE");
    this.setOutput(true, "Number");
    this.setColour('#00ffc8');
    this.setTooltip("Retorna el número MIDI d'una nota musical");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['tecla_chord_progression'] = {
  init: function () {
    this.appendDummyInput()
      .appendField("🎼 Progressió")
      .appendField(new Blockly.FieldDropdown([
        ["I–IV–V–I  (Pop)", "pop"],
        ["I–V–vi–IV  (Modern)", "modern"],
        ["ii–V–I  (Jazz)", "jazz"],
        ["I–vi–IV–V  (Anys 50)", "fifties"],
        ["I–IV–I–V  (Blues)", "blues"],
        ["i–VII–VI–VII  (Rock menor)", "rock"]
      ]), "PROG")
      .appendField("Key")
      .appendField(new Blockly.FieldDropdown([
        ["C", "0"], ["D", "2"], ["E", "4"], ["F", "5"],
        ["G", "7"], ["A", "9"], ["B", "11"]
      ]), "KEY");
    this.appendValueInput("BEATS_DUR")
      .setCheck("Number")
      .appendField("s/acord");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour('#00ffc8');
    this.setInputsInline(true);
    this.setTooltip("Toca una progressió d'acords completa en la tonalitat triada");
    this.setHelpUrl("");
  }
};

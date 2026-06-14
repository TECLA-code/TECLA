/**
 * Capa de compatibilitat per a Blockly 11.
 *
 * Blockly 11 va eliminar dues coses que els generadors d'aquest projecte
 * (escrits amb l'API de Blockly 10) encara fan servir:
 *   - Les constants d'ordre `Blockly.Python.ORDER_*` (ara són `python.Order.*`)
 *   - L'àlies `variableDB_` (ara és `nameDB_`)
 *
 * Aquest fitxer s'ha de carregar DESPRÉS de python_compressed.js i ABANS
 * de qualsevol generador propi.
 */
(function () {
  'use strict';

  if (typeof Blockly === 'undefined' || !Blockly.Python) {
    console.error('[TECLA] blockly_compat: Blockly.Python no està carregat');
    return;
  }

  // ORDER_ATOMIC, ORDER_FUNCTION_CALL, ... a partir de l'enum python.Order
  if (typeof python !== 'undefined' && python.Order) {
    for (const key of Object.keys(python.Order)) {
      if (isNaN(Number(key))) {
        Blockly.Python['ORDER_' + key] = python.Order[key];
      }
    }
  }
})();

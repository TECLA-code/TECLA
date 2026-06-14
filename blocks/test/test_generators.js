/**
 * Test headless dels generadors TECLA Blocks.
 *
 * Carrega Blockly (vendoritzat) + tots els blocs i generadors en Node,
 * crea un workspace amb un bloc de cada tipus del toolbox i comprova que
 * el codi Python generat compila (via `python3 -c ast.parse`).
 *
 * Ús:  node test/test_generators.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

// Entorn mínim de navegador per als scripts del projecte
global.window = global;

const ROOT = path.join(__dirname, '..');
const Blockly = require(path.join(ROOT, 'vendor/blockly/blockly_compressed.js'));
require(path.join(ROOT, 'vendor/blockly/blocks_compressed.js'));
const pythonModule = require(path.join(ROOT, 'vendor/blockly/python_compressed.js'));

global.Blockly = Blockly;
global.python = pythonModule;
// En Node l'UMD no fa l'assignació d'àlies que sí que fa al navegador
Blockly.Python = pythonModule.pythonGenerator;

// Missatges (els blocs natius els necessiten per construir-se)
Blockly.setLocale(require(path.join(ROOT, 'vendor/blockly/msg/ca.js')));

// Sense DOM: desactivem els events (serialitzen XML) i injectem un
// pseudo-document mínim per a Blockly.utils.xml
Blockly.Events.disable();
function _fakeElem(tag) {
  return {
    tagName: tag, attrs: {}, childNodes: [], textContent: '',
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k] ?? null; },
    appendChild(c) { this.childNodes.push(c); return c; },
  };
}
Blockly.utils.xml.injectDependencies({
  document: {
    createElementNS: (_ns, tag) => _fakeElem(tag),
    createTextNode: (t) => ({ textContent: t }),
  },
  DOMParser: class { parseFromString() { return { documentElement: _fakeElem('xml') }; } },
  XMLSerializer: class { serializeToString() { return '<xml></xml>'; } },
});

require(path.join(ROOT, 'generators/blockly_compat.js'));
require(path.join(ROOT, 'blocks/tecla_blocks.js'));
require(path.join(ROOT, 'blocks/scratch_compatible.js'));
require(path.join(ROOT, 'generators/tecla_python.js'));
require(path.join(ROOT, 'generators/tecla_python_extended.js'));
require(path.join(ROOT, 'generators/tecla_python_hid.js'));
require(path.join(ROOT, 'generators/scratch_python.js'));

// Tipus de bloc presents al toolbox d'index.html
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf-8');
const toolboxXml = html.match(/<xml id="toolbox"[\s\S]*?<\/xml>/)[0];
const types = [...new Set([...toolboxXml.matchAll(/block type="([a-z_0-9]+)"/g)].map(m => m[1]))];

let failed = 0;

// 1) Cada tipus té definició i generador, i es pot instanciar headless
const ws = new Blockly.Workspace();
for (const t of types) {
  try {
    if (!Blockly.Blocks[t]) throw new Error('sense definició de bloc');
    if (!Blockly.Python.forBlock[t]) throw new Error('sense generador Python');
    const b = ws.newBlock(t);
    if (b.initModel) b.initModel(); // crea variables de FieldVariable en mode headless
  } catch (e) {
    console.error(`FAIL ${t}: ${e.message}`);
    failed++;
  }
}
console.log(`Blocs instanciats: ${types.length - failed}/${types.length}`);

// 2) El codi generat amb TOTS els blocs alhora compila
const code = window._fullGenerateCode(ws);
if (code.includes('# Error generant codi')) {
  console.error('FAIL: la generació ha fallat:', code.slice(0, 300));
  failed++;
}
const tmpFile = path.join(require('os').tmpdir(), 'tecla_all_blocks.py');
fs.writeFileSync(tmpFile, code);
try {
  execFileSync('python3', ['-c', `import ast, sys; ast.parse(open(sys.argv[1]).read())`, tmpFile]);
  console.log(`Python OK: ${code.split('\n').length} línies compilen (${tmpFile})`);
} catch (e) {
  console.error('FAIL: el Python generat no compila:\n' + e.stderr);
  failed++;
}

ws.dispose();
if (failed) { console.error(`\n${failed} errors`); process.exit(1); }
console.log('\nTOT OK ✓');

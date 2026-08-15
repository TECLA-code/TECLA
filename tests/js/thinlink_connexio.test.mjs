/**
 * El diagnòstic de connexió del TeclaThinLink, sense maquinari.
 *
 * El cas que va passar de debò: el boot.py del dispositiu tenia
 * usb_cdc.enable(console=True, data=False) —el del MacroPad— i llavors
 * CircuitPython només exposa UN port CDC, el de la consola. L'app obria el
 * selector de ports una vegada i una altra i deia "tria l'altre", quan no
 * n'hi havia cap altre.
 *
 * Aquí es comprova que la sonda sap distingir els tres casos i que, amb un
 * sol port que és la consola, NO s'obre el selector i s'explica la causa.
 *
 *   node tests/js/thinlink_connexio.test.mjs
 */
import assert from 'node:assert';
const M = await import(new URL('../../codi/js/tecla-thinlink.js', import.meta.url));

function portFals(text, { obreFalla = false } = {}) {
  let cancel·lat = false;
  return {
    async open() { if (obreFalla) throw new Error('ocupat'); },
    async close() { },
    get readable() {
      return { getReader() {
        let dat = false;
        return {
          async read() {
            if (cancel·lat) return { done: true };
            if (!dat && text) { dat = true; return { value: new TextEncoder().encode(text) }; }
            return new Promise(() => { });      // silenci
          },
          async cancel() { cancel·lat = true; },
          releaseLock() { },
        };
      } };
    },
    get writable() { return { getWriter() { return { write() { }, releaseLock() { } }; } }; },
    getInfo() { return {}; },
  };
}

const casos = [
  ['port de dades',  'I 0000 10 20 30\n', 'dades', true],
  ['consola (REPL)', 'Adafruit CircuitPython 10.0.3\n>>> ', 'consola', false],
  ['port mut',       '', 'silenci', false],
];
const t = new M.TeclaThinLink();
for (const [nom, text, motiuEsperat, okEsperat] of casos) {
  const r = await t._probeDataPort(portFals(text), 300);
  assert.strictEqual(r.ok, okEsperat, `${nom}: ok`);
  assert.strictEqual(r.motiu, motiuEsperat, `${nom}: motiu (${r.motiu})`);
  console.log(`  ✓ ${nom.padEnd(16)} → ok=${r.ok} motiu=${r.motiu}`);
}
const r = await t._probeDataPort(portFals('x', { obreFalla: true }), 200);
assert.strictEqual(r.motiu, 'ocupat');
console.log('  ✓ port ja obert    → motiu=ocupat');

// El cas de debò: un sol port autoritzat i és la consola → CAP selector
Object.defineProperty(globalThis, 'navigator', { configurable: true, value: { serial: {
  async getPorts() { return [portFals('Adafruit CircuitPython\n>>> ')]; },
  async requestPort() { throw new Error('EL SELECTOR NO S’HAURIA D’OBRIR'); },
  addEventListener() { },
} } });
const t2 = new M.TeclaThinLink();
const res = await t2.connectAuto();
assert.strictEqual(res.success, false);
assert.strictEqual(res.sensePortDeDades, true, 'ha de dir que falta el canal de dades');
assert.match(res.error, /data=True/, 'ha d’explicar la causa');
console.log('  ✓ només la consola → sense selector, i diagnostica el boot.py');
console.log('\nTOT OK');

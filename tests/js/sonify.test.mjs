/**
 * L'anàlisi de sonificació, amb imatges fetes a mà on la resposta es coneix.
 *   node tests/js/sonify.test.mjs
 */
import assert from 'node:assert';
const S = await import(new URL('../../codi/js/tecla-sonify.js', import.meta.url));

/** Un llenç RGBA buit. */
function llenc(w, h) { return { data: new Uint8ClampedArray(w * h * 4), width: w, height: h }; }
function punt(img, x, y, v = 255) {
  const i = (y * img.width + x) * 4;
  img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255;
}

// ── 1. Una línia que puja ha de donar una corba que puja ──────────────────
{
  const w = 64, h = 64, img = llenc(w, h);
  for (let x = 0; x < w; x++) punt(img, x, h - 1 - Math.round((x / (w - 1)) * (h - 1)));
  const c = S.analitzaImatge(img, { columnes: 16, durada: 1600 });
  const notes = c.map(p => p[1]);
  for (let i = 1; i < notes.length; i++) {
    assert.ok(notes[i] >= notes[i - 1], `la corba baixa al pas ${i}: ${notes}`);
  }
  assert.ok(notes[0] < 20 && notes[notes.length - 1] > 107,
    `hauria d'anar de baix a dalt: ${notes[0]} → ${notes[notes.length - 1]}`);
  console.log(`  ✓ línia ascendent      → nota ${notes[0]} … ${notes[notes.length - 1]}`);
}

// ── 2. Una imatge negra no diu res ────────────────────────────────────────
{
  const c = S.analitzaImatge(llenc(32, 32), { columnes: 8 });
  assert.ok(c.every(p => p[2] === 0), 'una imatge negra no hauria de tenir força');
  console.log('  ✓ imatge negra         → força 0 a totes les columnes');
}

// ── 3. Una taca ampla ha de donar més AMPLADA que un punt ─────────────────
{
  const w = 32, h = 64;
  const fi = llenc(w, h), ample = llenc(w, h);
  for (let x = 0; x < w; x++) {
    punt(fi, x, 32);
    for (let y = 8; y < 56; y++) punt(ample, x, y);
  }
  const a = S.analitzaImatge(fi, { columnes: 4 })[1][3];
  const b = S.analitzaImatge(ample, { columnes: 4 })[1][3];
  assert.ok(b > a + 5, `la taca ampla hauria de ser més ampla: ${a} vs ${b}`);
  console.log(`  ✓ amplada              → punt ${a} · taca ${b}`);
}

// ── 4. Moviment: sense canvi entre fotogrames, energia zero ───────────────
{
  const w = 32, h = 32, a = llenc(w, h);
  for (let i = 0; i < w * h * 4; i += 4) { a.data[i] = a.data[i + 1] = a.data[i + 2] = 120; }
  const r = S.analitzaMoviment(a.data, a.data, w, h);
  assert.strictEqual(r.energia, 0, 'dos fotogrames idèntics no són moviment');
  // …i amb una taca que apareix a dalt, el centre ha de ser alt
  const b = llenc(w, h); b.data.set(a.data);
  for (let y = 0; y < 6; y++) for (let x = 0; x < w; x++) punt(b, x, y);
  const r2 = S.analitzaMoviment(b.data, a.data, w, h);
  assert.ok(r2.energia > 0, 'hi hauria d’haver moviment');
  assert.ok(r2.centre > 0.75, `el moviment és a dalt: centre ${r2.centre.toFixed(2)}`);
  console.log(`  ✓ moviment             → quiet 0 · taca a dalt centre ${r2.centre.toFixed(2)}`);
}

// ── 5. La reducció respecta el sostre i conserva la durada ────────────────
{
  const corba = [];
  for (let i = 0; i < 4000; i++) corba.push([25, 60 + Math.round(30 * Math.sin(i / 40)), 90, 8]);
  const durada = corba.reduce((s, p) => s + p[0], 0);
  const r = S.redueix(corba, { maxPunts: 200 });
  assert.ok(r.length <= 200, `no ha cabut al sostre: ${r.length}`);
  const durada2 = r.reduce((s, p) => s + p[0], 0);
  assert.ok(Math.abs(durada - durada2) <= 25, `la durada canvia: ${durada} → ${durada2}`);
  console.log(`  ✓ reducció             → 4000 → ${r.length} punts, durada intacta (${durada} ms)`);
}

// ── 6. Un tram quiet no gasta punts ───────────────────────────────────────
{
  const corba = [];
  for (let i = 0; i < 300; i++) corba.push([20, 64, 100, 8]);   // res es mou
  const r = S.redueix(corba, { maxDt: 100000 });
  assert.ok(r.length <= 3, `un tram quiet hauria de ser 2-3 punts i en són ${r.length}`);
  console.log(`  ✓ tram quiet           → 300 fotogrames → ${r.length} punts`);
}

// ── 7. El pes és el que es dirà a l'usuari ────────────────────────────────
{
  const corba = Array.from({ length: 300 }, () => [40, 64, 100, 8]);
  const kb = S.pesCorba(corba) / 1024;
  assert.ok(kb > 0.5 && kb < 8, `pes fora de mare: ${kb} KB`);
  console.log(`  ✓ pes                  → 300 punts ≈ ${kb.toFixed(1)} KB al .py`);
}
console.log('\nTOT OK');

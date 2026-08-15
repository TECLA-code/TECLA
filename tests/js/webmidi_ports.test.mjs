/**
 * El maneig de ports MIDI, amb un Web MIDI de mentida.
 *   node tests/js/webmidi_ports.test.mjs
 *
 * El que es prova aquí és justament el que a Windows fallava en silenci: cap
 * port, un port que no s'obre perquè el té un altre programa, i un port que
 * apareix DESPRÉS d'haver carregat la pàgina.
 */
import assert from 'node:assert';

/** Un MIDIAccess de mentida amb els ports que se li diguin. */
function fingeixEntorn({ ports = [], plataforma = 'Win32', segur = true, hiHaAPI = true } = {}) {
    const mapa = new Map();
    for (const p of ports) mapa.set(p.id, p);
    const access = { outputs: mapa, onstatechange: null };
    globalThis.window = { isSecureContext: segur };
    // El `navigator` del Node modern només té getter: cal redefinir-lo.
    Object.defineProperty(globalThis, 'navigator', {
        configurable: true, writable: true,
        value: {
            platform: plataforma,
            userAgent: plataforma,
            ...(hiHaAPI ? { requestMIDIAccess: async () => access } : {}),
        },
    });
    return { access, mapa };
}

/** Un port de sortida de mentida. */
function port(id, name, { obreFalla = false } = {}) {
    return {
        id, name, state: 'connected', enviats: [],
        async open() { if (obreFalla) throw Object.assign(new Error('in use'), { name: 'InvalidAccessError' }); return this; },
        send(d) { this.enviats.push(d); },
    };
}

const { WebMidiManager } = await import(new URL('../../codi/js/tecla-webmidi.js', import.meta.url));

// ── 1. Windows sense cap port: el diagnòstic ha de parlar del cable virtual ──
{
    fingeixEntorn({ ports: [], plataforma: 'Win32' });
    const m = new WebMidiManager();
    const r = await m.init();
    assert.equal(r.success, true, 'l\'accés s\'ha concedit igualment');
    assert.equal(m.outputs.length, 0);
    const d = m.diagnostic();
    assert.match(d, /loopMIDI/, `el consell de Windows ha de citar loopMIDI: ${d}`);
    assert.match(d, /Ableton/, `ha d\'aclarir que Ableton no crea cap port: ${d}`);
}

// ── 2. Al Mac el consell és un altre: el IAC Driver ─────────────────────────
{
    fingeixEntorn({ ports: [], plataforma: 'MacIntel' });
    const m = new WebMidiManager();
    await m.init();
    const d = m.diagnostic();
    assert.match(d, /IAC/, `al Mac ha de parlar del IAC Driver: ${d}`);
    assert.doesNotMatch(d, /loopMIDI/, 'loopMIDI no pinta res al Mac');
}

// ── 3. file:// — el cas que no dona cap error visible al navegador ──────────
{
    fingeixEntorn({ plataforma: 'Win32', segur: false });
    const m = new WebMidiManager();
    const r = await m.init();
    assert.equal(r.success, false);
    assert.match(r.error, /https/, `ha d'assenyalar el context segur: ${r.error}`);
}

// ── 4. Un port ocupat per un altre programa: s'ha de DIR, no callar ─────────
{
    fingeixEntorn({ ports: [port('p1', 'loopMIDI Port', { obreFalla: true })], plataforma: 'Win32' });
    const m = new WebMidiManager();
    await m.init();
    const avisos = [];
    m.onAvis = t => avisos.push(t);
    const r = await m.selectOutput('p1');
    assert.equal(r.ok, false, 'un port que no s\'obre no pot donar-se per bo');
    assert.match(r.motiu, /loopMIDI Port/, 'ha de dir quin port');
    assert.match(r.motiu, /un sol programa/, `a Windows ha d'explicar l'exclusivitat: ${r.motiu}`);
    assert.equal(avisos.length, 1, 'i ha d\'arribar a la interfície');
}

// ── 5. Un port que va bé: s'obre i hi passen les dades ──────────────────────
{
    const p = port('p1', 'IAC Bus 1');
    fingeixEntorn({ ports: [p], plataforma: 'MacIntel' });
    const m = new WebMidiManager();
    await m.init();
    const r = await m.selectOutput('p1');
    assert.equal(r.ok, true);
    assert.equal(r.nom, 'IAC Bus 1');
    m.send('note_on', 60, 100, 0);
    assert.deepEqual(p.enviats, [[0x90, 60, 100]]);
    assert.equal(m.diagnostic(), null, 'amb ports no hi ha res a diagnosticar');
}

// ── 6. Un port creat DESPRÉS de carregar: refresca() l'ha de trobar ─────────
{
    const { mapa } = fingeixEntorn({ ports: [], plataforma: 'Win32' });
    const m = new WebMidiManager();
    await m.init();
    assert.equal(m.outputs.length, 0);
    mapa.set('nou', port('nou', 'loopMIDI Port 1'));   // l'usuari obre loopMIDI ara
    assert.equal(m.outputs.length, 0, 'sense rellegir, encara no hi és');
    const ara = m.refresca();
    assert.equal(ara.length, 1, 'en rellegir, hi ha de ser');
    assert.equal(ara[0].name, 'loopMIDI Port 1');
}

// ── 7. Un port que peta a cada nota només ha d'avisar UN cop ────────────────
{
    const p = port('p1', 'Port dolent');
    fingeixEntorn({ ports: [p], plataforma: 'Win32' });
    const m = new WebMidiManager();
    await m.init();
    await m.selectOutput('p1');
    p.send = () => { throw new Error('boom'); };
    const avisos = [];
    m.onAvis = t => avisos.push(t);
    for (let i = 0; i < 50; i++) m.send('note_on', 60, 100, 0);
    assert.equal(avisos.length, 1, `el registre no es pot inundar: ${avisos.length} avisos`);
}

console.log('webmidi_ports: tot correcte ✓');

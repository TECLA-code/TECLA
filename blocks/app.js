/**
 * TECLA Blocks — Web version
 * Substitueix window.teclaAPI per APIs natives del navegador:
 *   - File System Access API per guardar/obrir/pujar al dispositiu
 *   - Blob download per exportar Python
 */

'use strict';

let workspace;
let simulationRunning = false;
let activeVisuals = [];

let currentProject = {
  name: 'Projecte sense títol',
  blocks: null
};

let codeCache = { hash: null, code: null };
let deviceDirHandle = null;

// ── Debounce util ─────────────────────────────────────────────
function debounce(fn, ms = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function getWorkspaceHash(ws) {
  const b = ws.getAllBlocks(false);
  return b.map(x => x.id).sort().join(',') + '|' + b.map(x => x.type).sort().join(',');
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initBlockly();
  setupTabs();
  setupButtons();
  setupFileOpen();
  initThemeSystem();
  updateStatusBar();
});

function initBlockly() {
  const theme = Blockly.Theme.defineTheme('tecla_dark', {
    base: Blockly.Themes.Classic,
    componentStyles: {
      workspaceBackgroundColour: '#0e0e0e',
      toolboxBackgroundColour: '#111',
      toolboxForegroundColour: '#ccc',
      flyoutBackgroundColour: '#141414',
      flyoutForegroundColour: '#ccc',
      flyoutOpacity: 0.97,
      scrollbarColour: '#333',
      scrollbarOpacity: 0.6
    }
  });

  workspace = Blockly.inject('blocklyDiv', {
    toolbox: document.getElementById('toolbox'),
    theme,
    grid: { spacing: 20, length: 3, colour: '#1e1e1e', snap: true },
    zoom: { controls: true, wheel: true, startScale: 1.0, maxScale: 3, minScale: 0.3, scaleSpeed: 1.2 },
    trashcan: true,
    move: { scrollbars: true, drag: true, wheel: true }
  });

  workspace.addChangeListener(debounce(onWorkspaceChange, 300));
}

function onWorkspaceChange(e) {
  const relevant = [
    Blockly.Events.BLOCK_CHANGE, Blockly.Events.BLOCK_CREATE,
    Blockly.Events.BLOCK_DELETE, Blockly.Events.BLOCK_MOVE
  ];
  if (!relevant.includes(e.type)) return;
  updateGeneratedCode();
  updateStatusBar();
}

function updateGeneratedCode() {
  const hash = getWorkspaceHash(workspace);
  if (codeCache.hash === hash && codeCache.code !== null) return codeCache.code;
  const code = generateCompletePythonCode(workspace);
  codeCache = { hash, code };
  document.getElementById('generatedCode').textContent = code;
  return code;
}

function updateStatusBar() {
  const n = workspace.getAllBlocks(false).length;
  document.getElementById('status-blocks').textContent = `Blocs: ${n}`;
}

// ── Tabs ──────────────────────────────────────────────────────
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.panel-content').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`panel-${btn.dataset.tab}`).classList.add('active');
    });
  });
}

// ── Buttons ───────────────────────────────────────────────────
function setupButtons() {
  document.getElementById('btn-new').addEventListener('click', newProject);
  document.getElementById('btn-open').addEventListener('click', openProject);
  document.getElementById('btn-save').addEventListener('click', saveProject);
  document.getElementById('btn-export').addEventListener('click', exportPython);
  document.getElementById('btn-connect').addEventListener('click', connectDevice);
  document.getElementById('btn-upload').addEventListener('click', uploadToDevice);
  document.getElementById('btn-fw-upload').addEventListener('click', uploadToDevice);
  document.getElementById('btn-midi-connect').addEventListener('click', connectMIDI);
  document.getElementById('midi-port-select').addEventListener('change', selectMIDIPort);
  document.getElementById('btn-copy-code').addEventListener('click', copyCode);
  document.getElementById('btn-simulate').addEventListener('click', runSimulation);
  document.getElementById('btn-stop-sim').addEventListener('click', stopSimulation);
  document.getElementById('btn-ex-melody').addEventListener('click', () => loadExample('melody'));
  document.getElementById('btn-ex-sequencer').addEventListener('click', () => loadExample('sequencer'));
  document.getElementById('btn-ex-buttons').addEventListener('click', () => loadExample('buttons'));
  document.getElementById('btn-ex-complex').addEventListener('click', () => loadExample('complex'));

  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveProject(); }
    if ((e.ctrlKey || e.metaKey) && e.key === 'o') { e.preventDefault(); openProject(); }
  });
}

// ── File open via hidden input ────────────────────────────────
function setupFileOpen() {
  document.getElementById('file-open-input').addEventListener('change', async e => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      loadProjectFromText(text, file.name);
    } catch (err) {
      toast('Error llegint fitxer', 'err');
    }
    e.target.value = '';
  });
}

// ── Project management ────────────────────────────────────────
function newProject() {
  if (!confirm('Vols crear un nou projecte? Els canvis no guardats es perdran.')) return;
  workspace.clear();
  currentProject = { name: 'Projecte sense títol', blocks: null };
  codeCache = { hash: null, code: null };
  document.getElementById('generatedCode').textContent = '# El teu codi apareixerà aquí...';
  updateStatusBar();
  toast('Nou projecte creat');
}

async function saveProject() {
  try {
    const state = Blockly.serialization.workspaces.save(workspace);
    const data = {
      name: currentProject.name,
      version: '2.0',
      format: 'json',
      blocks: state,
      timestamp: new Date().toISOString()
    };
    const json = JSON.stringify(data, null, 2);

    if ('showSaveFilePicker' in window) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: `${currentProject.name}.tblocks`,
          types: [{ description: 'TECLA Blocks', accept: { 'application/json': ['.tblocks'] } }]
        });
        const writable = await handle.createWritable();
        await writable.write(json);
        await writable.close();
        toast('Projecte guardat', 'ok');
        return;
      } catch (e) {
        if (e.name === 'AbortError') return;
      }
    }

    blobDownload(json, `${currentProject.name}.tblocks`, 'application/json');
    toast('Projecte descarregat', 'ok');
  } catch (err) {
    console.error(err);
    toast('Error guardant', 'err');
  }
}

function openProject() {
  if ('showOpenFilePicker' in window) {
    window.showOpenFilePicker({
      types: [{ description: 'TECLA Blocks / Python', accept: { 'application/json': ['.tblocks'], 'text/x-python': ['.py'] } }]
    }).then(async ([handle]) => {
      const file = await handle.getFile();
      const text = await file.text();
      loadProjectFromText(text, file.name);
    }).catch(e => { if (e.name !== 'AbortError') toast('Error obrint fitxer', 'err'); });
  } else {
    document.getElementById('file-open-input').click();
  }
}

function loadProjectFromText(text, filename) {
  workspace.clear();
  try {
    const data = JSON.parse(text);
    if (data.format === 'json' && data.blocks) {
      Blockly.serialization.workspaces.load(data.blocks, workspace);
      currentProject.name = data.name || filename || 'Projecte';
      toast('Projecte carregat', 'ok');
    } else if (data.blocks && typeof data.blocks === 'string' && data.blocks.trim().startsWith('<xml')) {
      const dom = Blockly.utils.xml.textToDom(data.blocks);
      Blockly.Xml.domToWorkspace(dom, workspace);
      toast('Projecte (XML) carregat', 'ok');
    } else {
      throw new Error('Format no reconegut');
    }
  } catch (jsonErr) {
    if (text.trim().startsWith('<xml')) {
      try {
        const dom = Blockly.utils.xml.textToDom(text);
        Blockly.Xml.domToWorkspace(dom, workspace);
        toast('Projecte XML carregat', 'ok');
        return;
      } catch (e) { /* fall through */ }
    }
    toast('Format no compatible', 'err');
    console.error(jsonErr);
  }
  updateGeneratedCode();
  updateStatusBar();
}

async function exportPython() {
  const code = updateGeneratedCode() || document.getElementById('generatedCode').textContent;
  const name = currentProject.name.replace(/[^a-z0-9_]/gi, '_');
  blobDownload(code, `${name}.py`, 'text/x-python');
  toast('Codi Python exportat', 'ok');
}

// ── Device connection (like MacroPad / MIDI apps) ─────────────
async function connectDevice() {
  if (!('showDirectoryPicker' in window)) {
    toast('Requereix Chrome o Edge (File System Access API)', 'err');
    return;
  }
  try {
    const dirHandle = await window.showDirectoryPicker({
      mode: 'readwrite',
      id: 'circuitpy',
      startIn: 'desktop'
    });
    deviceDirHandle = dirHandle;
    updateDeviceBadge(dirHandle.name, true);
    setStatus(`Connectat a ${dirHandle.name}`, 'ok');
    toast(`Connectat a ${dirHandle.name}`, 'ok');
  } catch (e) {
    if (e.name !== 'AbortError') { toast('Error connectant', 'err'); console.error(e); }
  }
}

async function uploadToDevice() {
  if (!deviceDirHandle) {
    await connectDevice();
    if (!deviceDirHandle) return;
  }
  try {
    const code = updateGeneratedCode() || document.getElementById('generatedCode').textContent;
    const fileHandle = await deviceDirHandle.getFileHandle('code.py', { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(code);
    await writable.close();
    toast(`code.py pujat a ${deviceDirHandle.name}`, 'ok');
    setStatus(`Pujat a ${deviceDirHandle.name}`, 'ok');
  } catch (e) {
    if (e.name === 'NotAllowedError') {
      deviceDirHandle = null;
      updateDeviceBadge(null, false);
      toast('Accés revocat. Torna a connectar.', 'err');
    } else {
      toast('Error pujant al dispositiu', 'err'); console.error(e);
    }
  }
}

function updateDeviceBadge(name, connected) {
  const badge = document.getElementById('device-badge');
  document.getElementById('device-name').textContent = name || 'desconnectat';
  badge.className = connected ? 'device-badge connected' : 'device-badge';
  document.getElementById('btn-upload').disabled = !connected;
  const connectBtn = document.getElementById('btn-connect');
  connectBtn.textContent = connected ? 'Desconnectar' : 'Connectar';
  connectBtn.onclick = connected ? disconnectDevice : connectDevice;
  const fwName = document.getElementById('fw-device-name');
  const fwStatus = document.getElementById('fw-device-status');
  if (fwName) fwName.textContent = name || '—';
  if (fwStatus) { fwStatus.textContent = connected ? name : 'desconnectat'; fwStatus.className = connected ? 'status-val ok' : 'status-val'; }
}

function disconnectDevice() {
  deviceDirHandle = null;
  updateDeviceBadge(null, false);
  setStatus('Dispositiu desconnectat');
  toast('Desconnectat');
}

// ── Copy code ─────────────────────────────────────────────────
function copyCode() {
  const code = codeCache.code || document.getElementById('generatedCode').textContent;
  navigator.clipboard.writeText(code).then(() => toast('Codi copiat', 'ok')).catch(() => toast('Error copiant', 'err'));
}

// ── Web MIDI ──────────────────────────────────────────────────
let midiAccess = null;
let midiOutput = null;

async function connectMIDI() {
  if (!navigator.requestMIDIAccess) {
    simLog('Web MIDI no disponible. Usa Chrome o Edge.', 'sys'); return;
  }
  try {
    midiAccess = await navigator.requestMIDIAccess({ sysex: false });
    midiAccess.onstatechange = updateMIDIPortList;
    updateMIDIPortList();
  } catch(e) {
    simLog('MIDI: ' + e.message, 'sys');
  }
}

function updateMIDIPortList() {
  const sel = document.getElementById('midi-port-select');
  if (!sel || !midiAccess) return;
  const prev = sel.value;
  sel.innerHTML = '<option value="">— port MIDI —</option>';
  midiAccess.outputs.forEach((port, id) => {
    const opt = document.createElement('option');
    opt.value = id; opt.textContent = port.name;
    if (port.state === 'connected') sel.appendChild(opt);
  });
  if (prev && sel.querySelector(`[value="${prev}"]`)) sel.value = prev;
  else if (midiAccess.outputs.size > 0) sel.value = [...midiAccess.outputs.keys()][0];
  selectMIDIPort();
}

function selectMIDIPort() {
  const sel = document.getElementById('midi-port-select');
  const id = sel?.value;
  midiOutput = (id && midiAccess) ? midiAccess.outputs.get(id) : null;
  const dot = document.getElementById('midi-status-dot');
  const txt = document.getElementById('midi-status-text');
  if (midiOutput) {
    if (dot) dot.style.background = 'var(--green)';
    if (txt) txt.textContent = midiOutput.name;
  } else {
    if (dot) dot.style.background = 'var(--border-h)';
    if (txt) txt.textContent = midiAccess ? 'selecciona port' : 'MIDI: desconnectat';
  }
}

function midiNoteOn(ch, note, vel) {
  if (!midiOutput) return;
  note = Math.max(0, Math.min(127, Math.round(note)));
  vel  = Math.max(0, Math.min(127, Math.round(vel)));
  midiOutput.send([0x90 | (ch - 1), note, vel]);
}
function midiNoteOff(ch, note) {
  if (!midiOutput) return;
  midiOutput.send([0x80 | (ch - 1), Math.max(0, Math.min(127, Math.round(note))), 0]);
}
function midiCC(ch, cc, val) {
  if (!midiOutput) return;
  midiOutput.send([0xB0 | (ch - 1), cc & 127, val & 127]);
}
function midiPC(ch, prog) {
  if (!midiOutput) return;
  midiOutput.send([0xC0 | (ch - 1), prog & 127]);
}
function midiPB(ch, val) {
  if (!midiOutput) return;
  const v = Math.max(0, Math.min(16383, Math.round((val + 1) * 8192)));
  midiOutput.send([0xE0 | (ch - 1), v & 127, (v >> 7) & 127]);
}

const NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
function noteToName(n) { return NOTE_NAMES[((n % 12) + 12) % 12] + (Math.floor(n / 12) - 1); }

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function evalValue(block) {
  if (!block) return 0;
  switch (block.type) {
    case 'math_number': return parseFloat(block.getFieldValue('NUM')) || 0;
    case 'math_arithmetic': {
      const a = await evalValue(block.getInputTargetBlock('A'));
      const b = await evalValue(block.getInputTargetBlock('B'));
      const op = block.getFieldValue('OP');
      return op==='ADD'?a+b: op==='MINUS'?a-b: op==='MULTIPLY'?a*b: op==='DIVIDE'&&b?a/b: op==='POWER'?Math.pow(a,b): a;
    }
    case 'math_random_int': {
      const a = await evalValue(block.getInputTargetBlock('FROM'));
      const b = await evalValue(block.getInputTargetBlock('TO'));
      return Math.floor(Math.random() * (b - a + 1)) + a;
    }
    default: {
      const f = block.getFieldValue('NUM') ?? block.getFieldValue('VALUE') ?? block.getFieldValue('A') ?? '0';
      return parseFloat(f) || 0;
    }
  }
}

async function getVal(block, name, def) {
  const ib = block.getInputTargetBlock(name);
  if (ib) return await evalValue(ib);
  const fv = block.getFieldValue(name);
  return fv !== null ? parseFloat(fv) || 0 : def;
}

function simLog(text, cls = 'note') {
  const out = document.getElementById('simulatorOutput');
  if (!out) return;
  const el = document.createElement('div');
  el.className = `sim-line ${cls}`;
  el.textContent = text;
  out.appendChild(el);
  out.scrollTop = out.scrollHeight;
}

function getChordNotes(name) {
  const R={C:60,D:62,E:64,F:65,G:67,A:69,B:71};
  const m = name.endsWith('m'), root = (R[name[0]]||60) + (m?0:0);
  return m ? [root,root+3,root+7] : [root,root+4,root+7];
}

async function execChain(block) {
  let cur = block;
  while (cur && simulationRunning) {
    await execBlock(cur);
    cur = cur.getNextBlock();
  }
}

async function execBlock(block) {
  if (!block || !simulationRunning) return;
  const ctx = document.getElementById('simulatorCanvas')?.getContext('2d');

  switch (block.type) {
    case 'tecla_play_note': {
      const note = await getVal(block,'NOTE',60);
      const vel  = await getVal(block,'VELOCITY',100);
      const dur  = await getVal(block,'DURATION',0.5);
      midiNoteOn(1, note, vel);
      if (ctx) visualizeNote(ctx, note, vel);
      simLog(`♪ ${noteToName(note)} (${Math.round(note)}) vel:${Math.round(vel)} dur:${dur}s`);
      await sleep(dur * 1000);
      midiNoteOff(1, note);
      break;
    }
    case 'tecla_play_chord': {
      const chord = block.getFieldValue('CHORD') || 'C';
      const dur   = parseFloat(block.getFieldValue('DURATION')) || 1;
      const notes = getChordNotes(chord);
      notes.forEach(n => { midiNoteOn(1,n,90); if(ctx) visualizeNote(ctx,n,90); });
      simLog(`♪ Acord ${chord} (${notes.map(noteToName).join(' ')})`);
      await sleep(dur * 1000);
      notes.forEach(n => midiNoteOff(1,n));
      break;
    }
    case 'tecla_wait': {
      const dur = await getVal(block,'DURATION',1);
      simLog(`⏱ Espera ${dur}s`, 'sys');
      await sleep(dur * 1000);
      break;
    }
    case 'tecla_cc_message': {
      const ch  = parseFloat(block.getFieldValue('CHANNEL'))||1;
      const cc  = parseFloat(block.getFieldValue('CC'))||1;
      const val = parseFloat(block.getFieldValue('VALUE'))||0;
      midiCC(ch, cc, val);
      simLog(`CC${cc}=${val} ch${ch}`, 'sys');
      break;
    }
    case 'tecla_program_change': {
      const ch   = parseFloat(block.getFieldValue('CHANNEL'))||1;
      const prog = parseFloat(block.getFieldValue('PROGRAM'))||0;
      midiPC(ch, prog);
      simLog(`PC:${prog} ch${ch}`, 'sys');
      break;
    }
    case 'tecla_pitch_bend': {
      const ch  = parseFloat(block.getFieldValue('CHANNEL'))||1;
      const val = await getVal(block,'VALUE',0);
      midiPB(ch, val);
      simLog(`PB:${val} ch${ch}`, 'sys');
      break;
    }
    case 'controls_repeat':
    case 'controls_repeat_ext': {
      const times = await getVal(block,'TIMES',1);
      const inner = block.getInputTargetBlock('DO');
      for (let i=0; i<Math.min(times,128) && simulationRunning; i++) await execChain(inner);
      break;
    }
    case 'controls_forEach':
    case 'controls_for': {
      const from_ = await getVal(block,'FROM',0);
      const to_   = await getVal(block,'TO',10);
      const by_   = await getVal(block,'BY',1) || 1;
      const inner = block.getInputTargetBlock('DO');
      for (let i=from_; i<=to_ && simulationRunning; i+=by_) await execChain(inner);
      break;
    }
    case 'controls_whileUntil': {
      const inner = block.getInputTargetBlock('DO');
      let guard = 0;
      while (simulationRunning && guard++ < 64) { await execChain(inner); }
      break;
    }
    default: {
      const inner = block.getInputTargetBlock('DO') || block.getInputTargetBlock('BODY') || block.getInputTargetBlock('STACK');
      if (inner) await execChain(inner);
      break;
    }
  }
}

// ── Simulator ─────────────────────────────────────────────────
async function runSimulation() {
  if (simulationRunning) return;
  simulationRunning = true;
  document.getElementById('btn-simulate').disabled = true;
  document.getElementById('btn-stop-sim').disabled = false;

  const canvas = document.getElementById('simulatorCanvas');
  const ctx = canvas.getContext('2d');
  activeVisuals = [];
  document.getElementById('simulatorOutput').innerHTML = '';

  simLog('▶ Inici', 'sys');
  if (midiOutput) simLog(`MIDI → ${midiOutput.name}`, 'sys');
  else simLog('Sense MIDI (connecta un port al panell)', 'sys');

  initVisualizer(ctx);

  const topBlocks = workspace.getTopBlocks(true);
  if (topBlocks.length === 0) { simLog('Cap bloc al workspace', 'sys'); }
  for (const block of topBlocks) {
    if (!simulationRunning) break;
    await execChain(block);
  }

  if (simulationRunning) {
    simLog('▣ Completat', 'sys');
    stopSimulation();
  }
}

function stopSimulation() {
  simulationRunning = false;
  document.getElementById('btn-simulate').disabled = false;
  document.getElementById('btn-stop-sim').disabled = true;
  simLog('■ Aturat', 'sys');
  setStatus('Llest per programar');
}

function initVisualizer(ctx) {
  const canvas = ctx.canvas;
  const bg = getComputedStyle(document.body).getPropertyValue('--bg').trim() || '#0a0a0a';
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  function render() {
    if (!simulationRunning) return;
    ctx.fillStyle = 'rgba(0,0,0,0.12)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    activeVisuals.forEach((v, i) => {
      ctx.beginPath();
      ctx.arc(v.x, v.y, v.life * 1.5, 0, Math.PI * 2);
      ctx.fillStyle = v.color;
      ctx.globalAlpha = v.life / 25;
      ctx.fill();
      ctx.globalAlpha = 1;
      v.life -= 0.6;
      if (v.life <= 0) activeVisuals.splice(i, 1);
    });
    requestAnimationFrame(render);
  }
  render();
}

function visualizeNote(ctx, note, vel) {
  const colors = ['#f472b6','#a78bfa','#60a5fa','#34d399','#fbbf24','#fb923c','#e879f9','#2dd4bf'];
  const canvas = ctx.canvas;
  const x = ((note - 21) / 87) * (canvas.width - 40) + 20;
  const y = Math.random() * (canvas.height - 40) + 20;
  activeVisuals.push({ x, y, color: colors[note % colors.length], life: 20 + vel / 5 });
}

// ── Examples ──────────────────────────────────────────────────
function loadExample(type) {
  if (!confirm('Vols carregar l\'exemple? El projecte actual es perdrà.')) return;
  workspace.clear();

  const xmlMap = {
    melody: `<xml><block type="controls_repeat_ext" x="50" y="50"><value name="TIMES"><shadow type="math_number"><field name="NUM">4</field></shadow></value><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">64</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">67</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value></block></next></block></next></block></statement></block></xml>`,
    sequencer: `<xml><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">36</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">120</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value></block></next></block></statement></block></xml>`,
    buttons: `<xml><block type="tecla_on_button_press" x="50" y="50"><field name="BUTTON">0</field><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">127</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value></block></statement></block></xml>`,
    complex: `<xml><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_probability"><value name="PERCENT"><shadow type="math_number"><field name="NUM">80</field></shadow></value><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value></block></statement><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.125</field></shadow></value></block></next></block></statement></block></xml>`
  };

  try {
    const dom = Blockly.utils.xml.textToDom(xmlMap[type] || xmlMap.melody);
    Blockly.Xml.domToWorkspace(dom, workspace);
    currentProject.name = `Exemple ${type}`;
    updateGeneratedCode();
    updateStatusBar();
    toast(`Exemple "${type}" carregat`);
  } catch (e) {
    toast('Error carregant exemple', 'err');
  }
}

// ── Utilities ─────────────────────────────────────────────────
function blobDownload(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function toast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast show${type ? ' ' + type : ''}`;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = 'toast'; }, 2800);
}

function setStatus(msg, type = '') {
  const el = document.getElementById('status-message');
  el.textContent = msg;
  el.className = type || '';
}

// ── Theme system (identical to MacroPad, key: tecla-blk-*) ───
const _THEMES = ['light','neon','warm','purple','ocean','forest','rose','ice','carbon','hc','crepuscle','cosmic','mint','slate','acid','sand'];
const _CUSTOM_KEY = 'tecla-blk-custom-themes';
const _CDEF = { bg:'#0c0c0c', surface:'#141414', surface2:'#1c1c1c', text:'#e0e0e0', accent:'#4a80f0' };
let _activeCustomId = null;

function _darken(hex, f) {
  if (!hex || hex.length < 7) return hex;
  const r=parseInt(hex.slice(1,3),16), g=parseInt(hex.slice(3,5),16), b=parseInt(hex.slice(5,7),16);
  const d = v => Math.round(Math.max(0,Math.min(255,v*f))).toString(16).padStart(2,'0');
  return '#'+d(r)+d(g)+d(b);
}
function _clearVars() {
  ['bg','surface','surface2','surface3','text','text2','text3','accent','accent-d'].forEach(v => document.documentElement.style.removeProperty('--'+v));
}
function _applyVars(v, up=true) {
  const R = document.documentElement;
  R.style.setProperty('--bg', v.bg); R.style.setProperty('--surface', v.surface);
  R.style.setProperty('--surface2', v.surface2); R.style.setProperty('--surface3', _darken(v.surface2,1.15));
  R.style.setProperty('--text', v.text); R.style.setProperty('--text2', _darken(v.text,0.53));
  R.style.setProperty('--text3', _darken(v.text,0.27));
  R.style.setProperty('--accent', v.accent); R.style.setProperty('--accent-d', _darken(v.accent,0.82));
  if (up) for (const k of ['bg','surface','surface2','text','accent']) { const el=document.getElementById('ct-'+k); if(el) el.value=v[k]||''; }
}
function _readPickers() { return Object.fromEntries(['bg','surface','surface2','text','accent'].map(k => [k, document.getElementById('ct-'+k)?.value || _CDEF[k]])); }
function _loadCT() { try { return JSON.parse(localStorage.getItem(_CUSTOM_KEY)||'[]'); } catch { return []; } }
function _saveCT(l) { localStorage.setItem(_CUSTOM_KEY, JSON.stringify(l)); }
function _updateModeIndicator() {
  const ind = document.getElementById('ct-mode-indicator'); if (!ind) return;
  if (_activeCustomId) { const t=_loadCT().find(x=>x.id===_activeCustomId); ind.textContent=t?`Editant: ${t.name}`:'Mode: Nou tema'; ind.style.color='var(--accent)'; }
  else { ind.textContent='Mode: Nou tema'; ind.style.color='var(--text3)'; }
}
function _renderSavedThemes() {
  const container = document.getElementById('theme-cards'); if (!container) return;
  container.querySelectorAll('[data-custom-id]').forEach(el => el.remove());
  _loadCT().forEach(t => {
    const card = document.createElement('div');
    card.className = 'theme-card' + (_activeCustomId===t.id?' active':'');
    card.dataset.customId = t.id;
    card.innerHTML = `<div class="theme-swatches"><span style="background:${t.vars.bg}"></span><span style="background:${t.vars.surface}"></span><span style="background:${t.vars.surface2}"></span><span style="background:${t.vars.accent}"></span></div><div class="theme-card-name">${t.name}</div><span data-del="${t.id}" title="Eliminar" style="position:absolute;top:2px;right:3px;font-size:13px;opacity:0;cursor:pointer;transition:opacity .12s">×</span>`;
    card.addEventListener('mouseenter', () => { card.querySelector('[data-del]').style.opacity='0.7'; });
    card.addEventListener('mouseleave', () => { card.querySelector('[data-del]').style.opacity='0'; });
    card.addEventListener('click', e => {
      if (e.target.dataset.del) {
        const updated = _loadCT().filter(x => x.id !== e.target.dataset.del);
        _saveCT(updated);
        if (_activeCustomId === e.target.dataset.del) { _activeCustomId=null; applyTheme('dark'); }
        _renderSavedThemes(); _updateModeIndicator(); return;
      }
      _activeCustomId = t.id; localStorage.setItem('tecla-blk-custom-active', t.id);
      applyTheme('custom'); _applyVars(t.vars);
      document.getElementById('ct-name').value = t.name;
      _renderSavedThemes(); _updateModeIndicator();
    });
    container.appendChild(card);
  });
}
function applyTheme(name, save=true) {
  _THEMES.forEach(t => document.body.classList.remove('theme-'+t));
  _clearVars();
  if (name === 'custom') {
    const themes = _loadCT(); const t = _activeCustomId ? themes.find(x=>x.id===_activeCustomId) : themes[themes.length-1];
    if (t) _applyVars(t.vars); else _applyVars(_CDEF);
  } else if (name !== 'dark') {
    document.body.classList.add('theme-'+name);
  }
  if (save) localStorage.setItem('tecla-blk-theme', name);
  document.querySelectorAll('.theme-card:not([data-custom-id])').forEach(b => b.classList.toggle('active', b.dataset.theme===name && name!=='custom'));
  if (name !== 'custom') { _activeCustomId=null; _renderSavedThemes(); }
  _updateModeIndicator();
  setTimeout(updateBlocklyColors, 0);
}

function updateBlocklyColors() {
  if (!workspace) return;
  const s = getComputedStyle(document.body);
  const get = v => s.getPropertyValue(v).trim() || getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const bg      = get('--bg')      || '#0a0a0a';
  const surface  = get('--surface') || '#111';
  const surface2 = get('--surface2')|| '#1a1a1a';
  const text     = get('--text')    || '#e0e0e0';

  const newTheme = Blockly.Theme.defineTheme('tecla_dynamic', {
    base: Blockly.Themes.Classic,
    componentStyles: {
      workspaceBackgroundColour: bg,
      toolboxBackgroundColour:   surface,
      toolboxForegroundColour:   text,
      flyoutBackgroundColour:    surface2,
      flyoutForegroundColour:    text,
      flyoutOpacity:             0.97,
      scrollbarColour:           surface2,
      scrollbarOpacity:          0.6
    }
  });
  workspace.setTheme(newTheme);

  const gridColor = surface2;
  document.querySelectorAll('#blocklyDiv svg pattern rect').forEach(r => r.setAttribute('fill', gridColor));
}
function initThemeSystem() {
  document.querySelectorAll('.theme-card').forEach(btn => {
    if (!btn.dataset.customId) btn.addEventListener('click', () => applyTheme(btn.dataset.theme));
  });
  ['bg','surface','surface2','text','accent'].forEach(f => {
    document.getElementById('ct-'+f)?.addEventListener('input', () => {
      _applyVars(_readPickers(),false);
      _THEMES.forEach(t => document.body.classList.remove('theme-'+t));
      setTimeout(updateBlocklyColors, 0);
    });
  });
  document.getElementById('btn-random-theme')?.addEventListener('click', () => {
    const rand = () => '#'+Math.floor(Math.random()*0xFFFFFF).toString(16).padStart(6,'0');
    const v = { bg:rand(), surface:rand(), surface2:rand(), text:rand(), accent:rand() };
    for (const k of ['bg','surface','surface2','text','accent']) { const el=document.getElementById('ct-'+k); if(el) el.value=v[k]; }
    _applyVars(v,false); _THEMES.forEach(t => document.body.classList.remove('theme-'+t));
  });
  document.getElementById('btn-save-custom-theme')?.addEventListener('click', () => {
    const vars=_readPickers(); const rawName=document.getElementById('ct-name')?.value?.trim()||''; const themes=_loadCT();
    if (_activeCustomId) {
      const idx=themes.findIndex(x=>x.id===_activeCustomId);
      if (idx>=0) { themes[idx].vars=vars; if(rawName) themes[idx].name=rawName; _saveCT(themes); applyTheme('custom'); _renderSavedThemes(); _updateModeIndicator(); return; }
    }
    const name=rawName||`Tema ${themes.length+1}`; const id=Date.now().toString(36)+Math.random().toString(36).slice(2,5);
    themes.push({id,name,vars}); _saveCT(themes); _activeCustomId=id; localStorage.setItem('tecla-blk-custom-active',id);
    applyTheme('custom'); _renderSavedThemes(); _updateModeIndicator();
  });
  document.getElementById('btn-reset-custom-theme')?.addEventListener('click', () => {
    _applyVars(_CDEF); document.getElementById('ct-name').value=''; _activeCustomId=null; localStorage.removeItem('tecla-blk-custom-active');
    for (const k of ['bg','surface','surface2','text','accent']) { const el=document.getElementById('ct-'+k); if(el) el.value=_CDEF[k]||''; }
    _updateModeIndicator();
  });
  document.getElementById('btn-new-theme')?.addEventListener('click', () => {
    _activeCustomId=null; localStorage.removeItem('tecla-blk-custom-active');
    _applyVars(_CDEF); document.getElementById('ct-name').value='';
    for (const k of ['bg','surface','surface2','text','accent']) { const el=document.getElementById('ct-'+k); if(el) el.value=_CDEF[k]||''; }
    _renderSavedThemes(); _updateModeIndicator();
  });
  const _st=localStorage.getItem('tecla-blk-theme')||'dark';
  const _sci=localStorage.getItem('tecla-blk-custom-active');
  if (_sci) _activeCustomId=_sci;
  applyTheme(_st,false); _renderSavedThemes(); _updateModeIndicator();
}

// ── Python code generator (depends on generators/*.js) ────────
function generateCompletePythonCode(ws) {
  try {
    if (typeof Blockly.Python === 'undefined') {
      return '# Error: generador Python no carregat';
    }
    return Blockly.Python.workspaceToCode(ws) || '# (sense blocs)';
  } catch (e) {
    console.error('Error generant codi:', e);
    return `# Error generant codi: ${e.message}`;
  }
}

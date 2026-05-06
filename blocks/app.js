/**
 * TECLA Blocks — Web version
 * Substitueix window.teclaAPI per APIs natives del navegador:
 *   - File System Access API per guardar/obrir/pujar al dispositiu
 *   - Blob download per exportar Python
 */

'use strict';

// ── i18n ──────────────────────────────────────────────────────
const _I18N = {
  ca: {
    'btn.back':'Inici','tab.code':'Codi','tab.sim':'Simulador','tab.guide':'Guia','tab.fw':'Firmware',
    'tab.theme':'Aparença','tab.proj':'Projectes','tab.device':'Tecles',
    'btn.new':'Nou','btn.open':'Obrir','btn.save':'Guardar','btn.export':'Exportar .py',
    'btn.connect':'Connectar','btn.upload':'Pujar','btn.copy':'Copiar',
    'btn.simulate':'Executar','btn.stop':'Aturar',
    'code.title':'Codi Python generat','sim.vis':'Visualitzador','sim.out':'Sortida',
    'btn.projsave':'↓ Guardar actual','btn.projimport':'↑ Importar .tblocks','proj.mine':'Els meus projectes'
  },
  es: {
    'btn.back':'Inicio','tab.code':'Código','tab.sim':'Simulador','tab.guide':'Guía','tab.fw':'Firmware',
    'tab.theme':'Apariencia','tab.proj':'Proyectos','tab.device':'Teclas',
    'btn.new':'Nuevo','btn.open':'Abrir','btn.save':'Guardar','btn.export':'Exportar .py',
    'btn.connect':'Conectar','btn.upload':'Subir','btn.copy':'Copiar',
    'btn.simulate':'Ejecutar','btn.stop':'Detener',
    'code.title':'Código Python generado','sim.vis':'Visualizador','sim.out':'Salida',
    'btn.projsave':'↓ Guardar actual','btn.projimport':'↑ Importar .tblocks','proj.mine':'Mis proyectos'
  },
  en: {
    'btn.back':'Home','tab.code':'Code','tab.sim':'Simulator','tab.guide':'Guide','tab.fw':'Firmware',
    'tab.theme':'Appearance','tab.proj':'Projects','tab.device':'Keys',
    'btn.new':'New','btn.open':'Open','btn.save':'Save','btn.export':'Export .py',
    'btn.connect':'Connect','btn.upload':'Upload','btn.copy':'Copy',
    'btn.simulate':'Run','btn.stop':'Stop',
    'code.title':'Generated Python code','sim.vis':'Visualizer','sim.out':'Output',
    'btn.projsave':'↓ Save current','btn.projimport':'↑ Import .tblocks','proj.mine':'My projects'
  }
};
let _curLang = 'ca';
function applyI18n(lang) {
  if (lang) _curLang = lang;
  const dict = _I18N[_curLang] || _I18N.ca;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const v = dict[el.dataset.i18n]; if (v) el.textContent = v;
  });
  const sel = document.getElementById('sel-lang'); if (sel) sel.value = _curLang;
  document.documentElement.lang = _curLang === 'en' ? 'en' : _curLang === 'es' ? 'es' : 'ca';
  localStorage.setItem('tecla-blk-lang', _curLang);
}

let workspace;
let simulationRunning = false;
let activeVisuals = [];
let currentBPM = 120;

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
  _curLang = localStorage.getItem('tecla-blk-lang') || 'ca';
  initBlockly();
  setupTabs();
  setupButtons();
  applyI18n(_curLang);
  setupFileOpen();
  initThemeSystem();
  initDeviceConfig();
  initProjectsLib();
  updateStatusBar();
});

function fixToolboxAlignment() {
  requestAnimationFrame(() => {
    const toolbox = document.querySelector('.blocklyToolboxDiv');
    if (!toolbox) { setTimeout(fixToolboxAlignment, 200); return; }

    console.log('[TECLA] Toolbox row HTML sample:',
      toolbox.querySelector('.blocklyTreeRow')?.outerHTML?.slice(0, 400));

    toolbox.querySelectorAll('.blocklyTreeRow').forEach(row => {
      row.style.setProperty('display', 'flex', 'important');
      row.style.setProperty('flex-direction', 'row', 'important');
      row.style.setProperty('align-items', 'center', 'important');
      row.style.setProperty('min-height', '40px', 'important');
      row.style.setProperty('padding', '0 10px', 'important');
    });

    toolbox.querySelectorAll('.blocklyTreeRowContentContainer').forEach(c => {
      c.style.setProperty('display', 'flex', 'important');
      c.style.setProperty('flex-direction', 'row', 'important');
      c.style.setProperty('align-items', 'center', 'important');
      c.style.setProperty('gap', '8px', 'important');
      c.style.setProperty('flex', '1', 'important');
    });

    toolbox.querySelectorAll('.blocklyTreeLabel').forEach(label => {
      label.style.setProperty('font-size', '15px', 'important');
      label.style.setProperty('font-weight', '600', 'important');
    });
  });
}

function initBlockly() {
  const theme = Blockly.Theme.defineTheme('tecla_dark', {
    base: Blockly.Themes.Classic,
    componentStyles: {
      workspaceBackgroundColour: '#0e0e0e',
      toolboxBackgroundColour: '#111',
      toolboxForegroundColour: '#d0d0d0',
      flyoutBackgroundColour: '#141414',
      flyoutForegroundColour: '#d0d0d0',
      flyoutOpacity: 0.97,
      scrollbarColour: '#333',
      scrollbarOpacity: 0.6
    },
    blockStyles: {
      logic_blocks:  { colourPrimary: '#00e676', colourSecondary: '#00b84e', colourTertiary: '#007a33' },
      loop_blocks:   { colourPrimary: '#ff9100', colourSecondary: '#c87200', colourTertiary: '#9e5800' },
      math_blocks:   { colourPrimary: '#40c8ff', colourSecondary: '#2899c0', colourTertiary: '#1a6e90' },
      text_blocks:   { colourPrimary: '#ffe500', colourSecondary: '#c8b400', colourTertiary: '#9e8e00' },
      list_blocks:   { colourPrimary: '#ff6e40', colourSecondary: '#c24a20', colourTertiary: '#902e10' },
      colour_blocks: { colourPrimary: '#e040fb', colourSecondary: '#a000b8', colourTertiary: '#700080' },
      variable_blocks: { colourPrimary: '#ff6e40', colourSecondary: '#c24a20', colourTertiary: '#902e10' },
      variable_dynamic_blocks: { colourPrimary: '#ff9100', colourSecondary: '#c87200', colourTertiary: '#9e5800' },
      procedure_blocks: { colourPrimary: '#76ff03', colourSecondary: '#4ec200', colourTertiary: '#308e00' }
    },
    categoryStyles: {
      logic_category:     { colour: '#00e676' },
      loop_category:      { colour: '#ff9100' },
      math_category:      { colour: '#40c8ff' },
      text_category:      { colour: '#ffe500' },
      list_category:      { colour: '#ff6e40' },
      colour_category:    { colour: '#e040fb' },
      variable_category:  { colour: '#ff6e40' },
      procedure_category: { colour: '#76ff03' }
    }
  });

  workspace = Blockly.inject('blocklyDiv', {
    toolbox: document.getElementById('toolbox'),
    theme,
    renderer: 'zelos',
    grid: { spacing: 22, length: 4, colour: '#1a1a1a', snap: true },
    zoom: { controls: true, wheel: true, startScale: 0.9, maxScale: 3, minScale: 0.3, scaleSpeed: 1.2 },
    trashcan: true,
    move: { scrollbars: true, drag: true, wheel: true }
  });

  try {
    const flyout = workspace.getFlyout?.();
    if (flyout?.setWidth) flyout.setWidth(248);
  } catch (_) {}

  fixToolboxAlignment();
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
      if (btn.dataset.tab === 'device')   renderDevicePanel();
      if (btn.dataset.tab === 'projects') renderProjectsPanel();
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
  document.getElementById('btn-gen-device-code').addEventListener('click', exportDeviceCode);
  document.getElementById('btn-upload-device-code').addEventListener('click', uploadDeviceCode);
  document.getElementById('btn-proj-save').addEventListener('click', saveCurrentToLib);
  document.getElementById('btn-proj-import').addEventListener('click', () => document.getElementById('proj-import-input').click());
  document.getElementById('proj-import-input').addEventListener('change', importProjectFiles);
  document.getElementById('btn-ex-melody').addEventListener('click', () => loadExample('melody'));
  document.getElementById('btn-ex-sequencer').addEventListener('click', () => loadExample('sequencer'));
  document.getElementById('btn-ex-buttons').addEventListener('click', () => loadExample('buttons'));
  document.getElementById('btn-ex-complex').addEventListener('click', () => loadExample('complex'));

  document.getElementById('sel-lang')?.addEventListener('change', e => applyI18n(e.target.value));
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
    case 'tecla_note_name':
      return parseFloat(block.getFieldValue('NOTE')) || 60;
    case 'tecla_transpose': {
      const tn = await evalValue(block.getInputTargetBlock('NOTE'));
      const ts = await evalValue(block.getInputTargetBlock('SEMITONES'));
      return Math.max(0, Math.min(127, tn + ts));
    }
    case 'tecla_humanize_vel': {
      const hb = await evalValue(block.getInputTargetBlock('BASE_VEL'));
      const hs = await evalValue(block.getInputTargetBlock('SPREAD'));
      return Math.max(1, Math.min(127, Math.round(hb + (Math.random()*2-1)*hs)));
    }
    case 'tecla_get_random_scale_note': {
      const scales={major:[0,2,4,5,7,9,11],minor:[0,2,3,5,7,8,10],pentatonic:[0,2,4,7,9],blues:[0,3,5,6,7,10],dorian:[0,2,3,5,7,9,10]};
      const roots={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
      const sc=scales[block.getFieldValue('SCALE')]||scales.major;
      const rt=roots[block.getFieldValue('ROOT')]||0;
      const oc=await evalValue(block.getInputTargetBlock('OCTAVE'))||4;
      return rt+sc[Math.floor(Math.random()*sc.length)]+(oc+1)*12;
    }
    default: {
      const f = block.getFieldValue('NUM') ?? block.getFieldValue('VALUE') ?? block.getFieldValue('NOTE') ?? block.getFieldValue('A') ?? '0';
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
      const dur = await getVal(block,'TIME',1);
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
    case 'tecla_repeat_forever': {
      const rfInner = block.getInputTargetBlock('DO');
      while (simulationRunning) {
        if (rfInner) await execChain(rfInner);
        await sleep(1);
      }
      break;
    }
    case 'tecla_set_bpm': {
      const bpm = await getVal(block,'BPM',120);
      currentBPM = Math.max(20, Math.min(300, bpm));
      simLog(`⏱ BPM: ${Math.round(currentBPM)}`, 'sys');
      break;
    }
    case 'tecla_wait_beat': {
      const beats = parseFloat(block.getFieldValue('BEATS')) || 1;
      await sleep((60000 / currentBPM) * beats);
      break;
    }
    case 'tecla_drum_hit': {
      const drum = parseInt(block.getFieldValue('DRUM')) || 36;
      const dvel = Math.round(await getVal(block,'VELOCITY',100));
      const drumNames={36:'Kick',38:'Snare',42:'HH↑',46:'HH↓',49:'Crash',51:'Ride',50:'Tom↑',47:'Tom~',45:'Tom↓',39:'Clap',56:'Cow'};
      midiNoteOn(10, drum, dvel);
      simLog(`🥁 ${drumNames[drum]||drum} vel:${dvel}`, 'note');
      await sleep(40);
      midiNoteOff(10, drum);
      break;
    }
    case 'tecla_drum_pattern': {
      const dpDrum = parseInt(block.getFieldValue('DRUM')) || 36;
      const dpPat  = block.getFieldValue('PATTERN') || '1000100010001000';
      const dpStep = await getVal(block,'STEP_DUR',0.125);
      simLog(`🥁 Patró: ${dpPat}`, 'sys');
      for (const s of dpPat) {
        if (!simulationRunning) break;
        if (s==='1') { midiNoteOn(10,dpDrum,100); await sleep(40); midiNoteOff(10,dpDrum); await sleep(Math.max(0,(dpStep*1000)-40)); }
        else { await sleep(dpStep*1000); }
      }
      break;
    }
    case 'tecla_seq_play_steps': {
      const sqNotes = (block.getFieldValue('NOTES')||'60').split(',').map(n=>parseInt(n.trim())).filter(n=>!isNaN(n));
      const sqVel   = Math.max(1,Math.min(127,Math.round(await getVal(block,'VELOCITY',90))));
      const sqDur   = await getVal(block,'STEP_DUR',0.25);
      const sqCtx   = document.getElementById('simulatorCanvas')?.getContext('2d');
      simLog(`🎵 Seqüència [${sqNotes.map(noteToName).join(' ')}]`,'note');
      for (const n of sqNotes) {
        if (!simulationRunning) break;
        midiNoteOn(1,n,sqVel); if(sqCtx) visualizeNote(sqCtx,n,sqVel);
        await sleep(sqDur*1000*0.85); midiNoteOff(1,n); await sleep(sqDur*1000*0.15);
      }
      break;
    }
    case 'tecla_arpeggio_dir': {
      const ACMAP={C:[48,52,55,60],D:[50,54,57,62],E:[52,56,59,64],F:[53,57,60,65],G:[55,59,62,67],A:[57,61,64,69],B:[59,63,66,71],Cm:[48,51,55,60],Dm:[50,53,57,62],Em:[52,55,59,64],Fm:[53,56,60,65],Gm:[55,58,62,67],Am:[57,60,64,69],Bm:[59,62,66,71]};
      const ach=block.getFieldValue('CHORD')||'Am', adir=block.getFieldValue('DIR')||'up';
      const asp=await getVal(block,'SPEED',0.12);
      let an=[...(ACMAP[ach]||ACMAP.Am)];
      if(adir==='down') an=an.reverse();
      if(adir==='updown') an=[...an,...[...an].reverse().slice(1,-1)];
      if(adir==='random') an.sort(()=>Math.random()-.5);
      const arpCtx=document.getElementById('simulatorCanvas')?.getContext('2d');
      simLog(`🎶 Arpegi ${ach} ${adir}`,'note');
      for(const n of an){
        if(!simulationRunning) break;
        midiNoteOn(1,n,90); if(arpCtx) visualizeNote(arpCtx,n,90);
        await sleep(asp*1000*.85); midiNoteOff(1,n); await sleep(asp*1000*.15);
      }
      break;
    }
    case 'tecla_chord_progression': {
      const CPMAP={pop:[[48,52,55],[53,57,60],[55,59,62],[48,52,55]],modern:[[48,52,55],[55,59,62],[57,60,64],[53,57,60]],jazz:[[50,53,57],[55,59,62],[48,52,55]],fifties:[[48,52,55],[57,60,64],[53,57,60],[55,59,62]],blues:[[48,52,55],[53,57,60],[48,52,55],[55,59,62]],rock:[[48,51,55],[46,50,53],[45,48,52],[46,50,53]]};
      const cpProg=block.getFieldValue('PROG')||'modern', cpKey=parseInt(block.getFieldValue('KEY'))||0;
      const cpDur=await getVal(block,'BEATS_DUR',1.5);
      const cpChords=(CPMAP[cpProg]||CPMAP.modern).map(ch=>ch.map(n=>n+cpKey));
      const cpCtx=document.getElementById('simulatorCanvas')?.getContext('2d');
      const cpKeyN={0:'C',2:'D',4:'E',5:'F',7:'G',9:'A',11:'B'};
      simLog(`🎼 Progressió ${cpProg} en ${cpKeyN[cpKey]||'C'}`,'note');
      for(const ch of cpChords){
        if(!simulationRunning) break;
        ch.forEach(n=>{midiNoteOn(1,n,88); if(cpCtx) visualizeNote(cpCtx,n,88);});
        simLog(`  ♪ [${ch.map(noteToName).join(' ')}]`,'note');
        await sleep(cpDur*1000); ch.forEach(n=>midiNoteOff(1,n)); await sleep(20);
      }
      break;
    }
    case 'tecla_midi_cc': {
      const ccT=block.getFieldValue('CC_TYPE');
      const ccN=ccT==='custom'?Math.round(await getVal(block,'CC_NUM',1)):parseInt(ccT);
      const ccV=Math.max(0,Math.min(127,Math.round(await getVal(block,'CC_VAL',64))));
      midiCC(1,ccN,ccV); simLog(`🎛️ CC${ccN}=${ccV}`,'sys'); break;
    }
    case 'tecla_midi_pitch_bend': {
      const pbA=await getVal(block,'AMOUNT',0);
      const pbV=Math.max(0,Math.min(16383,Math.round((pbA+63)*130)));
      if(midiOutput) midiOutput.send([0xE0,pbV&127,(pbV>>7)&127]);
      simLog(`🎵 PitchBend ${pbA>0?'+':''}${Math.round(pbA)}`,'sys'); break;
    }
    case 'tecla_midi_all_notes_off': {
      for(let c=1;c<=16;c++) midiCC(c,123,0);
      simLog('🚨 Panic – notes apagades','sys'); break;
    }
    case 'tecla_midi_sustain': {
      const suS=parseInt(block.getFieldValue('STATE'))||0;
      midiCC(1,64,suS); simLog(`🦶 Sustain ${suS>0?'ON':'OFF'}`,'sys'); break;
    }
    case 'tecla_midi_expression': {
      const exV=Math.max(0,Math.min(127,Math.round(await getVal(block,'VALUE',127))));
      midiCC(1,11,exV); simLog(`🎭 Expressió: ${exV}`,'sys'); break;
    }
    case 'tecla_note_on_only': {
      const nonNote=Math.round(await getVal(block,'NOTE',60));
      const nonVel =Math.round(await getVal(block,'VELOCITY',100));
      const nonCtx =document.getElementById('simulatorCanvas')?.getContext('2d');
      midiNoteOn(1,nonNote,nonVel); if(nonCtx) visualizeNote(nonCtx,nonNote,nonVel);
      simLog(`▶ NoteOn ${noteToName(nonNote)} vel:${nonVel}`,'note'); break;
    }
    case 'tecla_note_off_only': {
      const nofNote=Math.round(await getVal(block,'NOTE',60));
      midiNoteOff(1,nofNote); simLog(`■ NoteOff ${noteToName(nofNote)}`,'sys'); break;
    }
    case 'tecla_crescendo': {
      const crFrom=await getVal(block,'FROM_VAL',0), crTo=await getVal(block,'TO_VAL',127);
      const crDur=await getVal(block,'DURATION',2), crCC=parseInt(block.getFieldValue('CC'))||7;
      const crSt=20, crStT=(crDur*1000)/crSt;
      simLog(`📈 Crescendo CC${crCC} ${Math.round(crFrom)}→${Math.round(crTo)} en ${crDur}s`,'sys');
      for(let i=0;i<=crSt&&simulationRunning;i++){
        midiCC(1,crCC,Math.max(0,Math.min(127,Math.round(crFrom+(i/crSt)*(crTo-crFrom)))));
        await sleep(crStT);
      }
      break;
    }
    case 'tecla_riff_repeat': {
      const rrT=parseInt(block.getFieldValue('TIMES'))||4;
      const rrIn=block.getInputTargetBlock('RIFF');
      simLog(`🔄 Riff × ${rrT}`,'sys');
      for(let i=0;i<rrT&&simulationRunning;i++) if(rrIn) await execChain(rrIn);
      break;
    }
    case 'tecla_key_press': {
      const kpKey = block.getFieldValue('KEY');
      simLog(`⌨️ Tecla: ${kpKey}`, 'sys'); break;
    }
    case 'tecla_key_combo': {
      const kcMod = block.getFieldValue('MODIFIER');
      const kcKey = block.getFieldValue('KEY');
      simLog(`⌨️ Drecera: ${kcMod}+${kcKey}`, 'sys'); break;
    }
    case 'tecla_type_text': {
      const ttText = block.getFieldValue('TEXT');
      simLog(`⌨️ Escrivint: "${ttText}"`, 'sys'); break;
    }
    case 'tecla_media': {
      const mAction = block.getFieldValue('ACTION');
      simLog(`🏛️ Media: ${mAction}`, 'sys'); break;
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
  if (topBlocks.length === 0) { simLog('Cap bloc al workspace', 'sys'); stopSimulation(); return; }

  // Prioritzar el bloc que conté tecla_repeat_forever (bucle principal)
  // Si no n'hi ha, agafar el primer bloc top-left
  function chainContains(block, type) {
    let cur = block;
    while (cur) {
      if (cur.type === type) return true;
      const inner = cur.getInputTargetBlock('DO') || cur.getInputTargetBlock('BODY') || cur.getInputTargetBlock('STATEMENT');
      if (inner && chainContains(inner, type)) return true;
      cur = cur.getNextBlock();
    }
    return false;
  }
  const mainBlock = topBlocks.find(b => chainContains(b, 'tecla_repeat_forever')) || topBlocks[0];
  simLog(`▶ Executant cadena principal (${mainBlock.type})`, 'sys');
  await execChain(mainBlock);

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

// ── Projects Library System ─────────────────────────────────────
const _PROJLIB_KEY = 'tecla-blk-projects';
let projectsLib = [];
let _projAssignOpen = null;

const _PROJ_COLORS = ['#f472b6','#60a5fa','#34d399','#fbbf24','#a78bfa','#fb923c','#22d3ee','#e879f9','#4ade80','#f87171'];
function _projColor(name) {
  let h = 0; for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffff;
  return _PROJ_COLORS[h % _PROJ_COLORS.length];
}
function _projId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
function _projDate(iso) {
  try { const d = new Date(iso); return d.toLocaleDateString('ca',{day:'2-digit',month:'2-digit',year:'numeric'}); }
  catch { return ''; }
}

function initProjectsLib() {
  try { projectsLib = JSON.parse(localStorage.getItem(_PROJLIB_KEY)) || []; }
  catch { projectsLib = []; }
}
function _saveProjectsLib() { localStorage.setItem(_PROJLIB_KEY, JSON.stringify(projectsLib)); }

// ── Built-in example presets ──────────────────────────────────
const _BUILTIN_EXAMPLES = [
  { name: 'Pentatònica C', desc: 'Escala pentatònica de Do ascendent en bucle',
    blocks: `<xml xmlns="https://developers.google.com/blockly/xml"><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">90</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">62</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">85</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">64</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">80</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">67</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">75</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">69</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">70</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value></block></next></block></next></block></next></block></next></block></statement></block></xml>` },
  { name: 'Escala La Menor', desc: 'Escala natural de La menor completa',
    blocks: `<xml xmlns="https://developers.google.com/blockly/xml"><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">57</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">88</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">59</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">82</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">78</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">62</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">74</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">64</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">70</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">65</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">66</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">67</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">62</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.4</field></shadow></value><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value></block></next></block></next></block></next></block></next></block></next></block></next></block></statement></block></xml>` },
  { name: 'Acords Pop', desc: 'Progressió clàssica C – Am – F – G',
    blocks: `<xml xmlns="https://developers.google.com/blockly/xml"><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_play_chord"><field name="CHORD">C</field><field name="DURATION">1.5</field><next><block type="tecla_play_chord"><field name="CHORD">Am</field><field name="DURATION">1.5</field><next><block type="tecla_play_chord"><field name="CHORD">F</field><field name="DURATION">1.5</field><next><block type="tecla_play_chord"><field name="CHORD">G</field><field name="DURATION">1.5</field></block></next></block></next></block></next></block></statement></block></xml>` },
  { name: 'Arpegi La Menor', desc: 'Arpegi trencat ascendent i descendent de Am',
    blocks: `<xml xmlns="https://developers.google.com/blockly/xml"><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">57</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">85</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.3</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">80</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.3</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">64</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">75</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.3</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">69</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">70</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.3</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">64</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">73</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.3</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">68</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.3</field></shadow></value><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value></block></next></block></next></block></next></block></next></block></next></block></statement></block></xml>` },
  { name: 'Jazz II-V-I', desc: 'Progressió de jazz Dm – G – C',
    blocks: `<xml xmlns="https://developers.google.com/blockly/xml"><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_play_chord"><field name="CHORD">Dm</field><field name="DURATION">1</field><next><block type="tecla_play_chord"><field name="CHORD">G</field><field name="DURATION">1</field><next><block type="tecla_play_chord"><field name="CHORD">C</field><field name="DURATION">2</field><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value></block></next></block></next></block></next></block></statement></block></xml>` },
  { name: 'Ambient Capes', desc: 'Notes llargues i atmosfèriques, tempo lent',
    blocks: `<xml xmlns="https://developers.google.com/blockly/xml"><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">48</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">55</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">3.0</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">55</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">45</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">3.0</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">40</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">4.0</field></shadow></value><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value></block></next></block></next></block></next></block></statement></block></xml>` },
  { name: 'Ràfega Cromàtica', desc: 'Pujada cromàtica ràpida de 8 semitons',
    blocks: `<xml xmlns="https://developers.google.com/blockly/xml"><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">88</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">61</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">84</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">62</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">80</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">63</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">76</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">64</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">72</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">65</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">68</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">66</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">64</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">67</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.3</field></shadow></value><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.4</field></shadow></value></block></next></block></next></block></next></block></next></block></next></block></next></block></next></block></statement></block></xml>` },
  { name: 'Groove Probabilístic', desc: 'Ritme melòdic amb variació aleatòria',
    blocks: `<xml xmlns="https://developers.google.com/blockly/xml"><block type="tecla_repeat_forever" x="50" y="50"><statement name="DO"><block type="tecla_probability"><value name="PERCENT"><shadow type="math_number"><field name="NUM">80</field></shadow></value><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">95</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value></block></statement><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value><next><block type="tecla_probability"><value name="PERCENT"><shadow type="math_number"><field name="NUM">55</field></shadow></value><statement name="DO"><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">64</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">80</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value></block></statement><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value><next><block type="tecla_play_note"><value name="NOTE"><shadow type="math_number"><field name="NUM">67</field></shadow></value><value name="VELOCITY"><shadow type="math_number"><field name="NUM">88</field></shadow></value><value name="DURATION"><shadow type="math_number"><field name="NUM">0.12</field></shadow></value><next><block type="tecla_wait"><value name="TIME"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value></block></next></block></next></block></next></block></next></block></next></block></statement></block></xml>` }
];
let _exSelected = new Set();

function _renderExamplesSection() {
  const container = document.getElementById('proj-examples-section');
  if (!container) return;
  container.innerHTML = `
    <div class="proj-section">
      <div class="proj-sect-head">
        <span class="proj-sect-title">Exemples disponibles</span>
      </div>
      <p class="proj-sect-desc">Marca per afegir directament a la biblioteca.</p>
      <div class="checklist" id="ex-checklist"></div>
    </div>`;
  const checklist = container.querySelector('#ex-checklist');
  _BUILTIN_EXAMPLES.forEach(ex => {
    const inLib = projectsLib.some(p => p.name === ex.name);
    const label = document.createElement('label');
    label.className = 'cb';
    label.innerHTML = `<input type="checkbox"${inLib ? ' checked disabled' : ''}><span style="${inLib ? 'color:var(--text3)' : ''}" title="${ex.desc}">${ex.name}</span>`;
    if (!inLib) {
      label.querySelector('input').addEventListener('change', e => {
        if (!e.target.checked) return;
        projectsLib.push({ id: _projId(), name: ex.name, source: 'builtin',
          timestamp: new Date().toISOString(),
          tblocks: { name: ex.name, version: '1.0', format: 'legacy', blocks: ex.blocks } });
        _saveProjectsLib();
        renderProjectsPanel();
        toast(`✓ "${ex.name}" afegit a la biblioteca`, 'ok');
      });
    }
    checklist.appendChild(label);
  });
}

function _addExamplesToLib() {
  if (_exSelected.size === 0) { toast('Selecciona almenys un exemple', 'err'); return; }
  let added = 0;
  _BUILTIN_EXAMPLES.forEach(ex => {
    if (!_exSelected.has(ex.name) || projectsLib.some(p => p.name === ex.name)) return;
    projectsLib.push({ id: _projId(), name: ex.name, source: 'builtin', timestamp: new Date().toISOString(),
      tblocks: { name: ex.name, version: '1.0', format: 'legacy', blocks: ex.blocks } });
    added++;
  });
  _exSelected.clear();
  _saveProjectsLib();
  renderProjectsPanel();
  toast(`✓ ${added} exemple${added !== 1 ? 's' : ''} afegit${added !== 1 ? 's' : ''} a la biblioteca`, 'ok');
}

function renderProjectsPanel() {
  _renderExamplesSection();
  const list = document.getElementById('proj-list');
  if (!list) return;
  if (projectsLib.length === 0) {
    list.innerHTML = `<div class="proj-empty"><div class="proj-empty-icon">📂</div><div>Afegeix exemples de dalt o importa fitxers <strong>.tblocks</strong>.</div></div>`;
    return;
  }
  list.innerHTML = '';
  const srcLabel = { import: 'Importat', save: 'Guardat', builtin: 'Exemple' };
  projectsLib.forEach(proj => {
    const card = document.createElement('div');
    card.className = 'proj-card';
    const col = _projColor(proj.name);
    const isAssignOpen = _projAssignOpen === proj.id;
    card.innerHTML = `
      <div class="proj-dot" style="background:${col}"></div>
      <div class="proj-info">
        <div class="proj-name">${proj.name}</div>
        <div class="proj-meta">${srcLabel[proj.source] || 'Guardat'} · ${_projDate(proj.timestamp)}</div>
      </div>
      <div class="proj-actions">
        <button class="btn" data-act="open" title="Carregar al workspace">⇑ Obrir</button>
        <button class="btn" data-act="assign" title="Assignar a un botó del dispositiu" style="color:var(--accent)">→ Botó</button>
        <button class="btn btn-danger" data-act="del" title="Eliminar">✕</button>
      </div>
      ${isAssignOpen ? `<div class="proj-assign-overlay" style="width:100%;margin-top:0">
        <div class="proj-assign-title">Assignar a botó:</div>
        <div class="proj-btn-picker" id="picker-${proj.id}"></div>
      </div>` : ''}`;
    card.style.flexWrap = 'wrap';
    card.querySelector('[data-act="open"]').addEventListener('click', () => _openProjectFromLib(proj.id));
    card.querySelector('[data-act="assign"]').addEventListener('click', e => { e.stopPropagation(); _toggleAssignPicker(proj.id); });
    card.querySelector('[data-act="del"]').addEventListener('click', () => _deleteProjectFromLib(proj.id));
    if (isAssignOpen) _fillAssignPicker(card.querySelector(`#picker-${proj.id}`), proj.id);
    list.appendChild(card);
  });
}

function _toggleAssignPicker(projId) {
  _projAssignOpen = (_projAssignOpen === projId) ? null : projId;
  renderProjectsPanel();
}

function _fillAssignPicker(el, projId) {
  if (!el || !deviceConfig) return;
  deviceConfig.buttons.forEach(btn => {
    const taken = !!btn.project;
    const b = document.createElement('div');
    b.className = `proj-btn-pick${taken ? ' taken' : ''}`;
    b.title = taken ? `Botó ${btn.id}: ${btn.project.name}` : `Botó ${btn.id}: buit`;
    b.textContent = `B${btn.id}`;
    b.addEventListener('click', () => _assignProjToBtn(projId, btn.id));
    el.appendChild(b);
  });
}

function _assignProjToBtn(projId, btnId) {
  const proj = projectsLib.find(p => p.id === projId);
  const btn  = deviceConfig?.buttons.find(b => b.id === btnId);
  if (!proj || !btn) return;
  const xml  = proj.tblocks.format === 'legacy' ? proj.tblocks.blocks : Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(workspace));
  const code = proj.tblocks.pycode || '';
  btn.project = { name: proj.name, xml, code };
  _saveDC();
  _projAssignOpen = null;
  renderProjectsPanel();
  toast(`✓ "${proj.name}" → Botó ${btnId}`, 'ok');
}

function _openProjectFromLib(projId) {
  const proj = projectsLib.find(p => p.id === projId);
  if (!proj) return;
  if (workspace.getAllBlocks(false).length > 0 && !confirm(`Carregar "${proj.name}"? El workspace actual es perdrà.`)) return;
  loadProjectFromText(JSON.stringify(proj.tblocks), proj.name);
  toast(`⇑ "${proj.name}" carregat`, 'ok');
}

function _deleteProjectFromLib(projId) {
  const proj = projectsLib.find(p => p.id === projId);
  if (!proj || !confirm(`Eliminar "${proj.name}" de la biblioteca?`)) return;
  projectsLib = projectsLib.filter(p => p.id !== projId);
  _saveProjectsLib();
  if (_projAssignOpen === projId) _projAssignOpen = null;
  renderProjectsPanel();
  toast(`"${proj.name}" eliminat`);
}

function saveCurrentToLib() {
  if (workspace.getAllBlocks(false).length === 0) { toast('El workspace està buit', 'err'); return; }
  const existing = projectsLib.find(p => p.name === currentProject.name);
  if (existing) {
    if (!confirm(`"${currentProject.name}" ja existeix. Sobreescriure?`)) return;
    projectsLib = projectsLib.filter(p => p.id !== existing.id);
  }
  const xml  = Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(workspace));
  const code = updateGeneratedCode() || '';
  const entry = {
    id: _projId(),
    name: currentProject.name,
    source: 'save',
    timestamp: new Date().toISOString(),
    tblocks: { name: currentProject.name, version: '2.0', format: 'legacy', blocks: xml, pycode: code }
  };
  projectsLib.unshift(entry);
  _saveProjectsLib();
  renderProjectsPanel();
  toast(`✓ "${currentProject.name}" guardat a la biblioteca`, 'ok');
}

async function importProjectFiles(e) {
  const files = Array.from(e.target.files);
  if (!files.length) return;
  let imported = 0, skipped = 0;
  for (const file of files) {
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      if (!data.name || !data.blocks) { skipped++; continue; }
      const existing = projectsLib.find(p => p.name === data.name);
      if (existing) { skipped++; continue; }
      projectsLib.push({
        id: _projId(),
        name: data.name,
        source: 'import',
        timestamp: new Date().toISOString(),
        tblocks: data
      });
      imported++;
    } catch { skipped++; }
  }
  e.target.value = '';
  _saveProjectsLib();
  renderProjectsPanel();
  toast(`✓ ${imported} importat${imported !== 1 ? 's' : ''}${skipped ? ` (${skipped} omesos)` : ''}`, imported ? 'ok' : 'err');
}

// ── Device Configuration System ────────────────────────────────
const _DC_KEY = 'tecla-device-cfg';
let deviceConfig = null;

function _defaultDeviceCfg() {
  return {
    numButtons: 16,
    buttons: Array.from({ length: 16 }, (_, i) => ({
      id: i + 1, name: `Tecla ${i + 1}`, project: null
    })),
    pots: [
      { id: 0, name: 'X', cc: 74, channel: 1, min: 0, max: 127 },
      { id: 1, name: 'Y', cc: 71, channel: 1, min: 0, max: 127 },
      { id: 2, name: 'Z', cc:  7, channel: 1, min: 0, max: 127 }
    ]
  };
}

function initDeviceConfig() {
  try { deviceConfig = JSON.parse(localStorage.getItem(_DC_KEY)) || _defaultDeviceCfg(); }
  catch { deviceConfig = _defaultDeviceCfg(); }
  if (!deviceConfig || !deviceConfig.buttons) deviceConfig = _defaultDeviceCfg();
  while (deviceConfig.buttons.length < 16) {
    const i = deviceConfig.buttons.length;
    deviceConfig.buttons.push({ id: i + 1, name: `Tecla ${i + 1}`, project: null });
  }
  _saveDC();
}

function _saveDC() {
  localStorage.setItem(_DC_KEY, JSON.stringify(deviceConfig));
}

let _dcSel = null; // { type:'btn'|'pot', id:number }

const _CC_NAMES = {
  0:'Bank Sel',1:'Mod Wheel',2:'Breath',4:'Foot',5:'Portamento',7:'Volum',
  8:'Balance',10:'Paneo',11:'Expressió',12:'FX1',13:'FX2',
  16:'GP1',17:'GP2',18:'GP3',19:'GP4',
  64:'Sustain',65:'Portamento',66:'Sostenuto',67:'Soft Ped',68:'Legato',
  71:'Timbre',72:'Release',73:'Attack',74:'Brillantor',75:'Decay',
  76:'Vibrato R',77:'Vibrato D',78:'Vibrato D',
  84:'Portamento',91:'Reverb',92:'Tremolo',93:'Chorus',94:'Detune',95:'Phaser',
  120:'Sounds Off',121:'Reset',123:'Notes Off'
};
function _ccLabel(cc) { return _CC_NAMES[cc] ? _CC_NAMES[cc] : `CC ${cc}`; }

function renderDevicePanel() {
  if (!deviceConfig) return;
  _renderDCHardware();
  _renderDCConfigArea();
  const uploadBtn = document.getElementById('btn-upload-device-code');
  if (uploadBtn) uploadBtn.disabled = !deviceDirHandle;
}

function _renderDCHardware() {
  const potsCol  = document.getElementById('dev-pots-col');
  const keysGrid = document.getElementById('dev-keys-grid');
  if (!potsCol || !keysGrid) return;

  // Pots column
  potsCol.innerHTML = '';
  deviceConfig.pots.forEach(pot => {
    const sel = _dcSel && _dcSel.type === 'pot' && _dcSel.id === pot.id;
    const w = document.createElement('div');
    w.className = `dev-pot-w${sel ? ' selected' : ''}`;
    w.innerHTML = `
      <div class="dev-pot-knob"><div class="dev-pot-indicator"></div></div>
      <span class="dev-pot-lbl">${pot.name}</span>
      <span class="dev-pot-cc">${_ccLabel(pot.cc)}</span>`;
    w.addEventListener('click', () => {
      _dcSel = (sel) ? null : { type: 'pot', id: pot.id };
      _renderDCHardware(); _renderDCConfigArea();
    });
    potsCol.appendChild(w);
  });

  // Keys grid
  keysGrid.innerHTML = '';
  deviceConfig.buttons.forEach(btn => {
    const hp  = !!btn.project;
    const sel = _dcSel && _dcSel.type === 'btn' && _dcSel.id === btn.id;
    const el  = document.createElement('div');
    el.className = `dev-key-btn${hp ? ' assigned' : ''}${sel ? ' selected' : ''}`;
    el.innerHTML = `
      <span class="dev-key-num">${btn.id}</span>
      <span class="dev-key-name">${btn.name}</span>
      ${hp ? `<span class="dev-key-proj">${btn.project.name}</span>` : ''}`;
    el.addEventListener('click', () => {
      _dcSel = (sel) ? null : { type: 'btn', id: btn.id };
      _renderDCHardware(); _renderDCConfigArea();
    });
    keysGrid.appendChild(el);
  });
}

function _renderDCConfigArea() {
  const area = document.getElementById('dev-cfg-area');
  if (!area) return;
  if (!_dcSel) {
    area.innerHTML = `<div class="dev-cfg-hint">← Clica un botó o potenciòmetre per configurar-lo</div>`;
    return;
  }
  if (_dcSel.type === 'btn') {
    const btn = deviceConfig.buttons.find(b => b.id === _dcSel.id);
    if (!btn) return;
    const hp = !!btn.project;
    const libItems = projectsLib.length > 0
      ? projectsLib.map(p => `<div class="dcf-lib-item${btn.project && btn.project.name === p.name ? ' active' : ''}" data-pid="${p.id}">${p.name}</div>`).join('')
      : `<div style="font-size:11px;color:var(--text3);padding:4px 0">Cap projecte a la biblioteca</div>`;
    area.innerHTML = `
      <div class="dev-cfg-head">Botó <span>B${btn.id}</span></div>
      <div class="dev-cfg-name-row">
        <input id="dcf-bname" type="text" value="${btn.name.replace(/"/g,'&quot;')}" maxlength="16" placeholder="Nom del botó" style="width:100%;font-size:11px">
      </div>
      <div class="dev-cfg-proj-info ${hp ? 'has-proj' : 'no-proj'}">
        ${hp ? `📄 ${btn.project.name}` : '— Cap projecte assignat —'}
      </div>
      <div style="font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.06em;margin:6px 0 3px">Tria de la biblioteca</div>
      <div class="dcf-lib-picker">${libItems}</div>
      <div class="dev-cfg-btns">
        ${hp ? `<button class="btn" id="dcf-load">⇑ Carregar al workspace</button><button class="btn btn-danger" id="dcf-clear">✕ Netejar</button>` : ''}
      </div>`;
    area.querySelector('#dcf-bname').addEventListener('change', e => {
      btn.name = e.target.value.trim() || `Botó ${btn.id}`; _saveDC(); _renderDCHardware();
    });
    area.querySelectorAll('.dcf-lib-item').forEach(item => {
      item.addEventListener('click', () => {
        const proj = projectsLib.find(p => p.id === item.dataset.pid);
        if (!proj) return;
        btn.project = { name: proj.name, xml: proj.tblocks.blocks, code: proj.tblocks.pycode || '' };
        _saveDC(); renderDevicePanel();
        toast(`✓ "${proj.name}" → B${btn.id}`, 'ok');
      });
    });
    area.querySelector('#dcf-load')?.addEventListener('click', () => _loadBtnProject(btn.id));
    area.querySelector('#dcf-clear')?.addEventListener('click', () => _clearBtnProject(btn.id));
  } else {
    const pot = deviceConfig.pots.find(p => p.id === _dcSel.id);
    if (!pot) return;
    area.innerHTML = `
      <div class="dev-cfg-head">Potenciòmetre <span>${pot.name}</span></div>
      <div class="dev-pot-fields">
        <div class="dev-pot-field"><label>CC</label><input type="number" id="dcf-pcc" value="${pot.cc}" min="0" max="127"></div>
        <div class="dev-pot-field"><label>Mínim</label><input type="number" id="dcf-pmin" value="${pot.min}" min="0" max="127"></div>
        <div class="dev-pot-field"><label>Màxim</label><input type="number" id="dcf-pmax" value="${pot.max}" min="0" max="127"></div>
        <div class="dev-pot-field"><label>Canal</label><input type="number" id="dcf-pch" value="${pot.channel}" min="1" max="16"></div>
      </div>
      <div style="font-size:10px;color:var(--text3);margin-bottom:8px">${_ccLabel(pot.cc)}</div>
      <div class="dev-cfg-name-row">
        <input id="dcf-pname" type="text" value="${pot.name}" maxlength="8" placeholder="Etiqueta" style="width:100%;font-size:11px">
      </div>`;
    const upd = () => {
      const cc = parseInt(area.querySelector('#dcf-pcc').value) || 0;
      pot.cc      = cc;
      pot.min     = parseInt(area.querySelector('#dcf-pmin').value) || 0;
      pot.max     = parseInt(area.querySelector('#dcf-pmax').value) || 127;
      pot.channel = parseInt(area.querySelector('#dcf-pch').value)  || 1;
      const fn = area.querySelector('div[style*="font-size:10px"]');
      if (fn) fn.textContent = _ccLabel(cc);
      _saveDC(); _renderDCHardware();
    };
    ['#dcf-pcc','#dcf-pmin','#dcf-pmax','#dcf-pch'].forEach(id => area.querySelector(id)?.addEventListener('change', upd));
    area.querySelector('#dcf-pname').addEventListener('change', e => {
      pot.name = e.target.value.trim() || pot.name; _saveDC(); _renderDCHardware();
    });
  }
}

function _assignProject(btnId) {
  if (workspace.getAllBlocks(false).length === 0) {
    toast('El workspace està buit. Afegeix blocs primer.', 'err'); return;
  }
  const xml = Blockly.Xml.workspaceToDom(workspace);
  const xmlText = Blockly.Xml.domToText(xml);
  const code = updateGeneratedCode();
  const btn = deviceConfig.buttons.find(b => b.id === btnId);
  if (!btn) return;
  btn.project = { name: currentProject.name, xml: xmlText, code: code || '' };
  _saveDC();
  renderDevicePanel();
  toast(`✓ "${currentProject.name}" assignat al Botó ${btnId}`, 'ok');
}

function _loadBtnProject(btnId) {
  const btn = deviceConfig.buttons.find(b => b.id === btnId);
  if (!btn || !btn.project) return;
  if (!confirm(`Carregar "${btn.project.name}"? El workspace actual es perdrà.`)) return;
  workspace.clear();
  try {
    const dom = Blockly.utils.xml.textToDom(btn.project.xml);
    Blockly.Xml.domToWorkspace(dom, workspace);
    currentProject.name = btn.project.name;
    codeCache = { hash: null, code: null };
    updateGeneratedCode();
    updateStatusBar();
    toast(`⇑ Carregat: ${btn.project.name}`, 'ok');
  } catch (e) {
    toast('Error carregant projecte', 'err');
  }
}

function _clearBtnProject(btnId) {
  const btn = deviceConfig.buttons.find(b => b.id === btnId);
  if (!btn) return;
  btn.project = null;
  _saveDC();
  renderDevicePanel();
  toast(`Botó ${btnId} netejat`);
}

function _buildDeviceCode() {
  const cfg = deviceConfig;
  const N = cfg.buttons.length;
  let c = `# === TECLA Device Configuration ===\n# Generat per TECLA Blocks\n# Botons assignats: ${cfg.buttons.filter(b=>b.project).map(b=>`B${b.id} → ${b.project.name}`).join(', ') || 'cap'}\n\n`;
  c += `import usb_midi, adafruit_midi, board, digitalio, analogio, time\n`;
  c += `from adafruit_midi.note_on import NoteOn\n`;
  c += `from adafruit_midi.note_off import NoteOff\n`;
  c += `from adafruit_midi.control_change import ControlChange\n\n`;
  c += `_midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)\n\n`;

  const _allCode = cfg.buttons.map(b => b.project?.code || '').join('\n');
  if (_allCode.includes('_keyboard') || _allCode.includes('_layout') || _allCode.includes('_cc.')) {
    c += `import usb_hid\n`;
    c += `from adafruit_hid.keyboard import Keyboard\n`;
    c += `from adafruit_hid.keycode import Keycode\n`;
    c += `from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS\n`;
    c += `from adafruit_hid.consumer_control import ConsumerControl\n`;
    c += `from adafruit_hid.consumer_control_code import ConsumerControlCode\n`;
    c += `_keyboard = Keyboard(usb_hid.devices)\n`;
    c += `_layout = KeyboardLayoutUS(_keyboard)\n`;
    c += `_cc = ConsumerControl(usb_hid.devices)\n\n`;
  }

  // Button GPIO pins (GP0..GP7)
  c += `# Botons (ajusta els pins al teu hardware)\n`;
  c += `_BTN_PINS = [board.GP${Array.from({length:N},(_,i)=>i).join(', board.GP')}]\n`;
  c += `_btns = [digitalio.DigitalInOut(p) for p in _BTN_PINS]\n`;
  c += `for _b in _btns:\n    _b.direction = digitalio.Direction.INPUT\n    _b.pull = digitalio.Pull.UP\n\n`;

  // Pots
  c += `# Potenciòmetres\n`;
  c += `_POT_PINS = [board.A0, board.A1, board.A2]\n`;
  c += `_pots = [analogio.AnalogIn(p) for p in _POT_PINS]\n`;
  c += `_POT_CC  = [${cfg.pots.map(p=>p.cc).join(', ')}]\n`;
  c += `_POT_CH  = [${cfg.pots.map(p=>p.channel-1).join(', ')}]\n`;
  c += `_POT_MIN = [${cfg.pots.map(p=>p.min).join(', ')}]\n`;
  c += `_POT_MAX = [${cfg.pots.map(p=>p.max).join(', ')}]\n\n`;

  // Project functions
  cfg.buttons.forEach((btn, i) => {
    c += `# --- Botó ${btn.id}: ${btn.project ? btn.project.name : 'sense assignar'} ---\n`;
    c += `def _run_${i+1}():\n`;
    if (btn.project && btn.project.code) {
      btn.project.code.split('\n').forEach(line => { c += `    ${line}\n`; });
    } else {
      c += `    pass\n`;
    }
    c += `\n`;
  });

  // Dispatch table
  c += `_PROJECTS = [${Array.from({length:N},(_,i)=>`_run_${i+1}`).join(', ')}]\n\n`;

  // Main loop
  c += `_prev = [True] * ${N}\n`;
  c += `_ppot = [0] * 3\n\n`;
  c += `def _rpot(p, mn, mx):\n    return mn + int((p.value >> 9) * (mx - mn) / 127)\n\n`;
  c += `while True:\n`;
  c += `    for i in range(${N}):\n`;
  c += `        s = _btns[i].value\n`;
  c += `        if not s and _prev[i]: _PROJECTS[i]()\n`;
  c += `        _prev[i] = s\n`;
  c += `    for i in range(3):\n`;
  c += `        v = _rpot(_pots[i], _POT_MIN[i], _POT_MAX[i])\n`;
  c += `        if abs(v - _ppot[i]) > 1:\n`;
  c += `            adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=_POT_CH[i]).send(ControlChange(_POT_CC[i], max(0,min(127,v))))\n`;
  c += `            _ppot[i] = v\n`;
  c += `    time.sleep(0.01)\n`;
  return c;
}

function exportDeviceCode() {
  if (!deviceConfig.buttons.some(b => b.project)) {
    toast('Cap botó té cap projecte assignat', 'err'); return;
  }
  const code = _buildDeviceCode();
  blobDownload(code, 'code.py', 'text/x-python');
  toast('✓ code.py generat i descarregat', 'ok');
}

async function uploadDeviceCode() {
  if (!deviceDirHandle) { toast('Connecta el dispositiu primer', 'err'); return; }
  const code = _buildDeviceCode();
  try {
    const fh = await deviceDirHandle.getFileHandle('code.py', { create: true });
    const w  = await fh.createWritable();
    await w.write(code);
    await w.close();
    toast('✓ code.py pujat al dispositiu', 'ok');
  } catch (e) {
    toast('Error pujant codi', 'err'); console.error(e);
  }
}

// ── Utilities ─────────────────────────────────────────────────────────
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

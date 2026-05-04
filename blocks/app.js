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
  document.getElementById('btn-upload').addEventListener('click', () => openUploadModal());
  document.getElementById('btn-copy-code').addEventListener('click', copyCode);
  document.getElementById('btn-simulate').addEventListener('click', runSimulation);
  document.getElementById('btn-stop-sim').addEventListener('click', stopSimulation);
  document.getElementById('btn-upload-cancel').addEventListener('click', closeUploadModal);
  document.getElementById('btn-upload-confirm').addEventListener('click', uploadToDevice);
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

// ── Upload to device (File System Access API) ─────────────────
function openUploadModal() {
  document.getElementById('upload-modal').classList.add('open');
}
function closeUploadModal() {
  document.getElementById('upload-modal').classList.remove('open');
}

async function uploadToDevice() {
  closeUploadModal();

  if (!('showDirectoryPicker' in window)) {
    toast('El teu navegador no suporta File System Access API. Usa Chrome o Edge.', 'err');
    return;
  }

  try {
    const dirHandle = await window.showDirectoryPicker({
      mode: 'readwrite',
      id: 'circuitpy',
      startIn: 'desktop'
    });

    const code = updateGeneratedCode() || document.getElementById('generatedCode').textContent;

    const fileHandle = await dirHandle.getFileHandle('code.py', { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(code);
    await writable.close();

    deviceDirHandle = dirHandle;
    updateDeviceBadge(dirHandle.name);
    toast(`code.py pujat a ${dirHandle.name}`, 'ok');
    setStatus(`Pujat a ${dirHandle.name}`, 'ok');
  } catch (e) {
    if (e.name !== 'AbortError') { toast('Error pujant al dispositiu', 'err'); console.error(e); }
  }
}

function updateDeviceBadge(name) {
  const badge = document.getElementById('device-badge');
  document.getElementById('device-name').textContent = name || 'desconnectat';
  badge.className = name ? 'device-badge connected' : 'device-badge';
}

// ── Copy code ─────────────────────────────────────────────────
function copyCode() {
  const code = codeCache.code || document.getElementById('generatedCode').textContent;
  navigator.clipboard.writeText(code).then(() => toast('Codi copiat', 'ok')).catch(() => toast('Error copiant', 'err'));
}

// ── Simulator (canvas visualizer, no Python proxy) ────────────
function runSimulation() {
  if (simulationRunning) return;
  simulationRunning = true;
  document.getElementById('btn-simulate').disabled = true;
  document.getElementById('btn-stop-sim').disabled = false;

  const canvas = document.getElementById('simulatorCanvas');
  const ctx = canvas.getContext('2d');
  activeVisuals = [];

  const output = document.getElementById('simulatorOutput');
  output.innerHTML = '<div class="sim-line sys">Simulació iniciada (visualitzador local)</div>';

  const code = updateGeneratedCode() || '';
  const noteMatches = [...code.matchAll(/NoteOn\((\d+)/g)];
  noteMatches.forEach((m, i) => {
    setTimeout(() => {
      if (!simulationRunning) return;
      const note = parseInt(m[1]);
      visualizeNote(ctx, note, 100);
      const line = document.createElement('div');
      line.className = 'sim-line note';
      line.textContent = `♪ Note ${note}`;
      output.appendChild(line);
      output.scrollTop = output.scrollHeight;
    }, i * 400);
  });

  initVisualizer(ctx);
  setStatus('Simulació en curs…');
}

function stopSimulation() {
  simulationRunning = false;
  document.getElementById('btn-simulate').disabled = false;
  document.getElementById('btn-stop-sim').disabled = true;
  const output = document.getElementById('simulatorOutput');
  const line = document.createElement('div');
  line.className = 'sim-line';
  line.textContent = 'Simulació aturada';
  output.appendChild(line);
  setStatus('Llest per programar');
}

function initVisualizer(ctx) {
  const canvas = ctx.canvas;
  function render() {
    if (!simulationRunning) return;
    ctx.fillStyle = 'rgba(0,0,0,0.15)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    activeVisuals.forEach((v, i) => {
      ctx.beginPath();
      ctx.arc(v.x, v.y, v.life * 1.5, 0, Math.PI * 2);
      ctx.fillStyle = v.color;
      ctx.fill();
      v.life -= 0.8;
      if (v.life <= 0) activeVisuals.splice(i, 1);
    });
    requestAnimationFrame(render);
  }
  render();
}

function visualizeNote(ctx, note, vel) {
  const colors = ['#f472b6', '#a78bfa', '#60a5fa', '#34d399', '#fbbf24', '#fb923c', '#e879f9', '#2dd4bf'];
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

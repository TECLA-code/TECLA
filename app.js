/**
 * TECLA Blocks - Lògica principal de l'aplicació
 */

let workspace;
let currentProject = {
  name: 'Projecte sense títol',
  blocks: null,
  savedPath: null
};

// Cache per codi generat
let codeCache = {
  hash: null,
  code: null
};

// Biblioteca de projectes guardats (localStorage)
let savedProjects = [];
try {
  savedProjects = JSON.parse(localStorage.getItem('tecla_saved_projects') || '[]');
} catch (e) { savedProjects = []; }

// Assignació de projectes a tecles 1-16 (localStorage)
// Format: { '1': projectId, '5': projectId, ... }
let keyAssignments = {};
try {
  keyAssignments = JSON.parse(localStorage.getItem('tecla_key_assignments') || '{}');
} catch (e) { keyAssignments = {}; }

// Projecte seleccionat a la llista (per assignar a tecla)
let selectedProjectId = null;

// ==================== INICIALITZACIÓ ====================

/**
 * Funció debounce per optimitzar crides repetitives
 */
function debounce(func, wait = 300) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Calcula hash d'un workspace per detectar canvis
 */
function getWorkspaceHash(workspace) {
  const blocks = workspace.getAllBlocks(false);
  const blockIds = blocks.map(b => b.id).sort().join(',');
  const blockTypes = blocks.map(b => b.type).sort().join(',');
  return `${blockIds}-${blockTypes}`;
}

document.addEventListener('DOMContentLoaded', () => {
  initializeBlockly();
  setupEventListeners();
  updateStatusBar();
  renderProjectsList();
  renderKeyGrid();
  console.log('TECLA Blocks inicialitzat correctament');
});

function initializeBlockly() {
  // Configurar Blockly amb tema fosc
  const theme = Blockly.Theme.defineTheme('tecla_dark', {
    'base': Blockly.Themes.Classic,
    'componentStyles': {
      'workspaceBackgroundColour': '#1E1E1E',
      'toolboxBackgroundColour': '#2E2E2E',
      'toolboxForegroundColour': '#FFFFFF',
      'flyoutBackgroundColour': '#2E2E2E',
      'flyoutForegroundColour': '#CCCCCC',
      'flyoutOpacity': 0.95,
      'scrollbarColour': '#607D8B',
      'scrollbarOpacity': 0.5
    }
  });

  // Crear workspace
  workspace = Blockly.inject('blocklyDiv', {
    toolbox: document.getElementById('toolbox'),
    theme: theme,
    grid: {
      spacing: 20,
      length: 3,
      colour: '#333',
      snap: true
    },
    zoom: {
      controls: true,
      wheel: true,
      startScale: 1.0,
      maxScale: 3,
      minScale: 0.3,
      scaleSpeed: 1.2
    },
    trashcan: true,
    move: {
      scrollbars: true,
      drag: true,
      wheel: true
    }
  });

  // Event listener per actualitzar codi quan canvien els blocs
  workspace.addChangeListener(onWorkspaceChange);

  // Carregar exemple inicial (opcional)
  // loadExampleProgram();
}

function setupEventListeners() {
  // Botons de l'header
  document.getElementById('btn-new').addEventListener('click', newProject);
  document.getElementById('btn-open').addEventListener('click', openProject);
  document.getElementById('btn-save').addEventListener('click', saveProject);
  document.getElementById('btn-export').addEventListener('click', exportPython);
  document.getElementById('btn-upload').addEventListener('click', uploadToDevice);

  // Projectes panel
  document.getElementById('btn-save-to-library').addEventListener('click', saveProjectToLibrary);

  // Tecles panel
  document.getElementById('btn-upload-all').addEventListener('click', uploadAllKeys);

  // Pestanyes del panell lateral
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => switchTab(e.target.dataset.tab));
  });

  // Botons del simulador
  document.getElementById('btn-simulate').addEventListener('click', runSimulation);
  document.getElementById('btn-stop-sim').addEventListener('click', stopSimulation);
  document.getElementById('btn-stop-sim').addEventListener('click', stopSimulation);
  document.getElementById('btn-copy-code').addEventListener('click', copyCodeToClipboard);

  // Exemple Buttons
  const btnExMelody = document.getElementById('btn-ex-melody');
  if (btnExMelody) btnExMelody.addEventListener('click', () => loadExample('melody'));

  const btnExSequencer = document.getElementById('btn-ex-sequencer');
  if (btnExSequencer) btnExSequencer.addEventListener('click', () => loadExample('sequencer'));

  const btnExButtons = document.getElementById('btn-ex-buttons');
  if (btnExButtons) btnExButtons.addEventListener('click', () => loadExample('buttons'));

  const btnExComplex = document.getElementById('btn-ex-complex');
  if (btnExComplex) btnExComplex.addEventListener('click', () => loadExample('complex_synth'));

  const btnExRhythmic = document.getElementById('btn-ex-rhythmic');
  if (btnExRhythmic) btnExRhythmic.addEventListener('click', () => loadExample('mode_rhythmic'));



  // Botó Config MIDI (nou)
  const btnMidiConfig = document.getElementById('btn-midi-config');
  if (btnMidiConfig) {
    btnMidiConfig.addEventListener('click', () => {
      window.teclaAPI.openMidiConfig();
    });
  }

  // Inicialitzar MIDI Proxy (Python)
  console.log('Iniciant connexió amb MIDI Proxy...');

  // Escoltar respostes del Proxy
  window.teclaAPI.onMidiData((data) => {
    console.log('📬 MIDI Proxy:', data);

    if (data.type === 'ports_list') {
      const outputSelect = document.getElementById('midi-output-select');
      const currentVal = outputSelect.value;

      // Netejar menys la opció per defecte
      outputSelect.innerHTML = '<option value="">🔌 Sortida MIDI (Desactivada)</option>';

      const uniquePorts = [...new Set(data.ports)]; // Eliminar duplicats
      uniquePorts.forEach(port => {
        const option = document.createElement('option');
        option.value = port;
        option.textContent = "🎹 " + port;
        outputSelect.appendChild(option);
      });

      // Restaurar selecció si encara existeix
      if (uniquePorts.includes(currentVal)) {
        outputSelect.value = currentVal;
      }
    } else if (data.type === 'connected') {
      showMessage(`Connectat a: ${data.port}`, 'success');

    } else if (data.type === 'midi_event') {
      // Event rebut de l'execució en temps real
      const evt = data.data;
      if (evt.type === 'NoteOn' && evt.velocity > 0) {
        visualizeNote(evt.note, evt.velocity);

        // Log a consola simulada
        const output = document.getElementById('simulatorOutput');
        if (output) {
          const div = document.createElement('div');
          div.style.color = '#E91E63';
          div.innerText = `  ♪ Note ${evt.note}`;
          output.appendChild(div);
          output.scrollTop = output.scrollHeight;
        }
      } else if (evt.type === 'ProgramChange') {
        const output = document.getElementById('simulatorOutput');
        if (output) {
          const instruments = ["Piano", "Guitarra", "Violí", "Trompeta", "Synth", "Bateria"]; // Mapping basic
          output.innerHTML += `<div style="color: #9C27B0">🎷 Instrument: ${evt.patch}</div>`;
          output.scrollTop = output.scrollHeight;
        }
      } else if (evt.type === 'ControlChange') {
        const output = document.getElementById('simulatorOutput');
        if (output) {
          let name = `CC ${evt.control}`;
          let val = evt.value;
          let icon = '🎛️';
          let color = '#2196F3';

          // Mapping standard
          if (evt.control === 7) { name = "Volum"; icon = '🔊'; }
          if (evt.control === 10) { name = "Panning"; icon = '🎧'; }
          if (evt.control === 74) { name = "Filtre Cutoff"; icon = '🎚️'; color = '#FF9800'; }
          if (evt.control === 91) { name = "Reverb"; icon = '🌊'; color = '#9C27B0'; }
          if (evt.control === 12) { name = "Delay Time"; icon = '⏱️'; color = '#9C27B0'; }
          if (evt.control === 13) { name = "Delay Feedback"; icon = '🔁'; color = '#9C27B0'; }

          // Mapping Síntesi Avançada (VSynth)
          if (evt.control === 20) {
            name = "Oscil·lador Wave";
            icon = '🌊';
            const waves = ["Sinusoidal", "Quadrada", "Dent de Serra", "Triangular", "Pols", "Soroll"];
            val = waves[evt.value] || evt.value;
            color = '#E91E63';
          }
          if (evt.control === 21) { name = "Osc. Freqüència"; icon = '📈'; color = '#E91E63'; }
          if (evt.control === 22) { name = "Osc. Amplitud"; icon = '📢'; color = '#E91E63'; }

          if (evt.control === 23) { name = "LFO Rate"; icon = '〰️'; color = '#673AB7'; }
          if (evt.control === 24) { name = "LFO Depth"; icon = '〰️'; color = '#673AB7'; }

          if (evt.control === 25) { name = "Env. Attack"; icon = '📈'; }
          if (evt.control === 26) { name = "Env. Decay"; icon = '📉'; }
          if (evt.control === 27) { name = "Env. Sustain"; icon = '➖'; }

          output.innerHTML += `<div style="color: ${color}">${icon} ${name}: ${val}</div>`;
          output.scrollTop = output.scrollHeight;
        }
      }
    } else if (data.type === 'console_log') {
      const output = document.getElementById('simulatorOutput');
      if (output) {
        output.innerHTML += `<div style="color: #DDD">> ${data.message}</div>`;
        output.scrollTop = output.scrollHeight;
      }
    } else if (data.type === 'error') {
      const output = document.getElementById('simulatorOutput');
      if (output) output.innerHTML += `<div style="color: #F44336">❌ ${data.message}</div>`;
    }
  });

  // Demanar llista inicial
  setTimeout(() => {
    window.teclaAPI.sendMidiCommand({ command: 'list_ports' });
  }, 1000); // Petit delay perquè arrenqui Python

  // Gestió del desplegable
  const outputSelect = document.getElementById('midi-output-select');
  outputSelect.addEventListener('change', () => {
    const portName = outputSelect.value;
    if (portName) {
      window.teclaAPI.sendMidiCommand({ command: 'connect', port: portName });
    } else {
      window.teclaAPI.sendMidiCommand({ command: 'connect', port: null });
    }
  });

  // Listener del Toggle Mode Live
  const liveToggle = document.getElementById('toggle-live-mode');
  if (liveToggle) {
    liveToggle.addEventListener('change', (e) => {
      if (e.target.checked) {
        showMessage('⚡ Mode Live ACTIVAT', 'success');
        runSimulation();
      } else {
        showMessage('Mode Live DESACTIVAT', 'info');
      }
    });
  }
}
// Fi inicialització MIDI

// ==================== GESTIÓ DE WORKSPACE ====================

// Versions debounced
const debouncedUpdateCode = debounce(updateGeneratedCodeCached, 300);

const debouncedUpdateStatus = debounce(updateStatusBar, 100);
const debouncedRunSimulation = debounce(() => {
  console.log("⚡ Auto-Reloading Simulation...");
  restartSimulation();
}, 700);

function onWorkspaceChange(event) {
  // Filtrar només events rellevants
  const relevantEvents = [
    Blockly.Events.BLOCK_CHANGE,
    Blockly.Events.BLOCK_CREATE,
    Blockly.Events.BLOCK_DELETE,
    Blockly.Events.BLOCK_MOVE
  ];

  if (!relevantEvents.includes(event.type)) {
    return; // Ignorar altres events
  }

  // Comprovar si estem en Mode Live
  const liveToggle = document.getElementById('toggle-live-mode');
  if (liveToggle && liveToggle.checked) {
    debouncedRunSimulation();
  }

  // Events que necessiten actualització immediata
  if (event.type === Blockly.Events.BLOCK_DELETE) {
    updateStatusBar(); // Immediat quan s'esborra
  } else {
    debouncedUpdateStatus(); // Debouncing per altres canvis
  }

  // Generació de codi sempre amb debouncing
  debouncedUpdateCode();
}

function updateGeneratedCodeCached() {
  const currentHash = getWorkspaceHash(workspace);

  // Si no ha canviat, usar cache
  if (codeCache.hash === currentHash && codeCache.code !== null) {
    return codeCache.code;
  }

  // Si ha canviat, regenerar
  const code = generateCompletePythonCode(workspace);

  // Actualitzar cache
  codeCache.hash = currentHash;
  codeCache.code = code;

  // Actualitzar UI
  document.getElementById('generatedCode').textContent = code;

  return code;
}

function updateStatusBar() {
  const blocks = workspace.getAllBlocks(false);
  document.getElementById('status-blocks').textContent = `📦 Blocs: ${blocks.length}`;
}

// ==================== GESTIÓ DE PROJECTES ====================

async function newProject() {
  if (confirm('Vols crear un nou projecte? Els canvis no guardats es perdran.')) {
    workspace.clear();
    currentProject = {
      name: 'Projecte sense títol',
      blocks: null,
      savedPath: null
    };
    updateStatusBar();
    showMessage('Nou projecte creat');
  }
}

async function saveProject() {
  try {
    // Nova API: Blockly.serialization (Blockly 10+)
    const state = Blockly.serialization.workspaces.save(workspace);

    const projectData = {
      name: currentProject.name,
      version: '2.0',
      format: 'json',
      blocks: state,
      timestamp: new Date().toISOString(),
      metadata: {
        blockCount: workspace.getAllBlocks(false).length,
        topBlocks: workspace.getTopBlocks(false).length
      }
    };

    const result = await window.teclaAPI.saveProject(projectData);

    if (result.success) {
      currentProject.savedPath = result.filePath;
      showMessage('Projecte guardat correctament');
    } else if (!result.canceled) {
      showMessage('Error guardant el projecte', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showMessage('Error guardant el projecte', 'error');
  }
}

async function openProject() {
  try {
    const result = await window.teclaAPI.openProject();

    if (result.success) {
      const fileData = result.data;

      // DEBUG CRÍTIC (Temporal)
      // alert('FILE DATA TYPE: ' + typeof fileData + '\n\nCONTENT START:\n' + (typeof fileData === 'string' ? fileData.substring(0, 200) : 'OBJECT'));

      console.log('📦 Dades del fitxer rebudes. Iniciant càrrega universal...');

      // Netejar workspace actual
      workspace.clear();

      try {
        let loaded = false;

        // ESTRATÈGIA 1: Format JSON Estàndard (TECLA v2.0)
        if (fileData.format === 'json' && fileData.blocks) {
          console.log('🔹 Detectat format JSON (v2.0). Carregant...');
          Blockly.serialization.workspaces.load(fileData.blocks, workspace);
          loaded = true;
        }

        // ESTRATÈGIA 2: Format XML
        if (!loaded) {
          // ... (XML Logic omitted for brevity, logic remains same) ...
          try {
            if (fileData.blocks && typeof fileData.blocks === 'string' && fileData.blocks.trim().startsWith('<xml')) {
              const dom = Blockly.utils.xml.textToDom(fileData.blocks);
              Blockly.Xml.domToWorkspace(dom, workspace);
              loaded = true;
            } else if (typeof fileData === 'string' && fileData.trim().startsWith('<xml')) {
              const dom = Blockly.utils.xml.textToDom(fileData);
              Blockly.Xml.domToWorkspace(dom, workspace);
              loaded = true;
            }
          } catch (e) { }
        }

        // ESTRATÈGIA 3: Format Python
        if (!loaded && typeof fileData === 'string') {
          console.log('🔍 Analitzant arxiu de text...');

          // Regex tolerant a espais " = " o "="
          const regex = /TECLA_BLOCKS_EMBEDDED_JSON\s*=\s*'''([\s\S]+?)'''/;

          // DIAGNOSTIC ALERT
          const hasMarker = fileData.includes("TECLA_BLOCKS_EMBEDDED_JSON");
          const regexTest = regex.test(fileData);
          if (!regexTest) {
            alert(`DIAGNOSTIC:\nLength: ${fileData.length}\nHas Marker: ${hasMarker}\nRegex Pass: ${regexTest}\nStart: ${fileData.substring(0, 50)}`);
          }

          const embeddedMatch = fileData.match(regex);

          if (embeddedMatch && embeddedMatch[1]) {
            try {
              const jsonContent = JSON.parse(embeddedMatch[1]);
              Blockly.serialization.workspaces.load(jsonContent, workspace);
              loaded = true;
              showMessage("Projecte recuperat de Python");
            } catch (pyErr) {
              console.warn('Error Parsejing JSON del Python:', pyErr);
              alert("Error parsing extracted JSON: " + pyErr.message);
            }
          }
        }

        if (!loaded) {
          throw new Error('Format desconegut. Assegura\'t que és un arxiu .tblocks o .py generat per aquesta app.');
        }

        // Èxit
        currentProject = {
          name: fileData.name || 'Projecte Recuperat',
          blocks: fileData.blocks || null,
          savedPath: result.filePath
        };

        showMessage('✅ Projecte carregat!');
        updateGeneratedCodeCached();

      } catch (loadError) {
        console.error('Error Carregant:', loadError);
        alert('Error: L\'arxiu no és compatible.\n' + loadError.message);
      }

    } else if (!result.canceled) {
      showMessage('Error obrint: ' + result.error, 'error');
    }
  } catch (error) {
    console.error('Error crític:', error);
  }
}

async function exportPython() {
  try {
    const code = generateCompletePythonCode(workspace);
    const result = await window.teclaAPI.exportPython(code, currentProject.name);

    if (result.success) {
      showMessage('Codi Python exportat correctament');
    } else if (!result.canceled) {
      showMessage('Error exportant el codi', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showMessage('Error exportant el codi', 'error');
  }
}

// ==================== UPLOAD AL DISPOSITIU ====================

async function uploadToDevice() {
  try {
    showMessage('Cercant dispositiu TECLA...', 'info');

    const code = generateCompletePythonCode(workspace);
    const result = await window.teclaAPI.uploadToDevice(code, null);

    if (result.success) {
      showMessage('✅ Codi pujat a TECLA correctament!', 'success');
      document.getElementById('status-device').textContent = '📡 Dispositiu: Connectat';

      // Mostrar instruccions
      setTimeout(() => {
        alert('Codi pujat correctament!\n\n' +
          'El teu programa s\'executarà automàticament al dispositiu TECLA.\n' +
          'Si vols aturar-lo, prem Ctrl+C al terminal del dispositiu o desconnecta\'l.');
      }, 500);
    } else {
      showMessage('❌ ' + result.error, 'error');
      document.getElementById('status-device').textContent = '📡 Dispositiu: No connectat';
    }
  } catch (error) {
    console.error('Error:', error);
    showMessage('Error pujant al dispositiu', 'error');
  }
}

// ==================== BIBLIOTECA DE PROJECTES ====================

function saveProjectsToStorage() {
  localStorage.setItem('tecla_saved_projects', JSON.stringify(savedProjects));
}

function saveKeyAssignmentsToStorage() {
  localStorage.setItem('tecla_key_assignments', JSON.stringify(keyAssignments));
}

function generateProjectId() {
  return 'proj_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
}

function saveProjectToLibrary() {
  const nameInput = document.getElementById('project-name-input');
  const name = nameInput.value.trim() || currentProject.name || 'Projecte sense nom';

  const blockState = Blockly.serialization.workspaces.save(workspace);
  const code = generateCompletePythonCode(workspace);

  const project = {
    id: generateProjectId(),
    name: name,
    blocks: blockState,
    code: code,
    savedAt: new Date().toLocaleDateString('ca-ES', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
  };

  savedProjects.unshift(project);
  saveProjectsToStorage();
  renderProjectsList();
  nameInput.value = '';
  showMessage(`💾 Projecte "${name}" desat a la biblioteca`, 'success');
}

function loadProjectFromLibrary(id) {
  const project = savedProjects.find(p => p.id === id);
  if (!project) return;

  if (project.blocks) {
    Blockly.serialization.workspaces.load(project.blocks, workspace);
  }
  currentProject.name = project.name;
  selectedProjectId = id;
  renderProjectsList();
  showMessage(`📂 Projecte "${project.name}" carregat`, 'success');
}

function deleteProjectFromLibrary(id) {
  const project = savedProjects.find(p => p.id === id);
  if (!project) return;
  if (!confirm(`Eliminar el projecte "${project.name}"?`)) return;

  savedProjects = savedProjects.filter(p => p.id !== id);

  // Eliminar de tecles si estava assignat
  for (const key of Object.keys(keyAssignments)) {
    if (keyAssignments[key] === id) delete keyAssignments[key];
  }

  saveProjectsToStorage();
  saveKeyAssignmentsToStorage();
  if (selectedProjectId === id) selectedProjectId = null;
  renderProjectsList();
  renderKeyGrid();
  showMessage(`🗑️ Projecte "${project.name}" eliminat`, 'info');
}

function selectProjectInLibrary(id) {
  selectedProjectId = (selectedProjectId === id) ? null : id;
  renderProjectsList();
}

function renderProjectsList() {
  const list = document.getElementById('projects-list');
  if (!list) return;

  if (savedProjects.length === 0) {
    list.innerHTML = '<div class="empty-state">Cap projecte guardat.<br>Crea blocs i desa el projecte.</div>';
    return;
  }

  list.innerHTML = savedProjects.map(p => `
    <div class="project-item ${selectedProjectId === p.id ? 'selected' : ''}" data-id="${p.id}">
      <div class="project-item-name" title="${p.name}" onclick="selectProjectInLibrary('${p.id}')">${p.name}</div>
      <div class="project-item-date">${p.savedAt || ''}</div>
      <div class="project-item-actions">
        <button class="btn-load" onclick="loadProjectFromLibrary('${p.id}')">Obre</button>
        <button class="btn-load" style="background:#555" onclick="renameProjectInLibrary('${p.id}', this)" title="Reanomenar">✏️</button>
        <button class="btn-delete" onclick="deleteProjectFromLibrary('${p.id}')">✕</button>
      </div>
    </div>
  `).join('');
}

function renameProjectInLibrary(id, btn) {
  const item = btn.closest('.project-item');
  const nameDiv = item.querySelector('.project-item-name');
  const oldName = nameDiv.textContent;
  const input = document.createElement('input');
  input.value = oldName;
  input.className = 'project-name-input';
  input.style.cssText = 'flex:1;font-size:13px;';
  nameDiv.replaceWith(input);
  input.focus();
  input.select();
  const save = () => {
    const newName = input.value.trim() || oldName;
    const proj = savedProjects.find(p => p.id === id);
    if (proj && newName !== proj.name) { proj.name = newName; saveProjectsToStorage(); }
    renderProjectsList();
  };
  input.addEventListener('blur', save);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); save(); }
    if (e.key === 'Escape') { e.preventDefault(); renderProjectsList(); }
  });
}

// ==================== ASSIGNACIÓ DE TECLES ====================

function assignProjectToKey(keyNum) {
  if (!selectedProjectId) {
    showMessage('Selecciona primer un projecte a la pestanya Projectes', 'warning');
    switchTab('projectes');
    return;
  }
  const project = savedProjects.find(p => p.id === selectedProjectId);
  if (!project) return;

  // Regenerate code to ensure it's up to date
  if (project.blocks) {
    Blockly.serialization.workspaces.load(project.blocks, workspace);
    project.code = generateCompletePythonCode(workspace);
    saveProjectsToStorage();
  }

  keyAssignments[String(keyNum)] = selectedProjectId;
  saveKeyAssignmentsToStorage();
  renderKeyGrid();
  showMessage(`🎹 Tecla ${keyNum} assignada al projecte "${project.name}"`, 'success');
}

function unassignKey(keyNum) {
  delete keyAssignments[String(keyNum)];
  saveKeyAssignmentsToStorage();
  renderKeyGrid();
}

function renderKeyGrid() {
  const grid = document.getElementById('keys-grid');
  if (!grid) return;

  let html = '';
  for (let i = 1; i <= 16; i++) {
    const assignedId = keyAssignments[String(i)];
    const assignedProject = assignedId ? savedProjects.find(p => p.id === assignedId) : null;
    const isAssigned = !!assignedProject;
    const projectName = assignedProject ? assignedProject.name : 'Buida';

    html += `
      <div class="key-slot ${isAssigned ? 'assigned' : ''}" onclick="assignProjectToKey(${i})" title="${isAssigned ? 'Tecla ' + i + ': ' + projectName : 'Tecla ' + i + ': clica per assignar projecte seleccionat'}">
        <button class="key-clear-btn" onclick="event.stopPropagation(); unassignKey(${i})" title="Eliminar assignació">✕</button>
        <div class="key-num">${i}</div>
        <div class="key-project-name">${projectName}</div>
      </div>
    `;
  }
  grid.innerHTML = html;
}

// ==================== UPLOAD TOTES LES TECLES ====================

async function uploadAllKeys() {
  const assignments = {};

  for (const [keyStr, projectId] of Object.entries(keyAssignments)) {
    const project = savedProjects.find(p => p.id === projectId);
    if (project && project.code) {
      assignments[keyStr] = { code: project.code, name: project.name };
    }
  }

  if (Object.keys(assignments).length === 0) {
    showMessage('⚠️ No hi ha projectes assignats a cap tecla. Assigna projectes a la pestanya Tecles.', 'warning');
    return;
  }

  showMessage(`⏳ Pujant ${Object.keys(assignments).length} projecte(s) al dispositiu...`, 'info');

  try {
    const result = await window.teclaAPI.uploadKeyAssignments(assignments);

    if (result.success) {
      const fileList = result.uploadedFiles.join(', ');
      showMessage(`✅ ${result.uploadedFiles.length} projecte(s) pujat(s): ${fileList}`, 'success');
      document.getElementById('status-device').textContent = '📡 Dispositiu: Connectat';

      setTimeout(() => {
        alert(`✅ ${result.uploadedFiles.length} projecte(s) pujats al dispositiu!\n\n` +
          `Fitxers: ${fileList}\n\n` +
          `🎮 Per executar:\n` +
          `  1. Desconnecta TECLA del USB\n` +
          `  2. Encén el dispositiu\n` +
          `  3. Mantén la tecla corresponent durant 1.5s\n\n` +
          `💡 Cada tecla executa el seu projecte assignat.`);
      }, 300);
    } else {
      showMessage('❌ ' + result.error, 'error');
      document.getElementById('status-device').textContent = '📡 Dispositiu: No connectat';
    }
  } catch (error) {
    console.error('Error pujant tecles:', error);
    showMessage('❌ Error pujant al dispositiu: ' + error.message, 'error');
  }
}

// ==================== SIMULADOR ====================

let simulationInterval = null;
let simulationRunning = false;

function runSimulation() {
  if (simulationRunning) return;

  simulationRunning = true;
  document.getElementById('btn-simulate').disabled = true;
  document.getElementById('btn-stop-sim').disabled = false;

  // Restore Canvas Visualizer
  const canvas = document.getElementById('simulatorCanvas');
  const ctx = canvas.getContext('2d');
  activeVisuals = []; // Reset visuals
  initVisualizer(ctx);

  const outputDiv = document.getElementById('simulatorOutput');
  outputDiv.innerHTML = '<div style="color: #4CAF50">▶ Simulació iniciada...</div>';
  outputDiv.innerHTML += '<div style="color: #888">⏳ Enviant ordre al proxy...</div>';

  try {
    const code = generateCompletePythonCode(workspace);
    console.log("Generated Python Code:", code);

    // Use generic sendMidiCommand as runSimulation is not in preload
    window.teclaAPI.sendMidiCommand({
      command: 'run_script',
      code: code
    });
    outputDiv.innerHTML += '<div style="color: #888">🚀 Ordre enviada. Esperant resposta...</div>';
  } catch (error) {
    console.error('Error simulació:', error);
    simulationRunning = false;
    document.getElementById('btn-simulate').disabled = false;
    document.getElementById('btn-stop-sim').disabled = true;

    // Fix: Use outputDiv correctly
    outputDiv.innerHTML += `<div style="color: #F44336">❌ Error: ${error.message}</div>`;
  }
}

async function stopSimulation() {
  if (!simulationRunning) return;

  console.log("⏹ Aturant simulació...");

  // Use generic sendMidiCommand
  await window.teclaAPI.sendMidiCommand({ command: 'stop_script' });

  simulationRunning = false;
  document.getElementById('btn-simulate').disabled = false;
  document.getElementById('btn-stop-sim').disabled = true;
  document.getElementById('simulatorOutput').innerHTML += '<div style="color: #FFC107">⏹ Simulació aturada</div>';
}

// Funció per reiniciar (Live Mode)
async function restartSimulation() {
  console.log("♻️ Restarting simulation for Live Mode...");
  if (simulationRunning) {
    await stopSimulation();
    // Petit delay per assegurar neteja de ports MIDI
    await new Promise(r => setTimeout(r, 200));
  }
  runSimulation();
}

// ==================== VISUALITZADOR MIDI (CANVAS) ====================
let activeVisuals = []; // { note, x, y, color, life }

function initVisualizer(ctx) {
  // Bucle de renderitzat
  function render() {
    if (!simulationRunning) return;

    // Fons (fade effect) - Adaptat al tema
    const bgSimColor = getComputedStyle(document.documentElement).getPropertyValue('--bg-simulator').trim();

    // Convertir hex a rgba amb opacitat baixa per l'efecte de rastre
    // Si no és valid hex, fallback a negre
    let fadeColor = 'rgba(0, 0, 0, 0.1)';
    if (bgSimColor.startsWith('#')) {
      const r = parseInt(bgSimColor.slice(1, 3), 16);
      const g = parseInt(bgSimColor.slice(3, 5), 16);
      const b = parseInt(bgSimColor.slice(5, 7), 16);
      fadeColor = `rgba(${r}, ${g}, ${b}, 0.2)`; // Una mica més opac per tapar ràpid
    }

    ctx.fillStyle = fadeColor;
    ctx.fillRect(0, 0, 400, 300);

    // Dibuixar notes actives
    activeVisuals.forEach((v, i) => {
      ctx.beginPath();
      ctx.arc(v.x, v.y, v.life * 2, 0, Math.PI * 2);
      ctx.fillStyle = v.color;
      ctx.fill();

      v.life -= 1; // Decaure
      if (v.life <= 0) activeVisuals.splice(i, 1);
    });

    // Removed "LIVE SIMULATION" text per user request

    requestAnimationFrame(render);
  }
  render();
}

function visualizeNote(note, vel) {
  const colors = ['#FF5252', '#E040FB', '#7C4DFF', '#536DFE', '#40C4FF', '#18FFFF', '#69F0AE', '#FFD740'];
  const color = colors[note % colors.length];

  // Posició basada en la nota (pitch) per X, i aleatòria en Y
  const x = map(note, 21, 108, 20, 380);
  const y = Math.random() * 260 + 20;

  activeVisuals.push({
    note: note,
    x: x,
    y: y,
    color: color,
    life: 30 + (vel / 4) // Mida/durada basada en velocitat
  });
}

// Utilitat
function map(x, in_min, in_max, out_min, out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

function simulateProgram(code, ctx, output) {
  // Netejar canvas amb el color de fons
  const bgSimColor = getComputedStyle(document.documentElement).getPropertyValue('--bg-simulator').trim();
  ctx.fillStyle = bgSimColor || '#000';
  ctx.fillRect(0, 0, 400, 300);

  // Iniciar bucle visual
  activeVisuals = [];
  initVisualizer(ctx);

  output.innerHTML += '<div>🚀 Iniciant motor Python...</div>';

  // Executar codi REAL via Proxy
  window.teclaAPI.sendMidiCommand({
    command: 'run_script',
    code: code
  });
}

function stopSimulation() {
  if (simulationInterval) {
    clearInterval(simulationInterval);
    simulationInterval = null;
  }

  // Aturar script Python
  window.teclaAPI.sendMidiCommand({ command: 'stop_script' });

  simulationRunning = false;
  document.getElementById('btn-simulate').disabled = false;

  const output = document.getElementById('simulatorOutput');
  output.innerHTML += '<div style="color: #FF9800">⏹ Simulació aturada</div>';

  showMessage('Simulació aturada');
}

// ==================== PESTANYES ====================

function switchTab(tabName) {
  // Actualitzar botons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

  // Actualitzar panells
  document.querySelectorAll('.panel-content').forEach(panel => {
    panel.classList.remove('active');
  });
  document.getElementById(`panel-${tabName}`).classList.add('active');
}

// ==================== UTILITATS ====================

function copyCodeToClipboard() {
  // Usar cache si està disponible, sinó llegir del DOM
  const code = codeCache.code || document.getElementById('generatedCode').textContent;

  navigator.clipboard.writeText(code).then(() => {
    showMessage('Codi copiat al portapapers');
  }).catch(() => {
    showMessage('Error copiant el codi', 'error');
  });
}

function showMessage(message, type = 'info') {
  const statusMessage = document.getElementById('status-message');
  statusMessage.textContent = message;

  // Colors segons el tipus
  const colors = {
    'info': '#2196F3',
    'success': '#4CAF50',
    'error': '#F44336',
    'warning': '#FF9800'
  };

  statusMessage.style.color = colors[type] || colors.info;

  // Reset després de 3 segons
  setTimeout(() => {
    statusMessage.textContent = 'Llest per programar!';
    statusMessage.style.color = '#B0B0B0';
  }, 3000);
}


// ==================== DEBUG / SELF-REPAIR ====================

async function generateExampleFileForUser() {
  console.log('🔧 Generant exemple vàlid automàticament...');

  // Netejar i crear un bloc "Hola Món"
  workspace.clear();
  const block = workspace.newBlock('tecla_play_note');
  block.initSvg();
  block.render();
  block.moveBy(100, 100);

  // Serialitzar amb la versió ACTUAL de Blockly
  const state = Blockly.serialization.workspaces.save(workspace);

  const projectData = {
    name: "Projecte Generat Automàticament",
    version: "2.0",
    format: "json",
    blocks: state,
    timestamp: new Date().toISOString()
  };

  console.log('✅ Format Vàlid Generat:', JSON.stringify(state, null, 2));

  // Guardar-ho a disc perquè l'usuari ho pugui obrir
  try {
    const jsonContent = JSON.stringify(projectData, null, 2);
    const blob = new Blob([jsonContent], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "GENERATED_VALID.tblocks";
    a.click();
    console.log('Descarregant arxiu generat...');
  } catch (e) {
    console.error('Error generant:', e);
  }
}

// Exposar per consola
window.generateExample = generateExampleFileForUser;


// ==================== KEYBOARD SHORTCUTS ====================

// Enter key to toggle simulation
document.addEventListener('keydown', (e) => {
  // Ignorar si estem escrivint en un input
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

  if (e.code === 'Enter') { // Changed to Enter per user request in previous task, or Space? 
    // The user asked for "Enter" in previous task. The code I viewed showed 'Space'. I will support Enter too.
    // "Implement Enter Key Shortcut" was a previous task. 
    // Let's support both or just Enter if Space conflicts.
    // Previous code had Space (line 747).
    // I'll add Enter support.
    e.preventDefault();
    if (simulationRunning) {
      stopSimulation();
    } else {
      runSimulation();
    }
  }
});

// ==================== THEME LOGIC ====================
const defaultTheme = {
  '--color-primary': '#2196F3',
  '--color-secondary': '#607D8B', // Default secondary
  '--bg-darker': '#121212',
  '--bg-dark': '#1E1E1E',
  '--text-primary': '#FFFFFF',
  '--bg-workspace': '#1E1E1E', // Default workspace bg
  '--bg-toolbox': '#2E2E2E',  // Default toolbox bg
  '--bg-simulator': '#000000', // Default simulator bg
  '--bg-flyout': '#2E2E2E',    // Default flyout bg
  '--color-scrollbar': '#607D8B' // Default scrollbar color
};

function initTheme() {
  const saveThemeToStorage = (theme) => {
    localStorage.setItem('tecla_theme', JSON.stringify(theme));
  };

  const loadThemeFromStorage = () => {
    return JSON.parse(localStorage.getItem('tecla_theme') || '{}');
  };

  const applyTheme = (themeData) => {
    Object.keys(defaultTheme).forEach(key => {
      const val = themeData[key] || defaultTheme[key];
      document.documentElement.style.setProperty(key, val);

      // Update inputs if they exist
      const inputId = 'input-' + key.replace('--', '');
      const input = document.getElementById(inputId);
      if (input) input.value = val;
    });
  };

  // INITIAL LOAD
  applyTheme(loadThemeFromStorage());

  // Listeners
  const btnTheme = document.getElementById('btn-theme');
  if (btnTheme) btnTheme.addEventListener('click', () => document.getElementById('theme-modal').style.display = 'flex');

  const btnCloseTheme = document.getElementById('btn-close-theme');
  if (btnCloseTheme) btnCloseTheme.addEventListener('click', () => document.getElementById('theme-modal').style.display = 'none');

  const btnResetTheme = document.getElementById('btn-reset-theme');
  if (btnResetTheme) {
    btnResetTheme.addEventListener('click', () => {
      if (confirm('Vols restablir els colors per defecte?')) {
        localStorage.removeItem('tecla_theme');
        applyTheme({});
        showMessage('Tema restablert', 'info');
      }
    });
  }

  // Import/Export Buttons
  const btnExportTheme = document.getElementById('btn-export-theme');
  if (btnExportTheme) {
    btnExportTheme.addEventListener('click', async () => {
      const currentTheme = loadThemeFromStorage();
      const fullTheme = { ...defaultTheme, ...currentTheme };
      const result = await window.teclaAPI.saveThemeFile(fullTheme);
      if (result.success) showMessage('Tema guardat!', 'success');
    });
  }

  const btnImportTheme = document.getElementById('btn-import-theme');
  if (btnImportTheme) {
    btnImportTheme.addEventListener('click', async () => {
      const result = await window.teclaAPI.loadThemeFile();
      if (result.success && result.theme) {
        saveThemeToStorage(result.theme);
        applyTheme(result.theme);
        showMessage('Tema carregat!', 'success');
      }
    });
  }

  window.addEventListener('click', (e) => {
    const modal = document.getElementById('theme-modal');
    if (e.target === modal) modal.style.display = 'none';
  });

  // INPUTS MAPPING
  const inputs = {
    'input-color-primary': '--color-primary',
    'input-color-secondary': '--color-secondary', // Buttons
    'input-bg-darker': '--bg-darker',
    'input-bg-dark': '--bg-dark',                // Sidebar/Panels
    'input-text-primary': '--text-primary',
    'input-bg-workspace': '--bg-workspace',      // Grid area
    'input-bg-toolbox': '--bg-toolbox',          // Toolbox area
    'input-bg-simulator': '--bg-simulator',      // Simulator bg
    'input-bg-flyout': '--bg-flyout',            // Flyout bg
    'input-color-scrollbar': '--color-scrollbar' // Scrollbar handle
  };

  Object.keys(inputs).forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', (e) => {
        const varName = inputs[id];
        const val = e.target.value;
        document.documentElement.style.setProperty(varName, val);

        const currentTheme = loadThemeFromStorage();
        currentTheme[varName] = val;
        saveThemeToStorage(currentTheme);
      });
    }
  });

  // ==================== IPC MENU EVENTS ====================
  // Ensure we don't duplicate listeners if re-run
  // (In a real app, clean up old listeners, but for now we assume simple reload)

  if (window.teclaAPI && window.teclaAPI.onMenuAction) {
    window.teclaAPI.onMenuAction((action) => {
      console.log("Menu Action:", action);
      switch (action) {
        case 'new': newProject(); break;
        case 'open': openProject(); break;
        case 'save': saveProject(); break;
        case 'export': exportPython(); break;
      }
    });

    window.teclaAPI.onMenuThemeLoad((theme) => {
      console.log("Loading theme from file...");
      saveThemeToStorage(theme);
      applyTheme(theme);
      showMessage('Tema carregat!', 'success');
    });

    window.teclaAPI.onMenuThemeReset(() => {
      localStorage.removeItem('tecla_theme');
      applyTheme({});
      showMessage('Tema restablert', 'info');
    });

    window.teclaAPI.onMenuThemeRequestSave(async () => {
      const currentTheme = loadThemeFromStorage();
      // Merge with defaults to ensure complete file
      const fullTheme = { ...defaultTheme, ...currentTheme };

      const result = await window.teclaAPI.saveThemeFile(fullTheme);
      if (result.success) {
        showMessage('Tema guardat correctament', 'success');
      } else if (!result.canceled) {
        showMessage('Error guardant tema', 'error');
      }
    });
  }
}

// Inicialització
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
});
// This code will be appended to app.js
async function loadExample(type) {
  if (!confirm('Vols carregar l\'exemple? El projecte actual es perdrà.')) return;

  workspace.clear();
  let xmlText = '';

  if (type === 'melody') {
    xmlText = `
    <xml>
      <block type="controls_repeat_ext" x="50" y="50">
        <value name="TIMES"><shadow type="math_number"><field name="NUM">4</field></shadow></value>
        <statement name="DO">
          <block type="tecla_play_note">
             <value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value>
             <value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value>
             <value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value>
             <next>
                <block type="tecla_play_note">
                   <value name="NOTE"><shadow type="math_number"><field name="NUM">64</field></shadow></value>
                   <value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value>
                   <value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value>
                   <next>
                      <block type="tecla_play_note">
                         <value name="NOTE"><shadow type="math_number"><field name="NUM">67</field></shadow></value>
                         <value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value>
                         <value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value>
                      </block>
                   </next>
                </block>
             </next>
          </block>
        </statement>
      </block>
    </xml>`;
  } else if (type === 'sequencer') {
    xmlText = `
    <xml>
      <block type="tecla_repeat_forever" x="50" y="50">
        <statement name="DO">
           <block type="tecla_play_note">
             <value name="NOTE"><shadow type="math_number"><field name="NUM">36</field></shadow></value>
             <value name="VELOCITY"><shadow type="math_number"><field name="NUM">120</field></shadow></value>
             <value name="DURATION"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value>
             <next>
                <block type="tecla_wait">
                   <value name="TIME"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value>
                   <next>
                      <block type="tecla_play_note">
                        <value name="NOTE"><shadow type="math_number"><field name="NUM">42</field></shadow></value>
                        <value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value>
                        <value name="DURATION"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value>
                        <next>
                           <block type="tecla_wait">
                              <value name="TIME"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value>
                           </block>
                        </next>
                      </block>
                   </next>
                </block>
             </next>
           </block>
        </statement>
      </block>
    </xml>`;
  } else if (type === 'buttons') {
    xmlText = `
    <xml>
      <block type="tecla_on_button_press" x="50" y="50">
        <field name="BUTTON">0</field>
        <statement name="DO">
          <block type="tecla_play_note">
            <value name="NOTE"><shadow type="math_number"><field name="NUM">60</field></shadow></value>
            <value name="VELOCITY"><shadow type="math_number"><field name="NUM">127</field></shadow></value>
            <value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value>
          </block>
        </statement>
        <next>
            <block type="tecla_on_button_press">
                <field name="BUTTON">1</field>
                <statement name="DO">
                  <block type="tecla_play_note">
                    <value name="NOTE"><shadow type="math_number"><field name="NUM">62</field></shadow></value>
                    <value name="VELOCITY"><shadow type="math_number"><field name="NUM">127</field></shadow></value>
                    <value name="DURATION"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value>
                  </block>
                </statement>
            </block>
        </next>
      </block>
    </xml>`;
  } else if (type === 'complex_synth') {
    xmlText = `
    <xml>
      <block type="tecla_repeat_forever" x="50" y="50">
        <statement name="DO">
           <!-- Generative Melody -->
           <block type="tecla_probability">
             <value name="PERCENT"><shadow type="math_number"><field name="NUM">80</field></shadow></value>
             <statement name="DO">
               <block type="tecla_play_note">
                 <value name="NOTE">
                    <block type="tecla_scale_quantize">
                        <field name="SCALE">minor</field>
                        <field name="ROOT">C</field>
                        <value name="VALUE">
                            <block type="tecla_software_lfo">
                                <value name="RATE"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value>
                                <value name="MIN"><shadow type="math_number"><field name="NUM">48</field></shadow></value>
                                <value name="MAX"><shadow type="math_number"><field name="NUM">72</field></shadow></value>
                            </block>
                        </value>
                    </block>
                 </value>
                 <value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value>
                 <value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value>
               </block>
             </statement>
             <next>
                <block type="tecla_wait">
                    <value name="TIME"><shadow type="math_number"><field name="NUM">0.125</field></shadow></value>
                </block>
             </next>
           </block>
        </statement>
      </block>
    </xml>`;
  }

  if (xmlText) {
    try {
      const dom = Blockly.utils.xml.textToDom(xmlText);
      Blockly.Xml.domToWorkspace(dom, workspace);
      currentProject.name = `Exemple ${type.charAt(0).toUpperCase() + type.slice(1)}`;
      showMessage('Exemple carregat: ' + type);

      // Close side panel if it's annoying, or switch to code tab
      // switchTab('code'); 
    } catch (e) {
      console.error(e);
      showMessage('Error carregant exemple', 'error');
    }
  }
}

/**
 * TECLA Blocks - App educativa per programació visual
 * Main process d'Electron
 */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs').promises;

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    title: 'TECLA Blocks',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    backgroundColor: '#2E3440',
    show: false
  });

  createMenu(mainWindow);

  mainWindow.loadFile('index.html');

  // Mostrar finestra quan estigui llesta
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    startMidiProxy();
  });

  // DevTools en desenvolupament
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Inicialitzar app
app.whenReady().then(createWindow);

// Gestió de finestres per macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC Handlers per comunicació amb renderer

// Guardar projecte
ipcMain.handle('save-project', async (event, projectData) => {
  try {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
      title: 'Guardar Projecte TECLA',
      defaultPath: 'projecte-tecla.tblocks',
      filters: [
        { name: 'TECLA Blocks', extensions: ['tblocks'] },
        { name: 'Tots els arxius', extensions: ['*'] }
      ]
    });

    if (canceled || !filePath) {
      return { success: false, canceled: true };
    }

    await fs.writeFile(filePath, JSON.stringify(projectData, null, 2), 'utf8');
    return { success: true, filePath };
  } catch (error) {
    console.error('Error guardant projecte:', error);
    return { success: false, error: error.message };
  }
});

// Obrir projecte
ipcMain.handle('open-project', async () => {
  try {
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
      title: 'Obrir Projecte TECLA',
      filters: [
        { name: 'Projectes TECLA', extensions: ['tblocks', 'py'] },
        { name: 'Tots els arxius', extensions: ['*'] }
      ],
      properties: ['openFile']
    });

    if (canceled || filePaths.length === 0) {
      return { success: false, canceled: true };
    }

    const content = await fs.readFile(filePaths[0], 'utf8');

    let projectData;
    const isPython = filePaths[0].endsWith('.py');

    if (isPython) {
      console.log('Arxiu Python detectat. Passant contingut directament.');
      projectData = content;
    } else {
      try {
        projectData = JSON.parse(content);
      } catch (parseError) {
        console.log('L\'arxiu no és JSON. Passant contingut en brut al renderer...');
        projectData = content;
      }
    }

    return { success: true, data: projectData, filePath: filePaths[0] };
  } catch (error) {
    console.error('Error obrint projecte:', error);
    return { success: false, error: error.message };
  }
});

// Obrir Configuració MIDI (macOS)
ipcMain.handle('open-midi-config', async () => {
  const { exec } = require('child_process');
  exec('open -a "Audio MIDI Setup"', (error) => {
    if (error) {
      console.error('Error obrint MIDI Setup:', error);
    }
  });
  return { success: true };
});

// ==================== GESTIÓ MIDI PYTHON (PROXY) ====================
let midiProxyProcess = null;
const { spawn } = require('child_process');

function startMidiProxy() {
  if (midiProxyProcess) return;

  const scriptPath = path.join(__dirname, 'midi_proxy.py');
  console.log('Iniciant MIDI Proxy Python:', scriptPath);

  // Executar amb "python3" (assumim que està al path)
  midiProxyProcess = spawn('python3', [scriptPath]);

  midiProxyProcess.stdout.on('data', (data) => {
    try {
      const str = data.toString().trim();
      const rows = str.split('\n');
      rows.forEach(row => {
        if (!row) return;
        const json = JSON.parse(row);
        if (mainWindow) {
          mainWindow.webContents.send('midi-proxy-data', json);
        }
      });
    } catch (e) {
      console.error('Error parsejant output MIDI Proxy:', e);
    }
  });

  midiProxyProcess.stderr.on('data', (data) => {
    console.error('MIDI Proxy Error:', data.toString());
  });

  midiProxyProcess.on('close', (code) => {
    console.log('MIDI Proxy tancat amb codi:', code);
    midiProxyProcess = null;
  });
}

// IPCs per controlar el proxy
ipcMain.handle('midi-proxy-command', async (event, commandData) => {
  if (!midiProxyProcess) startMidiProxy();

  if (midiProxyProcess && midiProxyProcess.stdin) {
    midiProxyProcess.stdin.write(JSON.stringify(commandData) + '\n');
    return { success: true };
  }
  return { success: false, error: "Proxy no iniciat" };
});

app.on('before-quit', () => {
  if (midiProxyProcess) midiProxyProcess.kill();
});

// Exportar codi Python
ipcMain.handle('export-python', async (event, pythonCode, projectName) => {
  try {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
      title: 'Exportar Codi Python',
      defaultPath: `${projectName || 'tecla-program'}.py`,
      filters: [
        { name: 'Python', extensions: ['py'] },
        { name: 'Tots els arxius', extensions: ['*'] }
      ]
    });

    if (canceled || !filePath) {
      return { success: false, canceled: true };
    }

    await fs.writeFile(filePath, pythonCode, 'utf8');
    return { success: true, filePath };
  } catch (error) {
    console.error('Error exportant Python:', error);
    return { success: false, error: error.message };
  }
});

// Llistar dispositius sèrie (per connectar amb TECLA)
ipcMain.handle('list-serial-ports', async () => {
  try {
    const { SerialPort } = require('serialport');
    const ports = await SerialPort.list();
    return {
      success: true,
      ports: ports.map(p => ({
        path: p.path,
        manufacturer: p.manufacturer,
        serialNumber: p.serialNumber,
        productId: p.productId,
        vendorId: p.vendorId
      }))
    };
  } catch (error) {
    console.error('Error llistant ports sèrie:', error);
    return { success: false, error: error.message };
  }
});

// Detectar sistema de launcher
ipcMain.handle('detect-launcher-system', async () => {
  try {
    const circuitPyPath = await findCircuitPythonDrive();

    if (!circuitPyPath) {
      return { success: false, system: 'none' };
    }

    const hasLauncher = await fileExists(path.join(circuitPyPath, 'tecla_main.py'));

    if (!hasLauncher) {
      return { success: true, system: 'simple' };
    }

    // Detectar si és multi-slot (comprovar si existeix launcher amb BUTTONS)
    const launcherPath = path.join(circuitPyPath, 'code.py');
    try {
      const launcherContent = await fs.readFile(launcherPath, 'utf8');
      const isMultiSlot = launcherContent.includes('BUTTONS') &&
        launcherContent.includes('tecla_blocks_1.py');

      // Detectar quins slots estan ocupats
      const slots = {};
      for (let i = 1; i <= 4; i++) {
        const slotFile = path.join(circuitPyPath, `tecla_blocks_${i}.py`);
        slots[i] = await fileExists(slotFile);
      }

      return {
        success: true,
        system: isMultiSlot ? 'multi-slot' : 'single',
        slots: slots
      };
    } catch {
      return { success: true, system: 'single', slots: { 1: await fileExists(path.join(circuitPyPath, 'tecla_blocks.py')) } };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Upload codi al dispositiu TECLA
ipcMain.handle('upload-to-device', async (event, pythonCode, slot = null) => {
  try {
    // Detectar si és un dispositiu CircuitPython (apareix com a drive)
    const circuitPyPath = await findCircuitPythonDrive();

    if (circuitPyPath) {
      // Comprovar si té el launcher instal·lat
      const hasLauncher = await fileExists(path.join(circuitPyPath, 'tecla_main.py'));

      let targetPath, targetFile, message;

      if (hasLauncher) {
        // Detectar sistema multi-slot
        const launcherPath = path.join(circuitPyPath, 'code.py');
        let isMultiSlot = false;

        try {
          const launcherContent = await fs.readFile(launcherPath, 'utf8');
          isMultiSlot = launcherContent.includes('BUTTONS') &&
            launcherContent.includes('tecla_blocks_1.py');
        } catch { }

        if (isMultiSlot && slot) {
          // Sistema multi-slot → guardar al slot específic
          targetFile = `tecla_blocks_${slot}.py`;
          targetPath = path.join(circuitPyPath, targetFile);

          const buttonMap = { 1: '16', 2: '15', 3: '14', 4: '13' };
          message = `✅ Programa pujat al Slot ${slot}!\n\n` +
            `🎮 Per executar el teu programa:\n` +
            `  1. Desconnecta TECLA del USB\n` +
            `  2. Encén el dispositiu\n` +
            `  3. Mantén Botó ${buttonMap[slot]} durant 1.5s\n` +
            `     (El LED piscarà durant la comprovació)\n\n` +
            `💡 Per tornar a TECLA normal:\n` +
            `  Reinicia sense prémer cap botó`;
        } else {
          // Sistema launcher simple → guardar com tecla_blocks.py
          targetFile = 'tecla_blocks.py';
          targetPath = path.join(circuitPyPath, targetFile);
          message = '✅ Programa pujat correctament!\n\n' +
            '🎮 Per executar el teu programa:\n' +
            '  1. Desconnecta TECLA del USB\n' +
            '  2. Encén el dispositiu\n' +
            '  3. Mantén Botó 16 durant 1.5s\n' +
            '     (El LED piscarà durant la comprovació)\n\n' +
            '💡 Per tornar a TECLA normal:\n' +
            '  Reinicia sense prémer cap botó';
        }
      } else {
        // Sistema simple (sense launcher) → guardar com code.py
        targetFile = 'code.py';
        targetPath = path.join(circuitPyPath, targetFile);
        message = '✅ Codi pujat correctament!\n\n' +
          '⚠️ Recomanació: Configura el Launcher\n' +
          'Per no perdre els modes TECLA, consulta\n' +
          'el fitxer SETUP_LAUNCHER.md';
      }

      // Escriure el fitxer
      await fs.writeFile(targetPath, pythonCode, 'utf8');

      return {
        success: true,
        method: hasLauncher ? 'launcher' : 'simple',
        targetFile: targetFile,
        message: message
      };
    }

    // Si no trobem el drive
    return {
      success: false,
      error: 'No s\'ha trobat el dispositiu CIRCUITPY.\n\n' +
        'Connecta el teu TECLA via USB i espera\n' +
        'que aparegui el drive CIRCUITPY.'
    };
  } catch (error) {
    console.error('Error pujant codi:', error);
    return { success: false, error: error.message };
  }
});

// Funció auxiliar per trobar el drive CircuitPython
async function findCircuitPythonDrive() {
  const possiblePaths = await getPlatformSpecificPaths();

  for (const drivePath of possiblePaths) {
    try {
      await fs.access(drivePath);
      // Verificar que té boot_out.txt (característic de CircuitPython)
      const bootOutPath = path.join(drivePath, 'boot_out.txt');
      await fs.access(bootOutPath);

      // Verificar contingut per assegurar que és CircuitPython
      const bootContent = await fs.readFile(bootOutPath, 'utf8');
      if (bootContent.includes('CircuitPython') || bootContent.includes('Adafruit')) {
        return drivePath;
      }
    } catch {
      continue;
    }
  }

  return null;
}

// Upload múltiples projectes als seus slots de tecla corresponents
ipcMain.handle('upload-key-assignments', async (event, assignments) => {
  // assignments = { '1': { code: '...', name: '...' }, '5': { ... }, ... }
  try {
    const circuitPyPath = await findCircuitPythonDrive();

    if (!circuitPyPath) {
      return {
        success: false,
        error: 'No s\'ha trobat el dispositiu CIRCUITPY.\n\nConnecta el teu TECLA via USB i espera\nque aparegui el drive CIRCUITPY.'
      };
    }

    const uploadedFiles = [];

    for (const [keyStr, assignment] of Object.entries(assignments)) {
      const keyNum = parseInt(keyStr, 10);
      if (isNaN(keyNum) || keyNum < 1 || keyNum > 16) continue;

      const filename = `tecla_blocks_${keyNum}.py`;
      const targetPath = path.join(circuitPyPath, filename);
      await fs.writeFile(targetPath, assignment.code, 'utf8');
      uploadedFiles.push(filename);
      console.log(`Projecte "${assignment.name}" pujat com a ${filename}`);
    }

    return {
      success: true,
      uploadedFiles: uploadedFiles,
      message: `✅ ${uploadedFiles.length} projecte(s) pujat(s) correctament!\n\n` +
        `Fitxers: ${uploadedFiles.join(', ')}\n\n` +
        `🎮 Per executar:\n` +
        `  1. Desconnecta TECLA del USB\n` +
        `  2. Encén el dispositiu\n` +
        `  3. Mantén premuda la tecla assignada durant 1.5s`
    };
  } catch (error) {
    console.error('Error pujant assignació de tecles:', error);
    return { success: false, error: error.message };
  }
});

// Funció auxiliar per obtenir paths específics de cada plataforma
async function getPlatformSpecificPaths() {
  const platform = process.platform;

  if (platform === 'darwin') {
    // macOS - escantejar /Volumes
    return await getMacOSPaths();
  } else if (platform === 'win32') {
    // Windows - provar totes les lletres de A: a Z:
    return getWindowsPaths();
  } else {
    // Linux - escantejar /media i /mnt
    return await getLinuxPaths();
  }
}

// macOS: Buscar a /Volumes
async function getMacOSPaths() {
  const volumesPath = '/Volumes';
  const paths = [];

  try {
    const volumes = await fs.readdir(volumesPath);
    for (const volume of volumes) {
      if (volume.includes('CIRCUITPY') || volume.includes('PYBFLASH')) {
        paths.push(path.join(volumesPath, volume));
      }
    }
  } catch (error) {
    console.error('Error llegint /Volumes:', error);
  }

  return paths;
}

// Windows: Provar totes les lletres de drive
function getWindowsPaths() {
  const paths = [];

  // Provar lletres de A: fins Z:
  for (let i = 65; i <= 90; i++) {
    const letter = String.fromCharCode(i);
    paths.push(`${letter}:\\`);
  }

  return paths;
}

// Linux: Buscar a /media i /mnt
async function getLinuxPaths() {
  const paths = [];
  const os = require('os');
  const username = os.userInfo().username;

  const basePaths = [
    '/media',
    `/media/${username}`,
    '/mnt'
  ];

  for (const basePath of basePaths) {
    try {
      const entries = await fs.readdir(basePath);
      for (const entry of entries) {
        if (entry.includes('CIRCUITPY') || entry.includes('PYBFLASH')) {
          paths.push(path.join(basePath, entry));
        }
      }
    } catch {
      continue;
    }
  }

  return paths;
}

// Funció auxiliar per comprovar si un fitxer existeix
async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}
// ==================== MENÚ NATIU ====================
const { Menu } = require('electron');

function createMenu(win) {
  const isMac = process.platform === 'darwin';

  const template = [
    // { role: 'appMenu' }
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),
    // { role: 'fileMenu' }
    {
      label: 'Fitxer',
      submenu: [
        { label: 'Nou Projecte', click: () => win.webContents.send('menu-action', 'new') },
        {
          label: 'Obrir Projecte...', click: () => {
            // Trigger renderer to call openProject logic or handle here?
            // Sending event to renderer is safer to keep logic centralized
            win.webContents.send('menu-action', 'open');
          }
        },
        { label: 'Guardar Projecte', click: () => win.webContents.send('menu-action', 'save') },
        { type: 'separator' },
        { label: 'Exportar Python...', click: () => win.webContents.send('menu-action', 'export') },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },
    // { role: 'editMenu' }
    {
      label: 'Edició',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'delete' },
        { role: 'selectAll' }
      ]
    },
    // { role: 'viewMenu' }
    {
      label: 'Veure',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    // { role: 'windowMenu' }
    {
      label: 'Finestra',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        ...(isMac ? [
          { type: 'separator' },
          { role: 'front' },
          { type: 'separator' },
          { role: 'window' }
        ] : [
          { role: 'close' }
        ])
      ]
    },
    // THEME MENU
    {
      label: 'Tema',
      submenu: [
        {
          label: 'Guardar Tema Actual...',
          click: () => win.webContents.send('menu-theme-request-save')
        },
        {
          label: 'Carregar Tema...',
          click: async () => {
            const { canceled, filePaths } = await dialog.showOpenDialog(win, {
              title: 'Carregar Tema TECLA',
              filters: [{ name: 'JSON Theme', extensions: ['json'] }],
              properties: ['openFile']
            });
            if (!canceled && filePaths.length > 0) {
              try {
                const content = await fs.readFile(filePaths[0], 'utf8');
                const theme = JSON.parse(content);
                win.webContents.send('menu-theme-load', theme);
              } catch (err) {
                console.error("Error loading theme:", err);
              }
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Restablir per defecte',
          click: () => win.webContents.send('menu-theme-reset')
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}


// IPC Handler per guardar tema (rebut des del renderer)
ipcMain.handle('save-theme-file', async (event, themeData) => {
  try {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
      title: 'Guardar Tema TECLA',
      defaultPath: 'tecla_theme.json',
      filters: [{ name: 'JSON Theme', extensions: ['json'] }]
    });

    if (canceled || !filePath) return { success: false, canceled: true };

    await fs.writeFile(filePath, JSON.stringify(themeData, null, 2));
    return { success: true };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

// IPC Handler per carregar tema (rebut des del renderer)
ipcMain.handle('load-theme-file', async () => {
  try {
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
      title: 'Carregar Tema TECLA',
      filters: [{ name: 'JSON Theme', extensions: ['json'] }],
      properties: ['openFile']
    });

    if (canceled || filePaths.length === 0) return { success: false, canceled: true };

    const content = await fs.readFile(filePaths[0], 'utf8');
    const theme = JSON.parse(content);
    return { success: true, theme };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

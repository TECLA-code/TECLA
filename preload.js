/**
 * Preload script - Bridge segur entre main i renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Exposar API segura al renderer
contextBridge.exposeInMainWorld('teclaAPI', {
  // Gestió de projectes
  saveProject: (projectData) => ipcRenderer.invoke('save-project', projectData),
  openProject: () => ipcRenderer.invoke('open-project'),

  // Exportar codi
  exportPython: (pythonCode, projectName) => ipcRenderer.invoke('export-python', pythonCode, projectName),

  // Dispositius
  listSerialPorts: () => ipcRenderer.invoke('list-serial-ports'),
  uploadToDevice: (pythonCode, portPath) => ipcRenderer.invoke('upload-to-device', pythonCode, portPath),
  uploadKeyAssignments: (assignments) => ipcRenderer.invoke('upload-key-assignments', assignments),

  // Utilitats Sistema
  openMidiConfig: () => ipcRenderer.invoke('open-midi-config'),

  // MIDI Proxy (Python)
  sendMidiCommand: (cmd) => ipcRenderer.invoke('midi-proxy-command', cmd),
  onMidiData: (callback) => ipcRenderer.on('midi-proxy-data', (event, data) => callback(data)),

  // Theme Management
  saveThemeFile: (theme) => ipcRenderer.invoke('save-theme-file', theme),
  loadThemeFile: () => ipcRenderer.invoke('load-theme-file'),

  // Menu Events
  onMenuAction: (cb) => ipcRenderer.on('menu-action', (e, action) => cb(action)),
  onMenuThemeRequestSave: (cb) => ipcRenderer.on('menu-theme-request-save', () => cb()),
  onMenuThemeLoad: (cb) => ipcRenderer.on('menu-theme-load', (e, theme) => cb(theme)),
  onMenuThemeReset: (cb) => ipcRenderer.on('menu-theme-reset', () => cb()),
});

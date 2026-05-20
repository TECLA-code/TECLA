/**
 * MILLORA: Migració de Blockly.Xml (deprecated) a Blockly.serialization
 * 
 * Aquest fitxer mostra com migrar el codi antic de Blockly.Xml
 * a la nova API de Blockly.serialization (Blockly 10+)
 */

// ==================== FUNCIONS DE SERIALITZACIÓ ====================

/**
 * Guarda el workspace actual en format JSON modern
 * @param {Blockly.WorkspaceSvg} workspace - Workspace de Blockly
 * @returns {Object} - Estat serialitzat del workspace
 */
function saveWorkspaceModern(workspace) {
  // Nova API - més eficient i amb millor suport
  return Blockly.serialization.workspaces.save(workspace);
}

/**
 * Carrega un workspace des d'un estat serialitzat
 * @param {Object} state - Estat del workspace
 * @param {Blockly.WorkspaceSvg} workspace - Workspace de destí
 */
function loadWorkspaceModern(state, workspace) {
  // Netejar workspace abans de carregar
  workspace.clear();
  
  // Nova API - més robust i ràpida
  Blockly.serialization.workspaces.load(state, workspace);
}

// ==================== FUNCIONS DE COMPATIBILITAT ====================

/**
 * Converteix format XML antic a JSON modern
 * Útil per migrar projectes antics .tblocks
 */
function convertXmlToJson(xmlString, workspace) {
  try {
    // Carregar XML al workspace temporal
    const xml = Blockly.utils.xml.textToDom(xmlString);
    Blockly.Xml.domToWorkspace(xml, workspace);
    
    // Exportar com JSON modern
    const jsonState = Blockly.serialization.workspaces.save(workspace);
    
    return {
      success: true,
      state: jsonState,
      version: '2.0'
    };
  } catch (error) {
    console.error('Error convertint XML a JSON:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// ==================== EXEMPLE D'ÚS ====================

// ANTIC (DEPRECATED) ❌
function saveProjectOld(workspace) {
  const xml = Blockly.Xml.workspaceToDom(workspace);
  const xmlText = Blockly.Xml.domToText(xml);
  
  return {
    name: 'projecte',
    version: '1.0',
    blocks: xmlText,
    timestamp: new Date().toISOString()
  };
}

// NOU (RECOMANAT) ✅
function saveProjectNew(workspace, projectName) {
  const state = Blockly.serialization.workspaces.save(workspace);
  
  return {
    name: projectName,
    version: '2.0',
    format: 'json',
    blocks: state, // Objecte JSON, no string!
    timestamp: new Date().toISOString(),
    metadata: {
      blockCount: workspace.getAllBlocks(false).length,
      topBlocks: workspace.getTopBlocks(false).length
    }
  };
}

// ANTIC (DEPRECATED) ❌
function openProjectOld(projectData, workspace) {
  const xml = Blockly.Xml.textToDom(projectData.blocks);
  workspace.clear();
  Blockly.Xml.domToWorkspace(xml, workspace);
}

// NOU (RECOMANAT) ✅
function openProjectNew(projectData, workspace) {
  workspace.clear();
  
  // Suportar tant format antic com nou
  if (projectData.format === 'json' && typeof projectData.blocks === 'object') {
    // Format nou (v2.0+)
    Blockly.serialization.workspaces.load(projectData.blocks, workspace);
  } else if (typeof projectData.blocks === 'string') {
    // Format antic (v1.0) - convertir
    console.warn('Carregant projecte en format antic. Es convertirà automàticament.');
    const xml = Blockly.utils.xml.textToDom(projectData.blocks);
    Blockly.Xml.domToWorkspace(xml, workspace);
  } else {
    throw new Error('Format de projecte no reconegut');
  }
}

// ==================== EXPORTAR ====================

export {
  saveWorkspaceModern,
  loadWorkspaceModern,
  convertXmlToJson,
  saveProjectNew,
  openProjectNew
};

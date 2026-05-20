/**
 * MILLORA: Millor detecció de dispositius CircuitPython
 * 
 * Soluciona problemes amb la detecció de drives en Windows
 * i suporta múltiples dispositius connectats
 */

const fs = require('fs').promises;
const path = require('path');
const os = require('os');

// ==================== DETECCIÓ MULTIPLATAFORMA ====================

/**
 * Troba TOTS els drives CircuitPython connectats
 * @returns {Promise<Array>} - Array amb paths dels drives trobats
 */
async function findAllCircuitPythonDrives() {
    const platform = os.platform();
    let drives = [];

    if (platform === 'darwin') {
        // macOS
        drives = await findCircuitPyMacOS();
    } else if (platform === 'win32') {
        // Windows
        drives = await findCircuitPyWindows();
    } else {
        // Linux
        drives = await findCircuitPyLinux();
    }

    // Verificar que siguin realment CircuitPython
    const validDrives = [];
    for (const drive of drives) {
        if (await isCircuitPythonDrive(drive)) {
            validDrives.push(drive);
        }
    }

    return validDrives;
}

/**
 * Troba el primer drive CircuitPython (compatibilitat amb codi antic)
 */
async function findCircuitPythonDrive() {
    const drives = await findAllCircuitPythonDrives();
    return drives.length > 0 ? drives[0] : null;
}

// ==================== DETECCIÓ PER PLATAFORMA ====================

/**
 * Troba drives CircuitPython en macOS
 */
async function findCircuitPyMacOS() {
    const volumesPath = '/Volumes';
    const drives = [];

    try {
        const volumes = await fs.readdir(volumesPath);

        for (const volume of volumes) {
            const volumePath = path.join(volumesPath, volume);

            // Buscar noms comuns de CircuitPython
            if (volume.includes('CIRCUITPY') || volume.includes('PYBFLASH')) {
                drives.push(volumePath);
            }
        }
    } catch (error) {
        console.error('Error llegint /Volumes:', error);
    }

    return drives;
}

/**
 * Troba drives CircuitPython en Windows
 * Millora: Escaneja TOTES les lletres possibles
 */
async function findCircuitPyWindows() {
    const drives = [];

    // Provar totes les lletres de A: fins Z:
    for (let i = 65; i <= 90; i++) {
        const letter = String.fromCharCode(i);
        const drivePath = `${letter}:\\`;

        try {
            await fs.access(drivePath);

            // Comprovar si té boot_out.txt
            const bootOutPath = path.join(drivePath, 'boot_out.txt');
            await fs.access(bootOutPath);

            drives.push(drivePath);
        } catch {
            // Drive no existeix o no és CircuitPython
            continue;
        }
    }

    return drives;
}

/**
 * Troba drives CircuitPython en Linux
 */
async function findCircuitPyLinux() {
    const drives = [];
    const possiblePaths = [
        '/media',
        `/media/${os.userInfo().username}`,
        '/mnt'
    ];

    for (const basePath of possiblePaths) {
        try {
            const entries = await fs.readdir(basePath);

            for (const entry of entries) {
                const fullPath = path.join(basePath, entry);

                if (entry.includes('CIRCUITPY') || entry.includes('PYBFLASH')) {
                    drives.push(fullPath);
                }
            }
        } catch {
            continue;
        }
    }

    return drives;
}

// ==================== VERIFICACIÓ ====================

/**
 * Verifica que un path és realment un drive CircuitPython
 */
async function isCircuitPythonDrive(drivePath) {
    try {
        // Comprovar existència de boot_out.txt (característic de CircuitPython)
        const bootOutPath = path.join(drivePath, 'boot_out.txt');
        await fs.access(bootOutPath);

        // Llegir el contingut per verificar
        const bootContent = await fs.readFile(bootOutPath, 'utf8');

        // Comprovar que conté "CircuitPython" o "Adafruit"
        if (bootContent.includes('CircuitPython') || bootContent.includes('Adafruit')) {
            return true;
        }

        return false;
    } catch {
        return false;
    }
}

/**
 * Obté informació detallada d'un drive CircuitPython
 */
async function getCircuitPythonInfo(drivePath) {
    try {
        const bootOutPath = path.join(drivePath, 'boot_out.txt');
        const bootContent = await fs.readFile(bootOutPath, 'utf8');

        // Extreure informació
        const versionMatch = bootContent.match(/CircuitPython\s+([\d.]+)/);
        const boardMatch = bootContent.match(/Board ID:(.+)/);

        return {
            path: drivePath,
            version: versionMatch ? versionMatch[1] : 'Unknown',
            board: boardMatch ? boardMatch[1].trim() : 'Unknown',
            raw: bootContent
        };
    } catch (error) {
        return {
            path: drivePath,
            version: 'Unknown',
            board: 'Unknown',
            error: error.message
        };
    }
}

// ==================== DETECCIÓ AUTOMÀTICA ====================

/**
 * Cerca automàticament dispositius TECLA
 * (identifica per Board ID o altres característiques)
 */
async function findTECLADevices() {
    const allDrives = await findAllCircuitPythonDrives();
    const teclaDevices = [];

    for (const drive of allDrives) {
        const info = await getCircuitPythonInfo(drive);

        // Identificar TECLA per Board ID o altres característiques
        if (info.board && (
            info.board.includes('raspberry_pi_pico') ||
            info.board.includes('TECLA')
        )) {
            teclaDevices.push(info);
        }
    }

    return teclaDevices;
}

// ==================== EXPORTAR ====================

module.exports = {
    findCircuitPythonDrive,
    findAllCircuitPythonDrives,
    isCircuitPythonDrive,
    getCircuitPythonInfo,
    findTECLADevices
};

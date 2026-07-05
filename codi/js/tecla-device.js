/**
 * TECLADevice — File System Access API layer
 * Accés directe al dispositiu CIRCUITPY com a directori
 */
export class TECLADevice {
    constructor() {
        this.rootHandle = null;
        this.name = null;
    }

    async connect() {
        try {
            this.rootHandle = await window.showDirectoryPicker({
                mode: 'readwrite',
                id: 'circuitpy',
                startIn: 'desktop'
            });
            this.name = this.rootHandle.name;
            return { success: true, name: this.name };
        } catch (e) {
            if (e.name === 'AbortError') return { success: false, aborted: true };
            return { success: false, error: e.message };
        }
    }

    disconnect() {
        this.rootHandle = null;
        this.name = null;
    }

    isConnected() {
        return this.rootHandle !== null;
    }

    async isWritable() {
        if (!this.rootHandle) return false;
        try {
            const perm = await this.rootHandle.queryPermission({ mode: 'readwrite' });
            return perm === 'granted';
        } catch {
            return false;
        }
    }

    /** Navega fins al handle d'un directori donat un path relatiu */
    async _getDirHandle(relPath) {
        const parts = relPath.split('/').filter(Boolean);
        let current = this.rootHandle;
        for (const part of parts) {
            current = await current.getDirectoryHandle(part);
        }
        return current;
    }

    async readFile(path) {
        const parts = path.split('/').filter(Boolean);
        let current = this.rootHandle;
        for (let i = 0; i < parts.length - 1; i++) {
            current = await current.getDirectoryHandle(parts[i]);
        }
        const fileHandle = await current.getFileHandle(parts[parts.length - 1]);
        const file = await fileHandle.getFile();
        return await file.text();
    }

    async writeFile(path, content) {
        const parts = path.split('/').filter(Boolean);
        let current = this.rootHandle;
        for (let i = 0; i < parts.length - 1; i++) {
            current = await current.getDirectoryHandle(parts[i], { create: true });
        }
        const fileHandle = await current.getFileHandle(parts[parts.length - 1], { create: true });
        const writable = await fileHandle.createWritable();
        await writable.write(content);
        await writable.close();
    }

    async deleteFile(path) {
        const parts = path.split('/').filter(Boolean);
        let current = this.rootHandle;
        for (let i = 0; i < parts.length - 1; i++) {
            current = await current.getDirectoryHandle(parts[i]);
        }
        await current.removeEntry(parts[parts.length - 1]);
    }

    async fileExists(path) {
        // Només resol el handle: llegir el contingut sencer (com abans) era
        // innecessàriament car per a fitxers grans
        try {
            const parts = path.split('/').filter(Boolean);
            let current = this.rootHandle;
            for (let i = 0; i < parts.length - 1; i++) {
                current = await current.getDirectoryHandle(parts[i]);
            }
            await current.getFileHandle(parts[parts.length - 1]);
            return true;
        } catch {
            return false;
        }
    }

    /** Crea (si no existeix) tot el camí de directoris i retorna el handle del full */
    async mkdir(path) {
        const parts = path.split('/').filter(Boolean);
        let current = this.rootHandle;
        for (const part of parts) {
            current = await current.getDirectoryHandle(part, { create: true });
        }
        return current;
    }

    /** Calcula l'espai ocupat al dispositiu escanejant tots els fitxers recursivament */
    async getStorageInfo() {
        if (!this.rootHandle) return null;
        let usedBytes = 0;
        let fileCount = 0;
        const scan = async (dirHandle, depth = 0) => {
            if (depth > 10) return;
            for await (const [, handle] of dirHandle.entries()) {
                if (handle.kind === 'file') {
                    try { const f = await handle.getFile(); usedBytes += f.size; fileCount++; } catch { /* skip */ }
                } else if (handle.kind === 'directory') {
                    await scan(handle, depth + 1);
                }
            }
        };
        await scan(this.rootHandle);
        const totalBytes = 960 * 1024; // Raspberry Pi Pico típica: ~960 KB
        return { usedBytes, totalBytes, fileCount };
    }

    /** Compta els fitxers .py al directori /modes */
    async countModeFiles() {
        if (!this.rootHandle) return 0;
        try {
            const modesHandle = await this.rootHandle.getDirectoryHandle('modes');
            let count = 0;
            for await (const [name, handle] of modesHandle.entries()) {
                if (handle.kind === 'file' && (name.endsWith('.py') || name.endsWith('.mpy'))) count++;
            }
            return count;
        } catch {
            return 0;
        }
    }

    async listDir(path) {
        const parts = path.split('/').filter(Boolean);
        let current = this.rootHandle;
        for (const part of parts) {
            try {
                current = await current.getDirectoryHandle(part);
            } catch {
                return [];
            }
        }
        const entries = [];
        for await (const [name, handle] of current.entries()) {
            entries.push({ name, type: handle.kind });
        }
        return entries;
    }
}

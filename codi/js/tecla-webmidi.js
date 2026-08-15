/**
 * WebMidiManager — Capa Web MIDI API per al simulador TECLA
 * Gestiona l'accés als ports MIDI del sistema i l'enviament de missatges
 *
 * ── Per què això té tanta lletra ────────────────────────────────────────────
 * El MIDI del navegador es comporta de manera BEN diferent segons el sistema, i
 * quan falla ho fa en silenci: la llista de ports surt buida, o el port se
 * selecciona i no sona res, sense cap error enlloc. Aquí es mira de convertir
 * cada silenci d'aquests en una frase que digui què passa i què s'hi pot fer.
 *
 *   macOS   Porta un port virtual de fàbrica —el «IAC Driver», a Configuració
 *           d'Àudio i MIDI—, i diversos programes poden fer servir el mateix
 *           port alhora. Per això aquí tot sol funcionar a la primera.
 *
 *   Windows NO porta cap port virtual. I els programes com Ableton no en
 *           publiquen cap: en consumeixen, però no en creen. O sigui que si no
 *           hi ha res instal·lat, la llista surt buida i no hi ha cap error a
 *           enlloc, perquè de fet no hi ha res a trobar. Cal un cable MIDI
 *           virtual (loopMIDI és el més estès i és gratuït).
 *           A sobre, l'API antiga de Windows dona els ports en EXCLUSIVA: si un
 *           altre programa ja té el port obert, aquí ni s'obre ni s'avisa.
 *
 *   Linux   Amb ALSA/JACK va bé, però els ports depenen del que hi hagi corrent.
 */
export class WebMidiManager {
    constructor() {
        this.access = null;
        this.output = null;
        this.outputs = [];
        this.onLog = null;   // callback(type, a, b, ch)
        this.onUpdate = null;   // callback() quan canvien els ports
        this.onAvis = null;   // callback(text, mena) per als problemes de port
        this.error = null;
        this._avisat = false;   // perquè un port mut no ompli el registre
    }

    /** Windows no té ports virtuals de sèrie: el consell hi és un altre. */
    static esWindows() {
        const d = navigator.userAgentData;
        if (d && d.platform) return /win/i.test(d.platform);
        return /Win/i.test(navigator.platform || navigator.userAgent || '');
    }

    async init() {
        // Sense context segur no hi ha Web MIDI, i el navegador no ho diu: la
        // funció simplement no existeix. Obrir el fitxer amb doble clic
        // (file://) és la manera més fàcil d'acabar aquí sense saber per què.
        if (typeof window !== 'undefined' && window.isSecureContext === false) {
            this.error = 'cal obrir l\'app per https:// o localhost (amb file:// el navegador no dona MIDI)';
            return { success: false, error: this.error };
        }
        if (!navigator.requestMIDIAccess) {
            this.error = 'Web MIDI API no disponible (cal Chrome/Edge)';
            return { success: false, error: this.error };
        }
        try {
            this.access = await navigator.requestMIDIAccess({ sysex: false });
            this._updateOutputs();
            this.access.onstatechange = () => {
                this._updateOutputs();
                if (this.onUpdate) this.onUpdate(this.outputs);
            };
            return { success: true, outputs: this.outputs };
        } catch (e) {
            // Si l'usuari ha denegat el permís, o l'ha denegat una vegada i el
            // navegador se'n recorda, això peta aquí i no en cap altre lloc.
            this.error = `MIDI denegat: ${e.message}`;
            return { success: false, error: this.error };
        }
    }

    _updateOutputs() {
        this.outputs = [];
        if (!this.access) return;
        for (const [id, out] of this.access.outputs) {
            this.outputs.push({ id, name: out.name, port: out, state: out.state });
        }
    }

    /**
     * Torna a llegir la llista de ports ARA MATEIX.
     *
     * `onstatechange` hauria de bastar, però amb els cables virtuals de Windows
     * no sempre arriba: un port de loopMIDI creat després d'obrir la pestanya
     * pot no aparèixer fins que no es torna a mirar. Es crida en obrir el
     * desplegable, que és exactament quan l'usuari espera veure'l.
     */
    refresca() {
        this._updateOutputs();
        return this.outputs;
    }

    /**
     * Explica en una frase per què la llista de ports és buida.
     * És el missatge que es veu quan no hi ha res a triar.
     */
    diagnostic() {
        if (this.error) return this.error;
        if (!this.access) return 'encara no s\'ha demanat accés al MIDI';
        if (this.outputs.length) return null;
        if (WebMidiManager.esWindows()) {
            return 'cap port MIDI. Windows no en porta cap de virtual i els programes '
                 + 'com Ableton no en creen: instal·la un cable MIDI virtual (loopMIDI), '
                 + 'crea-hi un port i reinicia el navegador.';
        }
        return 'cap port MIDI. Al Mac, obre Configuració d\'Àudio i MIDI i activa '
             + 'el «IAC Driver» perquè n\'hi hagi un.';
    }

    /**
     * Tria el port i l'OBRE de debò.
     *
     * Obrir-lo explícitament no és cap floritura: a Windows els ports són
     * exclusius, i si un altre programa ja el té agafat, `open()` falla. Sense
     * aquesta crida, l'error només apareixeria en el primer `send()` —que el
     * descarta— i el resultat seria un port triat que no sona i no es queixa.
     */
    async selectOutput(id) {
        if (!id) { this.output = null; return { ok: true }; }
        const found = this.outputs.find(o => o.id === id);
        if (!found) return { ok: false, motiu: 'aquest port ja no hi és' };
        this.output = found.port;
        this._avisat = false;
        try {
            await found.port.open();
            return { ok: true, nom: found.name };
        } catch (e) {
            const extra = WebMidiManager.esWindows()
                ? ' A Windows els ports MIDI són d\'un sol programa a la vegada: tanca\'l allà (o fes servir un port de loopMIDI que no estigui ocupat).'
                : '';
            const motiu = `no s'ha pogut obrir «${found.name}».${extra}`;
            if (this.onAvis) this.onAvis(motiu, 'warn');
            return { ok: false, motiu, nom: found.name };
        }
    }

    /**
     * Envia un missatge MIDI al port seleccionat.
     * @param {string} type  'note_on' | 'note_off' | 'control_change' | 'pitchwheel'
     * @param {number} a     nota / control / pitch_bend_value
     * @param {number} b     velocitat / valor
     * @param {number} ch    canal (0-15)
     */
    send(type, a, b, ch = 0) {
        const channel = Math.max(0, Math.min(15, ch | 0));
        let data;
        switch (type) {
            case 'note_on':
                data = [0x90 | channel, a & 0x7F, b & 0x7F];
                break;
            case 'note_off':
                data = [0x80 | channel, a & 0x7F, b & 0x7F];
                break;
            case 'control_change':
                data = [0xB0 | channel, a & 0x7F, b & 0x7F];
                break;
            case 'pitchwheel': {
                const p = Math.max(-8192, Math.min(8191, a | 0)) + 8192;
                data = [0xE0 | channel, p & 0x7F, (p >> 7) & 0x7F];
                break;
            }
            default: return;
        }

        if (this.output) {
            try {
                this.output.send(data);
            } catch (e) {
                // Un port que peta ho fa a cada nota: s'avisa un cop i prou,
                // que si no el registre queda inservible.
                if (!this._avisat) {
                    this._avisat = true;
                    if (this.onAvis) this.onAvis(`el port MIDI ha deixat d'acceptar dades (${e.name || 'error'})`, 'warn');
                }
            }
        }
        if (this.onLog) this.onLog(type, a, b, ch);
    }

    allNotesOff() {
        for (let ch = 0; ch < 16; ch++) {
            this.send('control_change', 120, 0, ch);  // All Sound Off
            this.send('control_change', 123, 0, ch);  // All Notes Off
        }
    }

    isAvailable() { return !!this.access; }
}

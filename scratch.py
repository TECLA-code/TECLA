import re

with open('codi/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

ca_inj = """        toast_scale_saved: '✓ Escala desada',
        fw_step1_desc: `Descarrega el fitxer i <strong>arrossega'l al volum RPI-RP2</strong> al Finder. El dispositiu es reiniciarà automàticament.`,
        btn_dl_nuke: '⚠ Descarregar flash_nuke.uf2',
        btn_dl_cp: '⬇ Descarregar CircuitPython 10.0.3',
        fw_step1_note: `<strong>Per entrar al mode bootloader:</strong><br>Mantén premut BOOTSEL mentre connectes el USB-C.<br><strong>Després de descarregar:</strong><br>Obre el Finder → arrossega el .uf2 al volum RPI-RP2.`,
        fw_step2_desc: `Quan el dispositiu apareix com <strong>CIRCUITPY</strong>, connecta'l a la pestanya <strong>Tecles</strong> i instal·la el firmware.`,
        fw_preserve: 'Preservar configuració existent',
        guide_toc: `
            <a href="#gs-1">1. Instal·lar el CircuitPython</a>
            <a href="#gs-2">2. Instal·lar el firmware</a>
            <a href="#gs-3">3. Funcionament del dispositiu</a>
            <a href="#gs-4">4. Configuració</a>
            <a href="#gs-5">5. Pestanyes</a>
            <a href="#gs-6">6. Recomanacions</a>
        `,
        guide_s1: `
            <div class="guide-h1">1. Instal·lar el CircuitPython al TECLA</div>
            <p class="guide-li">Connecta el TECLA a l'ordinador via USB.</p>
            <p class="guide-li">Si apareix com a <strong>CIRCUITPY</strong> ves al punt 2.</p>
            <p class="guide-li">Si apareix com a <strong>RPI-RP2</strong> cal instal·lar el CircuitPython.</p>
            <p class="guide-li">Ves a la pestanya <em>Firmware</em> i segueix les instruccions del Pas 1.</p>
            <p class="guide-li">El dispositiu apareixerà amb el nom CIRCUITPY.</p>
        `,
        guide_s2: `
            <div class="guide-h1">2. Instal·lar el firmware al TECLA</div>
            <p class="guide-li">Connecta el TECLA a l'ordinador via USB.</p>
            <p class="guide-li">Ves a la pestanya <em>Firmware</em> → clica <strong>Instal·lar / Actualitzar</strong>.</p>
            <p class="guide-li">Espera que la barra de progrés arribi al 100%.</p>
            <p class="guide-li">Clica <strong>Verificar instal·lació</strong> (opcional).</p>
            <p class="guide-li">Fes un reset al dispositiu (botó físic de reset).</p>
            <div class="guide-note">El TECLA ja està llest per funcionar.</div>
        `,
        guide_s3: `
            <div class="guide-h1">3. Funcionament del TECLA</div>
            <div class="guide-h2">Capa 1 · Teclat</div>
            <p class="guide-li">Tecles <strong>1–8</strong>: notes / acords.</p>
            <p class="guide-li">Tecla <strong>9</strong>: canvi d'escala / progressió (cíclic).</p>
            <p class="guide-li">Tecla <strong>10</strong>: canvi de tonalitat (cercle de quintes).</p>
            <p class="guide-li">Tecla <strong>11</strong>: activar / desactivar mode acords.</p>
            <p class="guide-li">Tecla <strong>12</strong>: 1 clic → arpegiador + canvi de patró · 2 clics → desactivar arpegiador.</p>
            <p class="guide-li">Tecla <strong>13</strong>: 1 clic → capa 2 (Modes) · 2 clics → capa 1 (Teclat) · 2 s mantingut → canvi de capa de modes.</p>
            <p class="guide-li">Tecla <strong>14</strong>: baixar d'octava.</p>
            <p class="guide-li">Tecla <strong>15</strong>: pujar d'octava.</p>
            <p class="guide-li">Tecla <strong>16</strong>: aturar el so (All Notes Off).</p>
            <pre class="guide-diagram">┌──────────┬──────────┬──────────┬──────────┐
│    1     │    2     │    3     │    4     │
├──────────┼──────────┼──────────┼──────────┤
│    5     │    6     │    7     │    8     │
├──────────┼──────────┼──────────┼──────────┤
│    9     │   10     │   11     │   12     │
├──────────┼──────────┼──────────┼──────────┤
│   13     │   14     │   15     │   16     │
└──────────┴──────────┴──────────┴──────────┘</pre>
            <div class="guide-h2">Capa 2 · Modes</div>
            <p class="guide-li">S'activa amb la tecla 13. Es configura a la pestanya <em>Tecles</em>.</p>
            <p class="guide-li">Tecles <strong>1–12</strong>: modes assignats.</p>
            <p class="guide-li">Tecla <strong>13</strong>: torna a la capa teclat · 2 s mantingut → canvi de capa de modes.</p>
            <p class="guide-li">Tecla <strong>14</strong>: efecte temporal 1 (mantenir premuda) · 2 clics → canvia efecte (rotatiu).</p>
            <p class="guide-li">Tecla <strong>15</strong>: efecte temporal 2 (mantenir premuda) · 2 clics → canvia efecte (rotatiu).</p>
            <p class="guide-li">Tecla <strong>16</strong>: aturar el so.</p>
        `,
        guide_s4: `
            <div class="guide-h1">4. Configuració del dispositiu</div>
            <p class="guide-li">Ves a <em>Modes i Escales</em> → selecciona els modes, escales i efectes.</p>
            <p class="guide-li">Ves a <em>Tecles</em> → crea una capa i assigna modes a les tecles 1–12.</p>
            <p class="guide-li">Clica <strong>Guardar configuració</strong>.</p>
            <p class="guide-li">Ves a <em>Firmware</em> → <strong>Instal·lar / Actualitzar</strong> per sincronitzar el dispositiu.</p>
            <p class="guide-li">Fes un reset al dispositiu.</p>
        `,
        guide_s5: `
            <div class="guide-h1">5. Pestanyes</div>
            <div class="guide-h2">Tecles</div>
            <p class="guide-li">Crear capes de modes i assignar-los a les tecles 1–12.</p>
            <p class="guide-li">Seleccionar efectes temporals a les tecles 14 i 15.</p>
            <div class="guide-h2">Modes i Escales</div>
            <p class="guide-li">Seleccionar modes, escales, efectes temporals i patrons de l'arpegiador.</p>
            <p class="guide-li">Configurar els potenciòmetres del mode teclat i de l'arpegiador.</p>
            <div class="guide-h2">Progressions</div>
            <p class="guide-li">Crear progressions d'acords personalitzades.</p>
            <div class="guide-h2">Simulador</div>
            <p class="guide-li">Testejar modes sense el dispositiu físic. Requereix un DAW obert amb MIDI actiu.</p>
            <p class="guide-li">La tecla 13 canvia entre capa teclat i capa modes.</p>
            <div class="guide-h2">Firmware</div>
            <p class="guide-li">Instal·lar CircuitPython i el firmware del TECLA.</p>
            <div class="guide-h2">Aparença</div>
            <p class="guide-li">Canviar el tema de colors de l'app. Crear un tema personalitzat.</p>
        `,
        guide_s6: `
            <div class="guide-h1">6. Recomanacions</div>
            <p class="guide-li">Guardar sempre la configuració després de realitzar canvis.</p>
            <p class="guide-li">Actualitzar el firmware després de canviar modes o escales.</p>
            <p class="guide-li">No seleccionar més de 12 modes ni 12 escales/progressions.</p>
            <p class="guide-li">No crear més d'una capa de modes per evitar problemes de memòria.</p>
            <p class="guide-li">Provar els modes al simulador abans d'instal·lar-los al dispositiu.</p>
            <p class="guide-li">Tancar i obrir l'app si has afegit nous modes per actualitzar el simulador.</p>
            <div class="guide-note">Afegir més de 12 modes o dues capes al dispositiu pot generar problemes de memòria.</div>
        `"""

es_inj = """        toast_scale_saved: '✓ Escala guardada',
        fw_step1_desc: `Descarga el archivo y <strong>arrástralo al volumen RPI-RP2</strong> en Finder/Explorador. El dispositivo se reiniciará automáticamente.`,
        btn_dl_nuke: '⚠ Descargar flash_nuke.uf2',
        btn_dl_cp: '⬇ Descargar CircuitPython 10.0.3',
        fw_step1_note: `<strong>Para entrar en modo bootloader:</strong><br>Mantén pulsado BOOTSEL mientras conectas el USB-C.<br><strong>Después de descargar:</strong><br>Abre Finder/Explorador → arrastra el .uf2 al volumen RPI-RP2.`,
        fw_step2_desc: `Cuando el dispositivo aparezca como <strong>CIRCUITPY</strong>, conéctalo en la pestaña <strong>Teclas</strong> e instala el firmware.`,
        fw_preserve: 'Preservar configuración existente',
        guide_toc: `
            <a href="#gs-1">1. Instalar CircuitPython</a>
            <a href="#gs-2">2. Instalar el firmware</a>
            <a href="#gs-3">3. Funcionamiento del dispositivo</a>
            <a href="#gs-4">4. Configuración</a>
            <a href="#gs-5">5. Pestañas</a>
            <a href="#gs-6">6. Recomendaciones</a>
        `,
        guide_s1: `
            <div class="guide-h1">1. Instalar CircuitPython en el TECLA</div>
            <p class="guide-li">Conecta el TECLA al ordenador vía USB.</p>
            <p class="guide-li">Si aparece como <strong>CIRCUITPY</strong> ve al punto 2.</p>
            <p class="guide-li">Si aparece como <strong>RPI-RP2</strong> hay que instalar CircuitPython.</p>
            <p class="guide-li">Ve a la pestaña <em>Firmware</em> y sigue las instrucciones del Paso 1.</p>
            <p class="guide-li">El dispositivo aparecerá con el nombre CIRCUITPY.</p>
        `,
        guide_s2: `
            <div class="guide-h1">2. Instalar el firmware en el TECLA</div>
            <p class="guide-li">Conecta el TECLA al ordenador vía USB.</p>
            <p class="guide-li">Ve a la pestaña <em>Firmware</em> → haz clic en <strong>Instalar / Actualizar</strong>.</p>
            <p class="guide-li">Espera a que la barra de progreso llegue al 100%.</p>
            <p class="guide-li">Haz clic en <strong>Verificar instalación</strong> (opcional).</p>
            <p class="guide-li">Haz un reset al dispositivo (botón físico de reset).</p>
            <div class="guide-note">El TECLA ya está listo para funcionar.</div>
        `,
        guide_s3: `
            <div class="guide-h1">3. Funcionamiento del TECLA</div>
            <div class="guide-h2">Capa 1 · Teclado</div>
            <p class="guide-li">Teclas <strong>1–8</strong>: notas / acordes.</p>
            <p class="guide-li">Tecla <strong>9</strong>: cambio de escala / progresión (cíclico).</p>
            <p class="guide-li">Tecla <strong>10</strong>: cambio de tonalidad (círculo de quintas).</p>
            <p class="guide-li">Tecla <strong>11</strong>: activar / desactivar modo acordes.</p>
            <p class="guide-li">Tecla <strong>12</strong>: 1 clic → arpegiador + cambio de patrón · 2 clics → desactivar arpegiador.</p>
            <p class="guide-li">Tecla <strong>13</strong>: 1 clic → capa 2 (Modos) · 2 clics → capa 1 (Teclado) · 2 s mantenido → cambio de capa de modos.</p>
            <p class="guide-li">Tecla <strong>14</strong>: bajar de octava.</p>
            <p class="guide-li">Tecla <strong>15</strong>: subir de octava.</p>
            <p class="guide-li">Tecla <strong>16</strong>: detener el sonido (All Notes Off).</p>
            <pre class="guide-diagram">┌──────────┬──────────┬──────────┬──────────┐
│    1     │    2     │    3     │    4     │
├──────────┼──────────┼──────────┼──────────┤
│    5     │    6     │    7     │    8     │
├──────────┼──────────┼──────────┼──────────┤
│    9     │   10     │   11     │   12     │
├──────────┼──────────┼──────────┼──────────┤
│   13     │   14     │   15     │   16     │
└──────────┴──────────┴──────────┴──────────┘</pre>
            <div class="guide-h2">Capa 2 · Modos</div>
            <p class="guide-li">Se activa con la tecla 13. Se configura en la pestaña <em>Teclas</em>.</p>
            <p class="guide-li">Teclas <strong>1–12</strong>: modos asignados.</p>
            <p class="guide-li">Tecla <strong>13</strong>: vuelve a la capa teclado · 2 s mantenido → cambio de capa de modos.</p>
            <p class="guide-li">Tecla <strong>14</strong>: efecto temporal 1 (mantener pulsada) · 2 clics → cambia efecto (rotativo).</p>
            <p class="guide-li">Tecla <strong>15</strong>: efecto temporal 2 (mantener pulsada) · 2 clics → cambia efecto (rotativo).</p>
            <p class="guide-li">Tecla <strong>16</strong>: detener el sonido.</p>
        `,
        guide_s4: `
            <div class="guide-h1">4. Configuración del dispositivo</div>
            <p class="guide-li">Ve a <em>Modos y Escalas</em> → selecciona los modos, escalas y efectos.</p>
            <p class="guide-li">Ve a <em>Teclas</em> → crea una capa y asigna modos a las teclas 1–12.</p>
            <p class="guide-li">Haz clic en <strong>Guardar configuración</strong>.</p>
            <p class="guide-li">Ve a <em>Firmware</em> → <strong>Instalar / Actualizar</strong> para sincronizar el dispositivo.</p>
            <p class="guide-li">Haz un reset al dispositivo.</p>
        `,
        guide_s5: `
            <div class="guide-h1">5. Pestañas</div>
            <div class="guide-h2">Teclas</div>
            <p class="guide-li">Crear capas de modos y asignarlos a las teclas 1–12.</p>
            <p class="guide-li">Seleccionar efectos temporales en las teclas 14 y 15.</p>
            <div class="guide-h2">Modos y Escalas</div>
            <p class="guide-li">Seleccionar modos, escalas, efectos temporales y patrones del arpegiador.</p>
            <p class="guide-li">Configurar los potenciómetros del modo teclado y del arpegiador.</p>
            <div class="guide-h2">Progresiones</div>
            <p class="guide-li">Crear progresiones de acordes personalizadas.</p>
            <div class="guide-h2">Simulador</div>
            <p class="guide-li">Testear modos sin el dispositivo físico. Requiere un DAW abierto con MIDI activo.</p>
            <p class="guide-li">La tecla 13 cambia entre capa teclado y capa modos.</p>
            <div class="guide-h2">Firmware</div>
            <p class="guide-li">Instalar CircuitPython y el firmware del TECLA.</p>
            <div class="guide-h2">Apariencia</div>
            <p class="guide-li">Cambiar el tema de colores de la app. Crear un tema personalizado.</p>
        `,
        guide_s6: `
            <div class="guide-h1">6. Recomendaciones</div>
            <p class="guide-li">Guardar siempre la configuración después de realizar cambios.</p>
            <p class="guide-li">Actualizar el firmware después de cambiar modos o escalas.</p>
            <p class="guide-li">No seleccionar más de 12 modos ni 12 escalas/progresiones.</p>
            <p class="guide-li">No crear más de una capa de modos para evitar problemas de memoria.</p>
            <p class="guide-li">Probar los modos en el simulador antes de instalarlos en el dispositivo.</p>
            <p class="guide-li">Cerrar y abrir la app si has añadido nuevos modos para actualizar el simulador.</p>
            <div class="guide-note">Añadir más de 12 modos o dos capas al dispositivo puede generar problemas de memoria.</div>
        `"""

en_inj = """        toast_scale_saved: '✓ Scale saved',
        fw_step1_desc: `Download the file and <strong>drag it to the RPI-RP2 volume</strong> in Finder/Explorer. The device will restart automatically.`,
        btn_dl_nuke: '⚠ Download flash_nuke.uf2',
        btn_dl_cp: '⬇ Download CircuitPython 10.0.3',
        fw_step1_note: `<strong>To enter bootloader mode:</strong><br>Press and hold BOOTSEL while plugging in the USB-C cable.<br><strong>After downloading:</strong><br>Open Finder/Explorer → drag the .uf2 to the RPI-RP2 volume.`,
        fw_step2_desc: `When the device appears as <strong>CIRCUITPY</strong>, connect to it in the <strong>Keys</strong> tab and install the firmware.`,
        fw_preserve: 'Preserve existing configuration',
        guide_toc: `
            <a href="#gs-1">1. Install CircuitPython</a>
            <a href="#gs-2">2. Install firmware</a>
            <a href="#gs-3">3. Device operation</a>
            <a href="#gs-4">4. Configuration</a>
            <a href="#gs-5">5. Tabs</a>
            <a href="#gs-6">6. Recommendations</a>
        `,
        guide_s1: `
            <div class="guide-h1">1. Install CircuitPython on TECLA</div>
            <p class="guide-li">Connect TECLA to your computer via USB.</p>
            <p class="guide-li">If it appears as <strong>CIRCUITPY</strong>, skip to step 2.</p>
            <p class="guide-li">If it appears as <strong>RPI-RP2</strong>, you need to install CircuitPython.</p>
            <p class="guide-li">Go to the <em>Firmware</em> tab and follow Step 1 instructions.</p>
            <p class="guide-li">The device will then appear with the name CIRCUITPY.</p>
        `,
        guide_s2: `
            <div class="guide-h1">2. Install TECLA firmware</div>
            <p class="guide-li">Connect TECLA to your computer via USB.</p>
            <p class="guide-li">Go to the <em>Firmware</em> tab → click <strong>Install / Update</strong>.</p>
            <p class="guide-li">Wait for the progress bar to reach 100%.</p>
            <p class="guide-li">Click <strong>Verify installation</strong> (optional).</p>
            <p class="guide-li">Reset the device (physical reset button).</p>
            <div class="guide-note">The TECLA is now ready to use.</div>
        `,
        guide_s3: `
            <div class="guide-h1">3. TECLA Operation</div>
            <div class="guide-h2">Layer 1 · Keyboard</div>
            <p class="guide-li">Keys <strong>1–8</strong>: notes / chords.</p>
            <p class="guide-li">Key <strong>9</strong>: scale / progression change (cyclic).</p>
            <p class="guide-li">Key <strong>10</strong>: key change (circle of fifths).</p>
            <p class="guide-li">Key <strong>11</strong>: toggle chords mode.</p>
            <p class="guide-li">Key <strong>12</strong>: 1 click → arpeggiator + pattern change · 2 clicks → disable arpeggiator.</p>
            <p class="guide-li">Key <strong>13</strong>: 1 click → layer 2 (Modes) · 2 clicks → layer 1 (Keyboard) · Hold 2s → change modes layer.</p>
            <p class="guide-li">Key <strong>14</strong>: octave down.</p>
            <p class="guide-li">Key <strong>15</strong>: octave up.</p>
            <p class="guide-li">Key <strong>16</strong>: stop sound (All Notes Off).</p>
            <pre class="guide-diagram">┌──────────┬──────────┬──────────┬──────────┐
│    1     │    2     │    3     │    4     │
├──────────┼──────────┼──────────┼──────────┤
│    5     │    6     │    7     │    8     │
├──────────┼──────────┼──────────┼──────────┤
│    9     │   10     │   11     │   12     │
├──────────┼──────────┼──────────┼──────────┤
│   13     │   14     │   15     │   16     │
└──────────┴──────────┴──────────┴──────────┘</pre>
            <div class="guide-h2">Layer 2 · Modes</div>
            <p class="guide-li">Activated with key 13. Configured in the <em>Keys</em> tab.</p>
            <p class="guide-li">Keys <strong>1–12</strong>: assigned modes.</p>
            <p class="guide-li">Key <strong>13</strong>: back to keyboard layer · Hold 2s → change modes layer.</p>
            <p class="guide-li">Key <strong>14</strong>: temporary effect 1 (hold down) · 2 clicks → change effect (cyclic).</p>
            <p class="guide-li">Key <strong>15</strong>: temporary effect 2 (hold down) · 2 clicks → change effect (cyclic).</p>
            <p class="guide-li">Key <strong>16</strong>: stop sound.</p>
        `,
        guide_s4: `
            <div class="guide-h1">4. Device Configuration</div>
            <p class="guide-li">Go to <em>Modes & Scales</em> → select modes, scales, and effects.</p>
            <p class="guide-li">Go to <em>Keys</em> → create a layer and assign modes to keys 1–12.</p>
            <p class="guide-li">Click <strong>Save configuration</strong>.</p>
            <p class="guide-li">Go to <em>Firmware</em> → <strong>Install / Update</strong> to sync the device.</p>
            <p class="guide-li">Reset the device.</p>
        `,
        guide_s5: `
            <div class="guide-h1">5. Tabs</div>
            <div class="guide-h2">Keys</div>
            <p class="guide-li">Create modes layers and assign them to keys 1–12.</p>
            <p class="guide-li">Select temporary effects for keys 14 and 15.</p>
            <div class="guide-h2">Modes & Scales</div>
            <p class="guide-li">Select modes, scales, temporary effects, and arpeggiator patterns.</p>
            <p class="guide-li">Configure potentiometers for keyboard mode and arpeggiator.</p>
            <div class="guide-h2">Progressions</div>
            <p class="guide-li">Create custom chord progressions.</p>
            <div class="guide-h2">Simulator</div>
            <p class="guide-li">Test modes without physical device. Requires an open DAW with active MIDI.</p>
            <p class="guide-li">Key 13 switches between keyboard and modes layers.</p>
            <div class="guide-h2">Firmware</div>
            <p class="guide-li">Install CircuitPython and TECLA firmware.</p>
            <div class="guide-h2">Appearance</div>
            <p class="guide-li">Change app color theme. Create a custom theme.</p>
        `,
        guide_s6: `
            <div class="guide-h1">6. Recommendations</div>
            <p class="guide-li">Always save configuration after making changes.</p>
            <p class="guide-li">Update firmware after changing modes or scales.</p>
            <p class="guide-li">Do not select more than 12 modes or 12 scales/progressions.</p>
            <p class="guide-li">Do not create more than one modes layer to avoid memory issues.</p>
            <p class="guide-li">Test modes in the simulator before installing them on the device.</p>
            <p class="guide-li">Close and reopen the app if you added new modes to update the simulator.</p>
            <div class="guide-note">Adding more than 12 modes or two layers to the device may cause memory problems.</div>
        `"""

content = content.replace("toast_scale_saved: '✓ Escala desada',", ca_inj)
content = content.replace("toast_scale_saved: '✓ Escala guardada',", es_inj)
content = content.replace("toast_scale_saved: '✓ Scale saved',", en_inj)

with open('codi/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("done")

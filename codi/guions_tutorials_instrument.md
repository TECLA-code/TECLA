# Guions — Vídeos tutorials TECLA Instrument

Format: vídeos curts (60-90s), un per pestanya. To directe, "et mostro / fem clic a...". Gravació de pantalla amb dispositiu connectat.

---

## 0. Intro (30s) — Què és TECLA Instrument

**Guió:**
"Això és TECLA Instrument, l'app per configurar el teu TECLA com a controlador MIDI. A dalt tens el botó per connectar el dispositiu per USB, i a la barra veus les pestanyes: Dispositiu, Simulador, Firmware, Aparença, Guia i Configuració. En aquest vídeo et connectem el dispositiu i mirem ràpidament l'estat de connexió — el punt de color i el nom que apareix costat del logo TECLA."

**Accions a mostrar:**
- Clic a "Connecta dispositiu".
- Mostrar el badge que canvia a "connectat".
- Passar el cursor per les 6 pestanyes de la barra de navegació.

---

## 1. Pestanya Dispositiu — Capes (concepte general)

**Guió:**
"La pestanya Dispositiu és el centre de configuració. Aquí gestiones les CAPES del teu TECLA: cada capa pot ser de tipus Teclat (per tocar notes i acords) o de tipus Modes (per disparar sons o efectes assignats a cada tecla). A l'esquerra tens la llista de capes; amb el botó + Capa n'afegeixes una nova, i amb els dos botons de dalt (Teclat / Modes) tries de quin tipus és la capa seleccionada. Pots reanomenar-la fent doble clic al nom, i arrossegar-les per canviar l'ordre. La tecla física 13 del dispositiu et permet anar canviant de capa mentre toques."

**Accions a mostrar:**
- Clic a "+ Capa".
- Alternar entre botó "Teclat" i "Modes" al capçal.
- Doble clic al nom per reanomenar.
- Arrossegar una capa per canviar l'ordre.

---

## 2. Dispositiu → Capa tipus "Teclat"

**Guió:**
"Quan una capa és de tipus Teclat, aquí configures com sonen les tecles del teclat musical. Al diagrama central assignes una FUNCIÓ a cada botó — per exemple, nota, canvi d'escala, canvi de tonalitat o octava — arrossegant els xips de funcions de l'esquerra cap a cada casella. A sota tens Guardar i Restablir per defecte. Al menú de Configuració del teclat trobem cinc seccions: Escales i arpegiador, Acompanyaments, Harmonia, Tipologies d'acords, i Progressions i escales pròpies. Cada secció es desplega en fer-hi clic."

**Accions a mostrar:**
- Arrossegar un xip de funció a una casella del grid.
- Clic a "Guardar" / "Restablir per defecte".
- Clic per obrir cada secció del menú: Escales i arpegiador, Acompanyaments, Harmonia, Tipologies d'acords, Progressions i escales pròpies (mostrar breument el contingut de cadascuna).

---

## 2b. Secció "Escales i arpegiador" (dins Teclat) — opcional, vídeo curt propi

**Guió:**
"Dins d'Escales i arpegiador tries quines escales musicals estaran disponibles al teclat amb els botons de pastilla, dissenyes els teus propis patrons d'arpegiador amb el botó + Nou Patró, i a la dreta ordenes les tonalitats: l'ordre en què es van ciclant quan prems el botó de canvi de to."

**Accions a mostrar:**
- Activar/desactivar pastilles d'escales.
- Crear un patró d'arpegiador nou (obrir l'editor, marcar passos, guardar).
- Arrossegar per reordenar les tonalitats.

---

## 3. Dispositiu → Capa tipus "Modes"

**Guió:**
"Quan la capa és de tipus Modes, el diagrama de tecles ja no toca notes: cada tecla dispara un MODE, que és com un mini-instrument o efecte (per exemple, un sintetitzador, un mode de percussió...). A l'esquerra tens la llista de Modes disponibles: pots crear-ne un de nou amb Crear, afegir-ne més amb + Afegir, o eliminar-ne. Per assignar un mode a una tecla, l'arrossegues sobre la casella. A sota trobem els Efectes temporals per a les tecles 14 i 15, les Capes de Potenciòmetres — que permeten que els potes canviïn de funció en viu — i les Capes Guardades, on pots desar una foto de tota la configuració actual per recuperar-la després."

**Accions a mostrar:**
- Arrossegar un mode de la llista a una casella del teclat.
- Obrir el botó "✦ Crear" (mostrar només que s'obre, sense entrar en detall).
- Desplegar "Efectes temporals" i marcar-ne un.
- Clic a "+ Afegir capa" dins Configuració de Modes (potenciòmetres).
- Clic a "Guardar capa actual" a Capes Guardades.

---

## 4. Pestanya Simulador

**Guió:**
"El Simulador et permet provar el TECLA sense necessitat de tenir-lo connectat, o fins i tot sincronitzat amb el dispositiu real. A l'esquerra selecciones el mode que vols provar. A la barra superior tries la sortida MIDI, prems Iniciar, i pots activar el botó So per sentir-ho directament des de l'ordinador sense necessitar cap DAW. Al centre veus el teclat i els potenciòmetres virtuals — hi pots clicar per simular que els prems. I amb 'Sync dispositiu' pots fer que el TECLA físic per USB controli el simulador en directe."

**Accions a mostrar:**
- Seleccionar un mode a la llista.
- Triar sortida MIDI i clicar "Iniciar".
- Clicar "So" per activar el motor intern.
- Clicar una tecla virtual del simulador.
- Obrir "Config" del simulador.

---

## 5. Pestanya Firmware

**Guió:**
"A Firmware instal·les i actualitzes el sistema del TECLA. Primer veus l'Estat del sistema: si detecta el volum, la versió de CircuitPython i el firmware TECLA instal·lat. Si el dispositiu és nou, al Pas 1 instal·les CircuitPython connectant la Pico amb el botó BOOTSEL premut. Un cop instal·lat, al Pas 2 connectes normalment i prems Instal·lar / Actualitzar firmware per pujar-hi el codi de TECLA. Al final pots prémer Verificar instal·lació per assegurar-te que tot ha quedat correctament copiat."

**Accions a mostrar:**
- Clic a "Refrescar estat".
- Mostrar Pas 1 (Flash Nuke / Instal·lar CircuitPython) — sense executar-ho si no cal.
- Clic a "Instal·lar / Actualitzar firmware" i mostrar la barra de progrés.
- Clic a "Verificar instal·lació".

---

## 6. Pestanya Aparença

**Guió:**
"A Aparença canvies el tema visual de l'app: fosc, clar, neó, i molts més, cadascun amb el seu color d'accent. Si vols un toc personal, a l'Editor de temes pots crear el teu propi tema triant colors de fons, superfície, text i accent, o prement el botó de daus per generar-ne un d'aleatori. Es desa amb Desa i aplica."

**Accions a mostrar:**
- Clicar 2-3 targetes de tema (dark, ice, forest...).
- Clicar "Nou tema".
- Canviar un color amb el selector de color.
- Clicar "🎲 Aleatori".
- Clicar "Desa i aplica".

---

## 7. Pestanya Guia

**Guió:**
"La pestanya Guia és la documentació de referència de l'app: aquí trobes explicat, pas a pas i en el teu idioma, com funciona cada part del TECLA. És el lloc on tornar si et quedes encallat."

**Accions a mostrar:**
- Fer scroll per la guia mostrant els diferents apartats.
- Canviar d'idioma (CA/ES/EN) i mostrar que el contingut de la guia també canvia.

---

## 8. Pestanya Configuració

**Guió:**
"A Configuració ajustes paràmetres globals del dispositiu. Pots triar el Canal MIDI pel qual el TECLA envia totes les notes. A Identitat USB pots posar un nom personalitzat al port MIDI i al disc que apareix quan connectes el TECLA a l'ordinador — molt útil si tens més d'un TECLA. I al final tens el botó per Desconnectar el dispositiu de l'app."

**Accions a mostrar:**
- Canviar el canal MIDI i clicar "Guardar".
- Escriure un nom de port i clicar "Guardar".
- Escriure un sufix de disc i clicar "Guardar".
- Clicar "Desconnectar".

---

## Notes de producció
- Ordre recomanat de publicació: 0 → 1 → 2 → 2b → 3 → 4 → 5 → 6 → 7 → 8.
- Cada vídeo hauria de començar mostrant la pestanya activa a la barra de navegació (per orientar l'espectador).
- Si es vol reduir a menys vídeos, es poden fusionar 2+2b i deixar Guia/Configuració/Aparença com un únic vídeo de "pestanyes secundàries".

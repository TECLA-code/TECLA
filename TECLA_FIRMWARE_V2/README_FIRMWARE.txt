# 🎹 INSTAL·LACIÓ DEL NOVO FIRMWARE TECLA

Aquest firmware et permetrà utilitzar els teus programes creats amb TECLA Blocks sense perdre les funcionalitats originals del TECLA (sintetitzador, controlador MIDI, etc.).

## 🚀 Passos per instal·lar

1. Connecta el teu TECLA a l'ordinador via USB.
2. S'obrirà una unitat anomenada **CIRCUITPY**.
3. **Fes una còpia de seguretat** del fitxer `code.py` que hi ha actualment al CIRCUITPY (copia'l al teu escriptori per si de cas).
4. **Canvia el nom** del fitxer `code.py` de dins del CIRCUITPY a `tecla_main.py`.
   - Ara tindràs `tecla_main.py` al dispositiu.
5. **Copia** el fitxer `code.py` d'aquesta carpeta (la que acabes de descarregar) dins de CIRCUITPY.
   - Ara tindràs `code.py` (el nou selector) i `tecla_main.py` (l'antic programa original).

## 🎮 Com utilitzar-ho

### Per fer servir el TECLA normalment:
Simplement encén el dispositiu sense tocar cap botó. El LED no s'encendrà i funcionarà com sempre.

### Per carregar un programa de TECLA Blocks:
1. Puja el teu programa des de l'app de TECLA Blocks (prem "Pujar a TECLA").
2. Apaga el dispositiu (o desconnecta'l).
3. **Mantén premut el Botó 16** (l'últim botó de la dreta superior).
4. Encén el dispositiu (connecta l'USB) mentre mantens el botó.
5. El LED parpellejarà breument.
6. Quan s'hagi carregat, veuràs que el teu programa s'executa!

## 🔧 Opció Avançada (Multi-Slot)

Si vols tenir fins a 4 programes diferents:
1. Utilitza el fitxer `code_multi.py` en lloc del `code.py` (renombra'l a `code.py` en copiar-lo al TECLA).
2. Des de l'App, podràs escollir a quin "slot" (1-4) pujar el codi.
3. Per carregar:
   - Slot 1: Botó 16
   - Slot 2: Botó 15
   - Slot 3: Botó 14
   - Slot 4: Botó 13

---
Disfruita programant el teu TECLA!

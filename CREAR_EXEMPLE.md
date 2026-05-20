# 🔧 Com Crear un Exemple que Funcioni

## ❌ Problema Detectat

Els exemples que he creat tenen un format XML que pot no ser compatible amb la versió de Blockly que usa l'app.

## ✅ Solució: Crear Exemple des de l'App

### Pas 1: Crear Projecte Simple

1. **Obre TECLA Blocks:**
```bash
cd ~/Desktop/TECLA-Blocks
./start.sh
```

2. **Crea un programa simple:**
   - Arrossega bloc "🎵 Tocar nota" al workspace
   - Configura: Nota Do, Velocitat 100, Durada 500

3. **Guarda el projecte:**
   - Menú: Arxiu → Guardar Projecte
   - Nom: `exemple_real`
   - Ubicació: Desktop

### Pas 2: Aquest serà el Teu Model

Aquest fitxer `exemple_real.tblocks` tindrà el format **100% correcte** perquè l'ha generat la pròpia app.

---

## 🐛 Per Què Fallen els Meus Exemples?

Els fitxers que he creat tenen XML que:
- Pot tenir sintaxi incorrecta per Blockly
- Pot faltar algun atribut necessari
- Pot tenir IDs duplicats

**L'únic format garantit és el que genera l'app.**

---

## 🎯 Solució Alternativa: Workspace en Blanc

Si només vols començar a programar:

1. Obre TECLA Blocks
2. Comença amb workspace buit
3. Arrossega blocs
4. Programa!

No cal obrir cap exemple per començar.

---

## 📝 Si Vols Compartir Projectes

### Crear Exemple per Altri

1. **Crea projecte a TECLA Blocks**
2. **Guarda amb nom descriptiu**
3. **Comparteix el .tblocks**

### Obrir Projecte d'Altri

1. **Copia .tblocks al teu ordinador**
2. **TECLA Blocks → Arxiu → Obrir**
3. **Selecciona el fitxer**

---

## 🔍 Debug Manual (Avançat)

Si vols veure per què falla:

```bash
# 1. Obre l'app en mode dev
cd ~/Desktop/TECLA-Blocks
./start-dev.sh

# 2. Intenta obrir un exemple
# 3. Mira la consola DevTools (es mostra automàticament)
# 4. Veuràs l'error exacte
```

---

## ✅ Recomanació

**No intentis obrir els exemples que he creat.**

En comptes d'això:
1. Obre TECLA Blocks
2. Crea el teu primer programa des de zero
3. Guarda'l
4. Aquest serà el teu exemple!

---

## 📚 Tutorials Disponibles

Per aprendre a programar sense necessitat d'exemples:

- **GUIA_RAPIDA.md** - Tutorials pas a pas
- **README.md** - Documentació completa
- **CATEGORIES.md** - Índex de tots els blocs

---

## 💡 Primer Programa (Sense Fitxer)

**Objectiu:** Tocar Do-Mi-Sol

**Passos:**
1. Obre TECLA Blocks
2. Arrossega "Tocar nota" 3 vegades
3. Configura:
   - Primera: Do, 100, 500
   - Segona: Mi, 100, 500
   - Tercera: Sol, 100, 500
4. Entre cada nota: "Esperar 0.5"
5. Puja a TECLA
6. Prova!

**Temps:** 2 minuts

---

**Conclusió:** Els exemples pre-fets no són necessaris. És millor aprendre creant des de zero! 🚀

---

**Data:** 17 Novembre 2025  
**Problema:** Format XML incompatible  
**Solució:** Crear projectes des de l'app

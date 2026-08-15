# Contracte de temes de TECLA

Un **tema** no és una paleta de colors: és un sistema de disseny sencer —
geometria, tipografia, materialitat i color. La paleta és un eix a part, i
només el tema **Clàssic** la deixa canviar.

Aquest fitxer és el contracte. Qualsevol app de TECLA (Instrument, MacroPad,
Blocks) que el compleixi pot carregar els mateixos temes sense tocar-ne el CSS.

---

## Com funciona

1. `:root` de l'app defineix **tots** els tokens amb els valors del Clàssic.
2. Un tema és un fitxer `css/reserva-estetica/<id>.css` amb un únic bloc arrel:
   `body.skin-<id> { … }` que en redefineix els que li calen.
3. `applyskin('<id>')` posa `body.skin-<id>` i ho desa a `localStorage`.
4. El Clàssic **no** té classe: és l'absència de `skin-*`.

Un tema pot afegir, a sota del bloc de tokens, regles pròpies per als
components que necessitin un tractament que cap token pot expressar
(serigrafia, mecànica de pressió, capçaleres de panell). Aquestes regles han
d'anar **totes** sota `body.skin-<id>`, mai soltes: així el Clàssic queda
intacte per construcció.

---

## Els ganxos

### Superfícies i vores

| Token | Què és |
|---|---|
| `--bg` | fons base de l'app |
| `--surface` | panells, cards, capçalera |
| `--surface2` | controls, camps |
| `--surface3` | hover de control |
| `--raised` | superfície elevada (capçalera de panell, hover) |
| `--inset` | zona **enfonsada**: seqüenciadors, pistes, pantalles |
| `--border` · `--border-h` | vora normal i de hover |
| `--bd-strong` | vora de separació forta (grups, marcs) |
| `--bd-w` | gruix de vora base |

L'elevació es construeix amb **diferència de to entre superfícies**, no amb
ombres apilades.

### Text

`--text` (principal) · `--text2` (secundari) · `--text3` (terciari, silkscreen)

### Color amb rol

| Token | Rol — estricte |
|---|---|
| `--accent` / `--action` | **ho has fet tu**: selecció, edició, creació |
| `--green` / `--signal` | **està viu**: connexió, reproducció, senyal |
| `--red` | gravació / error — ús mínim |
| `--yellow` | pic / avís — ús mínim |

`--action` i `--signal` són àlies semàntics de `--accent` i `--green`. En
qualsevol pantalla s'ha de poder llegir en dos segons què és acció teva i què
està viu. Si un element no encaixa en cap dels dos rols, és gris.

### Geometria

`--radius` (controls) · `--r2` (panells) · `--r-pill` (càpsules) · `--bd-w`

### Tipografia

| Token | Ús |
|---|---|
| `--font` | editorial: titulars, noms, navegació, cos |
| `--mono` | tècnica: **tot dato** — xifres, BPM, canals, IDs, specs |
| `--lbl-font` · `--lbl-ls` · `--lbl-tr` | família, espaiat i caixa de les etiquetes de secció |
| `--data-font` | família dels datos |
| `--num` | `font-variant-numeric` dels datos (`tabular-nums` per alinear columnes) |

### Materialitat

| Token | Què fa |
|---|---|
| `--press` | profunditat tàctil: vora inferior extra dels pulsables |
| `--head-bg` | fons de la capçalera de panell |

---

## Regla per a codi nou

Si escrius un radi, una vora, una família tipogràfica o un color **a mà**, el
tema no hi arribarà mai. Fes servir el token. Quan calgui un valor que no hi
és, afegeix-lo primer al contracte amb el valor del Clàssic i documenta'l
aquí.

---

## Temes actuals

| id | Nom | Caràcter |
|---|---|---|
| *(cap)* | Clàssic | el de sempre: fosc neutre, fonts del sistema, l'únic amb selector de paleta |
| `oniric` | Oníric | consola tècnica: fosc càlid, Inter + IBM Plex Mono, serigrafia de maquinari, controls amb mecànica de pressió |
| `estudi` | Estudi | taller de dia: paper càlid, aire, etiquetes en minúscula, vores fines en comptes de caixes |
| `terminal` | Terminal | una sola família tipogràfica, cantonades a zero i fòsfor ambre — sense resplendor |

Els tres darrers demostren el rang del contracte: l'Oníric canvia la
materialitat, l'Estudi capgira la lluminositat sencera i el Terminal porta la
geometria a l'extrem. Cap dels tres toca ni una regla de l'app.

---

## Afegir-ne un de nou

1. `css/reserva-estetica/<id>.css` amb tot sota `body.skin-<id>`.
2. `<link>` al `<head>` de l'app.
3. Una entrada a `SKINS` de `js/tecla-skins.js` (`id`, `nom`, `rev`, `desc`,
   `paletes`, `mostra`).
4. L'`id` a la llista del script anti-parpelleig del `<head>`.

Res més: ni una línia de CSS de l'app.

### Les fonts

`fonts/fonts.css` serveix Inter i IBM Plex Mono **en local**, amb
`unicode-range` per subconjunt. Els fitxers `latin-ext` només es baixen si
apareix un caràcter d'aquell rang (la `ŀ` catalana, per exemple): ara mateix
no n'hi ha cap i el navegador no els demana mai.

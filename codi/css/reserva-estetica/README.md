# Reserva estètica — no està carregat enlloc

Res d'aquesta carpeta el llegeix l'app. Cap `<link>`, cap `import`. És material
guardat d'un intent de temes alternatius (juliol 2026) que es va provar i es va
aparcar. Es conserva perquè la idea segueix viva, no perquè s'hagi de fer servir
tal com està.

## Què hi ha

| Fitxer | Què és |
|---|---|
| `oniric.css` · `estudi.css` · `terminal.css` | Tres re-pintats complets de l'app (color, geometria, tipografia, materialitat) |
| `CONTRACTE.md` | Els ganxos que un tema podia tocar |
| `lab-consola.css` · `lab-consola-marcatge.html` | La composició de «consola» aplicada al Laboratori de Modes |

També hi ha `codi/fonts/` (Inter i IBM Plex Mono en local, OFL), que els temes
feien servir i que ara no carrega ningú.

## Per què es va aparcar

**Els tres temes.** Eren un canvi d'**aparença**, no de disseny. Canviaven el
color, el radi i la família tipogràfica, però la pantalla continuava tenint la
mateixa forma: les mateixes caixes als mateixos llocs. Massa poc per dir-ne
tema, i massa per posar-ho a la pestanya Aparença com si fos una decisió
important.

**La consola del Laboratori.** Aquesta sí que canviava la forma —tira de
lectura, panells amb capçalera, famílies en llista— però pel camí es va perdre
l'estètica de la mini-app, que és la que li dona caràcter. Canviar la
composició d'una pantalla que ja funciona surt car i no compensa si el resultat
no és clarament millor.

## El que se n'aprèn, per si es reprèn

1. **El color ja està resolt.** L'app té 167 usos de `var()` per 13 valors
   escrits a mà: repintar-la és trivial i és el que menys es nota.

2. **La forma no.** Hi ha ~60 radis, ~144 mides de lletra i ~95 coixins escrits
   a mà. Mentre siguin allà, cap sistema de tokens pot canviar la *forma* de
   res. Un tema de debò passa per aquí, no per la paleta.

3. **Una pantalla, sencera, val més que tota l'app a mitges.** L'error va ser
   voler tocar-ho tot alhora i acabar tocant-ho tot poc. Si es reprèn, val més
   agafar **una pestanya**, redissenyar-la de debò —composició inclosa— i
   comparar-la amb l'actual. Si guanya, es continua; si no, s'ha perdut una
   pestanya i no l'app.

4. **La mini-app original té una estètica pròpia i és un actiu.** El vidre, les
   cantonades llargues i les targetes amb resplendor no són un accident: són el
   que la fa sentir un lloc a part dins de l'app. Qualsevol proposta nova
   competeix contra això, no contra un full en blanc.

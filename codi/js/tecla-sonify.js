/**
 * Sonificació — d'una imatge o d'un vídeo a una corba de característiques.
 *
 * La regla que mana en tota aquesta família: **el vídeo no viatja**. L'anàlisi
 * es fa aquí, al navegador, on hi ha una GPU i gigabytes de RAM; el que s'
 * incrusta al mode generat és NOMÉS la corba resultant, que són uns quants
 * milers de bytes. A la Pico no hi arriba ni un píxel.
 *
 * És l'invers exacte de la família algorísmica: allà el que viatja és
 * l'algorisme i el resultat es calcula al dispositiu; aquí el que viatja és el
 * resultat, perquè l'algorisme no hi cabria de cap manera.
 *
 * ── El format de la corba ────────────────────────────────────────────────
 * Una llista de punts, i cada punt són quatre nombres sencers:
 *
 *   [dt, nota, força, amplada]
 *     dt       mil·lisegons des del punt anterior (el primer, des del principi)
 *     nota     0–127, la posició vertical del que passa (a dalt = agut)
 *     força    0–127, quanta energia hi ha
 *     amplada  0–36, com d'escampat està (→ obertura de l'acord)
 *
 * El `dt` en comptes d'un índex de fotograma és el que fa possible la
 * REDUCCIÓ: els trossos on no passa res no gasten cap punt, només allarguen
 * el dt del següent. Un vídeo de cinc minuts amb una càmera fixa pot ocupar
 * menys que un de deu segons ple de moviment, que és com ha de ser.
 */

/** Lluminositat perceptual d'un píxel RGB (Rec. 709). */
function llum(r, g, b) {
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
}

/**
 * Analitza UNA columna de píxels i en treu el centre, l'energia i l'amplada.
 * @param {Uint8ClampedArray} dades  píxels RGBA de la imatge sencera
 * @param {number} w  amplada en píxels
 * @param {number} h  alçada en píxels
 * @param {number} x  quina columna
 * @param {number} llindar  per sota d'això, el píxel no compta (0–1)
 * @returns {{centre:number, energia:number, amplada:number}}
 *   centre i amplada en 0–1 des de BAIX (0 = a baix de tot)
 */
export function analitzaColumna(dades, w, h, x, llindar = 0.06) {
    let suma = 0, sumaY = 0, sumaY2 = 0;
    for (let y = 0; y < h; y++) {
        const i = (y * w + x) * 4;
        const l = llum(dades[i], dades[i + 1], dades[i + 2]);
        if (l < llindar) continue;
        // y=0 és a dalt de la imatge; el capgirem perquè amunt sigui agut
        const py = (h - 1 - y) / (h - 1 || 1);
        suma += l;
        sumaY += l * py;
        sumaY2 += l * py * py;
    }
    if (suma <= 0) return { centre: 0, energia: 0, amplada: 0 };
    const centre = sumaY / suma;
    // Desviació típica ponderada: com d'escampada està la llum a la columna
    const varia = Math.max(0, sumaY2 / suma - centre * centre);
    return {
        centre,
        energia: Math.min(1, suma / h),
        amplada: Math.sqrt(varia),
    };
}

/**
 * Una IMATGE fixa → corba, llegint-la com una partitura: una columna que
 * escombra d'esquerra a dreta i, a cada moment, la llum diu quina alçada
 * sona. És com llegeix l'ANS rus o el Metasynth, i és la manera més directa
 * que hi ha de sentir un dibuix.
 *
 * @param {{data:Uint8ClampedArray, width:number, height:number}} img
 * @param {object} [opc]
 * @param {number} [opc.columnes=128]  quantes lectures d'esquerra a dreta
 * @param {number} [opc.durada=8000]   quant dura l'escombrada, en ms
 * @returns {number[][]} la corba [[dt, nota, força, amplada], …]
 */
export function analitzaImatge(img, opc = {}) {
    const { columnes = 128, durada = 8000 } = opc;
    const { data, width: w, height: h } = img;
    const n = Math.max(2, Math.min(columnes, w));
    const dt = Math.max(1, Math.round(durada / n));
    const corba = [];
    for (let k = 0; k < n; k++) {
        const x = Math.min(w - 1, Math.round((k / (n - 1)) * (w - 1)));
        const c = analitzaColumna(data, w, h, x);
        corba.push([
            dt,
            Math.round(c.centre * 127),
            Math.round(c.energia * 127),
            Math.round(c.amplada * 72),      // 0–0.5 típic → 0–36
        ]);
    }
    return corba;
}

/**
 * Dos fotogrames de VÍDEO → un punt de la corba, per DIFERÈNCIA.
 *
 * El que sona no és la imatge sinó el que s'hi MOU: es comparen els dos
 * fotogrames píxel a píxel i només compten els que han canviat prou. Amb una
 * càmera fixa i res al davant, l'energia és zero i el punt no arriba ni a
 * entrar a la corba.
 *
 * @returns {{centre:number, energia:number, amplada:number, deriva:number}}
 *   deriva = cap on s'ha desplaçat el centre respecte de l'anterior (−1..1)
 */
export function analitzaMoviment(ara, abans, w, h, opc = {}) {
    const { llindar = 0.08, mostreig = 2 } = opc;
    let suma = 0, sumaY = 0, sumaY2 = 0, sumaX = 0;
    for (let y = 0; y < h; y += mostreig) {
        for (let x = 0; x < w; x += mostreig) {
            const i = (y * w + x) * 4;
            const d = Math.abs(llum(ara[i], ara[i + 1], ara[i + 2])
                             - llum(abans[i], abans[i + 1], abans[i + 2]));
            if (d < llindar) continue;
            const py = (h - 1 - y) / (h - 1 || 1);
            suma += d;
            sumaY += d * py;
            sumaY2 += d * py * py;
            sumaX += d * (x / (w - 1 || 1));
        }
    }
    if (suma <= 0) return { centre: 0, energia: 0, amplada: 0, deriva: 0 };
    const centre = sumaY / suma;
    const varia = Math.max(0, sumaY2 / suma - centre * centre);
    return {
        centre,
        // Normalitzat pel nombre de píxels mirats, no per la mida del vídeo
        energia: Math.min(1, suma / ((w * h) / (mostreig * mostreig)) * 24),
        amplada: Math.sqrt(varia),
        deriva: sumaX / suma,
    };
}

/**
 * REDUCCIÓ de la corba: el que fa que això càpiga a una Pico.
 *
 * Es queda només els punts on de fet CANVIA alguna cosa. Els trams quiets no
 * gasten punts: només allarguen el `dt` del punt següent. A més de fer-ho
 * petit, musicalment és millor —un silenci llarg és un silenci, no dos-cents
 * fotogrames idèntics— i és exactament el que fa qualsevol format de vídeo.
 *
 * @param {number[][]} corba
 * @param {object} [opc]
 * @param {number} [opc.saltNota=3]   canvi mínim d'alçada per desar un punt
 * @param {number} [opc.saltForca=6]  canvi mínim de força
 * @param {number} [opc.maxPunts=512] sostre dur: es va afluixant fins a cabre-hi
 * @param {number} [opc.maxDt=2000]   més enllà d'això, un punt igualment
 * @returns {number[][]}
 */
export function redueix(corba, opc = {}) {
    const { saltNota = 3, saltForca = 6, maxPunts = 512, maxDt = 2000 } = opc;
    if (!corba || corba.length <= 2) return corba || [];

    const passada = (sn, sf) => {
        const out = [corba[0].slice()];
        let ref = corba[0], acumulat = 0;
        for (let i = 1; i < corba.length; i++) {
            const p = corba[i];
            acumulat += p[0];
            const canvia = Math.abs(p[1] - ref[1]) >= sn
                        || Math.abs(p[2] - ref[2]) >= sf
                        || acumulat >= maxDt;
            const últim = i === corba.length - 1;
            if (canvia || últim) {
                out.push([acumulat, p[1], p[2], p[3]]);
                ref = p;
                acumulat = 0;
            }
        }
        return out;
    };

    // S'afluixen els llindars fins que hi càpiga: així el sostre és dur i el
    // resultat, el més fidel que hi càpiga.
    let sn = saltNota, sf = saltForca, out = passada(sn, sf);
    let voltes = 0;
    while (out.length > maxPunts && voltes++ < 24) {
        sn = Math.ceil(sn * 1.45);
        sf = Math.ceil(sf * 1.45);
        out = passada(sn, sf);
    }
    return out;
}

/** Quants bytes ocuparà la corba dins del .py (aproximació honesta). */
export function pesCorba(corba) {
    // "(1234, 100, 90, 12)," → una quinzena de caràcters per punt
    return (corba || []).reduce((s, p) => s + p.join(',').length + 4, 0);
}

/** Estadístiques de la corba, per ensenyar-les al formulari. */
export function resumCorba(corba) {
    if (!corba || !corba.length) return { punts: 0, durada: 0, notaMin: 0, notaMax: 0, forcaMitja: 0 };
    let durada = 0, nMin = 127, nMax = 0, fSuma = 0, actius = 0;
    for (const [dt, nota, forca] of corba) {
        durada += dt;
        if (forca > 0) {
            if (nota < nMin) nMin = nota;
            if (nota > nMax) nMax = nota;
            fSuma += forca;
            actius++;
        }
    }
    return {
        punts: corba.length,
        durada,
        notaMin: actius ? nMin : 0,
        notaMax: actius ? nMax : 0,
        forcaMitja: actius ? Math.round(fSuma / actius) : 0,
    };
}

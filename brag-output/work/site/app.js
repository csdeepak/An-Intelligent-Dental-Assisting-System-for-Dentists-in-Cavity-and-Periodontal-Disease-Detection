/* Panel-review composition. Every frame is a pure function of t (seconds): window.renderAt(t).
   Timing comes from timeline.json (narration word boundaries), data from the traced pipeline run. */
(() => {
  const D = window.DATA, TL = D.timeline, IMG = D.image, TOTAL = TL.total;
  const S = {}; TL.scenes.forEach(s => { S[s.id] = s; s.end = s.start + s.dur; });
  const $ = q => document.querySelector(q);
  const $$ = q => Array.from(document.querySelectorAll(q));
  const NS = "http://www.w3.org/2000/svg";
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  const E = {
    lin: p => p,
    out: p => 1 - Math.pow(1 - p, 3),
    inOut: p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
    back: p => { const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); },
  };
  const P = (t, a, d) => clamp((t - a) / d);
  const norm = s => s.toLowerCase().replace(/[^a-z0-9\-]/g, "");
  const missing = [];
  function cue(id, word, n = 0) {           // global time of the n-th occurrence of `word` in scene `id`
    let k = 0;
    for (const w of S[id].words) if (norm(w.w) === norm(word)) { if (k === n) return S[id].start + w.t; k++; }
    missing.push(`${id}:${word}:${n}`);
    return S[id].start + S[id].voice_at;
  }
  window.__missingCues = missing;
  function alphaRange(t, t0, t1, fin = 0.45, fout = 0.4) {
    if (t < t0 || t > t1) return 0;
    return Math.min(clamp((t - t0) / fin), clamp((t1 - t) / fout));
  }
  function rv(el, t, t0, o = {}) {           // reveal: fade + rise (+ optional scale), pure in t
    if (!el) return 0;
    const d = o.d ?? 0.6, dy = o.dy ?? 22, dx = o.dx ?? 0, s0 = o.s ?? 1;
    const p = (o.ease || E.out)(P(t, t0, d));
    el.style.opacity = p * (o.max ?? 1);
    el.style.transform = `translate(${dx * (1 - p)}px, ${dy * (1 - p)}px) scale(${s0 + (1 - s0) * p})`;
    return p;
  }
  const fmt = (v, d = 1) => v.toFixed(d);
  const svgEl = (tag, attrs = {}, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };

  /* ------------------------------------------------------------ data helpers */
  const teeth = D.teeth.map(t => ({ ...t, cx: (t.box[0] + t.box[2]) / 2, cy: (t.box[1] + t.box[3]) / 2,
    w: t.box[2] - t.box[0], h: t.box[3] - t.box[1], q: Math.floor(t.fdi / 10) }));
  const byFdi = {}; teeth.forEach(t => byFdi[t.fdi] = t);
  const flagged = teeth.filter(t => t.caries !== "no_caries").map(t => t.fdi);
  const gtSet = new Set(D.gtCaries.map(g => g.fdi));
  const hits = flagged.filter(f => gtSet.has(f)), extras = flagged.filter(f => !gtSet.has(f));
  const missed = [...gtSet].filter(f => !flagged.includes(f)).sort((a, b) => a - b);
  const R = (() => {                        // the dentition's bounding region
    const x1 = Math.min(...teeth.map(t => t.box[0])), x2 = Math.max(...teeth.map(t => t.box[2]));
    const y1 = Math.min(...teeth.map(t => t.box[1])), y2 = Math.max(...teeth.map(t => t.box[3]));
    return { x1, x2, y1, y2, cx: (x1 + x2) / 2, cy: (y1 + y2) / 2, w: x2 - x1, h: y2 - y1 };
  })();
  const archOrder = [...teeth].sort((a, b) => {
    const row = t => (t.q === 1 || t.q === 2 ? 0 : 1);
    return row(a) - row(b) || a.cx - b.cx;
  });

  /* ------------------------------------------------------------ chrome */
  const PARTS = [
    { n: "01", title: "Introduction", a: "s02_problem", b: "s05_constant" },
    { n: "02", title: "Architecture — one image through every stage", a: "s06_input", b: "s13_truth" },
    { n: "03", title: "Results across the timeline", a: "s14_timeline", b: "s20_takeaway" },
  ];
  const partBig = $("#partBig"), partSmall = $("#partSmall");
  function renderChrome(t) {
    $("#progFill").style.width = `${(100 * t) / TOTAL}%`;
    const g = $("#glow");
    g.style.left = `${-200 + 380 * Math.sin(t / 23)}px`;
    g.style.top = `${-760 + 220 * Math.cos(t / 31)}px`;
    let big = 0, small = 0, part = null;
    for (const p of PARTS) {
      const t0 = S[p.a].start, t1 = S[p.b].end;
      if (t >= t0 && t <= t1) {
        part = p;
        const l = t - t0;
        big = l < 1.35 ? Math.min(clamp(l / 0.25), clamp((1.35 - l) / 0.4)) : 0;
        small = alphaRange(t, t0 + 1.25, t1, 0.5, 0.4);
        const shrink = E.inOut(P(l, 0.95, 0.4));
        partBig.style.transform = `translate(${-600 * shrink}px, ${-380 * shrink}px) scale(${1 - 0.6 * shrink})`;
      }
    }
    if (part) {
      partBig.querySelector(".pn").textContent = part.n;
      partBig.querySelector(".pt").textContent = part.title;
      partSmall.querySelector(".pn").textContent = part.n;
      partSmall.querySelector(".pt").textContent = part.title;
    }
    partBig.style.opacity = big;
    partSmall.style.opacity = small;
    // source line of the scene on screen
    let src = "", sa = 0;
    for (const s of TL.scenes) {
      const a = alphaRange(t, s.start, s.end, 0.5, 0.4);
      if (a > sa) { sa = a; src = document.getElementById(s.id)?.dataset.source || ""; }
    }
    const se = $("#source");
    if (se.textContent !== src) se.textContent = src;
    se.style.opacity = src ? sa * 0.95 : 0;
  }

  /* ============================================================ S01 TITLE */
  function s01(t) {
    const s = S.s01_title, el = $("#s01_title");
    el.style.opacity = alphaRange(t, s.start, s.end, 0.6, 0.5);
    if (t > s.end + 0.1) return;
    const l = t - s.start;
    $(".title-bg img").style.transform = `scale(${1.08 - 0.06 * (l / s.dur)}) translateX(${-30 * (l / s.dur)}px)`;
    $(".title-scan").style.transform = `translateX(${-260 + 2400 * E.inOut(P(l, 0.2, 4.5))}px)`;
    rv($("#s01_title .r1"), t, s.start + 0.35);
    rv($("#s01_title .r2"), t, s.start + 0.75, { dy: 34, d: 0.8 });
    rv($("#s01_title .r3"), t, cue("s01_title", "intelligent"));
    rv($("#s01_title .r4"), t, cue("s01_title", "reads"));
  }

  /* ============================================================ S02 PROBLEM */
  const lensPath = (() => {                  // the lens visits the upper teeth, left to right
    const up = teeth.filter(t => t.q === 1 || t.q === 2).sort((a, b) => a.cx - b.cx);
    return up.map(t => [t.cx, t.cy + t.h * 0.15]);
  })();
  function buildS02() {
    const m = $("#fdiMini");
    const rows = [[18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28],
                  [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]];
    rows.flat().forEach(c => { const d = document.createElement("div"); d.textContent = c; d.className = "q" + Math.floor(c / 10); m.appendChild(d); });
    const sw = svgEl("rect", { id: "p2band", x: 0, y: 0, width: 260, height: 1536, fill: "url(#p2grad)", opacity: 0 }, $("#p2sweep"));
    const defs = svgEl("defs", {}, $("#p2svg"));
    const lg = svgEl("linearGradient", { id: "p2grad", x1: 0, y1: 0, x2: 1, y2: 0 }, defs);
    svgEl("stop", { offset: 0, "stop-color": "#2DD4BF", "stop-opacity": 0 }, lg);
    svgEl("stop", { offset: 0.5, "stop-color": "#2DD4BF", "stop-opacity": 0.35 }, lg);
    svgEl("stop", { offset: 1, "stop-color": "#2DD4BF", "stop-opacity": 0 }, lg);
    return sw;
  }
  let p2band;
  function s02(t) {
    const s = S.s02_problem, el = $("#s02_problem");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#p2opg"), t, s.start + 1.2, { dy: 30, d: 0.8 });
    const te = cue("s02_problem", "every");
    p2band.setAttribute("opacity", Math.min(P(t, te, 0.3), 1 - P(t, te + 1.8, 0.4)));
    p2band.setAttribute("x", lerp(R.x1 - 300, R.x2 + 40, E.inOut(P(t, te, 2.0))));
    // magnifier
    const l0 = cue("s02_problem", "dentist"), l1 = cue("s02_problem", "automate");
    const la = Math.min(P(t, l0 - 0.3, 0.4), 1 - P(t, l1 + 0.6, 0.4));
    const p = E.inOut(P(t, l0, l1 - l0 + 0.5)) * (lensPath.length - 1);
    const i = Math.min(Math.floor(p), lensPath.length - 2), f = p - i;
    const cx = lerp(lensPath[i][0], lensPath[i + 1][0], f), cy = lerp(lensPath[i][1], lensPath[i + 1][1], f);
    $("#lensC").setAttribute("cx", cx); $("#lensC").setAttribute("cy", cy);
    $("#lensRing").setAttribute("cx", cx); $("#lensRing").setAttribute("cy", cy);
    $("#lensImg").setAttribute("transform", `translate(${cx} ${cy}) scale(2.1) translate(${-cx} ${-cy})`);
    $("#lensG").setAttribute("opacity", la); $("#lensRing").setAttribute("opacity", la);
    rv($("#st1"), t, cue("s02_problem", "find"), { dx: 40, dy: 0 });
    rv($("#st2"), t, cue("s02_problem", "number"), { dx: 40, dy: 0 });
    rv($("#st3"), t, cue("s02_problem", "report"), { dx: 40, dy: 0 });
    const tf = cue("s02_problem", "F");
    $$("#fdiMini div").forEach((d, k) => { d.style.opacity = E.out(P(t, tf + (k % 16) * 0.035 + Math.floor(k / 16) * 0.25, 0.3)); });
  }

  /* ============================================================ S03 BUILT */
  const NODE_X = [262, 470, 678, 886, 1094, 1302];
  function buildS03() {
    $$("#pipe .pnode").forEach((n, i) => n.style.left = NODE_X[i] + "px");
    const pipe = $("#pipe");
    const xs = [[230, 262], ...NODE_X.slice(0, 5).map((x, i) => [x + 178, NODE_X[i + 1]]), [1302 + 178, 1550]];
    xs.forEach(([a, b]) => { const c = document.createElement("div"); c.className = "conn";
      Object.assign(c.style, { position: "absolute", left: a + "px", top: "103px", width: (b - a) + "px", height: "3px", background: "#22314A" });
      const f = document.createElement("div"); Object.assign(f.style, { height: "100%", width: "0", background: "linear-gradient(90deg,#3B82F6,#2DD4BF)" });
      c.appendChild(f); pipe.appendChild(c); });
  }
  function s03(t) {
    const s = S.s03_built, el = $("#s03_built");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#s03_built .scene-title"), t, s.start + 0.2);
    const tn = cue("s03_built", "six-stage");
    $$("#pipe .pnode").forEach((n, i) => rv(n, t, tn + i * 0.16, { dy: 26 }));
    rv($("#pin"), t, tn - 0.2, { dx: -30, dy: 0 });
    const t0 = cue("s03_built", "takes"), t1 = cue("s03_built", "overlay");
    const pk = $("#packet"), pp = E.inOut(P(t, t0, t1 - t0));
    pk.style.left = lerp(150, 1640, pp) + "px";
    pk.style.opacity = Math.min(P(t, t0, 0.2), 1 - P(t, t1 + 0.2, 0.3));
    const px = lerp(150, 1640, pp);
    $$("#pipe .conn").forEach(c => { const a = parseFloat(c.style.left), w = parseFloat(c.style.width);
      c.firstChild.style.width = 100 * clamp((px - a) / w) + "%"; });
    $$("#pipe .pnode").forEach((n, i) => { const on = px > NODE_X[i] && px < NODE_X[i] + 178;
      n.style.borderColor = on ? "#2DD4BF" : (px > NODE_X[i] ? "#2C3A52" : "");
      n.style.boxShadow = on ? "0 0 30px rgba(45,212,191,0.35)" : ""; });
    rv($("#pout"), t, t1, { dx: 30, dy: 0 });
    const ta = cue("s03_built", "about"), tp = cue("s03_built", "ninety-five"), ts = cue("s03_built", "Streamlit");
    rv($("#stat1"), t, ta - 0.2); $("#cSpeed").textContent = fmt(1.70 * E.out(P(t, ta, 1.0)), 2);
    rv($("#stat2"), t, tp - 0.2); $("#cParams").textContent = fmt(95.3 * E.out(P(t, tp, 1.0)), 1);
    rv($("#stat3"), t, ts - 0.2);
  }

  /* ============================================================ S04 DATA */
  function s04(t) {
    const s = S.s04_data, el = $("#s04_data");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#s04_data .scene-title"), t, s.start + 0.2);
    rv($("#d1"), t, cue("s04_data", "Tufts") - 0.15, { dy: 30 });
    rv($("#d2"), t, cue("s04_data", "DENTEX") - 0.15, { dy: 30 });
    rv($("#d3"), t, cue("s04_data", "CariesXrays") - 0.15, { dy: 30 });
    rv($("#d4"), t, cue("s04_data", "Ningxia") - 0.15, { dy: 30 });
    rv($("#d5"), t, cue("s04_data", "UFBA-425") - 0.15, { dy: 30 });
    rv($("#d6"), t, cue("s04_data", "UFBA-425") + 1.6, { dy: 10 });
  }

  /* ============================================================ S05 CONSTANT */
  const CONST8 = [16, 17, 26, 27, 36, 37, 46, 47];
  function buildS05() {
    const ch = $("#toothChart");
    const up = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
    const lo = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];
    [up, lo].forEach((row, r) => row.forEach((c, i) => {
      const d = document.createElement("div"); d.className = "ttooth" + (r ? " low" : ""); d.textContent = c; d.dataset.fdi = c;
      const u = (i - 7.5) / 7.5, x = 6 + i * 62, y = (r ? 300 : 120) - 64 * u * u;
      d.style.left = x + "px"; d.style.top = y + "px"; ch.appendChild(d);
    }));
  }
  function s05(t) {
    const s = S.s05_constant, el = $("#s05_constant");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#s05_constant .scene-title"), t, s.start + 0.2);
    rv($(".chart-wrap"), t, s.start + 0.5, { dy: 30 });
    const tm = cue("s05_constant", "molars"), te = cue("s05_constant", "eight");
    $$(".ttooth").forEach((d, k) => {
      const f = +d.dataset.fdi, pos = f % 10, isM = pos >= 6, is8 = CONST8.includes(f);
      const warm = isM ? E.out(P(t, tm + (k % 16) * 0.02, 0.5)) : 0;
      const solid = is8 ? E.back(P(t, te + CONST8.indexOf(f) * 0.07, 0.45)) : 0;
      const fade8 = isM && !is8 ? P(t, te, 0.5) : 0;
      const a = solid > 0 ? 1 : warm * (1 - fade8) * 0.45;
      d.style.background = solid > 0 ? `rgba(245,158,11,${0.18 + 0.7 * clamp(solid)})` : `rgba(245,158,11,${a * 0.5})`;
      d.style.borderColor = solid > 0 ? "#F59E0B" : (a > 0.05 ? "rgba(245,158,11,0.6)" : "#33415A");
      d.style.color = solid > 0.5 ? "#1A1206" : "#9AA7BC";
      d.style.transform = `scale(${1 + 0.12 * Math.sin(Math.PI * clamp(solid))})`;
    });
    rv($(".chart-legend"), t, te + 0.8, { dy: 8 });
    rv($("#cs1"), t, cue("s05_constant", "ignores"), { dx: 40, dy: 0 });
    rv($("#cs2"), t, cue("s05_constant", "scores"), { dx: 40, dy: 0 });
    rv($("#cs3"), t, cue("s05_constant", "Every"), { dx: 40, dy: 0 });
  }

  /* ============================================================ PART 2 — FLOW */
  const VIEW_BIG = { x: 160, y: 215, w: 1600, h: 800 }, VIEW_SIDE = { x: 656, y: 210, w: 1168, h: 790 };
  const QCOL = { 1: "#60A5FA", 2: "#34D399", 3: "#FBBF24", 4: "#F472B6" };
  const SVG = { boxes: [], labels: [], badges: [], rings: [], les: [], links: [], gt: [], hitB: [], missB: [] };
  let scanRect, cropFdiRect, cropS4Rect, flyFdi, flyS4, slotFdiRect, slotS4Rect, hl16;

  function buildFlow() {
    const defs = $("#vsvg defs");
    const lg = svgEl("linearGradient", { id: "scanH", x1: 0, y1: 0, x2: 1, y2: 0 }, defs);
    svgEl("stop", { offset: 0, "stop-color": "#2DD4BF", "stop-opacity": 0 }, lg);
    svgEl("stop", { offset: 0.5, "stop-color": "#2DD4BF", "stop-opacity": 0.5 }, lg);
    svgEl("stop", { offset: 1, "stop-color": "#2DD4BF", "stop-opacity": 0 }, lg);
    $("#scan").remove();
    scanRect = svgEl("rect", { x: 0, y: 0, width: 220, height: IMG.h, fill: "url(#scanH)", opacity: 0 }, $("#rot"));
    $("#rot").insertBefore(scanRect, $("#gGT"));
    D.gtCaries.forEach(g => SVG.gt.push(svgEl("polygon", { points: g.points.map(p => p.join(",")).join(" "),
      fill: "rgba(52,211,153,0.16)", stroke: "#34D399", "stroke-linejoin": "round", opacity: 0 }, $("#gGT"))));
    teeth.forEach(t => {
      const r = svgEl("rect", { x: t.box[0], y: t.box[1], width: t.w, height: t.h, rx: 6, fill: "none", stroke: "#60A5FA", opacity: 0 }, $("#gBoxes"));
      r.dataset.per = 2 * (t.w + t.h); SVG.boxes.push(r);
      const g = svgEl("g", { opacity: 0 }, $("#gLabels"));
      const bg = svgEl("rect", { rx: 4, fill: "rgba(7,11,20,0.82)" }, g);
      const tx = svgEl("text", { "font-family": "Segoe UI Variable Text, Segoe UI", "font-weight": 700, fill: "#E8EDF5", "text-anchor": "middle" }, g);
      tx.textContent = t.fdi; SVG.labels.push({ g, bg, tx });
      const bgB = svgEl("g", { opacity: 0 }, $("#gBadges"));
      const bb = svgEl("rect", { rx: 4 }, bgB), bt = svgEl("text", { "font-family": "Segoe UI Variable Text, Segoe UI", "font-weight": 800, "text-anchor": "middle" }, bgB);
      SVG.badges.push({ g: bgB, bg: bb, tx: bt });
      SVG.rings.push(svgEl("rect", { x: t.box[0] - 14, y: t.box[1] - 14, width: t.w + 28, height: t.h + 28, rx: 14, fill: "rgba(167,139,250,0.12)", stroke: "#A78BFA", opacity: 0 }, $("#gBadges")));
      const hb = svgEl("g", { opacity: 0 }, $("#gBadges"));
      svgEl("circle", { r: 1, fill: "#34D399" }, hb); const ht = svgEl("text", { "text-anchor": "middle", "font-weight": 800, fill: "#06281D", "font-family": "Segoe UI Variable Text, Segoe UI" }, hb);
      ht.textContent = "✓"; SVG.hitB.push(hb);
      SVG.missB.push(svgEl("rect", { x: t.box[0] - 8, y: t.box[1] - 8, width: t.w + 16, height: t.h + 16, rx: 10, fill: "none", stroke: "#34D399", opacity: 0 }, $("#gBadges")));
    });
    D.lesions.forEach(l => {
      const [x1, y1, x2, y2] = l.box;
      const g = svgEl("g", { opacity: 0 }, $("#gLes"));
      svgEl("rect", { x: x1, y: y1, width: x2 - x1, height: y2 - y1, rx: 5, fill: "rgba(251,113,133,0.18)", stroke: "#FB7185" }, g);
      const tx = svgEl("text", { x: x1, y: y1 - 10, fill: "#FFC2CC", "font-family": "Consolas", "font-weight": 700 }, g);
      tx.textContent = l.conf.toFixed(2);
      const tt = byFdi[l.tooth];
      const ln = svgEl("line", { x1: (x1 + x2) / 2, y1: (y1 + y2) / 2, x2: tt.cx, y2: tt.cy, stroke: "#FB7185", "stroke-linecap": "round", opacity: 0 }, $("#gLinks"));
      SVG.les.push({ g, tx, l }); SVG.links.push(ln);
    });
    const cb = D.crops.crop_fdi.box, sb = D.crops.crop_s4.box;
    cropFdiRect = svgEl("rect", { x: cb[0], y: cb[1], width: cb[2] - cb[0], height: cb[3] - cb[1], rx: 8, fill: "rgba(45,212,191,0.08)", stroke: "#2DD4BF", opacity: 0 }, $("#gCrop"));
    cropS4Rect = svgEl("rect", { x: sb[0], y: sb[1], width: sb[2] - sb[0], height: sb[3] - sb[1], rx: 8, fill: "rgba(167,139,250,0.08)", stroke: "#A78BFA", opacity: 0 }, $("#gCrop"));
    const b16 = byFdi[16].box;
    hl16 = svgEl("rect", { x: b16[0] - 18, y: b16[1] - 18, width: b16[2] - b16[0] + 36, height: b16[3] - b16[1] + 36, rx: 14, fill: "none", stroke: "#FFFFFF", opacity: 0 }, $("#gBadges"));
    // panel pieces
    const hist = $("#hist"), confs = teeth.map(t => t.det).sort((a, b) => b - a);
    confs.forEach(c => { const b = document.createElement("div"); b.className = "bar"; b.dataset.h = (c - 0.5) / 0.5 * 150; hist.appendChild(b); });
    const thr = document.createElement("div"); thr.className = "thr"; thr.style.bottom = (Math.min(...confs) - 0.5) / 0.5 * 150 + "px"; hist.appendChild(thr);
    const quad = $("#quad");
    [[18, 17, 16, 15, 14, 13, 12, 11], [21, 22, 23, 24, 25, 26, 27, 28], [48, 47, 46, 45, 44, 43, 42, 41], [31, 32, 33, 34, 35, 36, 37, 38]]
      .flat().forEach(c => { const d = document.createElement("div"); d.textContent = c; d.dataset.fdi = c; quad.appendChild(d); });
    const sev = $("#sevlist");
    flagged.forEach(f => { const d = document.createElement("div"); const deep = byFdi[f].caries === "deep_caries";
      d.className = deep ? "deep" : ""; d.textContent = `${f} · ${deep ? "deep" : "caries"}`; d.dataset.fdi = f; sev.appendChild(d); });
    // JSON record
    const r = D.record16;
    const rec = { fdi: r.fdi, bbox_xyxy: r.bbox_xyxy, detection_confidence: r.detection_confidence, fdi_confidence: r.fdi_confidence,
      caries: { finding: r.caries.finding, severity: r.caries.severity, gate_confidence: r.caries.gate_confidence },
      bone_loss: { finding: r.bone_loss.finding, confidence: r.bone_loss.confidence, severity: r.bone_loss.severity }, assessable: r.assessable };
    const lines = JSON.stringify(rec, null, 2).replace(/\[\n\s+([^\]]+?)\n\s+\]/g, (m, a) => "[" + a.replace(/\s*\n\s*/g, " ") + "]").split("\n");
    $("#json").innerHTML = lines.map(L => `<div class="jl">${L
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/"([^"]+)":/g, '<span class="k">"$1"</span><span class="p">:</span>')
      .replace(/: "([^"]*)"/g, ': <span class="s">"$1"</span>')
      .replace(/(-?\d+\.?\d*)(?=[,\]\s]|$)/g, '<span class="n">$1</span>')}</div>`).join("");
    const M = D.models;
    $("#models").innerHTML = `<div style="color:#8C99AF;margin-bottom:4px">models block · sha256 (first 12)</div>` +
      [["detector", M.detector], ["fdi_head", M.fdi_head], ["caries", M.caries], ["stage 4", M.bone_loss]]
        .map(([k, v]) => `<div class="ml"><b>${k.padEnd(9, " ").replace(/ /g, "&nbsp;")}</b> ${v.sha}</div>`).join("");
    // flyers
    const st = $("#stage");
    const mk = src => { const im = document.createElement("img"); im.src = src; im.className = "flyer"; st.appendChild(im); return im; };
    flyFdi = mk("assets/crop_fdi.png"); flyS4 = mk("assets/crop_s4.png");
    const asp = b => (b[2] - b[0]) / (b[3] - b[1]);
    $("#slotFdi").style.cssText += `;height:150px;width:${Math.round(150 * asp(cb))}px`;
    $("#slotS4").style.cssText += `;height:160px;width:${Math.round(160 * asp(sb))}px`;
  }
  const relRect = el => { const s = $("#stage").getBoundingClientRect(), r = el.getBoundingClientRect();
    return { x: r.left - s.left, y: r.top - s.top, w: r.width, h: r.height }; };

  // camera -------------------------------------------------------------
  const IC = { cx: IMG.w / 2, cy: IMG.h / 2 };
  function regionView() { return { cx: R.cx, cy: R.cy + R.h * 0.02, w: Math.max(R.w * 1.1, R.h * 1.18 * (VIEW_SIDE.w / VIEW_SIDE.h)), rot: 0 }; }
  function boxView(b, aspect = VIEW_SIDE.w / VIEW_SIDE.h, fill = 0.42) {
    const w = b[2] - b[0], h = b[3] - b[1];
    return { cx: (b[0] + b[2]) / 2, cy: (b[1] + b[3]) / 2, w: Math.max(w / fill * 0.9, (h / fill) * aspect * 0.55), rot: 0 };
  }
  let CAM = [];
  function buildCamera() {
    const rv0 = regionView();
    const fullRot = { cx: IC.cx, cy: IC.cy, w: IMG.w * 1.08 * (VIEW_SIDE.w / VIEW_SIDE.h), rot: -90 };
    CAM = [
      { t: S.s06_input.start, d: 0.01, to: { cx: IC.cx, cy: IC.cy, w: IMG.w, rot: 0 } },
      { t: S.s06_input.start + 1.2, d: S.s06_input.dur - 1.0, to: { cx: IC.cx, cy: IC.cy + 30, w: IMG.w * 0.9, rot: 0 } },
      { t: S.s07_detect.start - 0.15, d: 1.1, to: rv0 },
      { t: cue("s07_detect", "rotated") - 0.2, d: 1.1, to: fullRot },
      { t: cue("s07_detect", "maps") - 0.1, d: 1.1, to: rv0 },
      { t: cue("s08_number", "Each"), d: 1.1, to: boxView(D.crops.crop_fdi.box) },
      { t: cue("s08_number", "one-to-one") - 0.2, d: 1.1, to: rv0 },
      { t: cue("s11_abnormal", "ResNet-18") - 0.2, d: 1.1, to: boxView(D.crops.crop_s4.box) },
      { t: cue("s11_abnormal", "here") - 0.4, d: 1.0, to: rv0 },
    ];
  }
  function camAt(t) {
    let s = { ...CAM[0].to };
    for (const k of CAM) {
      if (t < k.t) break;
      const p = E.inOut(P(t, k.t, k.d));
      s = { cx: lerp(s.cx, k.to.cx, p), cy: lerp(s.cy, k.to.cy, p), w: lerp(s.w, k.to.w, p), rot: lerp(s.rot, k.to.rot, p) };
    }
    return s;
  }
  function viewAt(t) {
    const p = E.inOut(P(t, S.s07_detect.start - 0.15, 1.1));
    return { x: lerp(VIEW_BIG.x, VIEW_SIDE.x, p), y: lerp(VIEW_BIG.y, VIEW_SIDE.y, p), w: lerp(VIEW_BIG.w, VIEW_SIDE.w, p), h: lerp(VIEW_BIG.h, VIEW_SIDE.h, p) };
  }
  function toScreen(b, t) {           // image-space box -> stage pixels (camera at time t, no rotation)
    const v = viewAt(t), c = camAt(t), vh = c.w * v.h / v.w, k = v.w / c.w;
    const x0 = c.cx - c.w / 2, y0 = c.cy - vh / 2;
    return { x: v.x + (b[0] - x0) * k, y: v.y + (b[1] - y0) * k, w: (b[2] - b[0]) * k, h: (b[3] - b[1]) * k };
  }
  function fly(el, t, t0, d, fromBox, slot, alpha) {
    if (t < t0) { el.style.opacity = 0; return; }
    const a = toScreen(fromBox, t0), b = slot, p = E.inOut(P(t, t0, d));
    const lift = Math.sin(Math.PI * p) * -60;
    Object.assign(el.style, { left: lerp(a.x, b.x, p) + "px", top: lerp(a.y, b.y, p) + lift + "px", width: lerp(a.w, b.w, p) + "px",
      height: lerp(a.h, b.h, p) + "px", opacity: alpha * clamp(p * 6) });
  }

  function flow(t) {
    const t0 = S.s06_input.start, t1 = S.s13_truth.end, layer = $("#flow");
    const A = alphaRange(t, t0, t1, 0.5, 0.45);
    layer.style.opacity = A;
    if (A <= 0) { flyFdi.style.opacity = 0; flyS4.style.opacity = 0; return; }
    const intro = E.out(P(t, t0 + 1.15, 0.7));
    // viewer layout + camera
    const v = viewAt(t), vw = $("#viewer");
    Object.assign(vw.style, { left: v.x + "px", top: v.y + "px", width: v.w + "px", height: v.h + "px", opacity: intro });
    const c = camAt(t), vh = c.w * v.h / v.w, k = c.w / v.w;     // k = image units per screen px
    $("#vsvg").setAttribute("viewBox", `${c.cx - c.w / 2} ${c.cy - vh / 2} ${c.w} ${vh}`);
    $("#rot").setAttribute("transform", `rotate(${c.rot} ${IC.cx} ${IC.cy})`);
    rv($("#metaChip"), t, cue("s06_input", "sixty-four") - 0.3, { dy: 12, max: 1 - P(t, S.s07_detect.start - 0.2, 0.4) });

    // rail
    const railA = E.out(P(t, cue("s06_input", "through") - 0.3, 0.6));
    $("#rail").style.opacity = railA;
    const stageAt = [["in", S.s06_input.start], ["1", S.s07_detect.start], ["2", S.s08_number.start], ["3", S.s09_lesion.start],
      ["4", S.s11_abnormal.start], ["5", S.s12_report.start]];
    let cur = 0; stageAt.forEach(([, st], i) => { if (t >= st) cur = i; });
    if (t >= S.s13_truth.start) cur = 6;
    $$("#rail .rnode").forEach((n, i) => { n.classList.toggle("on", i === cur); n.classList.toggle("done", i < cur); });
    const nodes = $$("#rail .rnode"), fillTo = cur >= 6 ? nodes[5] : nodes[cur];
    $("#railFill").style.width = (fillTo.offsetLeft + fillTo.offsetWidth / 2 - 40) + "px";

    // panel blocks: one per stage scene, dip between
    const blocks = ["s07_detect", "s08_number", "s09_lesion", "s10_severity", "s11_abnormal", "s12_report", "s13_truth"];
    blocks.forEach(id => { const b = $("#pb_" + id.slice(0, 3)), s = S[id];
      const a = alphaRange(t, s.start + (id === "s07_detect" ? 0.85 : 0.05), s.end, 0.5, 0.35);
      b.style.opacity = a; b.style.transform = `translateY(${(1 - E.out(clamp((t - s.start) / 0.6))) * 16}px)`; });

    const px = n => n * k;                                       // screen px -> image units
    // ---------------- Stage 1: scan + boxes
    const tRot = cue("s07_detect", "rotated"), tMaps = cue("s07_detect", "maps");
    const scanT0 = tRot + 0.9, scanT1 = tMaps - 0.15;
    const sp = P(t, scanT0, scanT1 - scanT0);
    scanRect.setAttribute("x", lerp(IMG.w, -220, sp));
    scanRect.setAttribute("opacity", t > scanT0 && t < scanT1 + 0.3 ? Math.min(1, 1 - P(t, scanT1, 0.3)) : 0);
    const s3 = S.s09_lesion.start, s12 = cue("s12_report", "overlay"), s13 = cue("s13_truth", "annotations");
    teeth.forEach((tt, i) => {
      const r = SVG.boxes[i], per = +r.dataset.per;
      const tAppear = scanT0 + (1 - tt.cx / IMG.w) * (scanT1 - scanT0) - 0.05;
      const pd = E.out(P(t, tAppear, 0.45));
      r.setAttribute("stroke-dasharray", per);
      r.setAttribute("stroke-dashoffset", per * (1 - pd));
      const isFlag = tt.caries !== "no_caries";
      const flagT = isFlag ? flagTimes[tt.fdi] : Infinity;
      const toOr = P(t, flagT, 0.4);
      let col = toOr > 0.5 ? "#F59E0B" : "#60A5FA", wpx = 2 + 1.2 * toOr, op = 1;
      if (t >= s3 && !isFlag) op = lerp(1, 0.55, P(t, s3, 0.6));
      // final overlay colouring (stages 5–6)
      const fin = P(t, s12 - 0.2, 0.5), finding = isFlag || tt.abn;
      if (fin > 0) { col = finding ? "#F59E0B" : "#3B82F6"; wpx = finding ? 3.2 : 1.8; op = lerp(op, finding ? 1 : 0.85, fin); }
      // truth check: dim everything that is not part of the comparison
      const tr = P(t, s13 - 0.2, 0.6);
      if (tr > 0) { const inCmp = isFlag || gtSet.has(tt.fdi); op = lerp(op, inCmp ? 0.9 : 0.18, tr); if (!isFlag) col = "#3B82F6"; }
      r.setAttribute("stroke", col); r.setAttribute("stroke-width", px(wpx)); r.setAttribute("opacity", pd > 0 ? op : 0);
    });
    // ---------------- Stage 2: crop + labels
    const tCrop = cue("s08_number", "cropped"), tPos = cue("s08_number", "position"), tCode = cue("s08_number", "code");
    const cf = Math.min(E.out(P(t, tCrop - 0.1, 0.5)), 1 - P(t, cue("s08_number", "one-to-one") - 0.3, 0.4));
    cropFdiRect.setAttribute("opacity", cf); cropFdiRect.setAttribute("stroke-width", px(3)); cropFdiRect.setAttribute("stroke-dasharray", `${px(12)} ${px(8)}`);
    const pb8 = S.s08_number;
    fly(flyFdi, t, tCrop + 0.35, 1.0, D.crops.crop_fdi.box, slotFdiRect, alphaRange(t, pb8.start, pb8.end, 0.3, 0.35));
    rv($("#predFdi"), t, tCode - 0.2, { dx: -16, dy: 0 });
    $("#netrow .plus").style.opacity = E.out(P(t, tPos - 0.2, 0.4));
    $("#netrow .net").style.opacity = 0.35 + 0.65 * E.out(P(t, tPos + 0.6, 0.4));
    const tLab = cue("s08_number", "one-to-one") + 0.5, labDur = 2.4;
    archOrder.forEach((tt, j) => {
      const i = teeth.indexOf(tt), L = SVG.labels[i];
      const pl = E.back(P(t, tLab + (j / archOrder.length) * labDur, 0.35));
      const fs = px(17), padX = px(7), padY = px(4);
      const upper = tt.q === 1 || tt.q === 2;
      const ly = upper ? tt.box[1] - px(14) : tt.box[3] + px(14) + fs * 0.75;
      let label = String(tt.fdi);
      const fin = t >= s12 - 0.2;
      if (L.tx.textContent !== label) L.tx.textContent = label;
      L.tx.setAttribute("font-size", fs); L.tx.setAttribute("x", tt.cx); L.tx.setAttribute("y", ly);
      const wch = label.length * fs * 0.58 + 2 * padX;
      L.bg.setAttribute("x", tt.cx - wch / 2); L.bg.setAttribute("y", ly - fs * 0.82 - padY); L.bg.setAttribute("width", wch); L.bg.setAttribute("height", fs + 2 * padY);
      L.bg.setAttribute("stroke", fin && (tt.caries !== "no_caries" || tt.abn) ? "#F59E0B" : QCOL[tt.q]); L.bg.setAttribute("stroke-width", px(1.6));
      let op = clamp(pl);
      if (t >= s3 && t < s12 - 0.2) op *= 0.55;
      if (t >= s13 - 0.2) op *= lerp(1, (tt.caries !== "no_caries" || gtSet.has(tt.fdi)) ? 1 : 0.2, P(t, s13 - 0.2, 0.6));
      L.g.setAttribute("opacity", op);
      L.g.setAttribute("transform", `translate(${tt.cx} ${ly}) scale(${0.6 + 0.4 * clamp(pl)}) translate(${-tt.cx} ${-ly})`);
      const qd = $(`#quad div[data-fdi="${tt.fdi}"]`);
      if (qd) { const on = P(t, tLab + (j / archOrder.length) * labDur, 0.25); qd.style.background = on > 0 ? `rgba(45,212,191,${0.08 + 0.14 * on})` : ""; qd.style.color = on > 0.5 ? "#E8EDF5" : "#5B677C"; qd.style.boxShadow = on > 0.5 ? `inset 0 -3px 0 ${QCOL[tt.q]}` : ""; }
    });
    const tc = cue("s08_number", "distinct");
    $("#cCodes").textContent = Math.round(32 * E.out(P(t, tLab, labDur)));
    // histogram + teeth counter (stage 1 panel)
    const tTeeth = cue("s07_detect", "thirty-two"), tEvery = cue("s07_detect", "every");
    $("#cTeeth").textContent = Math.round(32 * clamp(P(t, scanT0, scanT1 - scanT0)));
    $$("#hist .bar").forEach((b, j) => { b.style.height = (+b.dataset.h) * E.out(P(t, tEvery - 0.6 + j * 0.03, 0.5)) + "px"; });
    $("#hist .thr").style.opacity = P(t, tEvery + 0.6, 0.4);
    // ---------------- Stage 3a: lesions + links
    const tl0 = cue("s09_lesion", "finds"), tl1 = cue("s09_lesion", "boxes");
    const order = [...SVG.les.keys()].sort((a, b) => SVG.les[b].l.conf - SVG.les[a].l.conf);
    const lesOut = 1 - P(t, S.s10_severity.start + 0.5, 0.6);
    order.forEach((idx, j) => {
      const L = SVG.les[idx], ta = tl0 + j * ((tl1 - tl0) / order.length);
      const p = E.back(P(t, ta, 0.4));
      L.g.setAttribute("opacity", clamp(p) * lesOut);
      L.g.querySelector("rect").setAttribute("stroke-width", px(3));
      L.tx.setAttribute("font-size", px(16)); L.tx.setAttribute("y", L.l.box[1] - px(7));
      const cx = (L.l.box[0] + L.l.box[2]) / 2, cy = (L.l.box[1] + L.l.box[3]) / 2;
      L.g.setAttribute("transform", `translate(${cx} ${cy}) scale(${0.7 + 0.3 * clamp(p)}) translate(${-cx} ${-cy})`);
      const ln = SVG.links[idx], tlk = linkTimes[idx];
      const pl = E.out(P(t, tlk, 0.45));
      const x1 = +ln.getAttribute("x1"), y1 = +ln.getAttribute("y1"), tt = byFdi[L.l.tooth];
      const len = Math.hypot(tt.cx - x1, tt.cy - y1);
      ln.setAttribute("stroke-dasharray", len); ln.setAttribute("stroke-dashoffset", len * (1 - pl));
      ln.setAttribute("stroke-width", px(2.5)); ln.setAttribute("opacity", (pl > 0 ? 0.9 : 0) * lesOut);
    });
    $("#cLes").textContent = order.filter((idx, j) => t >= tl0 + j * ((tl1 - tl0) / order.length)).length;
    $("#cFlag").textContent = flagged.filter(f => t >= flagTimes[f] + 0.2).length;
    // ---------------- Stage 3b: severity badges
    const tg = cue("s10_severity", "grades"), t21 = cue("s10_severity", "twenty-one"), t46 = cue("s10_severity", "forty-six");
    const badgeOut = 1 - 0.15 * P(t, s12 - 0.4, 0.4);
    teeth.forEach((tt, i) => {
      const B = SVG.badges[i];
      if (tt.caries === "no_caries") { B.g.setAttribute("opacity", 0); return; }
      const j = flagged.indexOf(tt.fdi), deep = tt.caries === "deep_caries";
      const p = E.back(P(t, tg + 0.15 * j, 0.35));
      const fs = px(13), lab = deep ? "DEEP" : "CARIES", wB = lab.length * fs * 0.66 + px(10);
      const upper = tt.q === 1 || tt.q === 2, by = upper ? tt.box[3] - px(10) : tt.box[1] + px(10) + fs;
      B.tx.textContent = lab; B.tx.setAttribute("font-size", fs); B.tx.setAttribute("x", tt.cx); B.tx.setAttribute("y", by);
      B.tx.setAttribute("fill", deep ? "#2A0A10" : "#1A1206");
      B.bg.setAttribute("x", tt.cx - wB / 2); B.bg.setAttribute("y", by - fs * 0.86 - px(3)); B.bg.setAttribute("width", wB); B.bg.setAttribute("height", fs + px(6));
      B.bg.setAttribute("fill", deep ? "#FB7185" : "#F59E0B");
      const pulse = deep ? Math.max(Math.sin(Math.PI * P(t, tt.fdi === 21 ? t21 : t46, 0.7)), 0) : 0;
      B.g.setAttribute("opacity", clamp(p) * badgeOut * (t >= cue("s11_abnormal", "Stage") ? 0.7 : 1) * (1 - 0.75 * P(t, s13 - 0.2, 0.5)));
      B.g.setAttribute("transform", `translate(${tt.cx} ${by}) scale(${(0.6 + 0.4 * clamp(p)) * (1 + 0.35 * pulse)}) translate(${-tt.cx} ${-by})`);
    });
    $$("#sevlist div").forEach((d, j) => { rv(d, t, tg + 0.15 * j, { dy: 10, d: 0.4 }); const f = +d.dataset.fdi;
      if (f === 21 || f === 46) d.style.transform += ` scale(${1 + 0.12 * Math.max(Math.sin(Math.PI * P(t, f === 21 ? t21 : t46, 0.7)), 0)})`; });
    rv($("#sevWarn"), t, cue("s10_severity", "validated") - 0.2, { dy: 14 });
    // ---------------- Stage 4: taller crop, flight, rings
    const tTall = cue("s11_abnormal", "taller"), tEach = cue("s11_abnormal", "each");
    const c4 = Math.min(E.out(P(t, tTall - 0.1, 0.5)), 1 - P(t, cue("s11_abnormal", "here") - 0.5, 0.4));
    cropS4Rect.setAttribute("opacity", c4); cropS4Rect.setAttribute("stroke-width", px(3)); cropS4Rect.setAttribute("stroke-dasharray", `${px(12)} ${px(8)}`);
    const pb11 = S.s11_abnormal;
    fly(flyS4, t, tEach - 0.1, 1.0, D.crops.crop_s4.box, slotS4Rect, alphaRange(t, pb11.start, pb11.end, 0.3, 0.35));
    $("#netrow4 .net").style.opacity = 0.35 + 0.65 * E.out(P(t, tEach + 0.9, 0.4));
    rv($("#predS4"), t, cue("s11_abnormal", "flags") - 0.1, { dx: -16, dy: 0 });
    const ringT = { 11: cue("s11_abnormal", "eleven"), 37: cue("s11_abnormal", "thirty-seven"), 48: cue("s11_abnormal", "forty-eight") };
    teeth.forEach((tt, i) => {
      const rg = SVG.rings[i];
      if (!tt.abn) { rg.setAttribute("opacity", 0); return; }
      const p = E.back(P(t, (ringT[tt.fdi] ?? cue("s11_abnormal", "here")) - 0.1, 0.45));
      rg.setAttribute("stroke-width", px(3.5)); rg.setAttribute("opacity", clamp(p) * (1 - P(t, s12 - 0.3, 0.4) * 0.35) * (1 - P(t, s13 - 0.2, 0.5)));
      rg.setAttribute("transform", `translate(${tt.cx} ${tt.cy}) scale(${1.25 - 0.25 * clamp(p)}) translate(${-tt.cx} ${-tt.cy})`);
    });
    rv($("#s4Warn"), t, cue("s11_abnormal", "periodontal") - 0.3, { dy: 14 });
    // ---------------- Stages 5–6: JSON + models + final overlay
    const tj0 = cue("s12_report", "record") - 0.2, tj1 = cue("s12_report", "ran") - 0.4;
    const jl = $$("#json .jl");
    jl.forEach((d, j) => { const p = P(t, tj0 + (j / jl.length) * (tj1 - tj0), 0.25); d.style.opacity = p; d.style.transform = `translateX(${(1 - p) * 10}px)`; });
    rv($("#models"), t, cue("s12_report", "hash") - 0.2, { dy: 10 });
    hl16.setAttribute("stroke-width", px(3)); hl16.setAttribute("stroke-dasharray", `${px(10)} ${px(7)}`);
    hl16.setAttribute("opacity", Math.min(P(t, tj0, 0.4), 1 - P(t, cue("s12_report", "overlay") - 0.3, 0.4)) * (0.6 + 0.4 * Math.sin(t * 5)));
    $("#legend").style.opacity = Math.min(E.out(P(t, s12 - 0.1, 0.5)), 1 - P(t, s13 - 0.3, 0.4));
    // ---------------- truth check
    SVG.gt.forEach(pg => { pg.setAttribute("stroke-width", px(3)); pg.setAttribute("opacity", E.out(P(t, s13, 0.6))); });
    const tSeven = cue("s13_truth", "seven"), tFour = cue("s13_truth", "four");
    teeth.forEach((tt, i) => {
      const hb = SVG.hitB[i];
      const isHit = hits.includes(tt.fdi);
      if (!isHit) hb.setAttribute("opacity", 0);
      else {
        const j = hits.indexOf(tt.fdi), p = E.back(P(t, tSeven + 0.12 * j, 0.35));
        const r = px(15), upper = tt.q === 1 || tt.q === 2, y = upper ? tt.box[1] - px(40) : tt.box[3] + px(40);
        hb.querySelector("circle").setAttribute("r", r); hb.querySelector("circle").setAttribute("cx", tt.cx + tt.w * 0.32); hb.querySelector("circle").setAttribute("cy", y);
        const tx = hb.querySelector("text"); tx.setAttribute("x", tt.cx + tt.w * 0.32); tx.setAttribute("y", y + r * 0.42); tx.setAttribute("font-size", r * 1.3);
        hb.setAttribute("opacity", clamp(p));
      }
      const mb = SVG.missB[i];
      if (!missed.includes(tt.fdi)) mb.setAttribute("opacity", 0);
      else { const j = missed.indexOf(tt.fdi), p = E.out(P(t, tFour + 0.15 * j, 0.4));
        mb.setAttribute("stroke-width", px(3)); mb.setAttribute("stroke-dasharray", `${px(9)} ${px(7)}`); mb.setAttribute("opacity", p * (0.65 + 0.35 * Math.sin(t * 4))); }
    });
    rv($("#ta1"), t, tSeven - 0.2, { dx: -20, dy: 0 });
    rv($("#ta2"), t, cue("s13_truth", "land") + 0.3, { dx: -20, dy: 0 });
    rv($("#ta3"), t, tFour - 0.2, { dx: -20, dy: 0 });
    rv($("#ta4"), t, cue("s13_truth", "That") - 0.2, { dy: 12 });
  }
  // when each flagged tooth turns orange: as its lesion's link lands
  const flagTimes = {}, linkTimes = {};
  function buildFlagTimes() {
    const ta = cue("s09_lesion", "assigned") - 0.1, tb = cue("s09_lesion", "flagged");
    const order = D.lesions.map((l, i) => i).sort((a, b) => byFdi[D.lesions[a].tooth].cx - byFdi[D.lesions[b].tooth].cx);
    order.forEach((idx, j) => { const tl = ta + j * ((tb - ta) / order.length); linkTimes[idx] = tl;
      const f = D.lesions[idx].tooth; flagTimes[f] = Math.min(flagTimes[f] ?? Infinity, tl + 0.4); });
  }

  /* ============================================================ PART 3 — TIMELINE */
  const AX = { x: 140, w: 1640, d0: Date.UTC(2026, 7, 20), d1: Date.UTC(2026, 9, 16) };
  const xOf = (m, d) => AX.x + ((Date.UTC(2026, m - 1, d) - AX.d0) / (AX.d1 - AX.d0)) * AX.w;
  const MILES = [
    { m: 8, d: 24, date: "24 Aug", text: "Pipeline runs end to end", side: "up", tier: 2, cue: ["s14_timeline", "ran"] },
    { m: 8, d: 25, date: "25 Aug", text: "External validation · 4 Ningxia hospitals", side: "down", tier: 1, cue: ["s14_timeline", "validated"] },
    { m: 8, d: 28, date: "28 Aug", text: "Image-blind constant ties or beats the pipeline", side: "up", tier: 1, cls: "mwarn", cue: ["s14_timeline", "uncomfortable"] },
    { m: 9, d: 4, date: "4 Sep", text: "Lever B: lesion detector beats the constant, 2 of 3 cohorts", side: "down", tier: 1, cls: "mwin", cue: ["s14_timeline", "fourth"] },
  ];
  const RESP = [["11 Oct", "Tooth detector switched; manuscript rebuilt on it"], ["12 Oct", "First numbering figure on an unseen corpus"],
    ["13 Oct", "Stage 4a scored held out, then retrained by radiograph"], ["14 Oct", "Stage 4b retrained on true bands: not eligible"]];
  function buildTimeline() {
    const L = $("#tl");
    [[8, 20, "20 Aug"], [9, 1, "1 Sep"], [9, 15, "15 Sep"], [10, 1, "1 Oct"], [10, 15, "15 Oct"]].forEach(([m, d, s]) => {
      const e = document.createElement("div"); e.className = "mtick"; e.textContent = s; e.style.left = xOf(m, d) + "px"; L.appendChild(e); });
    const ms = $("#ms");
    MILES.forEach(M => {
      const e = document.createElement("div"); e.className = "mile " + (M.cls || ""); e.style.left = xOf(M.m, M.d) + "px"; e.style.top = "422px";
      const stemH = M.tier === 2 ? 150 : 62;
      e.innerHTML = `<div class="stem"></div><div class="dot"></div><div class="lab"><div class="d">${M.date}</div><div class="t">${M.text}</div></div>`;
      const st = e.querySelector(".stem"), lb = e.querySelector(".lab");
      if (M.side === "up") { st.style.top = -stemH + "px"; st.style.height = stemH + "px"; lb.style.bottom = (stemH + 8) + "px"; }
      else { st.style.top = "0px"; st.style.height = stemH + "px"; lb.style.top = (stemH + 8) + "px"; }
      ms.appendChild(e); M.el = e;
    });
    const rl = $("#respList");
    RESP.forEach(([d, s]) => { const e = document.createElement("div"); e.innerHTML = `<b>${d}</b><span>${s}</span>`; rl.appendChild(e); });
    const gb = $("#gbars");
    const LB = [["DENTEX · 148 images", "tie", [44.3, 48.9, 45.5]], ["CariesXrays-val · 1,200", "win", [31.7, 56.2, 68.4]], ["Ningxia · 337 images", "win", [40.8, 39.9, 50.0]]];
    LB.forEach(([n, v, vals]) => {
      const c = document.createElement("div"); c.className = "gb";
      c.innerHTML = `<div class="gname"><span>${n}</span><em class="${v}">${v}</em></div>` +
        [["retired gate", "#64748B"], ["constant", "#F59E0B"], ["lesion detector", "#2DD4BF"]].map(([l, col], i) =>
          `<div class="grow"><span class="gl">${l}</span><div class="gtrack"><div class="gfill" style="background:${col}" data-v="${vals[i]}"></div></div><span class="gv">${vals[i].toFixed(1)}%</span></div>`).join("");
      gb.appendChild(c);
    });
  }
  function timeline(t) {
    const t0 = S.s14_timeline.start, t1 = S.s15_review.end, L = $("#tl");
    const A = alphaRange(t, t0, t1, 0.5, 0.45);
    L.style.opacity = A;
    if (A <= 0) return;
    const ax = E.out(P(t, t0 + 1.2, 0.8));
    $("#axis").style.opacity = ax; $$(".mtick").forEach(e => e.style.opacity = ax);
    const sep7 = xOf(9, 7) - AX.x, oct14 = xOf(10, 14) - AX.x;
    const fillA = lerp(0, sep7, E.inOut(P(t, cue("s14_timeline", "August") - 0.3, cue("s14_timeline", "cohorts") - cue("s14_timeline", "August"))));
    const fillB = lerp(sep7, oct14, E.inOut(P(t, cue("s15_review", "tenth") - 0.6, 1.2)));
    $("#axisFill").style.width = (t < cue("s15_review", "tenth") - 0.6 ? fillA : fillB) + "px";
    MILES.forEach(M => rv(M.el, t, cue(...M.cue) - 0.15, { dy: M.side === "up" ? 16 : -16 }));
    const bt = $("#tlBefore"); bt.style.left = AX.x + "px"; bt.style.top = "160px"; bt.style.opacity = 0.9 * E.out(P(t, cue("s15_review", "tenth") - 0.2, 0.6));
    const rx = xOf(10, 10);
    const at = $("#tlAfter"); at.style.left = (rx + 18) + "px"; at.style.top = "236px"; at.style.opacity = E.out(P(t, cue("s15_review", "tenth") + 0.2, 0.6));
    const rw = $("#review"); rw.style.left = (rx - 2) + "px"; rv(rw, t, cue("s15_review", "tenth") - 0.2, { dy: -20, d: 0.7 });
    const az = $("#afterZone"); az.style.left = rx + "px"; az.style.width = (AX.x + AX.w - rx + 20) + "px"; az.style.opacity = E.out(P(t, cue("s15_review", "tenth"), 0.8));
    const lb = $("#leverB"), tlb = cue("s14_timeline", "first") - 0.3;
    lb.style.opacity = Math.min(E.out(P(t, tlb, 0.6)), 1 - P(t, S.s15_review.start, 0.4));
    lb.style.transform = `translateY(${(1 - E.out(P(t, tlb, 0.6))) * 24}px)`;
    $$("#gbars .gfill").forEach((f, i) => f.style.width = (+f.dataset.v / 80) * 100 * E.out(P(t, tlb + 0.3 + (i % 3) * 0.12, 0.7)) + "%");
    const fd = $("#finding"), tf = cue("s15_review", "found") - 0.3;
    rv(fd, t, tf, { dy: 24 }); fd.style.opacity = Math.min(+fd.style.opacity, 1 - P(t, cue("s15_review", "loss") + 1.4, 0.4));
    rv($("#f1"), t, tf + 0.2, { dx: -20, dy: 0 });
    rv($("#f2"), t, cue("s15_review", "split") - 0.2, { dx: -20, dy: 0 });
    rv($("#f3"), t, cue("s15_review", "label") - 0.2, { dx: -20, dy: 0 });
    const strike = P(t, cue("s15_review", "split"), 0.4);
    $("#f1 .fnum").style.textDecoration = strike > 0.5 ? "line-through" : "none";
    const tr = cue("s15_review", "loss") + 1.5;
    rv($("#resp"), t, tr, { dy: 20 });
    $$("#respList div").forEach((d, i) => rv(d, t, tr + 0.3 + i * 0.35, { dx: -14, dy: 0 }));
  }

  /* ============================================================ S16 FRONT END */
  const ROWS = [
    { n: "DENTEX · tooth recall", tag: ["in", "in-domain"], a: 70.8, b: 99.6, cue: ["s16_front", "recall"], f: v => v.toFixed(1) + "%", dd: "+28.8 pp" },
    { n: "DENTEX · numbering, end to end", tag: ["in", "in-domain"], a: 58.4, b: 92.8, cue: ["s16_front", "numbering"], f: v => v.toFixed(1) + "%", dd: "+34.4 pp" },
    { n: "UFBA-425 · numbering, end to end", tag: ["un", "unseen by both models"], a: 20.6, b: 44.5, cue: ["s16_front", "UFBA-425"], f: v => v.toFixed(1) + "%", dd: "+23.9 pp" },
    { n: "Tufts · box mAP@0.5, like-for-like", tag: ["cost", "the cost"], a: 72.3, b: 58.7, cue: ["s16_front", "cost"], f: v => (v / 100).toFixed(3), dd: "−0.136", neg: true },
    { n: "Tufts · numbering, end to end", tag: ["ns", "not separable"], a: 64.8, b: 63.5, cue: ["s16_front", "fell"], f: v => v.toFixed(1) + "%", dd: "−1.3 pp", neg: true, ns: true },
  ];
  const TX = v => 580 + v * 10;
  function buildS16() {
    const box = $("#dumb");
    ROWS.forEach(r => {
      const e = document.createElement("div"); e.className = "drow";
      e.innerHTML = `<div class="dl"><h4>${r.n}</h4><span class="tg ${r.tag[0]}">${r.tag[1]}</span></div><div class="tr"></div>` +
        [0, 25, 50, 75, 100].map(v => `<div class="tick" style="left:${TX(v)}px">${r.n.includes("mAP") ? (v / 100).toFixed(2) : v + "%"}</div>`).join("") +
        `<div class="seg"></div><div class="dot b"></div><div class="dot a ${r.neg ? "neg" : ""}"></div><div class="v0"></div><div class="v1 ${r.neg ? "neg" : ""}"></div><div class="dd"></div>`;
      box.appendChild(e); r.el = e;
    });
  }
  function s16(t) {
    const s = S.s16_front, el = $("#s16_front");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#s16_front .scene-title"), t, s.start + 0.2); rv($("#s16_front .sub-title"), t, s.start + 0.5);
    rv($("#s16_front .dlegend"), t, s.start + 0.9, { dy: 8 });
    ROWS.forEach(r => {
      const t0 = cue(...r.cue) - 0.3, e = r.el;
      rv(e, t, t0, { dy: 18 });
      const p = E.inOut(P(t, t0 + 0.7, 1.1)), v = lerp(r.a, r.b, p);
      const db = e.querySelector(".dot.b"), da = e.querySelector(".dot.a"), seg = e.querySelector(".seg");
      db.style.left = TX(r.a) + "px"; da.style.left = TX(v) + "px"; da.style.opacity = P(t, t0 + 0.6, 0.2);
      seg.style.left = TX(Math.min(r.a, v)) + "px"; seg.style.width = Math.abs(TX(v) - TX(r.a)) + "px";
      seg.style.background = r.neg ? "rgba(251,113,133,0.5)" : "linear-gradient(90deg,#64748B,#2DD4BF)";
      const vb = e.querySelector(".v0"), va = e.querySelector(".v1");
      vb.textContent = r.f(r.a); vb.style.left = TX(r.a) + (r.neg ? 40 : -40) + "px";
      va.textContent = r.f(v); va.style.left = TX(v) + (r.neg ? -40 : 40) + "px"; va.style.opacity = P(t, t0 + 0.6, 0.3);
      const dd = e.querySelector(".dd"); dd.textContent = r.dd; dd.style.color = r.ns ? "#B7C3D4" : r.neg ? "#FB7185" : "#2DD4BF"; dd.style.opacity = P(t, t0 + 1.7, 0.4);
    });
  }

  /* ============================================================ S17 / S18 bar charts */
  function bars(container, spec) {   // spec: [{v, max, col, label, cap, fmt}]
    container.innerHTML = "";
    return spec.map(b => { const e = document.createElement("div"); e.className = "vb";
      e.innerHTML = `<div class="val" style="color:${b.col}">${b.fmt(b.v)}</div><div class="col" style="background:${b.bg || b.col}"></div><div class="cap"><b>${b.label}</b>${b.cap || ""}</div>` + (b.stamp ? `<div class="stamp">${b.stamp}</div>` : "");
      container.appendChild(e); b.el = e; return b; });
  }
  let B1, B2, B3, B4;
  function buildBars() {
    const f3 = v => v.toFixed(3), pc = v => v.toFixed(1) + "%";
    B1 = bars($("#vb1"), [{ v: 0.376, max: 0.6, col: "#94A3B8", bg: "#64748B", label: "Previous front end", cap: "lesion detector", fmt: f3 },
                          { v: 0.498, max: 0.6, col: "#2DD4BF", bg: "linear-gradient(180deg,#2DD4BF,rgba(45,212,191,0.35))", label: "Current front end", cap: "default pipeline", fmt: f3 }]);
    B2 = bars($("#vb2"), [{ v: 39.9, max: 80, col: "#F59E0B", bg: "rgba(245,158,11,0.55)", label: "Constant", cap: "previous", fmt: pc },
                          { v: 50.0, max: 80, col: "#94A3B8", bg: "#64748B", label: "Lesion detector", cap: "previous", fmt: pc },
                          { v: 59.1, max: 80, col: "#F59E0B", bg: "rgba(245,158,11,0.55)", label: "Constant", cap: "current", fmt: pc },
                          { v: 68.4, max: 80, col: "#2DD4BF", bg: "linear-gradient(180deg,#2DD4BF,rgba(45,212,191,0.35))", label: "Lesion detector", cap: "current", fmt: pc }]);
    B3 = bars($("#vb3"), [{ v: 83.1, max: 100, col: "#94A3B8", bg: "#64748B", label: "Reported, 7 Sep", cap: "crop-level validation", fmt: pc, stamp: "shared radiographs" },
                          { v: 7.6, max: 100, col: "#FB7185", bg: "#FB7185", label: "Held out, 13 Oct", cap: "821 unseen radiographs", fmt: pc },
                          { v: 27.5, max: 100, col: "#2DD4BF", bg: "linear-gradient(180deg,#2DD4BF,rgba(45,212,191,0.35))", label: "Retrained, seed 42", cap: "radiograph-level split", fmt: pc }]);
    B4 = bars($("#vb4"), [{ v: 0.721, max: 0.8, col: "#94A3B8", bg: "#64748B", label: "Reported", cap: "52 validation crops", fmt: f3, stamp: "labels = image contrast" },
                          { v: 0.294, max: 0.8, col: "#2DD4BF", bg: "linear-gradient(180deg,#2DD4BF,rgba(45,212,191,0.35))", label: "Retrained, seed 42", cap: "true bands · 182 test teeth", fmt: f3 },
                          { v: 0.334, max: 0.8, col: "#F59E0B", bg: "rgba(245,158,11,0.55)", label: "Tooth-position prior", cap: "image-blind", fmt: f3 }]);
    // constant line on F1 chart
    const hl = document.createElement("div"); hl.className = "hline"; hl.id = "constLine";
    hl.style.bottom = (0.320 / 0.6) * 390 + "px"; hl.innerHTML = "<span>image-blind constant · 0.320</span>"; $("#vb1").appendChild(hl);
    // seed markers on the retrained bar
    [16.5, 11.0].forEach((v, i) => { const m = document.createElement("div"); m.className = "sd"; m.style.bottom = (v / 100) * 400 + "px";
      const l = document.createElement("div"); l.className = "sdl"; l.textContent = `seed ${43 + i}: ${v.toFixed(1)}%`; l.style.bottom = (v / 100) * 400 + "px";
      B3[2].el.appendChild(m); B3[2].el.appendChild(l); });
  }
  function growBar(b, t, t0, h) {
    const p = E.out(P(t, t0, 0.9));
    b.el.style.opacity = E.out(P(t, t0 - 0.1, 0.3));
    b.el.querySelector(".col").style.height = (b.v / b.max) * h * p + "px";
    b.el.querySelector(".val").textContent = b.fmt(b.v * p);
  }
  function s17(t) {
    const s = S.s17_caries, el = $("#s17_caries");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#s17_caries .scene-title"), t, s.start + 0.2); rv($("#s17_caries .sub-title"), t, s.start + 0.5);
    rv($("#ccF1"), t, s.start + 0.4, { dy: 24 });
    growBar(B1[0], t, cue("s17_caries", "rose") - 0.1, 390);
    growBar(B1[1], t, cue("s17_caries", "to") - 0.1, 390);
    rv($("#constLine"), t, cue("s17_caries", "against") - 0.1, { dy: 0, dx: -30 });
    rv($("#dl1"), t, cue("s17_caries", "lead") - 0.2, { dy: 12 });
    const tn = cue("s17_caries", "Across");
    rv($("#ccNx"), t, tn - 0.4, { dy: 24 });
    growBar(B2[0], t, tn, 390); growBar(B2[1], t, tn + 0.25, 390);
    growBar(B2[2], t, cue("s17_caries", "reached") - 0.3, 390); growBar(B2[3], t, cue("s17_caries", "reached"), 390);
    rv($("#dl2"), t, cue("s17_caries", "nine") - 0.2, { dy: 12 });
    rv($("#ccFoot"), t, cue("s17_caries", "lead") + 1.2, { dy: 10 });
  }
  function s18(t) {
    const s = S.s18_stage4, el = $("#s18_stage4");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#s18_stage4 .scene-title"), t, s.start + 0.2); rv($("#s18_stage4 .sub-title"), t, s.start + 0.5);
    rv($("#cc4a"), t, s.start + 0.4, { dy: 24 });
    growBar(B3[0], t, cue("s18_stage4", "old") - 0.2, 400);
    B3[0].el.querySelector(".stamp").style.opacity = E.back(P(t, cue("s18_stage4", "inflated"), 0.4));
    growBar(B3[1], t, cue("s18_stage4", "seven") - 0.2, 400);
    growBar(B3[2], t, cue("s18_stage4", "twenty-seven") - 0.2, 400);
    const ts = cue("s18_stage4", "eleven");
    B3[2].el.querySelectorAll(".sd, .sdl").forEach(m => m.style.opacity = E.out(P(t, ts - 0.2, 0.5)));
    rv($("#s4chips"), t, cue("s18_stage4", "ninety-six") - 0.3, { dy: 10 });
    rv($("#cc4b"), t, cue("s18_stage4", "severity") - 0.4, { dy: 24 });
    growBar(B4[0], t, cue("s18_stage4", "severity"), 340);
    B4[0].el.querySelector(".stamp").style.opacity = E.back(P(t, cue("s18_stage4", "contrast") - 0.1, 0.4));
    growBar(B4[1], t, cue("s18_stage4", "Retrained", 1) - 0.1, 340);
    growBar(B4[2], t, cue("s18_stage4", "prior") - 0.3, 340);
    rv($("#verdict"), t, cue("s18_stage4", "withheld") - 0.4, { dy: 12 });
  }

  /* ============================================================ S19 – S21 */
  function s19(t) {
    const s = S.s19_engineering, el = $("#s19_engineering");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#s19_engineering .scene-title"), t, s.start + 0.2); rv($("#s19_engineering .sub-title"), t, s.start + 0.5);
    const t1 = cue("s19_engineering", "Automatically") - 0.2, t2 = cue("s19_engineering", "tests") - 0.2, t3 = t2 + 1.6;
    rv($("#tile1"), t, t1, { dy: 24 }); rv($("#tile2"), t, t2, { dy: 24 }); rv($("#tile3"), t, t3, { dy: 24 });
    $("#n1").textContent = Math.round(lerp(127, 206, E.out(P(t, cue("s19_engineering", "two") - 0.2, 1.0))));
    $("#n2").textContent = Math.round(lerp(174, 197, E.out(P(t, cue("s19_engineering", "ninety-seven") - 0.4, 1.0))));
    rv($("#engChips"), t, cue("s19_engineering", "default") - 0.3, { dy: 14 });
  }
  function s20(t) {
    const s = S.s20_takeaway, el = $("#s20_takeaway");
    el.style.opacity = alphaRange(t, s.start, s.end);
    if (t < s.start - 0.1 || t > s.end + 0.1) return;
    rv($("#s20_takeaway .scene-title"), t, s.start + 0.2);
    rv($("#tk1"), t, cue("s20_takeaway", "lowered") - 0.3, { dx: -30, dy: 0 });
    rv($("#tk2"), t, cue("s20_takeaway", "raised") - 0.3, { dx: -30, dy: 0 });
    rv($("#tk3"), t, cue("s20_takeaway", "named") - 0.3, { dx: -30, dy: 0 });
  }
  function s21(t) {
    const s = S.s21_close, el = $("#s21_close");
    el.style.opacity = alphaRange(t, s.start, s.end + 0.01, 0.5, 1.2);
    if (t < s.start - 0.1) return;
    rv($("#cl0"), t, s.start + 0.3);
    rv($("#cl1"), t, cue("s21_close", "six-page") - 0.3);
    rv($("#cl2"), t, cue("s21_close", "venue") - 0.3);
    rv($("#cl3"), t, cue("s21_close", "Thank") - 0.2, { dy: 30, s: 0.94, d: 0.8 });
    rv($("#cl4"), t, cue("s21_close", "Thank") + 0.5, { dy: 10 });
  }

  /* ============================================================ init + loop */
  buildS02 && (p2band = buildS02());
  buildS03(); buildS05(); buildFlow(); buildFlagTimes(); buildCamera(); buildTimeline(); buildS16(); buildBars();
  slotFdiRect = relRect($("#slotFdi")); slotS4Rect = relRect($("#slotS4"));
  if (hits.length !== 7 || extras.length !== 2 || missed.length !== 4) console.error("truth tallies changed", hits, extras, missed);

  function renderAt(t) {
    t = clamp(t, 0, TOTAL);
    renderChrome(t); s01(t); s02(t); s03(t); s04(t); s05(t); flow(t); timeline(t); s16(t); s17(t); s18(t); s19(t); s20(t); s21(t);
  }
  window.renderAt = renderAt;
  window.TOTAL = TOTAL;
  const imgs = ["assets/opg.jpg", "assets/overlay.jpg", "assets/crop_fdi.png", "assets/crop_s4.png"].map(src => { const i = new Image(); i.src = src; return i.decode().catch(() => {}); });
  window.ready = Promise.all([document.fonts.ready, ...imgs]).then(() => { renderAt(0); return true; });

  const q = new URLSearchParams(location.search);
  if (q.has("capture")) return;
  const still = q.get("t");
  if (still !== null) { window.ready.then(() => renderAt(parseFloat(still))); return; }
  window.ready.then(() => { const t0 = performance.now(); const loop = () => { renderAt((performance.now() - t0) / 1000); requestAnimationFrame(loop); }; loop(); });
})();

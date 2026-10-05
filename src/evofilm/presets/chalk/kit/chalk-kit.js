/* chalk-kit.js — EvoFilm's blackboard toolkit (preset `chalk`), distilled from the first solve films.
   Copied into every new chalk project as assets/chalk-kit.js — load it before your frame script:
     <script src="assets/chalk-kit.js"></script>   →   window.ChalkKit
   Everything is deterministic (seeded PRNG) and seek-safe. Put film-specific geometry in your own
   assets/<film>-kit.js on top of it (one kit per film, so every frame lines up).

   const K = ChalkKit, C = K.C;
   const U = K.coords(270, 135, 1180);              // 1 unit = 270 px, origin at (135,1180), y up
   const A = U(0, 2), B = U(3, 0);                   // screen points from problem coordinates
   K.board(groundDiv, 5);  const f = K.defs(svg, "f01").chalk;
   const ab = K.stroke(svg, K.seg(A, B, 7), { width: 6, filter: f });  K.draw(tl, ab, 0.4, 0.6);
   K.write(tl, htmlNode, 1.2, 0.5);                  // left→right "writing" of any HTML element
   K.region(svg, [A, B, C0], C.yellow, "f01-r", 0)   // filled polygon (fade its opacity in)
   K.text(svg, "1 份", x, y, { halo: true })         // halo = readable on top of coloured regions
   K.box(x1, y1, x2, y2, seed) · K.tick(svg, P, Q) · K.rightMark(svg, foot, from, lx, ly) ·
   K.brace(svg, x1, x2, y, "3") · K.dust(svg, tl, x, y, at, seed) · K.foot(P, Q1, Q2)
*/
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const C = { board: "#22302B", chalk: "#F2EFE6", soft: "#B9BFB8", blue: "#8EC5E8", pink: "#F08A9B", yellow: "#F4D35E", green: "#9BD39B" };

  function rng(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  /* the composition's canvas (data-width/height on the frame root); 9:16 if none is found */
  function canvas(node) {
    const root = node && node.closest ? node.closest("[data-width][data-height]") : null;
    const w = root ? +root.getAttribute("data-width") : 0, h = root ? +root.getAttribute("data-height") : 0;
    return w > 0 && h > 0 ? { w, h } : { w: 1080, h: 1920 };
  }

  /* board: soft lighter centre + seeded eraser smudges (static), sized to the canvas — 16:9, 9:16 or 1:1
     (w/h override the detected canvas) */
  function board(div, seed, w, h) {
    const cv = w && h ? { w, h } : canvas(div);
    div.style.background = "radial-gradient(ellipse 70% 55% at 50% 42%, #2D3E38 0%, #22302B 58%, #18231F 100%)";
    const svg = el("svg", { viewBox: `0 0 ${cv.w} ${cv.h}`, width: cv.w, height: cv.h, style: "position:absolute;inset:0" }, div);
    const r = rng(seed || 3), k = Math.min(cv.w, cv.h) / 1080;
    for (let i = 0; i < 9; i++) {
      el("ellipse", { cx: r() * cv.w, cy: cv.h * 0.1 + r() * cv.h * 0.68, rx: (120 + r() * 220) * k, ry: (30 + r() * 60) * k,
        fill: "#F2EFE6", opacity: (0.018 + r() * 0.02).toFixed(3), transform: `rotate(${(r() - 0.5) * 30})` }, svg);
    }
    return svg;
  }

  /* chalk filter: a faint dusty edge (weak displacement — strong values shred thin lines) */
  function defs(svg, pre) {
    const d = el("defs", {}, svg);
    const f = el("filter", { id: pre + "-chalk", x: "-5%", y: "-5%", width: "110%", height: "110%" }, d);
    el("feTurbulence", { type: "fractalNoise", baseFrequency: "0.9", numOctaves: "2", seed: "4", result: "n" }, f);
    el("feDisplacementMap", { in: "SourceGraphic", in2: "n", scale: "2.2", xChannelSelector: "R", yChannelSelector: "G" }, f);
    return { chalk: `url(#${pre}-chalk)`, defs: d };
  }

  function wobble(points, amp, seed) {
    const r = rng(seed);
    const p = points.map(([x, y]) => [x + (r() - 0.5) * amp, y + (r() - 0.5) * amp]);
    let d = `M${p[0][0].toFixed(1)},${p[0][1].toFixed(1)}`;
    for (let i = 1; i < p.length; i++) {
      const [x0, y0] = p[i - 1], [x1, y1] = p[i];
      d += ` Q${x0.toFixed(1)},${y0.toFixed(1)} ${((x0 + x1) / 2).toFixed(1)},${((y0 + y1) / 2).toFixed(1)}`;
    }
    const last = p[p.length - 1];
    return d + ` T${last[0].toFixed(1)},${last[1].toFixed(1)}`;
  }

  /* a straight chalk stroke as a lightly wobbled multi-point path */
  function line(x1, y1, x2, y2, seed, amp) {
    const n = Math.max(2, Math.round(Math.hypot(x2 - x1, y2 - y1) / 60));
    const pts = [];
    for (let i = 0; i <= n; i++) pts.push([x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n]);
    return wobble(pts, amp == null ? 3 : amp, seed);
  }

  /* a chalk box: four slightly wobbly straight sides (curve-smoothing a rectangle turns it into a blob) */
  function box(x1, y1, x2, y2, seed) {
    return [line(x1, y1, x2, y1, seed, 2), line(x2, y1, x2, y2, seed + 1, 2), line(x2, y2, x1, y2, seed + 2, 2), line(x1, y2, x1, y1 - 4, seed + 3, 2)].join(" ");
  }

  function stroke(svg, d, o) {
    o = o || {};
    return el("path", { d, fill: "none", stroke: o.color || C.chalk, "stroke-width": o.width || 5, "stroke-linecap": "butt",
      "stroke-linejoin": "round", opacity: o.opacity == null ? 0.95 : o.opacity, id: o.id || "", filter: o.filter || "" }, svg);
  }

  /* draw-on: dash L, gap 2L, start past the end (no sliver before the stroke begins) */
  function draw(tl, path, at, dur, ease) {
    const L = path.getTotalLength() + 8;
    tl.fromTo(path, { strokeDasharray: `${L} ${2 * L}`, strokeDashoffset: L + 6 },
      { strokeDashoffset: 0, duration: dur || 0.6, ease: ease || "power1.inOut" }, at);
  }

  /* "write" an HTML element left→right */
  function write(tl, node, at, dur) {
    tl.fromTo(node, { clipPath: "inset(-10% 100% -10% 0)", opacity: 1 },
      { clipPath: "inset(-10% 0% -10% 0)", duration: dur || 0.5, ease: "power1.out" }, at);
  }

  function text(svg, str, x, y, o) {
    o = o || {};
    const t = el("text", { x, y, fill: o.color || C.chalk, "font-family": o.family || "Noto Sans SC", "font-size": o.size || 34,
      "font-weight": o.weight || 500, "text-anchor": o.anchor || "middle", opacity: o.opacity == null ? 1 : o.opacity, id: o.id || "" }, svg);
    if (o.halo) {   // a board-coloured outline keeps labels readable on top of coloured regions
      t.setAttribute("stroke", C.board); t.setAttribute("stroke-width", "7"); t.setAttribute("paint-order", "stroke");
      t.setAttribute("stroke-linejoin", "round");
    }
    t.textContent = str;
    return t;
  }

  function seg(a, b, seed, amp) { return line(a[0], a[1], b[0], b[1], seed, amp == null ? 2 : amp); }

  /* problem coordinates (y up) → screen points */
  function coords(scale, ox, oy) { return (u, v) => [ox + scale * u, oy - scale * v]; }

  /* foot of the perpendicular from P onto line Q1Q2 (screen points) */
  function foot(P, Q1, Q2) {
    const dx = Q2[0] - Q1[0], dy = Q2[1] - Q1[1];
    const t = ((P[0] - Q1[0]) * dx + (P[1] - Q1[1]) * dy) / (dx * dx + dy * dy);
    return [Q1[0] + t * dx, Q1[1] + t * dy];
  }

  /* intersection of lines P1P2 and Q1Q2 (screen points) */
  function meet(P1, P2, Q1, Q2) {
    const d = (P1[0] - P2[0]) * (Q1[1] - Q2[1]) - (P1[1] - P2[1]) * (Q1[0] - Q2[0]);
    const a = P1[0] * P2[1] - P1[1] * P2[0], b = Q1[0] * Q2[1] - Q1[1] * Q2[0];
    return [(a * (Q1[0] - Q2[0]) - (P1[0] - P2[0]) * b) / d, (a * (Q1[1] - Q2[1]) - (P1[1] - P2[1]) * b) / d];
  }

  /* a filled polygon from screen points, starts at the given opacity (default invisible) */
  function region(svg, pts, color, id, opacity) {
    return el("polygon", { points: pts.map((p) => p.join(",")).join(" "), fill: color, opacity: opacity == null ? 0 : opacity, id: id || "" }, svg);
  }

  /* a point label in serif, offset from the point */
  function label(svg, name, p, dx, dy, o) {
    o = o || {};
    return text(svg, name, p[0] + (dx || 0), p[1] + (dy || 0), { size: o.size || 48, family: "Noto Serif SC", weight: 600, color: o.color, id: o.id, halo: o.halo });
  }

  /* equal-length tick across a segment's midpoint */
  function tick(svg, a, b, seed, color) {
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
    const px = -dy / L * 16, py = dx / L * 16;
    return stroke(svg, line(mx - px, my - py, mx + px, my + py, seed, 1), { width: 5, color: color || C.chalk });
  }

  /* right-angle mark at foot F for a height coming from point Q onto a line with direction (lx,ly) */
  function rightMark(svg, F, Q, lx, ly, color) {
    const L = Math.hypot(lx, ly), ux = lx / L * 22, uy = ly / L * 22;
    const qx = Q[0] - F[0], qy = Q[1] - F[1], ql = Math.hypot(qx, qy), vx = qx / ql * 22, vy = qy / ql * 22;
    return stroke(svg, `M${F[0] + ux},${F[1] + uy} L${F[0] + ux + vx},${F[1] + uy + vy} L${F[0] + vx},${F[1] + vy}`, { width: 3.5, color: color || C.chalk });
  }

  /* a dimension brace under a horizontal segment from x1 to x2 at y, label below */
  function brace(svg, x1, x2, y, str, color, seed, dx) {
    const mid = (x1 + x2) / 2, c = color || C.chalk;
    const d = wobble([[x1, y - 14], [x1 + 8, y], [mid - 18, y + 2], [mid, y + 16], [mid + 18, y + 2], [x2 - 8, y], [x2, y - 14]], 1.5, seed || 7);
    const p = stroke(svg, d, { width: 4, color: c, opacity: 0.9 });
    const t = text(svg, str, mid + (dx || 0), y + 62, { size: 48, color: c, family: "JetBrains Mono", weight: 600 });
    return { p, t };
  }

  /* chalk-dust puff at (x,y): seeded specks that drift out and fade, starting at `at` */
  function dust(svg, tl, x, y, at, seed, color) {
    const r = rng(seed || 9);
    for (let i = 0; i < 16; i++) {
      const a = r() * Math.PI * 2, d = 26 + r() * 46;
      const c = el("circle", { cx: x, cy: y, r: 1.5 + r() * 2.5, fill: color || C.chalk, opacity: 0 }, svg);
      tl.fromTo(c, { attr: { cx: x, cy: y }, opacity: 0.9 },
        { attr: { cx: x + Math.cos(a) * d, cy: y + Math.sin(a) * d * 0.7 }, opacity: 0, duration: 0.9 + r() * 0.4, ease: "power2.out",
          immediateRender: false }, at);   // a visible from-state must not render before `at`
    }
  }

  window.ChalkKit = { C, canvas, rng, el, board, defs, wobble, line, box, stroke, draw, write, text, seg, coords, foot, meet, region, label, tick, rightMark, brace, dust };
})();

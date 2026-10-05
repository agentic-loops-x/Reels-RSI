// the original chalk-dust puff from a release-test film: specks showed up before the puff
function dust(svg, tl, x, y, at, seed) {
  for (let i = 0; i < 16; i++) {
    const c = el("circle", { cx: x, cy: y, r: 2, fill: "#F4D35E", opacity: 0 }, svg);
    tl.fromTo(c, { attr: { cx: x, cy: y }, opacity: 0.9 },
      { attr: { cx: x + 40, cy: y + 20 }, opacity: 0, duration: 0.9, ease: "power2.out" }, at);
  }
}

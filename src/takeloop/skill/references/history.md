# History mode — 历史简介 / 朝代速览 / 战役 / 人物 / 文明史

Read for any history, culture, biography, war, empire or "N years of X" film. Everything here
was built and rendered in a TakeLoop smoke test (maps, routes, timeline overlay, Commons images).

## Pick the format

| Format | Example | Structure | Preset | Signature visual |
|---|---|---|---|---|
| 速览 sweep | 中华五千年 · 250 years of US history | era → era, one iconic image each, a timeline overlay advancing the whole film | `notebook` (line art) · `ink` | the drawing that unfolds + the year ruler |
| 事件 event | 赤壁之战 · Battle of Austerlitz | setup (situation map) → forces → turning point → outcome → legacy | `atlas` | maps at changing zoom, armies as arrows, the decisive moment |
| 路线 route | 丝绸之路 · 郑和下西洋 · Magellan | origin → stops in order → consequences | `atlas` | a gold route drawing across the map, cities popping in |
| 人物 biography | 苏轼的一生 · Napoleon | birth → turning points (3–5) → death → why remembered | `ink` / `atlas` | period portrait plate + a life timeline + places on a map |
| 文明 civilization | Western civilization · 丝路文明 | big arc in 5–7 movements, a recurring motif tying them | any; mix styles per movement deliberately | a motif (a flame, a road, a hand) that morphs between eras |

Wordless or music-led variants ("sand animation of 250 years", "origami history of humanity")
drop SCRIPT.md, use `music:` with a mood, and lean on year labels as the only text.

## Accuracy rules (stricter than science films)

- Every year, number, name and place in SCRIPT.md is verified (2 sources for contested facts);
  sources go in BRIEF.md `## Notes`. Casualty/army figures are "约" with the standard account.
- Historical borders are approximate — draw them from a cited map and say "示意" / "约" on screen
  or in narration. Never present a modern border as a historical one.
- Real people are shown via period images (public domain), silhouettes, or objects — never an
  invented "portrait" of a real person.
- Dates: 公元前 = 前221年 on screen; mono digits; one dating style per film.

## Maps (d3-geo + Natural Earth)

```bash
takeloop geo --project . --layers countries,coastline,rivers [--scale 50m]
```
In the frame (classic scripts, in this order, inside the template):
```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script src="assets/geo/countries-110m.js"></script>
```
```js
const proj = d3.geoNaturalEarth1().center([75, 38]).scale(900).translate([1100, 470]);  // or geoMercator / geoOrthographic (globe)
const path = d3.geoPath(proj);
TL_GEO.countries.features.forEach(f => { /* <path d={path(f)}> per country, class f02-country */ });
const china = TL_GEO.countries.features.find(f => f.properties.ISO_A3 === "CHN");
// a route through [lon, lat] stops — d3 bends it along great circles
const route = { type: "LineString", coordinates: stops.map(s => [s.lon, s.lat]) };
routeEl.setAttribute("d", path(route));
const L = routeEl.getTotalLength();
tl.fromTo(routeEl, { strokeDasharray: L, strokeDashoffset: L }, { strokeDashoffset: 0, duration: 2.6, ease: "power1.inOut" }, cue);
const [x, y] = proj([108.9, 34.3]);   // 长安 → screen point for a pin/label
```
- **Camera** — wrap the map SVG in a `.world` div and tween `scale` + `x/y` (cheap, smooth) for
  push-ins to a region; re-project only if you need a globe rotation (`geoOrthographic().rotate`
  inside an `onUpdate` proxy — redraw paths each frame; keep ≤ 200 paths).
- **Territory expansion** — draw the territory polygon at successive dates as separate paths and
  crossfade them, or reveal one polygon with an animated clip-path circle/wipe from the capital.
- **Armies / campaigns** — thick tapered arrows (a path + marker) drawn on; opposing sides in two
  colors (oxblood vs navy); formations as rows of small rectangles that translate together.
- **Battle zoom** — continent → region → field: three map frames at increasing scale with
  `zoom-through` transitions, or one frame with a 3-phase camera.
- **Labels** — city pins pop in on their spoken word; cartouche titles for regions; keep labels
  above y = 900 and ≥ 22px.
- **No draw-on attribute trap** — never put a `stroke-dasharray` attribute in the markup of a path
  you animate; set it only in the tween (an attribute made the route appear fully drawn).
- Historical polygons you author yourself: keep them as `[[lon, lat], …]` arrays with an honest
  comment — cite a source map only if you actually traced from it; otherwise say "hand-sketched, 示意".
- **Winding order** — d3-geo wants polygon rings CLOCKWISE on screen (north edge eastward, then down,
  then back west). A counter-clockwise ring means "the whole globe minus this shape": `fitExtent`
  then shrinks the entire map to a speck and pins/armies collapse with it.
- **Anachronistic present-day geography** — Natural Earth rivers/coasts are modern. Check whether
  the era's geography differed (e.g. the Yellow River ran south into the Huai 1194–1855; old
  coastlines, lakes, canals) and redraw that stretch as a hand path marked 示意.
- **Map camera = CSS on a wrapper div** (`transform-origin: 0 0`, tween x/y/scale; screen = x + p·S).
  Scaling the SVG map group with `svgOrigin` broke both the zoom target and the pull-back.
- **Filters at map scale** — SVG displacement/blur filters are in user units, so inside a world zoomed
  5–6× they grow 5–6× and shred small silhouettes (riders became a smudge). Give small figures on a
  zoomed map a weaker map-scale filter (displacement ≈ 1) and space them generously.
- **One shared kit per film** — put the projection, city coordinates, territory polygon, brush/seal
  helpers in `assets/<film>-kit.js` and load it in every frame, so all map frames line up.

## Timeline that spans the whole film (overlay)

Frames each have their own clock, so a year ruler that keeps advancing across frames is an
**overlay**: `compositions/overlays/timeline.html`, root `data-composition-id="overlay-timeline"`,
registered at `window.__timelines["overlay-timeline"]`. `takeloop finalize` mounts every overlay for the
whole film under the captions. Overlays see global time — get frame
windows from `takeloop times --project . --list` and key the playhead
to them (e.g. jump/ease to 前221 when frame 3 starts). Keep it in the top band (y 40–110), with
contrast against every frame it crosses (a translucent backing strip if frames vary light/dark).

## Period images (Wikimedia Commons)

```bash
takeloop commons search "Qin Shi Huang portrait"
takeloop commons get --project . --name qinshihuang "File:…jpg"
```
Only public domain / CC0 / CC BY(-SA) are accepted; each download is appended to `CREDITS.md`
(CC BY/BY-SA attribution must go in the video description). Place as `<img src="public/x.jpg">`
inside a vignetted "plate" with a slow Ken Burns on its wrapper; grade it to the palette with a
CSS filter (`sepia(.35) contrast(1.05)`), and put code layers on top (name label, date, a line to
a map location).

## Sound for history

`music:` keywords pick the bed: 历史/纪录/庄重 → `cinematic` (low pad, timpani hit on every cut,
swell into each cut); 战/史诗/激昂 → `epic` (adds a driving low pulse). SFX: `impact` on a decisive
moment or a date slam, `whoosh` on map flights, `chime` on a reveal, `swell` before the turn.

## Style recipes that read as "history"

line-art unfolding (notebook) · ink wash and seals (ink) · antique atlas with gold routes (atlas) ·
sand animation (sepia silhouettes, grain) · paper-cut / origami layers · engraving hatch · oil
painting (Kuwahara filter on a 3D/canvas scene). Recipes in `references/styles.md`.

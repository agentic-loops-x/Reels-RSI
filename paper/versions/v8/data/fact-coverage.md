# Fact coverage, baseline vs evolved skill — the 8 topics of evolve round 20261006-001942

Read from the two SCRIPT.md files per topic (spoken lines only). A "fact" is a checkable claim
(a number, a name, a date, a causal step), not phrasing. "Dropped" = stated by the baseline and absent
from the candidate; "added" = stated by the candidate and absent from the baseline.

| topic | dropped by the candidate | added by the candidate | net |
|---|---|---|---|
| sci-rainbow | white light split into seven colours; violet at ~40° (red 42° kept); the viewer stands at the apex of a cone | — | −3 |
| hist-chibi | Cao Cao had just unified the north; the Sun–Liu alliance (tens of thousands) held the river; soldiers unacclimatised (水土不服) | chained ships became the target of the fire attack (causal link made explicit) | −2 |
| solve-chicken-rabbit | — | the general rule: assume all chickens, divide the missing feet by two | +1 |
| en-seasons | Earth is closest to the Sun in early January (the misconception-buster); in winter light spreads thin and days shrink | — | −2 |
| sci-tides | the two high tides are ~12 h 25 min apart because the Moon moves on | the Moon's pull differs across the Earth (the gradient, named) | 0 |
| hist-silk-road | Emperor Wu of Han; Zhang Qian as the envoy; Buddhism travelling east | Yumen Pass; porcelain west, glass east | −1 |
| solve-buoyancy | the worked numbers: 1.3 N vs 10 N, 1 000 cm³ | Archimedes' principle stated (buoyancy equals the weight of the displaced water) | −2 |
| poem-jingyesi | the framing (the poet cannot sleep) — scene-setting, not a fact | — | 0 |

Totals: the candidate drops at least one baseline-stated fact on 6 of 8 topics (13 facts) and adds a new
one on 5 of 8 (6 facts). Script length is unchanged (1 092 → 1 063 characters, −2.7 %): the evolved
skill substitutes rather than compresses.

Pairwise votes (sonnet, round 1): candidate preferred on all 8 topics (3–0, 2–1, 3–0, 3–0; 2–1 ×4).
Absolute composite: train 75.3 → 74.9, holdout 72.8 → 73.5.

## Round 2 (evolve 20261007-045637, baseline = the round-1 skill, position-robust gate)

| topic | dropped by the candidate | added by the candidate |
|---|---|---|
| sci-rainbow | — | violet at ~40°; the cone is centred on the antisolar point |
| hist-chibi | the alliance named as Sun–Liu (kept as "the allied army of tens of thousands") | plague in Cao's camp; an overstretched front (contestable) |
| solve-chicken-rabbit | — | — |
| en-seasons | — | the axis always points the same way |
| sci-tides | each day's high tide ~50 min later (the Moon moves on) | spring tides when the Sun helps (new and full moon) |
| hist-silk-road | Zhang Qian; 138 BCE | the Tarim basin; Buddhism and technology travelling the road |
| solve-buoyancy | the worked numbers (1 kg iron, 127 mL, 1.2 N vs 9.8 N) | Archimedes' principle; the ship's average density is below water's |
| poem-jingyesi | — | — |

Dropped ≈ 5 facts over 4 topics; added ≈ 9 over 6. The round-1 trade (−13/+6) did not recur.
Gate: train 4 won / 0 lost (raw 14–2; candidate-first wins 6/8), holdout 2 won / 2 lost (raw 8–8;
candidate-first 3/8); second-shown reel picked 20/32 = 62 %. Absolute composite train 73.8 → 77.2,
holdout 76.5 → 73.8 (sci-tides judge 60.0 → 48.7). Accepted by the gate; not applied.

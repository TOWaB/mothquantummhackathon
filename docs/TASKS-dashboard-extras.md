# TASKS: dashboard extras

**For:** Aja, after the site copy task
**Reference file:** `dashboard-reference.html`, in the repo root. Open it in a browser. It is a static mock with no server, no API calls, and every number hard-coded from the real state as of 26 September.

These three are additions to `/data`. Everything already specced in `TASKS-current.md` section C stays.

---

## 1. Stat card: highest floor

A dark card, ink background, signal number.

```
0.06
side 12, after 473 jobs
the musicians are still 94% protected there
```

- The number is `max(floors.json.values())`, two decimals.
- The second line names which side and how many jobs have run, from the count of `submit` events in `api_log.jsonl`.
- The third line is `round((1 - max) * 100)` percent.

**Why it earns a card.** It is the single number that says whether the erosion is working. Right now it says it is not.

---

## 2. Table: every side as it stands

One row per side, twelve rows, under the charts.

| Column | Source |
|---|---|
| Side | 01 to 12 |
| Versions | count of entries in `versions.json` for that side |
| Last method | `method` on the last entry |
| Strength | `params.strength` on the last entry |
| Radius | `params.mask_radius` on the last entry |
| Floor | `floors.json`, three decimals, violet mono |
| Protected | `round((1 - floor) * 100)` percent |

Header row in 9px mono uppercase steel. Numeric columns right aligned in mono. Hairline `--mist` between rows, none above the first.

**Why.** The charts show shape, the table shows the actual values a judge will ask about.

---

## 3. Projection toggle

Three buttons above the panels: **Now**, **300 changes at step 0.02**, **300 changes at step 0.08**.

Every panel redraws against the selected data. A small mono label next to the buttons says `real, read from floors.json` or `projected, reflecting walk, uniform over the twelve`.

### The simulation

Seeded so it is reproducible. Starts from the real current floors.

```js
function reflect(x){ if (x < 0) x = -x; if (x > 1) x = 2 - x; return x; }

function simulate(startFloors, startVersions, n, step, seed) {
  let s = seed >>> 0;
  const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
  const floors = startFloors.slice();
  const versions = startVersions.slice();
  const hist = floors.map((f, i) => [{ x: 0, y: f }]);
  for (let k = 1; k <= n; k++) {
    const side = Math.floor(rnd() * 12);            // uniform over the twelve
    floors[side] = reflect(floors[side] + (rnd() < 0.5 ? -step : step));
    versions[side]++;
    hist[side].push({ x: k, y: floors[side] });
  }
  return { floors, versions, hist, n };
}
```

Run it twice at load, once at 0.02 and once at 0.08, and cache both. Do not recompute on every toggle.

### Why this is not decoration

It is the tool for choosing the step size. At the current 0.02 the highest floor after 300 changes reaches about 0.25 and most sides barely move. At 0.08 the sides separate and the protected column drops into the fifties, which is the piece the intro paragraph on the main screen describes.

**Known limitation, worth stating on the page in one line.** The simulation assumes visitors pick sides uniformly. They will not, because the solid faces one way and most people will press without turning it. The versions-per-side panel is what will show the real distribution on Sunday.

---

## 4. One warning on panel 1

When the toggle is on **Now**, put a violet note under the floor bars:

> After a full day of building, the highest floor anywhere is 0.06. At the current step of 0.02 this panel will show a row of near-empty bars on Sunday. Compare the two projections above.

Remove it when either projection is selected. A dashboard that renders twelve empty bars in front of a judge is worse than no dashboard.

---

## Design

Same tokens as everywhere else. Ink bars on `--track`. Violet for floors, job ids and elapsed. Signal once per screen, on the stat card number. Inline SVG, no chart library.

`dashboard-reference.html` has all of it working. Read its source rather than rebuilding from this description where they disagree, but the data must come from the real files, not from the mock's hard-coded arrays.

---

## Not required

If time runs short, build 1 and 2 and skip 3. The stat card and the table are the parts a judge reads. The projection is the part that helps us pick a number before Sunday, and that decision can be made from the mock instead.

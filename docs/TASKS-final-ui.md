# TASKS: final UI batch

Six tasks. Each is small and independent. Do them in order and stop after each so nothing runs long.

---

## 1. Photographer credit under the face image

Under `#faceimg` in the Facing you panel, above the Show mask button.

The filename prefix tells you who shot it:

```
2V0…  →  Cristina Tănase
H66…  →  Petrică Tănase
```

```js
function photographer(filename){
  if (filename.startsWith("2V0")) return "Cristina Tănase";
  if (filename.startsWith("H66")) return "Petrică Tănase";
  return null;
}
```

The side blends two source photographs, so show both:

```
Petrică Tănase and Cristina Tănase · George Enescu International Festival, 2023
```

If both prefixes are the same, show the one name. If neither matches, show nothing rather than a guess.

**Style:** 11.5px, `--slate`, sits directly under the image. Diacritics, UTF-8, check on the live box.

**Leave the First photo and Second photo rows as they are.** They show the new short names and that is fine.

---

## 2. Floor check

`floors.json` showed side 12 at 0.06 this morning. The screen now shows 0.00 on every side and 0.00 on all three version rows, after 18 spins.

Do not fix anything yet. Report four things:

1. Current contents of `floors.json`.
2. Does `reroll` step the floor, or only `reblend`?
3. Is `floor` written to the version record at the moment it is created, or read later from `floors.json`?
4. Is the floor read before or after the step when the mask is baked?

**Report only. No changes.**

---

## 3. Engine line

**Now:** `Side picked by four coin-toss-v1 flips, picture from telablur-v1. backend aer · mode emu`

**Change to:** `Side picked by coin-toss-v1 flips, picture from telablur-v1. backend aer · mode emu`

"Four" is wrong against the log sitting next to it: 156 flips across 18 spins is 8.7 each, because a draw over eleven is thrown away and redrawn.

---

## 4. Move the numbers to their own page

The main screen is full. Everything in task 5 goes on `/data`, not on `/`.

- Add a link in the footer of the main screen, small, mono, reads `the numbers`, pointing at `/data`.
- `/data` gets the same topbar, the byline and the title, and a back link reading `the object`.
- `/data` must render server side with JavaScript off.

---

## 5. The panels on /data

Reference file `dashboard-reference.html` is in the repo root. Open it in a browser. Full spec is in `TASKS-dashboard-extras.md`.

Build in this order and stop after each:

**5a. Highest floor stat card.** Dark, ink background, signal number.
```
0.06
side 12, after 473 jobs
the musicians are still 94% protected there
```

**5b. Table, twelve rows.** Side, versions, last method, strength, radius, floor, protected percent. Floor in violet mono, three decimals. Numeric columns right aligned.

**5c. Floor bars, twelve.** Ink on `--track`, side number under each, value above.

**5d. Floor over time.** One line per side against change number, the highest in solid ink and labelled.

**5e. What images changed.** Twelve horizontal bars, versions made per side.
**This panel is called "What images changed", not "Where people looked".**

**5f. Draws thrown away.** One big number, percent of draws with `accepted: false`.

Skip the projection toggle for now. That can wait.

---

## 6. Document the new event

`spin_mask_ready` appears in the log and is not in `docs/08-structure.md`. Add it to the event list with its full shape as written.

---

## Order

1, then 3, then 6. All three are small.
Then 2, and report back before touching anything.
Then 4, then 5a to 5f one at a time.

Stop and report after each numbered task.

# 07. Design

Visual Hive Signal, adapted from A4 print to a screen that runs all day.

---

## Where it is shown

| Surface | Constraint |
|---|---|
| Laptop or monitor at 19 D'Arblay Street | Primary. Three columns. Read from about a metre. |
| Projector, if the basement has one | Same layout, but smallest readable type rises to 13px and the log drops off |
| Visitor phones via QR | Single column, stacked, log collapsed behind a tap |

Design for the laptop. Check the phone before Sunday. Do not design for the projector unless one appears.

---

## The one idea

A white instrument panel around a dark stage. The photographs are the only saturated things on the screen; everything else is ink on paper. A visitor's eye goes to the solid, then to the face image, then to the numbers if they want them.

Consequence: never put a coloured fill over a photograph. The first version tinted the selected face yellow at 28 percent and the photograph disappeared. Selection is an edge, not a wash.

---

## Colour

```css
:root {
  --paper:  #ffffff;   /* background, always white */
  --ink:    #141414;   /* text, the stage, rules, bar fills */
  --signal: #f0f22e;   /* the one live thing. Never text on white */
  --circuit:#4634e0;   /* job ids, elapsed times, credits. Nothing else */
  --slate:  #6a696d;   /* secondary text, data labels */
  --steel:  #7b7d86;   /* meta, kickers, field names */
  --mist:   #d3d6d8;   /* hairlines, borders */
  --track:  #f0f0f1;   /* bar tracks, inactive pills */
}
```

**Rules.**

1. Yellow appears **once per screen state**, on the thing that is happening now. Active stage pill, or the selected face edge, or the drift bar fill. Never two at once.
2. Yellow as text is allowed only on ink. On white it is a pill background, a highlight underlay behind bold ink text, or a single bar fill.
3. Violet carries `job_id`, `ibm_job_id`, `elapsed_s` and credits. Nothing else. It is the colour of a number you can go and check.
4. Slate for labels, steel for the API field names under them, ink for the values.
5. `#stage` is ink. Everything around it is paper. There is no grey middle ground.

**Highlight underlay**, for one phrase per state at most:

```css
background: linear-gradient(transparent 58%, var(--signal) 58%);
```

Used on the side number in the done state. Nowhere else.

---

## Type

Inter Tight and JetBrains Mono, both from Google Fonts on the web build. The print pipeline uses fontsource on jsdelivr because Google Fonts is blocked there, so the repo keeps both import lines with the print one commented.

| Role | Family | Size | Weight | Tracking |
|---|---|---|---|---|
| Page title | Inter Tight | 15px | 700 | −0.01em |
| State line | Inter Tight | 15 to 17px | 600 | −0.01em |
| Face name | Inter Tight | 19px | 700 | −0.02em |
| Counter number | Inter Tight | 15 to 16px | 600 | |
| Body, labels | Inter Tight | 12 to 13px | 400 | |
| Data value | Inter Tight | 11.5px | 600 | |
| Kicker, panel head | JetBrains Mono | 9.5 to 10px uppercase | 400 | 0.1em |
| API field name | JetBrains Mono | 9 to 9.5px | 400 | |
| Job id, elapsed, credits | JetBrains Mono | 10 to 11px | 400 | |
| Log row | JetBrains Mono | 10 to 10.5px | 400 | |

Nothing below 9px. If a column forces it lower, drop the column instead.

**Do not** use all caps for anything except the mono kickers. Do not accent a single word in a heading in a different colour. Both read as filler.

---

## Spacing

Multiples of 1, 2, 3, 5, 7, 9, 11, 13, 14, 18, 22. In practice:

| Gap | Use |
|---|---|
| 4 to 6px | inside a data row |
| 9 to 11px | between elements in a card |
| 11 to 14px | between cards |
| 18 to 22px | page padding on desktop |

Card padding is `12px 13px`. Radius is 10px on cards, 99px on pills and buttons, 6 to 7px on images and the log.

---

## Components

### Card

```css
.card { border:1px solid var(--mist); border-radius:10px; padding:12px 13px; }
.card > .kicker { display:block; margin-bottom:8px; }
```

Every panel is a card. No shadows on screen; the border does the work.

### Dark stat card

Ink background, signal number, `#c9c9c9` label. **Maximum two per screen**, and only for numbers that carry the argument. On this screen that is flips taken and versions made. Everything else is a plain counter.

### Data row

```css
.r { display:grid; grid-template-columns:1fr auto; gap:10px;
     padding:5px 0; border-bottom:1px solid var(--mist); align-items:baseline; }
```

Plain label on top in slate, API field name underneath in mono steel, value right-aligned in ink 600. Violet and mono when the value is an id or a time. Last row has no border.

### Pill

Mono, 9.5px, `padding:2px 9px`, radius 99px. Track background when inactive, signal background with ink text when active.

### Bar

Label, track, value in a three-column grid. Track 13px tall, `--track`, fully rounded. Fill ink. The single lead value may be signal with a 1px ink outline.

### Ladder rung

```css
.rung { display:grid; grid-template-columns:44px 46px 20px 1fr; gap:8px;
        padding:5px 0; border-bottom:1px solid var(--mist);
        opacity:0; transform:translateY(-4px);
        transition:opacity .28s ease, transform .28s ease; }
.rung.in { opacity:1; transform:none; }
```

Columns are flip number, outcome, bit, job id. The bit gets a track background at 0 and an ink background at 1, so a draw reads as a row of blocks before you read the numbers.

### Log row

Three columns: time 52px, event type 104 to 112px, detail fills. Event type takes signal by default, `#9aa0ff` for `submit`, `#8ad8b5` for `complete`. Detail truncates with ellipsis rather than wrapping, because a wrapped log row destroys the scan.

### Buttons

Solid ink for the primary action, white with an ink border for everything else, radius 99px. HUD buttons on the stage are white at 10 percent on ink with a 25 percent border, and invert to solid white when pressed.

---

## States

| State | Treatment |
|---|---|
| Hover | No colour change on cards or rows. Cursor only. |
| Focus | `outline: 2px solid var(--circuit); outline-offset: 2px`. Never removed. |
| Disabled | `opacity: .4`, cursor default |
| Active, pressed | `aria-pressed="true"` inverts the button |
| Selected face | Signal edge glow on the pentagon, never a fill |
| In flight | The one signal pill on the current stage |

---

## Motion

Three kinds, nothing else.

1. **The solid.** Idle drift at 0.0018 rad per frame after 2.8 seconds without input. Inertia decays 0.95 a frame and cuts below 0.0006. Snap slerps over 700ms with a cubic ease.
2. **Rungs landing.** 280ms fade and 4px rise as each flip arrives. This is the only thing on the screen that animates during the wait, which is why it reads.
3. **Bars.** 700ms ease on width.

No fade-and-rise on cards at load. No hover transitions. `prefers-reduced-motion` kills all of it, including the idle drift.

---

## Layout

```
desktop  ≥1180px   1.35fr solid | 1fr facing you | 0.95fr activity
tablet   760–1180  1.2fr solid | 1fr facing you, activity full width below
phone    <760      single column, stacked
```

The right column is the wait, in the order it happens: button, three status lines, the flips, the log. During a spin it is the only thing anyone looks at.

`min-height: 0` on every flex and grid child that contains a scroller, or the log will push the page instead of scrolling.

---

## Accessibility

- Focus ring on every interactive element, violet, never removed.
- `prefers-reduced-motion` respected, including the idle spin.
- The solid is draggable with the arrow keys as well as a pointer.
- Colour never carries meaning alone. A thrown-away draw says so in words as well as going grey.
- Smallest type is 9px mono and only on API field names, which duplicate a plain label directly above.
- Contrast: slate on paper is 5.6:1, steel on paper is 4.6:1. Do not go lighter than steel for anything a visitor needs.

---

## What not to do

- No coloured wash over a photograph.
- No shadows. The border and the ink stage carry the depth.
- No second accent colour. If something needs to stand out and signal is taken, restructure instead.
- No icon set. There are no icons on this screen and it does not need any.
- No em dashes anywhere, in the interface or the docs.
- No `clip-path`, `filter`, `opacity` below 1, `mask` or `overflow` on an element carrying a 3D transform. See `03-solid.md`.

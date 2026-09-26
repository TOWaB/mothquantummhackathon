# TASKS: the live site, copy and header

**For:** Aja
**Live:** https://mothhack26.visualhive.co
**Everything below is copy and markup.** No API work, no new state.

---

## 1. Replace the logo with a byline

Remove the Visual Hive wordmark and the yellow square from `#topbar`. In its place:

```html
<span class="byline">TheOneWithABeard</span>
```

```css
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap');

.byline{
  font-family:"Instrument Serif",Georgia,serif;
  font-style:italic;
  font-size:21px;
  letter-spacing:-.01em;
  color:var(--ink);
}
```

**Why Instrument Serif.** It is a byline, not a logo, and it should read as a person signing a piece of work rather than a company badge. It sits against Inter Tight and JetBrains Mono without competing. Free on Google Fonts, one weight, no build step.

If it reads too soft against the photographs, the alternatives in order are **Fraunces** (more idiosyncratic), **Newsreader** (quieter), **Bricolage Grotesque** (no serif, more contemporary).

---

## 2. The intro block

Sits directly under the `<h1>`, above the counters. Collapsible, open on first visit.

### Markup

```html
<section id="intro" open>
  <p class="lede">Press the button and one of these twelve photographs changes for good.</p>

  <p>The photographs are Petrică and Cristina Tănase's. They have shot the George
  Enescu International Festival in Bucharest for more than ten years, and they gave
  me six frames each from 2023. Every side of this solid holds one of his and one of
  hers, pushed into each other by a quantum engine until you cannot say where one
  ends.</p>

  <p>But I do not choose which side you get. Four coin flips on Moth's Atlas make a
  number between zero and fifteen, and anything over eleven is thrown away and drawn
  again, because there are only twelve sides. Eighty test flips came back with no
  repeats and 45 percent heads.</p>

  <p>The musicians are protected at first. A mask cut from each photograph holds them
  out of the blend, but every change lifts that protection a fraction, so the players
  are the last thing to go. Nothing resets. Whatever you make stays for whoever
  comes next.</p>

  <button id="introToggle" aria-expanded="true" aria-controls="intro">Hide</button>
</section>
```

### Style

```css
#intro{max-width:66ch;margin:2px 0 4px}
#intro .lede{font-size:17px;font-weight:600;letter-spacing:-.015em;margin:0 0 8px}
#intro p{font-size:13.5px;line-height:1.55;color:var(--slate);margin:0 0 7px;max-width:66ch}
#intro[hidden]{display:none}
#introToggle{
  font-family:"JetBrains Mono",monospace;font-size:9.5px;text-transform:uppercase;
  letter-spacing:.1em;color:var(--steel);background:none;border:0;padding:4px 0;
  cursor:pointer;text-decoration:underline;text-underline-offset:3px;
}
#introToggle:hover{color:var(--ink)}
```

### Behaviour

- Button toggles the three paragraphs. The first line stays visible always.
- Label flips between `Hide` and `What is this`.
- Remember the choice in `localStorage`, wrapped in try/catch, so a returning visitor is not shown it again.
- On a phone, collapse it by default. Three paragraphs above the object is too much on a small screen.

**Confirm the diacritics before this ships.** Petrică and Cristina Tănase. Ask Petrică rather than guessing.

---

## 3. Every remaining string

### Counters

Remove the credits counter entirely. Five becomes four.

```
27 coin flips · 12 sides · 14 versions made · 4 spins
```

### The claim line, under the counters

**Replace:** `Every side here was chosen by a flip on Atlas, and every flip has a job id.`

**With:** `Every side is chosen by a flip nobody can predict. Eighty test flips, no repeats, 45 percent heads.`

A1 has run, so the claim is earned. Keep the sample size next to it, because a claim with its evidence beside it answers the question and a bare claim invites it.

### Engine line

Unchanged. `backend aer · mode emu` stays. Unpredictable is not the same as quantum hardware.

### The button

**Was:** `Spin it`
**Now:** `Change a side`

"Spin" reads as a slot machine and frames the visitor as receiving an outcome. It is also already in use, because the solid spins when you drag it.

### The five states

| State | Line 1 | Line 2 |
|---|---|---|
| Ready | Press the button and one side changes. | Four flips decide which one. About 3.6 seconds each. |
| Flipping | Working out which side you get. Flip 2 of 4. | came back heads |
| Thrown away | That is 15. Only 12 sides, so it goes and we draw again. | |
| Picked | Side 8 is yours. Making the new version now. | 8 flips, one go thrown away. |
| Done | Side 8 has changed. Version 4, and nobody knew it would be side 8. | It stays that way for whoever comes next. Took 9.2s, job f32b267e. |

All credit references removed from line 2.

### The empty state

The live site currently shows zeroes and a blank image, because the box has no state. Until the twelve baked faces are deployed, or for any fresh install:

**Facing you panel:** `Twelve sides, made before anyone arrived. Press the button to change one.`

### The three untested states

Nothing has failed in 473 jobs, so none of these has ever rendered.

| State | Copy |
|---|---|
| A flip fails | That flip did not come back. Trying again. |
| Atlas unreachable | Cannot reach Atlas. Showing the sides as they were. |
| Someone else is mid-change | Someone is changing a side right now. You are next. |

The third replaces the bare 409. A public URL with a 90 to 245 second change and a hard reject reads as broken the moment two people are on it.

### The version labels

`reroll` and `reblend` are currently inverted in `docs/06-copy.md` against the code. Read `app.py`, then set them to match:

- One of them picks new settings and rebuilds from the original photograph.
- The other reuses the settings and feeds the current rendered image back in.

Write the plain-English label for each against what the code actually does, not against the doc.

### Panel heads

`Facing you` · `The coin flips` · `Atlas log` · `Every version of this side`

Unchanged.

---

## 4. Check before shipping

```bash
grep -rniE "spin it|press spin|credits|nobody knew that before" templates/ static/
```

Should return nothing. `nobody knew it would be side 8` is the new wording and is fine; `nobody knew that before you pressed` is the old one and is not.

---

## 5. Order

1. Byline and font
2. Intro block, desktop
3. Intro collapsed by default on mobile
4. Button and the five states
5. Counters, credits removed
6. Claim line
7. Empty state
8. The three untested states
9. reroll and reblend read from the code

1 to 6 are the ones a visitor sees first.

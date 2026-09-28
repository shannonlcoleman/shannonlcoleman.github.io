# Site style spec

The visual system for shannonlcoleman.com. Use it to match new pages (such as the Capability Question tool) to the rest of the site. Every page carries its own inline `<style>` block; there is no shared stylesheet.

The direction: a well-set research journal. White pages, one ink color, one accent, and typography and rules doing most of the work. No italic accent words in headlines, no monospace, no uppercase-tracked labels, no pill shapes, no gradients, and no tinted or cream backgrounds.

## Fonts

Load both from Google Fonts:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap">
```

| Role | Family | Weights |
| --- | --- | --- |
| Headlines, titles, pull quotes, decks | Newsreader | 400 (500 for the site logo only) |
| Body, UI, labels, buttons, numbers | IBM Plex Sans | 400, 500, 600 |

Headlines are always roman and one color. If markup contains `<em>` inside a headline, neutralize it: `font-style: normal; color: inherit;`.

Numbers shown as figures (stats, step numbers) use Plex Sans with `font-variant-numeric: lining-nums tabular-nums`.

## Color tokens

```css
:root {
  --paper:         #ffffff;  /* every page background */
  --ink:           #1c1b19;  /* text, rules, primary buttons, the dark footer band */
  --ink-2:         #55514b;  /* body copy, secondary text (7.9:1 on white) */
  --ink-3:         #6b665f;  /* meta, dates, captions (5.7:1 on white) */
  --rule:          #dcd8d2;  /* hairlines only, never text */
  --accent:        #9b3a22;  /* labels, figures, links (6.9:1 on white) */
  --accent-on-ink: #e8a48b;  /* accent on the dark band (8.3:1 on ink) */
  --on-ink-2:      #c9c5bf;  /* secondary text on the dark band (10:1 on ink) */
  --data-2:        #2f5f6b;  /* second data series in charts (7.1:1 on white) */
  --serif: 'Newsreader', Georgia, 'Times New Roman', serif;
  --sans:  'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif;
}
```

Chart-only colors: green `#3b6b45`, ochre `#8a6414`, and bar-track fill `#eeece8`. The fill is for chart tracks only, never a page or panel background.

The only dark surface is the contact and footer band at the bottom of a page (`--ink`).

## Type scale

| Element | Font | Size | Line height | Other |
| --- | --- | --- | --- | --- |
| Hero name / page title | Newsreader 400 | `clamp(44px, 7.4vw, 96px)` (up to 112px on the homepage) | 1.0 | letter-spacing -0.025em |
| Case study title | Newsreader 400 | `clamp(38px, 6vw, 76px)` | 1.02 | letter-spacing -0.025em, `text-wrap: balance` |
| Section heading (h2) | Newsreader 400 | `clamp(32px, 4.2vw, 50px)` | 1.1 | letter-spacing -0.015em, max-width about 24 to 30ch |
| Deck / hero statement | Newsreader 400 | `clamp(22px, 2.3vw, 28px)` | 1.35 | `--ink` or `--ink-2` |
| Card or list title | Newsreader 400 | 23 to 29px | 1.2 | |
| Pull quote | Newsreader 400 | 21px | 1.5 to 1.55 | roman, not italic |
| Body | Plex Sans 400 | 17px (16px under 700px) | 1.65 to 1.75 | `--ink-2`, max-width about 64 to 68ch |
| Small body / descriptions | Plex Sans 400 | 15 to 16px | 1.6 to 1.65 | `--ink-2` |
| Meta, dates, captions | Plex Sans 400 or 500 | 14px | 1.5 | `--ink-3` |
| Stat figure | Plex Sans 400 | `clamp(34px, 3.8vw, 46px)` | 1.0 | `--accent`, letter-spacing -0.02em |
| Step number | Plex Sans 400 | 28px | 1.0 | `--accent`, written as 1, 2, 3 (not 01) |

## Section labels

Small sans in the accent color, sitting under a full-width ink rule. Sentence or title case as written; never uppercase-transformed, never monospace, never numbered.

```css
.section-label {
  font-family: var(--sans);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--accent);
  border-top: 1px solid var(--ink);
  padding-top: 14px;
  margin-bottom: 20px;
}
```

Sidebar and card labels use the same type without the rule.

## Buttons

Plain rectangles with 2px corners. Text as written, no uppercase transform.

```css
.btn-primary, .btn-secondary {
  display: inline-flex;
  align-items: center;
  font: 500 15px/1.2 var(--sans);
  padding: 12px 18px;
  min-height: 46px;
  border-radius: 2px;
  border: 1px solid var(--ink);
  text-decoration: none;
}
.btn-primary   { background: var(--ink); color: var(--paper); }
.btn-primary:hover { background: var(--accent); border-color: var(--accent); }
.btn-secondary { background: transparent; color: var(--ink); }
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
```

On the dark band, invert them: primary is paper on ink text, secondary is a `--on-ink-2` outline with paper text. Under 480px, buttons stack full width.

Text links inside copy: `--accent`, underlined with `text-underline-offset: 3px`.

## Cards, panels, and lists

Prefer rules to boxes, and vary the treatment by role so cards never all look the same.

- **Index lists** (case studies, articles): no box. Each entry sits between 1px `--rule` hairlines, with title in Newsreader and meta in `--ink-3`. Hover turns the title `--accent`.
- **Column grids** (methods, services, impact): no box. Each item starts with a 1px `--ink` top rule, then a figure or label, a Plex Sans 600 title or Newsreader title, and `--ink-2` text. Column gap 32 to 56px.
- **Stat rows**: figures left-aligned on a strip bounded by `--rule` hairlines, with `--rule` dividers between items. No boxes, no centering.
- **Outlined panels** (featured tool, advisory and resume cards, diagrams): white, 1px `--ink` border, 2px radius, 28 to 32px padding.
- **Callouts and pull quotes**: white, 1px `--rule` border with a 3px `--accent` left border. The label is in accent Plex Sans 600 at 14px, with body in Newsreader or Plex Sans.
- **Tag lists**: running text in `--ink-3` at 14px, separated by a middle dot (`·`). Never chips or pills.

## Layout

- Content width 1080px, 48px side padding (20px under 700px).
- Section spacing 96 to 104px (64 to 72px on mobile).
- Header: white, 68px, 1px `--rule` bottom border, sticky. The logo is the name in Newsreader 500 at 21px; nav links are Plex Sans 500 at 15px in `--ink-2`, with an accent underline on hover and an ink underline on the current page.
- Footer: `--ink` band, Plex Sans at 14px in `--on-ink-2`, left-aligned, with 44px minimum tap targets.
- No entrance animations and no decorative gradients, glows, or background patterns.
- Focus: `outline: 2px solid var(--accent); outline-offset: 3px`.

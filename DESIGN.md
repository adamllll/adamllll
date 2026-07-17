---
name: ADAM Commit City
description: A living ADAM word mark shaped by weekly GitHub activity.
colors:
  night-deep: "#090d16"
  night-horizon: "#161022"
  footer-void: "#090c13"
  cobalt-wordmark: "#315ee8"
  wordmark-deep: "#13275a"
  electric-cyan: "#00d8ff"
  signal-green: "#06ffa5"
  activity-violet: "#c774e8"
  activity-magenta: "#ff6ad5"
  signal-yellow: "#fffd82"
  text-primary: "#f7f3ff"
  text-muted: "#a997b7"
  website-muted: "#8091be"
typography:
  display:
    fontFamily: "Arial Black, Arial, sans-serif"
    fontSize: "520px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "0"
  title:
    fontFamily: "Arial Black, Arial, sans-serif"
    fontSize: "22px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "0"
  label:
    fontFamily: "Courier New, Consolas, monospace"
    fontSize: "14px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0"
rounded:
  none: "0px"
spacing:
  activity-band-step: "28.46px"
  canvas-edge: "60px"
  footer-height: "60px"
components:
  activity-poster:
    backgroundColor: "{colors.night-deep}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.none}"
    width: "1600px"
    height: "720px"
  activity-wordmark:
    backgroundColor: "{colors.night-deep}"
    textColor: "{colors.cobalt-wordmark}"
    typography: "{typography.display}"
    rounded: "{rounded.none}"
    width: "1480px"
    height: "424px"
  website-signal:
    backgroundColor: "{colors.footer-void}"
    textColor: "{colors.website-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0px"
---

# Design System: ADAM Commit City

## Overview

**Creative North Star: "The Name Is the City"**

The profile is one large, self-contained digital poster. The 52 vertical bands inside ADAM each represent one week of GitHub activity. Dim cobalt keeps the name legible; contribution height and brightness build a data-driven skyline inside the letters themselves.

This system rejects conventional developer-profile filler, generic cyberpunk effects, and compositions where the brand and the data compete as separate objects. It is dark because the subject is a night signal. ADAM remains the only dominant idea; the compact timeline, labels, and website entry stay quiet.

**Key Characteristics:**

- One full-width 1600 x 720 poster
- Sharp pixel geometry with no rounded containers
- One 1480px ADAM word mark built from exactly 52 weekly bands
- Cobalt architectural typography over a near-black night field
- Data-driven fill height, brightness, and activity color inside the letters
- One choreographed load sequence plus low-frequency ambient motion
- A linked poster with a deliberately subdued website signal

## Colors

The palette combines a deep blue-black city field with cobalt identity color and a small data-visualization spectrum.

### Primary

- **City Cobalt:** The word mark, footer rule, and website signal use the primary identity color.

### Secondary

- **Electric Cyan:** Busy weekly fills, stars, and the signal rail.
- **Signal Green:** The current-week marker.
- **Activity Violet:** High-activity weekly fills below the peak tier.
- **Activity Magenta:** Peak weekly fills.
- **Signal Yellow:** The contribution total and recent-activity pulse.

### Neutral

- **Deep Night:** The field behind the activity word mark.
- **Horizon Violet:** The lower night gradient behind the timeline.
- **Primary Text:** High-contrast labels that must be read immediately.
- **Muted Text:** Secondary explanation and timeline copy.
- **Website Muted:** The personal-site label, held above WCAG AA without becoming a focal point.

**The Data Color Rule.** Cyan, green, magenta, and yellow communicate contribution intensity or live signal state. They are never added as unrelated decoration.

## Typography

**Display Font:** Arial Black (with Arial and sans-serif fallbacks)
**Body Font:** Courier New (with Consolas and monospace fallbacks)
**Label/Mono Font:** Courier New (with Consolas and monospace fallbacks)

**Character:** Heavy system display type makes ADAM the architecture and the data surface at once. The mono labels feel like signal infrastructure without turning the page into a fake terminal.

### Hierarchy

- **Display** (900, 520px, 1): ADAM only, once per poster.
- **Title** (900, 22px, 1): The 52-week concept line only.
- **Body** (400, 15-16px, 1.2): Timeline and explanatory data labels.
- **Label** (700, 12-14px, 1.2, normal spacing): Footer explanation and website entry.

**The One Monument Rule.** ADAM is the only oversized text. No other label competes through scale.

## Elevation

The system is flat by default. Depth comes from a dim word base, bright activity fills, horizontal floor cuts, weekly band gaps, and a crisp cobalt outline. There are no card shadows, glass panels, broad neon glows, or separate background scenery.

**The Pixel Depth Rule.** Build depth with hard geometry and tonal layers. Blur is prohibited in the signature scene.

## Components

### Activity Poster

- **Shape:** Sharp 1600 x 720 SVG canvas with zero corner radius.
- **Background:** Deep Night to Horizon Violet vertical field.
- **Behavior:** The complete poster scales to the README width and remains fully visible without horizontal scrolling.
- **Link:** The README wraps the poster in one link to the personal website.

### Activity Word Mark

- **Shape:** One 1480px ADAM word mark clipped across exactly 52 vertical weekly bands.
- **Data:** Every band keeps a dim cobalt base. Bright fill height and opacity derive from weekly contributions.
- **Structure:** Horizontal cuts turn the bands into letter-sized building floors without adding a separate skyline.
- **Motion:** Bands rise in chronological sequence. A periodic scan crosses the word, while only the four most recent active bands pulse.

### Compact Timeline

- **Shape:** The same 52-band geometry is repeated at small scale below the word mark.
- **Data:** Bar height, brightness, and color use the same weekly values as the word mark.
- **Labels:** Only quarterly anchors and NOW are shown.

### Website Signal

- **Shape:** No button, card, fill, or large icon. A 6px cobalt signal, two short labels, and a 1px underline sit in the footer.
- **Color:** Muted blue text over Footer Void.
- **Motion:** One slow opacity pulse on the 6px signal only.

## Do's and Don'ts

### Do:

- **Do** update the generator and regenerate the SVG; never hand-edit generated output.
- **Do** keep all motion inside the SVG and preserve `prefers-reduced-motion`.
- **Do** animate transforms, opacity, and stroke offsets rather than layout geometry.
- **Do** keep the 52 weekly bands aligned between the word mark and compact timeline.
- **Do** keep the website entry quiet while making the entire poster clickable.
- **Do** verify desktop, mobile-width scaling, XML validity, contrast, and reduced motion after major changes.

### Don't:

- **Don't** add badge walls, skill clouds, project cards, or filler sections.
- **Don't** add a separate contribution graph or dashboard-style metric grid.
- **Don't** separate ADAM from the activity visualization; the name is the data surface.
- **Don't** use constant glitching, excessive neon glow, glassmorphism, or fake terminal copy.
- **Don't** introduce JavaScript, external fonts, or external runtime dependencies into the SVG.
- **Don't** enlarge the personal-website CTA until it competes with the city.
- **Don't** use rounded containers, gradient text, decorative status dots, or repeated section labels.

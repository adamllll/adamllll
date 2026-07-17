---
name: ADAM Commit City
description: A living GitHub activity city and personal profile poster.
colors:
  night-deep: "#090d16"
  night-horizon: "#161022"
  footer-void: "#090c13"
  cobalt-wordmark: "#315ee8"
  electric-cyan: "#00d8ff"
  signal-green: "#06ffa5"
  activity-magenta: "#ff6ad5"
  sun-yellow: "#fffd82"
  text-primary: "#f7f3ff"
  text-muted: "#a997b7"
  website-muted: "#8091be"
typography:
  display:
    fontFamily: "Arial Black, Arial, sans-serif"
    fontSize: "196px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "0"
  title:
    fontFamily: "Arial Black, Arial, sans-serif"
    fontSize: "30px"
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
  tower-step: "28px"
  canvas-edge: "70px"
  footer-height: "72px"
components:
  activity-poster:
    backgroundColor: "{colors.night-deep}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.none}"
    width: "1600px"
    height: "720px"
  website-signal:
    backgroundColor: "{colors.footer-void}"
    textColor: "{colors.website-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0px"
---

# Design System: ADAM Commit City

## Overview

**Creative North Star: "The Living Night City"**

The profile is one large, self-contained digital poster. A cobalt ADAM word mark establishes the identity, while 52 weekly activity towers convert real contribution data into the skyline. The composition is cinematic but not noisy: the initial scan and tower boot tell a short story, then the scene settles into sparse city signals.

This system rejects conventional developer-profile filler and generic cyberpunk effects. It is dark because the subject is a night city, not because developer pages are expected to be dark. The city remains the only dominant idea; labels, legend, and website entry stay quiet.

**Key Characteristics:**

- One full-width 1600 x 720 poster
- Sharp pixel geometry with no rounded containers
- Cobalt identity typography over a near-black night field
- Data-driven cyan, green, magenta, and yellow activity signals
- One choreographed load sequence plus low-frequency ambient motion
- A linked poster with a deliberately subdued website signal

## Colors

The palette combines a deep blue-black city field with cobalt identity color and a small data-visualization spectrum.

### Primary

- **City Cobalt:** The word mark, footer rule, and website signal use the primary identity color.

### Secondary

- **Electric Cyan:** Busy weeks, stars, and the horizon data signal.
- **Signal Green:** Low-activity weeks and the current-week marker.
- **Activity Magenta:** Peak weeks and the horizon edge.
- **Sun Yellow:** The sun crown, tower beacons, and the contribution total.

### Neutral

- **Deep Night:** The upper field behind the identity and skyline.
- **Horizon Violet:** The lower night gradient and reflection atmosphere.
- **Primary Text:** High-contrast labels that must be read immediately.
- **Muted Text:** Secondary explanation and timeline copy.
- **Website Muted:** The personal-site label, held above WCAG AA without becoming a focal point.

**The Data Color Rule.** Cyan, green, magenta, and yellow communicate contribution intensity or live signal state. They are never added as unrelated decoration.

## Typography

**Display Font:** Arial Black (with Arial and sans-serif fallbacks)
**Body Font:** Courier New (with Consolas and monospace fallbacks)
**Label/Mono Font:** Courier New (with Consolas and monospace fallbacks)

**Character:** Heavy system display type makes ADAM read as architecture. The mono labels feel like city infrastructure without turning the page into a fake terminal.

### Hierarchy

- **Display** (900, 196px, 1): ADAM only, once per poster.
- **Title** (900, 30px, 1): COMMIT CITY only.
- **Body** (400, 15-16px, 1.2): Timeline and explanatory data labels.
- **Label** (700, 12-14px, 1.2, normal spacing): Footer legend and website entry.

**The One Monument Rule.** ADAM is the only oversized text. No other label competes through scale.

## Elevation

The system is flat by default. Depth comes from skyline overlap, atmospheric opacity, the sun behind the towers, and the perspective reflection plane. There are no card shadows, glass panels, or broad neon glows.

**The Pixel Depth Rule.** Build depth with hard geometry and tonal layers. Blur is prohibited in the signature scene.

## Components

### Activity Poster

- **Shape:** Sharp 1600 x 720 SVG canvas with zero corner radius.
- **Background:** Deep Night to Horizon Violet vertical field.
- **Behavior:** The complete poster scales to the README width and remains fully visible without horizontal scrolling.
- **Link:** The README wraps the poster in one link to the personal website.

### Contribution Tower

- **Shape:** A 21px rectangular weekly band with an optional 13px cap and 2px activity-colored edge.
- **Data:** Height and lit-window count derive from weekly contributions.
- **Motion:** Towers rise in chronological sequence during boot. Only selected windows, beacons, and the current week continue moving.

### Website Signal

- **Shape:** No button, card, fill, or large icon. A 6px cobalt signal, two short labels, and a 1px underline sit in the footer.
- **Color:** Muted blue text over Footer Void.
- **Motion:** One slow opacity pulse on the 6px signal only.

## Do's and Don'ts

### Do:

- **Do** update the generator and regenerate the SVG; never hand-edit generated output.
- **Do** keep all motion inside the SVG and preserve `prefers-reduced-motion`.
- **Do** animate transforms, opacity, and stroke offsets rather than layout geometry.
- **Do** keep the website entry quiet while making the entire poster clickable.
- **Do** verify desktop, mobile-width scaling, XML validity, contrast, and reduced motion after major changes.

### Don't:

- **Don't** add badge walls, skill clouds, project cards, or filler sections.
- **Don't** add a separate contribution graph or dashboard-style metric grid.
- **Don't** use constant glitching, excessive neon glow, glassmorphism, or fake terminal copy.
- **Don't** introduce JavaScript, external fonts, or external runtime dependencies into the SVG.
- **Don't** enlarge the personal-website CTA until it competes with the city.
- **Don't** use rounded containers, gradient text, decorative status dots, or repeated section labels.

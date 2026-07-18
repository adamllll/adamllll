---
name: ADAM_OS Commit Signal
description: A living ADAM word mark shaped by weekly GitHub activity inside a night-mode Win95 profile window.
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
  os-titlebar: "#13275a"
  os-taskbar: "#0d1428"
  chrome-highlight: "#8091be"
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
  website-entry:
    backgroundColor: "{colors.footer-void}"
    textColor: "{colors.website-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0px"
  os-shell:
    backgroundColor: "{colors.os-titlebar}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.none}"
    behavior: "light title bar and taskbar at rest; CTA-launched pixel frame and 52 data conduits during boot"
  os-entry:
    backgroundColor: "{colors.cobalt-wordmark}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.none}"
    label: "OPEN ADAM_OS"
  system-directory:
    backgroundColor: "transparent"
    textColor: "{colors.cobalt-wordmark}"
    rounded: "{rounded.none}"
    behavior: "text-only GitHub-compatible links below the poster"
---

# Design System: ADAM_OS Commit Signal

## Overview

**Creative North Star: "The Name Is the Running System"**

The profile is one large, self-contained digital poster framed as a night-mode Win95 profile window. The 52 vertical bands inside ADAM each represent one week of GitHub activity. Dim cobalt keeps the name legible; contribution height and brightness build a data-driven signal inside the letters themselves.

This system rejects conventional developer-profile filler, generic cyberpunk effects, and compositions where the brand and the data compete as separate objects. It is dark because the subject is a night signal. ADAM remains the only dominant idea; the compact timeline, OS chrome, labels, and website entry stay subordinate to it.

**Key Characteristics:**

- One full-width 1600 x 720 profile window
- Sharp pixel geometry with no rounded containers
- One 1480px ADAM word mark built from exactly 52 weekly bands
- Cobalt architectural typography over a near-black night field
- Data-driven fill height, brightness, and activity color inside the letters
- A boot-only frame launched from `OPEN ADAM_OS`, followed by 52 vertical data conduits that load the word mark
- One integrated `OPEN ADAM_OS` website entry
- One compact `SYSTEM DIRECTORY` rail for secondary navigation

## Colors

The palette combines a deep blue-black city field with cobalt identity color and a small data-visualization spectrum.

### Primary

- **City Cobalt:** The word mark, title bar, taskbar accents, and website entry use the primary identity color.

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
- **OS Titlebar:** Deep cobalt structure that ties the profile to the real personal OS.
- **Chrome Highlight:** Cool lavender edge used for the boot frame and pixel bevels.

**The Data Color Rule.** Cyan, green, magenta, and yellow communicate contribution intensity or live signal state. They are never added as unrelated decoration.

## Typography

**Display Font:** Arial Black (with Arial and sans-serif fallbacks)
**Body Font:** Courier New (with Consolas and monospace fallbacks)
**Label/Mono Font:** Courier New (with Consolas and monospace fallbacks)

**Character:** Heavy system display type makes ADAM the architecture and the data surface at once. The mono labels and Win95 chrome feel like a running personal system without turning the page into a fake terminal.

### Hierarchy

- **Display** (900, 520px, 1): ADAM only, once per poster.
- **Title** (900, 22px, 1): The 52-week concept line only.
- **Body** (400, 15-16px, 1.2): Timeline and explanatory data labels.
- **Label** (700, 12-14px, 1.2, normal spacing): Taskbar status and website entry.

**The One Monument Rule.** ADAM is the only oversized text. No other label competes through scale.

## Elevation

The system is flat by default. Depth comes from a dim word base, bright activity fills, horizontal floor cuts, weekly band gaps, and a crisp cobalt outline. There are no card shadows, glass panels, broad neon glows, or separate background scenery.

**The Pixel Depth Rule.** Build depth with hard geometry and tonal layers. Blur is prohibited in the signature scene.

## Components

### Activity Poster

- **Shape:** Sharp 1600 x 720 SVG canvas with zero corner radius.
- **Background:** Deep Night to Horizon Violet vertical field.
- **Behavior:** The complete poster scales to the README width and remains fully visible without horizontal scrolling.
- **Link:** The README wraps the complete window in one link to the personal website.

### OS Shell

- **Resting state:** A night-mode title bar and taskbar remain visible while the full frame is absent.
- **Boot state:** A crisp pixel frame expands outward from `OPEN ADAM_OS`; 52 vertical conduits then travel from the timeline into their matching ADAM bands.
- **Structure:** The shell is part of the same SVG and never becomes a second panel or separate image.
- **Reduced motion:** The full frame and boot label are skipped; the resting shell is shown immediately.

### Activity Word Mark

- **Shape:** One 1480px ADAM word mark clipped across exactly 52 vertical weekly bands.
- **Data:** Every band keeps a dim cobalt base. Bright fill height and opacity derive from weekly contributions.
- **Structure:** Horizontal cuts turn the bands into letter-sized building floors without adding a separate skyline.
- **Motion:** Each timeline position sends one vertical boot conduit into its matching weekly band. Bands rise in chronological sequence, the completed word performs one short cyan-magenta lock, and all boot geometry disappears. A periodic scan then crosses the word, while only the four most recent active bands pulse.

### Compact Timeline

- **Shape:** The same 52-band geometry is repeated at small scale below the word mark.
- **Data:** Bar height, brightness, and color use the same weekly values as the word mark.
- **Labels:** Only quarterly anchors and NOW are shown.

### Website Entry

- **Shape:** A single raised pixel button labeled `OPEN ADAM_OS` sits in the taskbar, with the real URL below it.
- **Color:** Cobalt button fill with cool-white bevel highlights and a small green live signal.
- **Behavior:** The button is a visual entry cue; the complete SVG remains the single link target.
- **Motion:** The button settles in during boot, then the live signal pulses slowly.

### System Directory

- **Shape:** One centered text-only rail below the SVG, separated with plain slashes.
- **Links:** `PROJECTS.EXE`, `BLOG.DB`, and `ABOUT.SYS` point to real pages on the personal website.
- **Constraint:** The rail never repeats `OPEN ADAM_OS` and never grows into a card grid or badge wall.

## Do's and Don'ts

### Do:

- **Do** update the generator and regenerate the SVG; never hand-edit generated output.
- **Do** keep all motion inside the SVG and preserve `prefers-reduced-motion`.
- **Do** animate transforms, opacity, and stroke offsets rather than layout geometry.
- **Do** keep the 52 weekly bands aligned between the word mark and compact timeline.
- **Do** keep the OS shell structural and the website entry subordinate while making the entire poster clickable.
- **Do** verify desktop, mobile-width scaling, XML validity, contrast, and reduced motion after major changes.

### Don't:

- **Don't** add badge walls, skill clouds, project cards, or filler sections.
- **Don't** add a separate contribution graph or dashboard-style metric grid.
- **Don't** separate ADAM from the activity visualization; the name is the data surface.
- **Don't** use constant glitching, excessive neon glow, glassmorphism, or fake terminal copy.
- **Don't** introduce JavaScript, external fonts, or external runtime dependencies into the SVG.
- **Don't** split the OS entry into a second image, card, or unrelated README section.
- **Don't** use rounded containers, gradient text, decorative status dots, or repeated section labels.

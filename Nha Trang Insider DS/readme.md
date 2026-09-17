# Nha Trang Insider — Design System

## Overview

**Nha Trang Insider** is a Russian-language travel and services brand based in **Nha Trang (Нья Чанг), Vietnam**. The brand helps Russian-speaking tourists navigate the Cam Ranh (Камрань) airport area and the broader Nha Trang region.

### Core Services
| Service | Russian | Description |
|---|---|---|
| Fast-Track | Быстрый проход | VIP accelerated immigration & customs at Cam Ranh airport |
| VIP Transfers | VIP Трансфер | Private airport pickup and city transport |
| Overstay / Legal | Виза / Юридическая помощь | Visa extension, overstay resolution, legal assistance |
| Insider Guides | Советы инсайдера | Local knowledge — islands, beaches, restaurants |

**Primary platform:** Instagram (Russian-language). Target audience: Russian-speaking tourists and expats in Vietnam.

---

## Sources
- **Logo badge** — extracted from uploaded image (circular navy + gold ring + airplane + luggage icons)
- **Three content style references** — screenshots of existing Instagram posts (viral dark, tropical info, premium navy)
- No Figma file or production codebase was provided; system was derived from visual reference + brand brief
- Competitor reference accounts noted: `@viet.privet`, `@thecreative.social`

> ⚠️ **Logo note:** The uploaded logo image appears cropped (bottom half cut off). Request the full circular badge from the brand owner for clean usage.

---

## CONTENT FUNDAMENTALS

### Language
All consumer-facing copy is in **Russian (Cyrillic)**. Internal code, token names, and component props use English.

### Voice & Tone
- **Expert but accessible** — the brand is the insider friend who already knows Vietnam
- **Direct and punchy** — short sentences, no filler. Russians value efficiency
- **Confident, never salesy** — state facts and let them sell themselves
- **Warm, not stiff** — use conversational Russian, not formal corporate language

### Copywriting patterns
- Headlines in **ALL CAPS** (like the existing posts) for impact
- Body in sentence case, relaxed rhythm
- Numbers and specifics are trust signals: "2000+ видов кораллов", "20 минут vs 3 часа"
- CTAs: imperative mood — "Заказать", "Узнать цену", "Сохрани", "Поделиться"
- Emoji used **sparingly and functionally** — as bullet markers (🌊 🎢 🏖) or attention hooks (⏱ ✈️ 💸), never decoratively

### Post formats
| Format | Style notes |
|---|---|
| Карусель (Carousel) | Hook slide with question → answer slides → CTA slide |
| Reels cover | Bold visual + 1 punchy Cyrillic question |
| Инфо-пост (Info post) | Structured data with visual hierarchy |

---

## VISUAL FOUNDATIONS

### Color System
The brand has **one core palette** (Navy + Gold) and **three accent modes** for content variety:

| Palette | Hex | Usage |
|---|---|---|
| Navy 900 | `#0D1741` | Logo background, dark slides, primary CTA |
| Gold 500 | `#C9941A` | Logo ring, accents, divider lines |
| Black | `#0A0A0A` | Viral / dark-mode content |
| Lime 500 | `#7FE030` | Viral accent — neon headlines on black |
| Coral 500 | `#E8583A` | New warm direction — CTAs, warm posts |
| Sand 300 | `#F0C88A` | Warm background, card tints |
| Sea 500 | `#1E8AA8` | Ocean / tropical content |
| Amber 500 | `#F5C200` | Tropical info cards (yellow splash) |

### Typography
- **Montserrat** — display headlines, buttons, badge labels (Cyrillic ✓)
  - 900 Black: hero titles, viral hooks
  - 800 ExtraBold: main slide headlines
  - 700 Bold: section headers, buttons
  - 600 SemiBold: subheadings, body emphasis
- **PT Sans** — body copy, captions, info text (designed for Cyrillic)
  - 400 Regular: running text
  - 700 Bold: callouts, emphasized info
- **Oswald** — condensed service labels, badge text (Cyrillic ✓)
  - 700 → service titles in compressed layouts

All text set with `text-wrap: pretty` where supported. Headlines uppercase with `letter-spacing: -0.02em` for tight, premium feel.

### Content Style Modes
The brand currently operates in **three visual modes** and is developing a fourth:

| Mode | BG | Headline | Body | When to use |
|---|---|---|---|---|
| **Premium Navy** | `#0D1741` | White 900 caps | White 400 | Service promos, airport info |
| **Viral Dark** | `#000000` | Lime 500 caps | White 400 | Viral hooks, money/tips posts |
| **Tropical Info** | Sea gradient | Amber card | White cards | Island/beach guides, info |
| **Warm Coral** *(new)* | Sunset gradient | White 900 | White 400 | Fast-Track CTAs, lifestyle |

### Backgrounds
- No photographic backgrounds in the system (post over photo is done in Canva separately)
- Gradient backgrounds simulate mood: navy for authority, sunset for warmth, teal for ocean
- Overlays (`--overlay-navy-strong`, `--overlay-black-mid`) protect text on photo posts

### Spacing & Radius
- Base unit: **4px**. All spacing is multiples of 4
- Cards: `border-radius: 16–24px` (generous rounding, feels friendly not corporate)
- Badges/pills: `border-radius: 9999px` (fully rounded)
- Buttons: fully rounded pill shape

### Shadows
- Cards on dark: `--shadow-navy` (deep blue-tinted shadow)
- Gold CTAs: `--shadow-gold` (warm ambient glow)
- Coral CTAs: `--shadow-coral` (warm red ambient)

### Motion & Interaction
- Transitions: 150ms fast (hover) / 280ms normal / 450ms slow entries
- Spring easing (`cubic-bezier(0.34, 1.56, 0.64, 1)`) for bouncy badge reveals
- No infinite decorative animations on post content
- Hover: slight shadow increase + 2px lift (`translateY(-2px)`)

### Glass Effect
- `--glass-navy` (`rgba(13,23,65,0.72)` + `backdrop-filter: blur(14px)`) — for text overlay cards on ocean/photo backgrounds
- Used on Warm Coral template bottom card

---

## ICONOGRAPHY

- **No custom icon font** — the brand does not use an icon set
- **Emoji** used as functional markers in tropical / info posts: 🌊 🎢 🏖 ⏱ ✈️ 💸
- **SVG icons** used inline only for the logo badge (airplane + luggage shapes in gold)
- The **logo badge** (navy circle + gold ring) is the only persistent brand mark
- Arrow icon (→) used as CTA indicator in text

> ⚠️ **Logo note**: Only a cropped version of the logo is available. Full circular badge recommended. Current file: `assets/logo.png`

### Reference assets
| File | Description |
|---|---|
| `assets/logo.png` | Brand badge (cropped — top half only) |
| `assets/style-viral.png` | Reference: viral dark carousel style |
| `assets/style-tropical.png` | Reference: tropical island guide style |
| `assets/style-premium.png` | Reference: premium navy airport style |

---

## FILE INDEX

```
styles.css                          Global CSS entry point (imports only)
readme.md                           This file
SKILL.md                            Claude Code skill definition

tokens/
  colors.css                        Color custom properties (146 tokens)
  typography.css                    Font faces + size/weight/spacing tokens
  spacing.css                       Space scale, radius, shadow tokens
  effects.css                       Gradients, overlays, blur, transitions

components/
  core/
    Button.jsx + .d.ts + .prompt.md Primary CTA control (5 variants)
    Badge.jsx  + .d.ts + .prompt.md Label chip (7 variants)
    Card.jsx   + .d.ts + .prompt.md Container (9 variants)
    Tag.jsx    + .d.ts + .prompt.md Category pill (8 variants)
    core.card.html                  Component showcase card

guidelines/
  colors-navy.card.html             Navy scale swatches
  colors-gold.card.html             Gold scale swatches
  colors-warm.card.html             Coral + Sand swatches
  colors-sea.card.html              Sea + Turquoise swatches
  colors-accent.card.html           Lime + Amber swatches
  colors-neutral.card.html          Full neutral scale
  gradients.card.html               Named gradient strips
  type-display.card.html            Montserrat display specimens
  type-body.card.html               PT Sans body specimens
  type-labels.card.html             Oswald label specimens
  spacing.card.html                 Visual spacing scale
  logo.card.html                    Logo on 3 backgrounds
  content-styles.card.html          4 post style thumbnails

assets/
  logo.png                          Brand badge (nav+gold, cropped)
  style-viral.png                   Reference post — dark/lime
  style-tropical.png                Reference post — tropical/yellow
  style-premium.png                 Reference post — navy/gold

ui_kits/
  instagram/
    index.html                      Interactive 4-template post system
```

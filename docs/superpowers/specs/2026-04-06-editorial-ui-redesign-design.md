# Editorial UI Redesign

## Goal

Recast Paper Insight from a generic knowledge-base interface into an editorial publication for recommendation research: cultural-review atmosphere, academic clarity, stronger contrast, lighter navigation, and a unified visual language across home, article, and benchmark pages.

## Approved Direction

- Tone: cultural review publication with academic rigor
- Motion: restrained only
- Home: cover-like landing first, then content flow
- Priority fixes:
  - typography and color contrast
  - presentation style
  - more dynamic overall layout

## Visual System

- Use a warm paper background instead of flat app-white.
- Replace large-area blue UI with deep ink text and a single warm editorial accent.
- Pair an expressive serif display face for headlines with a restrained sans-serif for navigation, metadata, and dense data surfaces.
- Build hierarchy through spacing, borders, alignment, scale, and rhythm rather than colored pills and generic cards.

## Page Design

### Home

- Add a cover-style hero with title, editorial note, update metadata, and a curated set of recent papers.
- Keep article discovery directly below the hero so the site still behaves like a research archive.
- Render the article list in an editorial rhythm:
  - one lead item
  - two supporting items
  - a compact archive list after that

### Sidebar

- Turn the sidebar into a table-of-contents rail.
- Remove blue category text as the default state.
- Express active state with accent color, rules, and spacing instead of solid fills.
- Keep category counts visible but visually secondary.

### Article Detail

- Use a more publication-like masthead with title, metadata, actions, and category labels.
- Give the article body a calmer reading measure, better heading hierarchy, and more polished tables/code blocks.
- Preserve analysis-state messaging and source links.

### Benchmark

- Pull the benchmark page into the same editorial system with a masthead, section framing, and toned-down data styling.
- Keep leaderboard functionality and link resolution unchanged.
- Make the right rail feel like an annotated research index rather than a utility widget block.

## Interaction

- Keep motion restrained: entrance fades, hover lift, subtle transform on major modules, and lightweight sidebar behavior on mobile.
- Preserve existing search and category filtering behavior.

## Constraints

- No regression in homepage filtering, category routing, article rendering, or benchmark analysis links.
- Stay compatible with the current Jekyll/Liquid setup.

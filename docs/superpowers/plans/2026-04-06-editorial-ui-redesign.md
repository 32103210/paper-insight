# Editorial UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the site into a publication-grade editorial interface without breaking filtering, article rendering, or benchmark analysis behavior.

**Architecture:** Keep the existing Jekyll content model and JavaScript data bootstrapping, but redesign the shell, homepage composition, article masthead, and benchmark presentation around a shared editorial design system. Introduce small testable JS helpers for homepage composition so visual layout changes still have deterministic behavior.

**Tech Stack:** Jekyll, Liquid, vanilla JavaScript, CSS, Node built-in test runner

---

### Task 1: Add deterministic editorial helper coverage

**Files:**
- Modify: `assets/js/app.js`
- Test: `tests/app.test.cjs`

- [ ] Add a pure helper that partitions posts into lead/support/archive groups.
- [ ] Export the helper for Node-based unit testing without breaking the browser build.
- [ ] Write and run red-green tests for the helper and keep homepage filtering behavior intact.

### Task 2: Rebuild the site shell and homepage presentation

**Files:**
- Modify: `_layouts/page.html`
- Modify: `_includes/sidebar.html`
- Modify: `_includes/header.html`
- Modify: `index.md`
- Modify: `assets/css/style.css`
- Modify: `assets/js/app.js`

- [ ] Add the new editorial shell, type loading, and mobile sidebar trigger.
- [ ] Replace the generic search/list landing page with a cover-style hero and editorial article flow.
- [ ] Restyle category navigation, search, and post listings around the new design system.

### Task 3: Redesign article detail presentation

**Files:**
- Modify: `_layouts/post.html`
- Modify: `assets/css/style.css`

- [ ] Convert the article page to a publication-style masthead and reading layout.
- [ ] Preserve analysis state messaging, tags, and source links while improving visual hierarchy.

### Task 4: Unify benchmark page styling

**Files:**
- Modify: `benchmark/index.md`
- Modify: `assets/css/style.css`

- [ ] Replace the page-local utility styling with the shared editorial visual system.
- [ ] Keep current benchmark JavaScript behavior and analysis link resolution intact.

### Task 5: Verify, commit, and push

**Files:**
- Modify: relevant files from Tasks 1-4

- [ ] Run Node helper tests, Python regression tests, JS syntax checks, and a Jekyll build where possible.
- [ ] Review the rendered diff for layout regressions.
- [ ] Commit and push the redesign to `main`.

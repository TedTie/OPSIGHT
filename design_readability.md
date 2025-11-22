# UI Redesign – Ensuring Text Readability (2025 Green Theme)

## 1. Typography & Hierarchy
- **Font**: `Inter` (already set in `--font-family`).
- **Base size**: `16px` with `line-height: 1.6` for body text.
- **Heading scale**:
  - H1 / `.page-title`: `32px`, `font-weight: 700`.
  - H2: `28px`, `font-weight: 600`.
  - H3: `24px`, `font-weight: 600`.
- **Weight usage**: 
  - Strong text: `--font-weight-bold` (700).
  - Normal text: `--font-weight-regular` (400).
  - Emphasis: `--font-weight-medium` (500).

## 2. Color Contrast
- **Backgrounds**: Light (`--bg-page: #f8fafb`, `--bg-elevated: #ffffff`).
- **Text colors**:
  - Primary: `--text-strong` (`#0f172a`).
  - Normal: `--text-normal` (`#334155`).
  - Muted: `--text-muted` (`#64748b`).
- **Brand accent**: `--color-primary` (`#10b981`) used for links, buttons, focus outlines – always on a light background to keep contrast ≥ 4.5:1.
- **Semantic colors** (error, warning, success) keep their original contrast.

## 3. Component Styling
### Cards & Panels
- Use **solid white** (`background: #ffffff`) with **soft shadows** (`var(--shadow-sm)` / `var(--shadow-md)`).
- Avoid heavy glass‑morphism on text‑heavy cards – it reduces readability.

### Inputs & Buttons
- **Input focus**: `border-color: var(--color-primary); box-shadow: var(--shadow-glow);` text stays `--text-strong`.
- **Primary buttons**: `background: var(--gradient-primary); color: #fff;` hover adds subtle lift.

### Sidebar & Header
- Light backgrounds with `var(--border-color)` separators.
- Hover/active states use `var(--surface-hover)` and `var(--color-primary)` for text, preserving contrast.

## 4. Accessibility (WCAG AA)
- **Contrast**: ≥ 4.5:1 for normal text, ≥ 3:1 for large text.
- **Focus indicator**: `outline: 2px solid var(--color-primary);` on all interactive elements.
- **ARIA**: Add `aria-label` to icon‑only buttons, `role="grid"` to tables.

## 5. Responsive Adjustments
- Increase base font to **17 px** on screens ≤ 480 px.
- Ensure line‑height remains ≥ 1.5.
- Keep sufficient padding/margin so text never gets cramped.

## 6. Implementation Checklist
- [ ] Update `style.css` with the variables above (already done).
- [ ] Apply heading classes (`.page-title`, `.h2`, `.h3`) throughout Vue templates.
- [ ] Replace dark‑mode card backgrounds with solid white + soft shadow.
- [ ] Verify all inputs/buttons use the new focus styles.
- [ ] Run an accessibility audit (Lighthouse) and fix any contrast warnings.
- [ ] Test on mobile to confirm readability.

---
*This document outlines a concise, actionable plan to make every piece of text in the app clear, legible, and accessible while keeping the fresh 2025 green visual language.*

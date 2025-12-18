# AInfluencer UI/UX Redesign Master Plan

**Version:** 1.0  
**Date:** 2025-01-15  
**Status:** Planning Document (No Implementation)  
**Author:** Principal Product Designer + Design Systems Lead

---

## Executive Summary

This document defines a comprehensive visual and interaction redesign for AInfluencer, transforming it into a modern, premium, futuristic platform that is accessible to non-technical creators. The redesign prioritizes clarity, guided workflows, and beautiful aesthetics while eliminating clutter and dead routes.

**Core Philosophy:** "Setup → Create → Generate → Library" — a clear, linear journey for users who want to create AI influencer content without technical complexity.

---

## Table of Contents

1. [North Star & Product Principles](#north-star--product-principles)
2. [Information Architecture & Navigation](#information-architecture--navigation)
3. [Visual Design System (Tokens)](#visual-design-system-tokens)
4. [Component Library Specification](#component-library-specification)
5. [Motion & Micro-Interactions](#motion--micro-interactions)
6. [Page-by-Page Redesign Plan](#page-by-page-redesign-plan)
7. [Remove / Merge / Hide List (Scope Control)](#remove--merge--hide-list-scope-control)
8. [Free Assets Strategy](#free-assets-strategy)
9. [Accessibility & UX Quality Bar](#accessibility--ux-quality-bar)
10. [Implementation Readiness](#implementation-readiness)

---

## North Star & Product Principles

### Target User Profile

**Primary:** Non-technical creator (e.g., "grandma-friendly")

- Wants to create AI influencer content
- Needs guided, step-by-step workflows
- Expects clear feedback and error messages
- Prefers visual over technical information
- Should never encounter a "broken" state without a clear path forward

**Secondary:** Power users who need advanced controls

- Can access advanced features via "Advanced" toggle
- Technical diagnostics and configuration available but hidden by default

### Core User Journey

```
1. Setup → Install/Repair/Diagnose system (one-time or when needed)
2. Create → Build AI influencer characters
3. Generate → Create images/videos using ComfyUI
4. Library → View, organize, and export generated content
```

### Design Principles

1. **"No Broken States"**

   - Every error becomes a guided state with a clear CTA
   - Empty states include actionable next steps
   - System issues surface with remediation buttons

2. **"Advanced Hides Complexity"**

   - Default views show only essential controls
   - Advanced features (Models, ComfyUI management, Workflows) live under "Advanced" toggle
   - Technical diagnostics available but not prominent

3. **"Guided by Default"**

   - Presets and templates reduce decision fatigue
   - Smart defaults for all settings
   - Progressive disclosure: show basics first, reveal details on demand

4. **"Visual Over Technical"**

   - Status indicators use colors/icons, not just text
   - Preview images before generation
   - Gallery-first content browsing

5. **"Premium but Accessible"**
   - Beautiful gradients and subtle 3D effects
   - High-quality icons and typography
   - Smooth animations that don't compromise performance
   - Works on low-end machines (graceful degradation)

---

## Information Architecture & Navigation

### Current State Analysis

**Existing Routes (Verified):**

- `/` - Dashboard
- `/installer` - Setup/Installer
- `/characters` - Character list
- `/characters/create` - Create character
- `/characters/[id]` - Character detail
- `/characters/[id]/edit` - Edit character
- `/generate` - Generate images
- `/models` - Models management
- `/analytics` - Analytics
- `/comfyui` - ComfyUI management
- `/marketplace` - Marketplace (exists but may be incomplete)
- `/videos` - Videos library

**Routes Referenced but Missing (404 Risk):**

- `/content` - Referenced in MainNavigation.tsx as "Library" but no page exists
- `/workflows` - Referenced in Advanced nav but no page exists
- `/settings` - Referenced in Advanced nav but no page exists

### Proposed Final Navigation Map

#### Top-Level Navigation (Always Visible)

```
[Logo: AInfluencer]  [Setup]  [Create]  [Generate]  [Library]  [Advanced ▼]
```

**Main Navigation Items:**

1. **Setup** (`/installer`)

   - Single entry point for all system setup, diagnostics, repair
   - Replaces current installer page but with better UX
   - Shows system health at a glance

2. **Create** (`/characters`)

   - Character list and creation
   - Primary action: "Create Character" button

3. **Generate** (`/generate`)

   - Image/video generation interface
   - ComfyUI status gating (if not ready, show setup CTA)

4. **Library** (`/content` - **NEW PAGE TO CREATE**)

   - Unified content library (images + videos)
   - Grid view, filters, export
   - Replaces need for separate `/videos` page (merge into Library)

5. **Advanced** (Dropdown/Toggle)
   - Models (`/models`)
   - Analytics (`/analytics`)
   - ComfyUI Manager (`/comfyui`)
   - Workflows (`/workflows` - **IMPLEMENT LATER OR REMOVE LINK**)
   - Settings (`/settings` - **IMPLEMENT LATER OR REMOVE LINK**)

#### Route Policy

**Immediate Actions:**

- ✅ Keep: `/`, `/installer`, `/characters/*`, `/generate`, `/models`, `/analytics`, `/comfyui`
- ✅ Create: `/content` (Library page - merge videos into this)
- ⚠️ Remove links (keep pages if they exist): `/workflows`, `/settings` (hide from nav until implemented)
- ⚠️ Merge: `/videos` → `/content` (redirect old route to new)

**404 Handling:**

- Custom 404 page with:
  - "Page not found" message
  - Link back to Dashboard
  - Search suggestions for common routes
  - "Report broken link" option (optional)

### Navigation Component Structure

**AppShell (Persistent):**

- Header: Logo + Main Nav (Setup, Create, Generate, Library)
- Advanced Toggle: Dropdown or slide-out panel
- Breadcrumbs: For nested pages (e.g., Characters > Character Name > Edit)
- Status Bar: Optional system health indicator (collapsible)

**Secondary Navigation (Page-Specific):**

- Tabs within pages (e.g., Character Detail: Overview, Content, Styles, Activity)
- Sidebar for filters/settings (e.g., Library filters)

---

## Visual Design System (Tokens)

### Color System

**Base Palette (Dark Mode Default, Light Mode Optional):**

```css
/* Background Hierarchy */
--bg-base: #0a0a0a; /* Deep black (dark mode) / #ffffff (light) */
--bg-surface: #181818; /* Elevated surface (dark) / #f9fafb (light) */
--bg-elevated: #242424; /* Cards, modals (dark) / #ffffff (light) */
--bg-overlay: rgba(0, 0, 0, 0.8); /* Modal overlays */

/* Borders */
--border-base: #2a2a2a; /* Default borders (dark) / #e5e7eb (light) */
--border-elevated: #3a3a3a; /* Elevated borders (dark) / #d1d5db (light) */
--border-focus: #6366f1; /* Focus rings (indigo) */

/* Text Hierarchy */
--text-primary: #f9fafb; /* Primary text (dark) / #111827 (light) */
--text-secondary: #d1d5db; /* Secondary text (dark) / #6b7280 (light) */
--text-muted: #9ca3af; /* Muted text (dark) / #9ca3af (light) */
--text-disabled: #6b7280; /* Disabled text */

/* Accent Colors */
--accent-primary: #6366f1; /* Indigo (primary actions) */
--accent-primary-hover: #4f46e5;
--accent-secondary: #8b5cf6; /* Purple (secondary actions) */
--accent-tertiary: #06b6d4; /* Cyan (info, links) */

/* Semantic Colors */
--success: #10b981; /* Green (success states) */
--success-bg: rgba(16, 185, 129, 0.1);
--warning: #f59e0b; /* Amber (warnings) */
--warning-bg: rgba(245, 158, 11, 0.1);
--error: #ef4444; /* Red (errors) */
--error-bg: rgba(239, 68, 68, 0.1);
--info: #3b82f6; /* Blue (info) */
--info-bg: rgba(59, 130, 246, 0.1);
```

**Gradient Rules:**

- **Allowed Gradients:**
  - Hero sections: `linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))`
  - Card hover: Subtle `linear-gradient(180deg, transparent, rgba(var(--accent-primary), 0.05))`
  - Background textures: Very subtle mesh gradients (opacity < 0.03)
- **Intensity Limits:**
  - Never exceed 20% opacity for background gradients
  - Text gradients only for headings (sparingly)
- **Reduced Motion Fallback:**
  - Solid colors when `prefers-reduced-motion` is enabled
  - No animated gradients

### Typography

**Font Strategy:**

- **Primary:** Geist Sans (already loaded via Next.js Google Fonts)
- **Monospace:** Geist Mono (for code, logs, technical data)
- **Fallback:** System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`)

**Type Scale (4px base, 1.25 ratio):**

```css
/* Display (Hero, Landing) */
--text-display-2xl: 4.5rem; /* 72px - Hero headlines */
--text-display-xl: 3.75rem; /* 60px - Section headlines */
--text-display-lg: 3rem; /* 48px - Large headlines */

/* Headings */
--text-h1: 2.25rem; /* 36px - Page titles */
--text-h2: 1.875rem; /* 30px - Section titles */
--text-h3: 1.5rem; /* 24px - Subsection titles */
--text-h4: 1.25rem; /* 20px - Card titles */
--text-h5: 1.125rem; /* 18px - Small headings */

/* Body */
--text-base: 1rem; /* 16px - Default body */
--text-sm: 0.875rem; /* 14px - Secondary text */
--text-xs: 0.75rem; /* 12px - Labels, captions */
--text-2xs: 0.625rem; /* 10px - Fine print */

/* Line Heights */
--leading-tight: 1.2; /* Headings */
--leading-normal: 1.5; /* Body */
--leading-relaxed: 1.75; /* Long-form content */

/* Font Weights */
--weight-light: 300;
--weight-normal: 400;
--weight-medium: 500;
--weight-semibold: 600;
--weight-bold: 700;
```

**Typography Usage Rules:**

- Page titles: `h1` with `--text-h1`, `--weight-bold`
- Section titles: `h2` with `--text-h2`, `--weight-semibold`
- Card titles: `h3` or `h4` with `--weight-medium`
- Body text: `--text-base` with `--leading-normal`
- Labels: `--text-xs` with `--weight-medium`, `--text-secondary`
- Code/logs: `--font-mono`, `--text-sm`

### Spacing Scale

**4px Base System:**

```css
--space-0: 0;
--space-1: 0.25rem; /* 4px */
--space-2: 0.5rem; /* 8px */
--space-3: 0.75rem; /* 12px */
--space-4: 1rem; /* 16px */
--space-5: 1.25rem; /* 20px */
--space-6: 1.5rem; /* 24px */
--space-8: 2rem; /* 32px */
--space-10: 2.5rem; /* 40px */
--space-12: 3rem; /* 48px */
--space-16: 4rem; /* 64px */
--space-20: 5rem; /* 80px */
--space-24: 6rem; /* 96px */
```

**Component Padding Standards:**

- Cards: `--space-5` (20px) or `--space-6` (24px)
- Buttons: `--space-3` vertical, `--space-4` horizontal (12px/16px)
- Inputs: `--space-3` vertical, `--space-4` horizontal
- Sections: `--space-8` or `--space-10` between major sections
- Page container: `--space-6` horizontal padding, `--space-8` vertical

### Radius Scale

```css
--radius-none: 0;
--radius-sm: 0.25rem; /* 4px - Small elements */
--radius-md: 0.5rem; /* 8px - Buttons, inputs (default) */
--radius-lg: 0.75rem; /* 12px - Cards */
--radius-xl: 1rem; /* 16px - Large cards, modals */
--radius-2xl: 1.5rem; /* 24px - Hero sections */
--radius-full: 9999px; /* Pills, badges */
```

### Shadows & Elevation

```css
/* Elevation Levels */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

/* Usage */
--elevation-1: --shadow-sm; /* Subtle lift (hover states) */
--elevation-2: --shadow-md; /* Cards */
--elevation-3: --shadow-lg; /* Elevated cards, dropdowns */
--elevation-4: --shadow-xl; /* Modals, popovers */
--elevation-5: --shadow-2xl; /* Hero overlays */
```

### Blur & Glass Effects

**Rules:**

- Use sparingly (max 2-3 instances per page)
- Backdrop blur: `backdrop-filter: blur(12px)` with `rgba(0, 0, 0, 0.3)` background
- Only for: Navigation bars, modal overlays, floating action buttons
- **Never use:** As a crutch for poor contrast or readability

### Icon Sizing Rules

```css
--icon-xs: 0.75rem; /* 12px - Inline with small text */
--icon-sm: 1rem; /* 16px - Default inline icons */
--icon-md: 1.25rem; /* 20px - Button icons */
--icon-lg: 1.5rem; /* 24px - Card icons */
--icon-xl: 2rem; /* 32px - Feature icons */
--icon-2xl: 3rem; /* 48px - Hero icons */
```

**Icon Library:** Choose ONE primary set (see Free Assets Strategy section)

### Layout Grid

```css
/* Container */
--container-max-width: 1280px; /* Max content width */
--container-padding: var(--space-6); /* Horizontal padding */

/* Breakpoints */
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;

/* Grid Gutters */
--grid-gutter: var(--space-4); /* 16px default */
--grid-gutter-lg: var(--space-6); /* 24px for large screens */
```

**Grid System:**

- 12-column grid (flexbox or CSS Grid)
- Responsive: 1 col (mobile) → 2 cols (tablet) → 3-4 cols (desktop)
- Cards: Min width 280px, max width 400px per card

### Dark Mode + Light Mode Strategy

**Default:** Dark mode (matches current aesthetic)

**Light Mode Support:**

- Implement via CSS variables (already partially in place)
- Toggle in Settings (when implemented) or system preference
- Ensure all colors have light mode equivalents
- Test contrast ratios in both modes

**Implementation:**

- Use `prefers-color-scheme` media query for system preference
- Store user preference in localStorage
- Apply class to `<html>` element: `data-theme="dark"` or `data-theme="light"`

---

## Component Library Specification

### AppShell

**Purpose:** Persistent navigation and layout wrapper

**Structure:**

```
┌─────────────────────────────────────────┐
│ [Logo] [Setup] [Create] [Generate] [Library] [Advanced▼] │
├─────────────────────────────────────────┤
│                                         │
│         Page Content                    │
│                                         │
└─────────────────────────────────────────┘
```

**States:**

- Default: Navigation visible, sticky header
- Mobile: Hamburger menu (collapsible)
- Advanced open: Dropdown or slide-out panel

**Props:**

- `children`: Page content
- `showBreadcrumbs?: boolean`
- `statusBar?: ReactNode` (optional system health)

### PageHeader

**Purpose:** Consistent page titles and actions

**Structure:**

```
┌─────────────────────────────────────────┐
│ Title                    [Action Button] │
│ Description                             │
└─────────────────────────────────────────┘
```

**Variants:**

- Default: Title + description + primary action
- With tabs: Title + tabs below
- With filters: Title + filter bar

**Props:**

- `title: string`
- `description?: string`
- `action?: ReactNode` (primary button)
- `tabs?: Array<{id, label, href}>`

### SectionCard

**Purpose:** Grouped content sections

**Structure:**

```
┌─────────────────────────────────────────┐
│ Section Title              [Optional Action] │
│                                         │
│ Content...                              │
└─────────────────────────────────────────┘
```

**Variants:**

- Default: White/dark surface, border, padding
- Elevated: Shadow, slightly raised
- Bordered: Prominent border (for important sections)

**States:**

- Default
- Hover: Subtle shadow lift (`--elevation-1`)
- Loading: Skeleton content
- Empty: Empty state component

**Props:**

- `title?: string`
- `description?: string`
- `children: ReactNode`
- `variant?: "default" | "elevated" | "bordered"`
- `loading?: boolean`
- `empty?: boolean`

### MetricCard

**Purpose:** Display key metrics/statistics

**Structure:**

```
┌─────────────────────────────────────────┐
│ [Icon]  Label                           │
│         123,456                         │
│         +12% vs last month              │
└─────────────────────────────────────────┘
```

**Variants:**

- Default: Number + label + trend
- Icon: With icon/emoji
- Chart: With mini sparkline

**Props:**

- `label: string`
- `value: string | number`
- `trend?: {value: number, label: string}`
- `icon?: ReactNode`
- `variant?: "default" | "icon" | "chart"`

### Buttons

#### PrimaryButton

**Purpose:** Main actions (Create, Generate, Save)

**States:**

- Default: `--accent-primary` background, white text
- Hover: Darker shade, slight lift
- Active: Pressed state (scale 0.98)
- Disabled: 50% opacity, no interaction
- Loading: Spinner + disabled state

**Props:**

- `children: ReactNode`
- `onClick?: () => void`
- `disabled?: boolean`
- `loading?: boolean`
- `icon?: ReactNode`
- `size?: "sm" | "md" | "lg"`

#### SecondaryButton

**Purpose:** Secondary actions (Cancel, Back)

**States:**

- Default: Border, transparent background
- Hover: Background fill, border color change
- Active/Disabled/Loading: Same as PrimaryButton

#### GhostButton

**Purpose:** Tertiary actions (View, Edit)

**States:**

- Default: No border, transparent
- Hover: Subtle background
- Active/Disabled: Same pattern

#### IconButton

**Purpose:** Icon-only actions (Close, Delete, More)

**States:**

- Default: Square/circle, icon centered
- Hover: Background fill
- Active: Scale down
- Sizes: `sm` (32px), `md` (40px), `lg` (48px)

### Form Components

#### Input

**Purpose:** Text input fields

**States:**

- Default: Border, padding, placeholder
- Focus: Border color change, ring outline
- Error: Red border, error message below
- Disabled: Grayed out, no interaction
- Loading: Spinner icon (for async validation)

**Props:**

- `label?: string`
- `placeholder?: string`
- `error?: string`
- `helperText?: string`
- `required?: boolean`
- `disabled?: boolean`
- `type?: "text" | "email" | "password" | "number"`

#### Textarea

**Purpose:** Multi-line text input

**States:** Same as Input

**Props:**

- Same as Input
- `rows?: number`
- `resize?: "none" | "vertical" | "both"`

#### Select

**Purpose:** Dropdown selection

**States:**

- Default: Border, chevron icon
- Open: Dropdown menu below
- Focus: Ring outline
- Error: Red border
- Disabled: Grayed out

**Props:**

- `label?: string`
- `options: Array<{value, label}>`
- `value?: string`
- `onChange?: (value: string) => void`
- `error?: string`
- `placeholder?: string`

#### FormGroup

**Purpose:** Group related form fields

**Structure:**

```
┌─────────────────────────────────────────┐
│ Group Label                             │
│   [Field 1]                             │
│   [Field 2]                             │
│   Helper text                           │
└─────────────────────────────────────────┘
```

**Props:**

- `label?: string`
- `description?: string`
- `children: ReactNode`
- `error?: string`

#### InlineHelp

**Purpose:** Contextual help text/icons

**Variants:**

- Tooltip: Hover to reveal
- Inline: Text next to label
- Info icon: Click to reveal modal

**Props:**

- `content: string | ReactNode`
- `variant?: "tooltip" | "inline" | "icon"`

### Feedback Components

#### Toast

**Purpose:** Temporary success/error messages

**Variants:**

- Success: Green background, checkmark icon
- Error: Red background, X icon
- Info: Blue background, info icon
- Warning: Amber background, warning icon

**Behavior:**

- Auto-dismiss after 5 seconds
- Manual dismiss button
- Stack multiple toasts
- Slide in from top-right

**Props:**

- `message: string`
- `variant: "success" | "error" | "info" | "warning"`
- `duration?: number` (ms)
- `onDismiss?: () => void`

#### Alert

**Purpose:** Persistent important messages

**Variants:**

- Success/Error/Info/Warning: Same as Toast but persistent
- With action: Includes CTA button

**Props:**

- `title?: string`
- `message: string`
- `variant: "success" | "error" | "info" | "warning"`
- `action?: {label: string, onClick: () => void}`
- `dismissible?: boolean`

#### ErrorBanner

**Purpose:** Page-level errors with remediation

**Structure:**

```
┌─────────────────────────────────────────┐
│ ⚠️ Error Title                           │
│ Error message with context               │
│ [Fix It] [Learn More]                    │
└─────────────────────────────────────────┘
```

**Props:**

- `title: string`
- `message: string`
- `remediation?: {label: string, onClick: () => void}`
- `dismissible?: boolean`

### Loading States

#### LoadingSkeleton

**Purpose:** Placeholder while content loads

**Variants:**

- Text: Animated lines
- Card: Animated card shape
- Image: Animated rectangle
- List: Multiple animated lines

**Props:**

- `variant: "text" | "card" | "image" | "list"`
- `count?: number` (for lists)
- `width?: string`
- `height?: string`

#### ProgressIndicator

**Purpose:** Show progress for long operations

**Variants:**

- Linear: Horizontal bar
- Circular: Spinner with percentage
- Steps: Multi-step progress (e.g., installer)

**Props:**

- `value?: number` (0-100)
- `variant: "linear" | "circular" | "steps"`
- `steps?: Array<{id, label, completed}>`
- `label?: string`

### Empty States

**Purpose:** Guide users when no content exists

**Variants:**

- Characters empty: "Create your first character" with CTA
- Models empty: "No models installed" with install CTA
- ComfyUI not installed: "Install ComfyUI" with setup CTA
- Library empty: "Generate your first image" with CTA

**Structure:**

```
┌─────────────────────────────────────────┐
│         [Illustration/Icon]              │
│         Title                            │
│         Description                      │
│         [Primary Action Button]          │
└─────────────────────────────────────────┘
```

**Props:**

- `icon?: ReactNode`
- `title: string`
- `description: string`
- `action: {label: string, onClick: () => void}`
- `secondaryAction?: {label: string, onClick: () => void}`

### Status Components

#### StatusChip / Badge

**Purpose:** Show status (Healthy, Warning, Offline, etc.)

**Variants:**

- Success: Green background, "Healthy"
- Warning: Amber background, "Warning"
- Error: Red background, "Error" / "Offline"
- Info: Blue background, "Info"

**States:**

- Default: Colored background, white text
- With icon: Icon + text
- Pulsing: Animated pulse for active/warning states

**Props:**

- `status: "success" | "warning" | "error" | "info"`
- `label?: string` (defaults to status name)
- `icon?: ReactNode`
- `pulsing?: boolean`

---

## Motion & Micro-Interactions

### Motion Principles

**Core Philosophy:** "Calm, premium, informative"

- **Purposeful:** Every animation serves a purpose (feedback, guidance, delight)
- **Fast but smooth:** 150-300ms for most interactions
- **Respectful:** Honor `prefers-reduced-motion`
- **Performant:** Use `transform` and `opacity` (GPU-accelerated)

### Allowed Transitions

**Duration Scale:**

```css
--duration-instant: 0ms; /* Immediate (no transition) */
--duration-fast: 150ms; /* Hover, press */
--duration-normal: 200ms; /* Default transitions */
--duration-slow: 300ms; /* Page transitions, modals */
--duration-slower: 500ms; /* Complex animations */
```

**Easing Functions:**

```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.68, -0.55, 0.265, 1.55); /* Bouncy (sparingly) */
```

**Usage Rules:**

- Hover: `--duration-fast`, `--ease-out`
- Press: `--duration-fast`, `--ease-in`
- Page transitions: `--duration-slow`, `--ease-in-out`
- Modals: `--duration-slow`, `--ease-out` (fade + scale)

### Hover Interactions

**Card Hover:**

- Lift: `translateY(-2px)`, `--shadow-lg`
- Duration: `--duration-fast`
- Border color change (subtle)

**Button Hover:**

- Background color change
- Scale: `scale(1.02)` (subtle)
- Duration: `--duration-fast`

**Icon Hover:**

- Scale: `scale(1.1)`
- Color change (if applicable)

### Press Interactions

**Button Press:**

- Scale: `scale(0.98)`
- Duration: `--duration-fast`
- Immediate feedback (no delay)

### Card Shimmer (Loading)

**Purpose:** Indicate loading content

**Implementation:**

- Subtle gradient animation (opacity 0.3 → 0.6)
- Duration: 1.5s, infinite
- Only for skeleton states, not actual content

### Page Transitions

**Framework Support:** Next.js App Router supports page transitions

**Strategy:**

- Fade: `opacity 0 → 1`, `--duration-slow`
- Slide: `translateX(-10px) → 0`, `--duration-slow`
- Combined: Fade + subtle slide

**Implementation:**

- Use Next.js `useTransition` or Framer Motion (if added)
- Fallback: CSS transitions on route change

### Reduced Motion Compliance

**Implementation:**

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**What to Disable:**

- All hover animations
- Page transitions
- Loading spinners (use static indicators)
- Gradient animations

**What to Keep:**

- Essential state changes (color, visibility)
- Progress indicators (but static, not animated)

### Performance Constraints

**GPU Effects:**

- Limit `backdrop-filter` usage (max 2 per page)
- Avoid heavy `box-shadow` on many elements
- Use `will-change` sparingly (only for actively animating elements)

**Low-End Machine Considerations:**

- Detect device performance (optional)
- Reduce animation complexity on low-end devices
- Lazy load heavy assets (images, 3D elements)

---

## Page-by-Page Redesign Plan

### 1. Dashboard (`/`)

**Goal:** System health overview + quick next actions

**Key User Actions:**

- See system status at a glance
- Quick access to Create, Generate, Library
- View recent characters and activity

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header: Logo + Nav]                    │
├─────────────────────────────────────────┤
│ Hero: System Health Status              │
│ [4 Metric Cards: Characters, Posts, etc] │
├─────────────────────────────────────────┤
│ Quick Actions Grid (5 cards)            │
├─────────────────────────────────────────┤
│ Recent Characters (Grid, 8 items)       │
├─────────────────────────────────────────┤
│ System Status (Collapsible)             │
│ - Backend, Frontend, ComfyUI status    │
│ - System info (OS, Python, GPU)         │
└─────────────────────────────────────────┘
```

**Required Components:**

- `AppShell`
- `PageHeader` (optional, or inline title)
- `MetricCard` (4x)
- `SectionCard` (for each section)
- `StatusChip` (for system health)
- `ServiceCard` (custom, for backend/frontend/comfyui)
- `EmptyState` (if no characters)

**States:**

- Loading: Skeleton cards
- Empty: Empty state for characters
- Error: Error banner with retry
- Healthy: Green status indicators
- Warning: Amber status with remediation CTA

**Errors:**

- Backend unreachable → "Backend not running" + "Start Backend" button
- ComfyUI not installed → "Install ComfyUI" + link to Setup
- No characters → Empty state + "Create Character" CTA

### 2. Setup (`/installer`)

**Goal:** One-stop setup, repair, diagnostics hub

**Key User Actions:**

- Install system (one-click)
- Repair broken installation
- Run diagnostics
- View system check results

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ Hero: "Setup AInfluencer"                │
│ [Big Primary Button: Install/Repair]     │
│ Status: [Progress Bar]                   │
├─────────────────────────────────────────┤
│ System Check Results                     │
│ - Python, Tools, GPU, Disk              │
│ - Issues with Fix buttons               │
├─────────────────────────────────────────┤
│ Installation Logs (Collapsible)         │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader`
- `PrimaryButton` (big, prominent)
- `ProgressIndicator` (linear, for install progress)
- `SectionCard` (for system check)
- `StatusChip` (for each check item)
- `Alert` (for issues)
- `ErrorBanner` (for critical errors)
- Log viewer (custom, terminal-style)

**States:**

- Idle: "Start Installation" button
- Running: Progress bar + logs
- Succeeded: "System Ready" success state
- Failed: Error banner + "Retry" button
- Repair needed: "Repair System" button

**Errors:**

- Python version wrong → "Fix Python" button
- Missing tools → "Install Tools" button
- Port conflicts → "Fix Ports" button
- All errors have remediation CTAs

### 3. Characters (`/characters`)

**Goal:** List and manage characters

**Key User Actions:**

- View all characters (grid/table)
- Create new character
- Filter/search
- Quick actions (pause, delete)

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ PageHeader: "Characters" + [Create]     │
│ [Search] [Filter: Status] [View: Grid/Table] │
├─────────────────────────────────────────┤
│ Character Grid (responsive)             │
│ - Card: Image, Name, Status, Actions    │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader`
- `PrimaryButton` (Create)
- `Input` (search)
- `Select` (filter)
- `SectionCard` (character cards)
- `StatusChip` (character status)
- `EmptyState` (no characters)
- `LoadingSkeleton` (loading)

**States:**

- Loading: Skeleton grid
- Empty: Empty state + "Create Character" CTA
- With data: Grid of character cards
- Error: Error banner

**Character Card:**

- Image (or placeholder gradient)
- Name
- Status badge
- Quick actions (Edit, Delete, Pause/Resume)
- Hover: Lift + shadow

### 4. Character Detail (`/characters/[id]`)

**Goal:** View and manage single character

**Key User Actions:**

- View character info
- Edit character
- View associated content
- Manage styles

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ Character Header:                       │
│ [Image] Name, Bio, Status               │
│ [Edit] [Delete]                         │
├─────────────────────────────────────────┤
│ Tabs: Overview | Content | Styles | Activity │
├─────────────────────────────────────────┤
│ Tab Content (dynamic)                   │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader` (with breadcrumbs)
- Tabs component (custom)
- `SectionCard` (for each tab section)
- `PrimaryButton` / `SecondaryButton` (actions)
- Content grid (for content tab)
- Style cards (for styles tab)

**States:**

- Loading: Skeleton
- Error: Error banner
- Empty content: Empty state
- Active: Full character data

### 5. Character Create/Edit (`/characters/create`, `/characters/[id]/edit`)

**Goal:** Create or edit character

**Key User Actions:**

- Fill form (name, bio, image, etc.)
- Save character
- Preview

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ PageHeader: "Create Character"           │
├─────────────────────────────────────────┤
│ Form (2-column on desktop):             │
│ Left: Form fields                        │
│ Right: Preview (optional)                │
├─────────────────────────────────────────┤
│ [Cancel] [Save]                         │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader`
- `FormGroup`
- `Input`, `Textarea`, `Select`
- `PrimaryButton`, `SecondaryButton`
- Image upload component (custom)
- Preview card (optional)

**States:**

- Default: Empty form
- Validating: Loading state on save
- Error: Field-level errors + banner
- Success: Redirect to character detail

**Validation:**

- Real-time validation (on blur)
- Error messages below fields
- Submit disabled until valid

### 6. Generate (`/generate`)

**Goal:** Generate images via ComfyUI

**Key User Actions:**

- Enter prompt
- Select preset (optional)
- Configure settings
- Generate image
- View results

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ PageHeader: "Generate"                  │
├─────────────────────────────────────────┤
│ ComfyUI Status Banner (if not ready)   │
├─────────────────────────────────────────┤
│ Generation Form:                        │
│ - Preset selector                       │
│ - Prompt (textarea)                     │
│ - Negative prompt                       │
│ - Settings (collapsible)               │
│ - [Generate] button                     │
├─────────────────────────────────────────┤
│ Job Status (if generating)              │
│ - Progress indicator                    │
│ - Preview image                         │
├─────────────────────────────────────────┤
│ Gallery (below fold)                    │
│ - Grid of generated images              │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader`
- `Alert` (ComfyUI status)
- `Select` (preset, checkpoint, sampler)
- `Textarea` (prompt)
- `Input` (negative prompt, settings)
- `PrimaryButton` (Generate)
- `ProgressIndicator` (job status)
- `SectionCard` (gallery)
- `EmptyState` (no images)

**States:**

- ComfyUI not ready: Alert with setup CTA
- Ready: Full form
- Generating: Progress + preview
- Success: Image in gallery
- Error: Error banner + retry

**ComfyUI Gating:**

- If not installed: "Install ComfyUI" → Setup page
- If not running: "Start ComfyUI" button
- If ready: Show form

### 7. Library (`/content` - **NEW PAGE TO CREATE**)

**Goal:** Unified content library (images + videos)

**Key User Actions:**

- Browse generated content
- Filter by type, date, character
- Export/download
- Delete content

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ PageHeader: "Library"                   │
│ [Filter: Type, Date, Character]        │
│ [Sort: Newest/Oldest]                   │
├─────────────────────────────────────────┤
│ Content Grid (masonry or uniform)       │
│ - Image/Video thumbnails               │
│ - Hover: Actions (Download, Delete)    │
├─────────────────────────────────────────┤
│ [Load More] or Infinite scroll         │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader`
- `Select` (filters)
- `SectionCard` (content grid)
- `EmptyState` (no content)
- Image/Video thumbnail component (custom)
- `IconButton` (actions)

**States:**

- Loading: Skeleton grid
- Empty: Empty state + "Generate Content" CTA
- With data: Grid of content
- Filtered: Filtered results

**Note:** Merge `/videos` into this page. Redirect old route.

### 8. Models (`/models`)

**Goal:** Manage AI models (catalog, queue, installed)

**Key User Actions:**

- Browse model catalog
- Install models
- View installed models
- Manage download queue

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ PageHeader: "Models"                     │
│ Tabs: Catalog | Installed | Queue       │
├─────────────────────────────────────────┤
│ Tab Content:                             │
│ - Catalog: Searchable grid              │
│ - Installed: List with actions          │
│ - Queue: Download progress              │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader`
- Tabs component
- `SectionCard`
- `PrimaryButton` (Install)
- `ProgressIndicator` (downloads)
- `EmptyState` (no models)

**States:**

- Loading: Skeleton
- Empty: Empty state
- Installing: Progress indicator
- Installed: List of models

### 9. ComfyUI Manager (`/comfyui`)

**Goal:** Manage ComfyUI installation and status

**Key User Actions:**

- Install ComfyUI
- Start/Stop ComfyUI
- View logs
- Configure settings

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ PageHeader: "ComfyUI Manager"           │
├─────────────────────────────────────────┤
│ Status Card:                            │
│ - Installation status                   │
│ - Running status                        │
│ - Port, URL                            │
│ [Install] [Start] [Stop] [Restart]      │
├─────────────────────────────────────────┤
│ Logs (Collapsible)                      │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader`
- `SectionCard`
- `StatusChip`
- `PrimaryButton`, `SecondaryButton`
- Log viewer

**States:**

- Not installed: "Install" button
- Installed but stopped: "Start" button
- Running: "Stop" button + status
- Error: Error banner + remediation

**Note:** This could also live inside Setup page as a section, but keeping separate for Advanced users.

### 10. Analytics (`/analytics`)

**Goal:** View performance metrics

**Key User Actions:**

- View overview metrics
- Filter by character, platform, date
- View trends and charts

**Layout:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ PageHeader: "Analytics"                 │
│ [Filters: Character, Platform, Date]    │
├─────────────────────────────────────────┤
│ Metric Cards (4-6)                      │
├─────────────────────────────────────────┤
│ Charts Section:                         │
│ - Engagement trends                     │
│ - Platform breakdown                   │
│ - Top performing posts                  │
└─────────────────────────────────────────┘
```

**Required Components:**

- `PageHeader`
- `MetricCard`
- `SectionCard`
- Chart components (use a charting library)
- `Select` (filters)
- `EmptyState` (no data)

**States:**

- Loading: Skeleton
- No data: "Not configured" message (graceful degradation)
- With data: Full analytics dashboard
- Error: Error banner

**Graceful Degradation:**

- If analytics not configured: Show "Analytics not set up" message + link to setup
- Don't show broken charts or errors

### Error/404 Handling

**404 Page:**

```
┌─────────────────────────────────────────┐
│ [Header]                                 │
├─────────────────────────────────────────┤
│ [Illustration: 404]                     │
│ "Page not found"                         │
│ "The page you're looking for doesn't exist." │
│ [Go to Dashboard]                        │
│ [Report broken link] (optional)         │
└─────────────────────────────────────────┘
```

**Route Policy:**

- Remove links to `/workflows` and `/settings` until implemented
- Redirect `/videos` → `/content`
- All other routes: Show 404 with helpful message

---

## Remove / Merge / Hide List (Scope Control)

### Remove (Delete or Hide Links)

1. **`/workflows`**

   - **Action:** Remove from Advanced nav
   - **Reason:** Page doesn't exist, feature not implemented
   - **Future:** Implement later or remove permanently

2. **`/settings`**

   - **Action:** Remove from Advanced nav
   - **Reason:** Page doesn't exist
   - **Future:** Implement later (could merge into Setup)

3. **Duplicate Navigation Items**
   - **Action:** Consolidate into single nav model
   - **Current:** Some pages have their own nav links
   - **Fix:** Use AppShell navigation only

### Merge

1. **`/videos` → `/content`**

   - **Action:** Merge videos into unified Library page
   - **Implementation:** Create `/content` page, redirect `/videos` → `/content`
   - **UX:** Single place for all generated content

2. **ComfyUI Manager into Setup (Optional)**
   - **Action:** Consider moving ComfyUI management into Setup page
   - **Alternative:** Keep separate for Advanced users
   - **Decision:** Keep separate (Advanced users need quick access)

### Hide Behind Advanced

1. **Models** (`/models`)

   - **Status:** Already in Advanced nav ✅
   - **Action:** Keep there

2. **Analytics** (`/analytics`)

   - **Status:** Already in Advanced nav ✅
   - **Action:** Keep there, but ensure graceful degradation

3. **ComfyUI Manager** (`/comfyui`)
   - **Status:** Already in Advanced nav ✅
   - **Action:** Keep there

### Move to Setup

1. **System Diagnostics**

   - **Current:** Partially in Dashboard
   - **Action:** Move detailed diagnostics to Setup page
   - **Keep in Dashboard:** High-level status only

2. **Repair Functions**
   - **Current:** In Setup ✅
   - **Action:** Keep there, ensure prominent

### Feature Flags / "Coming Soon"

1. **Workflows**

   - **Action:** If keeping for future, show "Coming Soon" placeholder
   - **UX:** Don't show broken 404, show helpful message

2. **Marketplace**
   - **Status:** Page exists but may be incomplete
   - **Action:** If incomplete, hide from nav or show "Beta" badge
   - **Future:** Complete or remove

### Reduce Clutter

1. **Dashboard Quick Actions**

   - **Current:** 5 quick action cards
   - **Action:** Keep but make more compact
   - **Alternative:** Move to sidebar or reduce to 3-4

2. **Character Detail Tabs**

   - **Current:** Overview, Content, Styles, Activity
   - **Action:** Keep all (each serves purpose)
   - **Optimization:** Lazy load tab content

3. **Generate Page Settings**
   - **Current:** Many advanced settings visible
   - **Action:** Collapse advanced settings by default
   - **UX:** "Advanced Settings" toggle

---

## Free Assets Strategy

### Icon Library

**Primary Choice: Lucide Icons** (or similar free icon set)

**Rationale:**

- MIT License (permissive)
- Large icon set (1000+ icons)
- Consistent style
- SVG format (scalable, customizable)
- No attribution required (but nice to credit)

**Alternative Options:**

- Heroicons (MIT)
- Feather Icons (MIT)
- Tabler Icons (MIT)

**Usage Rules:**

- Use consistent stroke width (1.5px or 2px)
- Consistent size scale (see Icon Sizing Rules)
- Color via CSS (inherit or custom)
- No mixing icon sets (pick one and stick with it)

**Implementation:**

- Install via npm: `lucide-react` or similar
- Import icons as React components
- Or use SVG sprite sheet

### Background Textures / Gradient Meshes

**Strategy:**

- Generate programmatically (CSS gradients)
- Use subtle mesh gradients (opacity < 0.03)
- No external image dependencies

**Example:**

```css
.hero-background {
  background: radial-gradient(
      circle at 20% 50%,
      rgba(99, 102, 241, 0.1),
      transparent 50%
    ), radial-gradient(
      circle at 80% 80%,
      rgba(139, 92, 246, 0.1),
      transparent 50%
    ), var(--bg-base);
}
```

**Rules:**

- Max 2-3 gradient layers
- Opacity < 0.1
- Use brand colors (indigo, purple)
- Disable on reduced motion

### 2D/3D Decorative Assets

**Strategy:**

- Use sparingly (hero sections only)
- Generate with CSS/SVG (no external files)
- Or use free SVG illustrations (with proper license)

**Free SVG Illustration Sources:**

- unDraw.co (MIT)
- Open Peeps (CC0)
- Blush (various licenses, check per asset)

**Style Constraints:**

- Match brand colors
- Minimal, abstract shapes
- No complex illustrations (keep it simple)
- Use as background elements, not focal points

**Usage:**

- Hero sections: Subtle background shapes
- Empty states: Simple illustrations
- Loading states: Animated shapes (optional)

### Licensing Checklist

**Before Adding Any Asset:**

1. ✅ **License Type:**

   - MIT, Apache 2.0, CC0, CC-BY (with attribution) = ✅ OK
   - CC-BY-NC (non-commercial) = ❌ NO (commercial use)
   - Proprietary = ❌ NO

2. ✅ **Attribution Required:**

   - If yes, add to footer or credits page
   - Keep attribution minimal but visible

3. ✅ **Usage Rights:**

   - Commercial use allowed? ✅
   - Modification allowed? ✅ (preferred)
   - Redistribution allowed? ✅

4. ✅ **Documentation:**
   - Document source and license in `ASSETS_LICENSE.md` (optional)
   - Keep list of all external assets

**Recommended Approach:**

- Prefer programmatically generated assets (CSS, SVG)
- Use icon libraries with permissive licenses
- Avoid external image dependencies when possible
- When needed, use free illustration sites with clear licensing

---

## Accessibility & UX Quality Bar

### Contrast Requirements

**WCAG AA Compliance (Minimum):**

- Normal text: 4.5:1 contrast ratio
- Large text (18px+): 3:1 contrast ratio
- UI components: 3:1 contrast ratio

**WCAG AAA (Target):**

- Normal text: 7:1 contrast ratio
- Large text: 4.5:1 contrast ratio

**Testing:**

- Use browser DevTools contrast checker
- Test all text on all background colors
- Test in both dark and light modes

### Focus States

**Requirements:**

- All interactive elements must have visible focus indicators
- Focus ring: 2px solid `--border-focus` (indigo)
- Offset: `outline-offset: 2px`
- Never remove focus styles (accessibility requirement)

**Implementation:**

```css
:focus-visible {
  outline: 2px solid var(--border-focus);
  outline-offset: 2px;
  border-radius: var(--radius-md);
}
```

### Keyboard Navigation

**Requirements:**

- All interactive elements keyboard accessible
- Tab order: Logical, top-to-bottom, left-to-right
- Skip links: "Skip to main content" link (optional but recommended)
- Keyboard shortcuts: Document common shortcuts (⌘R refresh, etc.)

**Testing:**

- Navigate entire app using only keyboard
- Test modals, dropdowns, tabs
- Ensure no keyboard traps

### Form Validation

**Copy Style:**

- **Error messages:** Short, actionable, specific

  - ❌ Bad: "Error"
  - ✅ Good: "Name is required"
  - ✅ Better: "Please enter a character name"

- **Helper text:** Contextual, helpful

  - ✅ Good: "Choose a unique name for your character"

- **Success feedback:** Positive, clear
  - ✅ Good: "Character created successfully"

**Validation Timing:**

- Real-time: On blur (after user leaves field)
- On submit: Show all errors at once
- Never: On every keystroke (too aggressive)

### Error Copy Rubric

**Template:**

```
[Title: What went wrong]
[Message: Brief explanation]
[Remediation: What to do next]
[CTA: Action button]
```

**Examples:**

1. **ComfyUI Not Installed:**

   - Title: "ComfyUI Not Installed"
   - Message: "ComfyUI is required to generate images."
   - Remediation: "Install ComfyUI to continue."
   - CTA: "Install ComfyUI" → Setup page

2. **Backend Unreachable:**

   - Title: "Backend Service Unavailable"
   - Message: "Unable to connect to the backend service."
   - Remediation: "Check if the backend is running and try again."
   - CTA: "Retry" or "View Logs"

3. **Character Creation Failed:**
   - Title: "Failed to Create Character"
   - Message: "An error occurred while creating the character."
   - Remediation: "Please check your input and try again."
   - CTA: "Try Again"

**Rules:**

- Never blame the user
- Always provide next steps
- Use plain language (no technical jargon for non-technical users)
- Include remediation CTA when possible

### Consistency Rules

**Error States:**

- Every error must have a remediation CTA (when possible)
- Use consistent error styling (red border, error icon)
- Show errors in context (field-level + page-level)

**Empty States:**

- Every empty state must have a primary CTA
- Use consistent empty state design
- Include helpful description

**Loading States:**

- Use skeletons, not spinners (where possible)
- Show progress for long operations
- Never show infinite loading without feedback

**Success States:**

- Show success feedback (toast or inline)
- Redirect or update UI immediately
- Clear form after successful submission

---

## Implementation Readiness

### Implementation Phases

#### Phase 1: Design System Foundation

**Duration:** 1-2 weeks

**Tasks:**

- [ ] Set up design tokens (CSS variables)
- [ ] Implement color system (dark + light mode)
- [ ] Set up typography scale
- [ ] Create spacing/radius/shadow tokens
- [ ] Set up icon library (Lucide or similar)
- [ ] Create base component styles (buttons, inputs, etc.)

**Deliverables:**

- Design tokens file (`globals.css` or `tokens.css`)
- Base component library (styling only, no logic)
- Style guide documentation

#### Phase 2: Core Components

**Duration:** 2-3 weeks

**Tasks:**

- [ ] Build AppShell (navigation, header)
- [ ] Build PageHeader component
- [ ] Build SectionCard component
- [ ] Build MetricCard component
- [ ] Build all Button variants
- [ ] Build Form components (Input, Textarea, Select)
- [ ] Build Feedback components (Toast, Alert, ErrorBanner)
- [ ] Build Loading states (Skeleton, Progress)
- [ ] Build Empty states component
- [ ] Build StatusChip component

**Deliverables:**

- Component library in `/components/ui/`
- Storybook or component documentation (optional)
- All components with all states (hover, active, disabled, loading, error)

#### Phase 3: Core Pages

**Duration:** 3-4 weeks

**Tasks:**

- [ ] Redesign Dashboard (`/`)
- [ ] Redesign Setup (`/installer`)
- [ ] Redesign Characters list (`/characters`)
- [ ] Redesign Character detail (`/characters/[id]`)
- [ ] Redesign Character create/edit (`/characters/create`, `/characters/[id]/edit`)
- [ ] Redesign Generate (`/generate`)

**Deliverables:**

- All core pages redesigned
- Navigation working
- All states handled (loading, error, empty)
- Responsive design (mobile, tablet, desktop)

#### Phase 4: Advanced Pages

**Duration:** 2-3 weeks

**Tasks:**

- [ ] Create Library page (`/content`) - merge videos
- [ ] Redesign Models (`/models`)
- [ ] Redesign ComfyUI Manager (`/comfyui`)
- [ ] Redesign Analytics (`/analytics`) - with graceful degradation
- [ ] Create 404 page

**Deliverables:**

- All advanced pages complete
- Library page unified (images + videos)
- Redirects in place (`/videos` → `/content`)

#### Phase 5: Polish & Motion

**Duration:** 1-2 weeks

**Tasks:**

- [ ] Add micro-interactions (hover, press)
- [ ] Add page transitions
- [ ] Add loading animations
- [ ] Test reduced motion compliance
- [ ] Performance optimization
- [ ] Accessibility audit

**Deliverables:**

- Smooth animations throughout
- Reduced motion support
- Performance benchmarks met
- Accessibility compliance verified

#### Phase 6: Cleanup & Documentation

**Duration:** 1 week

**Tasks:**

- [ ] Remove dead routes/links (`/workflows`, `/settings` from nav)
- [ ] Update all internal links
- [ ] Test all navigation paths
- [ ] Document component usage
- [ ] Create style guide (optional)

**Deliverables:**

- Clean codebase (no 404 nav links)
- All routes working
- Documentation complete

### Definition of Done for UI Work

**For Each Component:**

- [ ] All variants implemented
- [ ] All states implemented (default, hover, active, disabled, loading, error)
- [ ] Keyboard accessible
- [ ] Focus states visible
- [ ] Responsive (mobile, tablet, desktop)
- [ ] Dark mode + light mode support
- [ ] Reduced motion support
- [ ] WCAG AA contrast compliance
- [ ] No console errors
- [ ] TypeScript types defined

**For Each Page:**

- [ ] All user flows working
- [ ] Loading states implemented
- [ ] Error states implemented (with remediation CTAs)
- [ ] Empty states implemented (with CTAs)
- [ ] Responsive design
- [ ] No 404 links
- [ ] Navigation working
- [ ] Forms validated
- [ ] Success feedback implemented

**For Overall Redesign:**

- [ ] All pages redesigned
- [ ] Navigation consistent
- [ ] No broken routes
- [ ] Performance acceptable (< 3s initial load)
- [ ] Accessibility audit passed
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)
- [ ] Mobile tested (iOS, Android)

### Smoke Test UX Checklist

**After Redesign Completion:**

**Navigation:**

- [ ] All nav links work (no 404s)
- [ ] Breadcrumbs work (where applicable)
- [ ] Advanced dropdown works
- [ ] Mobile menu works

**Content:**

- [ ] All text readable (contrast OK)
- [ ] All images load
- [ ] All icons display
- [ ] No broken images/icons

**Interactions:**

- [ ] All buttons work
- [ ] All forms submit
- [ ] All links navigate correctly
- [ ] All modals open/close
- [ ] All dropdowns work

**States:**

- [ ] Loading states show (no blank screens)
- [ ] Error states show remediation CTAs
- [ ] Empty states show CTAs
- [ ] Success feedback appears

**Responsive:**

- [ ] Mobile layout works (< 640px)
- [ ] Tablet layout works (640px - 1024px)
- [ ] Desktop layout works (> 1024px)
- [ ] No horizontal scroll on mobile

**Accessibility:**

- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Screen reader friendly (test with NVDA/JAWS)
- [ ] Contrast ratios pass

**Performance:**

- [ ] Initial load < 3 seconds
- [ ] Page transitions smooth
- [ ] No janky animations
- [ ] Images lazy load

**Browser Compatibility:**

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

---

## Appendix: Repository Facts

### Framework & Styling (Verified)

- **Framework:** Next.js 16.0.10 (App Router)
- **React:** 19.2.1
- **Styling:** Tailwind CSS v4
- **TypeScript:** Yes
- **Fonts:** Geist Sans, Geist Mono (Google Fonts)

### Existing Routes (Verified)

- ✅ `/` - Dashboard
- ✅ `/installer` - Setup
- ✅ `/characters` - Character list
- ✅ `/characters/create` - Create character
- ✅ `/characters/[id]` - Character detail
- ✅ `/characters/[id]/edit` - Edit character
- ✅ `/generate` - Generate images
- ✅ `/models` - Models management
- ✅ `/analytics` - Analytics
- ✅ `/comfyui` - ComfyUI management
- ✅ `/marketplace` - Marketplace (exists, completeness unknown)
- ✅ `/videos` - Videos (exists, should merge into Library)

### Missing Routes (404 Risk)

- ❌ `/content` - Referenced as "Library" in nav, but no page exists
- ❌ `/workflows` - Referenced in Advanced nav, but no page exists
- ❌ `/settings` - Referenced in Advanced nav, but no page exists

### Current Navigation Structure

**Main Nav (MainNavigation.tsx):**

- Setup (`/installer`)
- Create (`/characters`)
- Generate (`/generate`)
- Library (`/content` - **404**)

**Advanced Nav:**

- Models (`/models`)
- Analytics (`/analytics`)
- Workflows (`/workflows` - **404**)
- ComfyUI (`/comfyui`)
- Settings (`/settings` - **404**)

### Assumptions Made

1. **Next.js App Router:** Using file-based routing (verified)
2. **Tailwind CSS v4:** Using latest Tailwind (verified)
3. **No UI Library:** No existing component library (verified - only custom components)
4. **Dark Mode Default:** Current design uses dark colors (assumed, to be confirmed)
5. **Geist Fonts:** Already loaded, continue using (verified)

---

## Document Status

**Status:** ✅ Complete - Ready for Implementation

**Next Steps:**

1. Review this document with team
2. Prioritize implementation phases
3. Begin Phase 1: Design System Foundation
4. Create component library
5. Redesign pages incrementally

**Questions/Clarifications:**

- Confirm dark mode as default
- Confirm icon library choice (Lucide recommended)
- Confirm timeline and resources
- Confirm any feature scope changes

---

**End of Document**

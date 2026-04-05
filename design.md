# Design Direction — JobReach Dashboard

## Vibe
Dark-mode tech dashboard. Inspired by the reference image's editorial boldness and deep green palette — translated into a dark-background SaaS dashboard. Clean, high-density, professional. Confident and direct — not flashy.

## Colors
- Background: `#0a0f0a` (near-black with green tint)
- Surface/Card: `#111a11` (dark forest)
- Surface Elevated: `#162016` (slightly lifted cards)
- Border: `#1e2e1e` (subtle dark green border)
- Primary Accent: `#22c55e` (bright green — actions, CTAs, status indicators)
- Accent Muted: `#16a34a` (hover states)
- Text Primary: `#f0faf0` (near-white with green tint)
- Text Secondary: `#6b9b6b` (muted green-grey)
- Text Tertiary: `#3d6b3d` (very muted)
- Status — Generated: `#3b82f6` (blue)
- Status — Sent: `#f59e0b` (amber)
- Status — Replied: `#22c55e` (green)
- Status — No Reply: `#ef4444` (red)
- Status — Interview: `#a855f7` (purple)
- Status — Filtered: `#374151` (grey)

## Typography
- Display/Headings: `Syne` (bold, geometric) — Google Fonts
- Body: `DM Sans` (clean, readable) — Google Fonts
- Mono/Data: `JetBrains Mono` — for job IDs, timestamps, code

## Layout
- Full-width dark sidebar (260px) + main content area
- Sidebar: logo at top, nav items, pipeline status indicator at bottom
- Main: sticky top bar with run trigger button + breadcrumb
- Cards with thin green border, subtle inner glow on hover
- Data tables: compact rows, alternating row shade
- No rounded overload — use `rounded-lg` for cards, `rounded-md` for badges

## Motion
- Page load: staggered fade-in (opacity 0→1, translateY 8px→0)
- Status badge transitions
- Table row hover: slight bg shift

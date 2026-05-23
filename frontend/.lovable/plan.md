# Accessible Medical Facilitation App — Core Slice

Stack: TanStack Start (template default), TypeScript, Tailwind v4, shadcn/ui, Lucide icons, mock data. React Router v6 not used — TanStack Router covers routing the same way.

## Scope (this iteration)

Core slice of 4 pages + shared shell:
1. Dashboard (`/`)
2. Medications (`/medications`)
3. How I Feel Today (`/how-i-feel`)
4. Emergency confirmation (`/emergency`)

Plus the shared shell: bottom nav (mobile) / sidebar (tablet+), persistent floating CALL FOR HELP button, top greeting bar. The remaining 3 pages (Profile/History, Caregiver view, Calendar/Home visits) will be stubbed as routes with "Coming next" placeholders so the bottom nav is fully wired and navigable — we'll fill them in the next pass.

## Design system

Implemented in `src/styles.css` as semantic tokens (oklch):
- `--background` warm light grey `#F5F4F2`
- `--primary` deep teal `#1A6B6B`
- `--accent` warm amber `#D4860A`
- `--destructive` emergency red `#C0392B` (reserved for emergency only — enforced by convention; status/feedback uses teal/amber/blue)
- Radii: 16–24px cards, 999px buttons
- Fonts: Fraunces (headings) + Atkinson Hyperlegible (body/UI), loaded via Google Fonts in `__root.tsx` head
- Base body 18px, key actions 24px+, min touch target 56×56 enforced via a `min-h-14 min-w-14` utility pattern on shadcn Button variants

A custom `accessible` Button variant (size `xl`, rounded-full, 18–20px label, focus-visible ring 4px amber) and `Tile` card component for dashboard quick actions (icon + label, ≥120px tall).

## Files to create

```
src/routes/
  __root.tsx                 (edit: add fonts, providers, <main>, shell with bottom nav + floating emergency FAB)
  index.tsx                  (Dashboard)
  medications.tsx
  how-i-feel.tsx
  emergency.tsx
  profile.tsx                (stub)
  caregiver.tsx              (stub)
  calendar.tsx               (stub)
src/components/
  layout/AppShell.tsx        (bottom nav, sidebar at md+, top greeting bar)
  layout/EmergencyFab.tsx    (persistent, 1-tap to /emergency, aria-label)
  ui/Tile.tsx                (large icon+label quick-action tile)
  ui/AlertBanner.tsx
  meds/MedicationCard.tsx
  feel/SymptomPicker.tsx
  feel/PainSlider.tsx        (1–10 with emoji anchors, paired numeric label)
src/data/mock.ts             (1 patient, 3 meds, 4 appts, 2 caregivers, 5 notifications)
src/lib/patient-context.tsx  (React Context for current patient + "I took this" handlers)
src/styles.css               (edit: tokens, fonts, focus ring, AAA contrast)
```

## Accessibility rules baked in

- Single `<main>` in `__root.tsx`, wrapping `<Outlet />`
- All icon-only buttons have `aria-label`
- Status indicators always pair icon + label (never color-only); color-blind-safe palette (teal/amber/blue) for non-emergency
- Focus-visible: 4px amber ring, 2px offset, on every interactive element
- Min tap target 56×56 on all actionable controls
- Plain-language confirmation step before destructive actions (emergency screen has explicit Confirm/Cancel, both ≥64px)
- Bottom nav 64px, 5 tabs (icon + short label), always visible on mobile; collapses to left sidebar at `md`
- `lang="en"` already on `<html>`; uses `h-dvh` not `h-screen`
- Reduced-motion respected via Tailwind `motion-reduce:` on any transitions

## Data

`src/data/mock.ts` exports typed mocks: `patient`, `medications[3]`, `appointments[4]`, `caregivers[2]`, `notifications[5]`. Context provides `markMedicationTaken(id)` updating in-memory state.

No Django wiring this iteration — when ready, we swap `src/data/mock.ts` for a typed `src/lib/api.ts` (fetch wrapper hitting DRF base URL) without touching components.

## Out of scope (next iteration)

- Profile & Medical History full build
- Caregiver Dashboard full build
- Calendar + Home Visit request form
- Notification center page (banner on dashboard only for now)
- DRF API client, auth, real persistence

## Verification

- Manual viewport check at 375 / 768 / 1280
- Confirm CALL FOR HELP reachable in ≤1 tap from every route (FAB)
- Confirm no color-only status indicators
- Build passes

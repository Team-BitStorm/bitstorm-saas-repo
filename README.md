Project Structure
bitstorm-saas-repo/
├── backend/          # Django API (accounts, core, marketplace)
│   ├── accounts/     # Auth, 2FA, CNP utilities
│   ├── core/         # Models, booking/slot services, marketplace views
│   └── db/           # CSV seed data (Romanian demo dataset)
├── frontend/         # React SPA (patient companion + auth pages)
├── REQUIREMENTS.md   # Full product & architecture design doc
└── README.md
Security & Privacy Highlights
CNP never returned in API responses — encrypted at rest, hashed for lookup
Domicile isolation — owner_user on geo rows; visit addresses only via booking APIs
Role-based permissions — Separate customer vs provider API namespaces
Transactional bookings — Atomic slot reservation to prevent double-booking
HTTPS + CORS — Configured for Render production origins
Roadmap
Phase 1 — Provider MVP
Wire frontend auth into app shell
Provider onboarding, pricing, availability calendar UI
End-to-end provider schedule management
Phase 2 — Customer marketplace
Provider discovery + slot picker UI
Booking confirmation and history
Post-visit review flows
Future
Real SMS/notifications
Provider credential verification
Payment gateway integration
Decide whether companion features (meds, emergency) merge into BitHealth or ship separately
License
MIT — Copyright (c) 2026 Team-BitStorm

Team & Context
Item	Detail
Event
Cluj hackathon 2026
Team
Team BitStorm
Product names in repo
BitHealth (product), CarePath (frontend package name)
Design doc
See REQUIREMENTS.md for full API contracts and phased backlog
Summary
BitHealth targets a gap most healthcare platforms ignore: finding and booking qualified providers who travel to the patient’s home, with Romanian identity support, strict address privacy, and an accessibility-first interface for older users. The backend already implements the full marketplace logic (discovery → booking → invoice → review); the frontend today is a polished patient companion prototype that is being extended toward the marketplace vision described in REQUIREMENTS.md.

If you want, I can paste this directly into README.md or trim it to a shorter GitHub “About” blurb (~120 words).

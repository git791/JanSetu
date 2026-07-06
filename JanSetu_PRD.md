# JanSetu — AI Constituency Intelligence Platform
### Product Requirements Document (PRD)

**Tagline:** *People's Priorities, Proven by Data.*
**Author:** Mohammed Ayaan Adil Ahmed
**Hackathon:** Code for Communities (hack2skill)
**Track:** People's Priorities — AI for Constituency Development Planning
**Version:** 1.0 (MVP Build)

---

## 1. Problem Statement

Every day, an MP's office receives development requests through public meetings ("*durbars*"), handwritten letters, WhatsApp forwards, social media tags, and grievance portals like CPGRAMS. Meanwhile, the local development plan already lists dozens of competing proposed works — road upgrades, school renovations, drainage, vocational centres.

Today this reconciliation is done manually, by memory and political instinct. There is no objective way to:
- Consolidate scattered, multilingual citizen feedback into real, de-duplicated demand signals
- Tell whether 40 letters about "the school" are 40 people or 4 people writing 10 times
- Weigh a request for a school upgrade against actual enrollment, seat shortage, and travel distance — versus a competing proposal like a new vocational centre
- Prove, transparently, *why* one project was funded over another

Existing systems (CPGRAMS, MP citizen portals, e.g. the Punjab RS MP's AI portal launched Jan 2026) digitize **complaint intake and tracking**. None of them **fuse citizen demand with objective public data to produce a ranked, explainable investment plan**. That gap is what JanSetu closes.

## 2. Vision

JanSetu turns an MP's inbox into an **evidence-based capital allocation engine**. Citizens speak in their own language, through channels they already use (WhatsApp, phone call, photo). The AI does the unglamorous work — transcribing, translating, deduplicating, geotagging, and checking every claim against real government datasets — so the MP's office sees a clean, ranked, *explainable* shortlist instead of a pile of paper.

**What makes this different from every grievance portal that exists today:**

| Existing systems (CPGRAMS, MP portals, CIVIC) | JanSetu |
|---|---|
| Log and track individual complaints | Clusters thousands of individual voices into de-duplicated "Need Clusters" |
| No cross-check against real-world data | Every cluster is scored against enrollment (UDISE+), census/SECC, travel-distance (Google Maps isochrones), satellite land-use (Earth Engine), and the existing development plan |
| Ranking, if any, is manual/political | Ranking is a transparent, published, re-computable formula — a "glass-box," not a black-box score |
| Closed loop — citizen never learns why a request wasn't funded | Every citizen who raised an issue gets a WhatsApp update when their cluster is scored, funded, or deferred — with the reason |
| Single-channel or single-language | Voice call (IVR), WhatsApp, photo, web/app — 10+ Indic languages, normalized centrally |

## 3. Target Users

1. **Citizens** — urban and rural, varying literacy, feature-phone to smartphone. Primary channel: voice/WhatsApp in their own language.
2. **MP & Constituency Office Staff** — need a ranked, explainable shortlist, not a raw complaint dump.
3. **District Administration / Line Departments** (PWD, Education, Health) — receive verified, geotagged, data-backed project briefs instead of vague requests.
4. **Public / Civil Society** — transparency dashboard showing what was proposed, how it ranked, and what happened to it.

## 4. Goals & Success Metrics (Hackathon MVP + Vision)

| Goal | Metric |
|---|---|
| Reduce time to consolidate constituency demand | From weeks of manual sorting → minutes, continuously updated |
| Increase objectivity of prioritization | 100% of ranked projects carry a visible, sourced evidence trail |
| Increase citizen trust | % of submitters who receive a status update within 14 days |
| Reduce duplicate/inflated demand signals | De-duplication reduces raw submission volume by an estimated 60–80% into true unique need clusters |
| Multilingual reach | Support for Hindi, English + 8 major Indic languages at MVP; extensible via Cloud Translation |

## 5. Core Features

### 5.1 Multichannel Multimodal Intake
- **WhatsApp Business integration** — citizens send text, voice notes, or photos of a broken road/school/handwritten letter.
- **IVR voice line** — feature-phone users record a complaint by speaking; Speech-to-Text (Indic language models) transcribes and translates automatically.
- **Web/PWA + mobile** — form-based submission with camera and geolocation capture, works on low bandwidth.
- **Public meeting digitization** — MP's staff can bulk-upload photos of handwritten *durbar* petitions; Gemini's multimodal OCR extracts structured requests.

### 5.2 Semantic Deduplication & Clustering Engine
- Every submission is embedded (Vertex AI embeddings) and geotagged.
- Near-duplicate and thematically-similar submissions (e.g., "school building leaking," "roof collapse risk at govt school") are merged into a single **Need Cluster**, with a live count of unique citizens behind it and an authenticity/spam score.
- Prevents both accidental undercounting (same issue, different words) and manipulation (bot/astroturf inflation).

### 5.3 Evidence Fusion Engine
For every Need Cluster, the system automatically pulls in relevant public and administrative data:
- **UDISE+ / school data** — enrollment, seats, teacher ratio, building condition
- **Census / SECC** — population, literacy, vulnerability indices for that ward
- **Google Maps Platform** — real travel-time/distance from settlements to nearest facility (isochrone analysis), not straight-line distance
- **Earth Engine satellite imagery** — verifies land status (e.g., is a proposed vocational-centre plot actually vacant, encroached, or flood-prone)
- **Existing local development plan** — flags overlap/duplication with already-sanctioned works
- **Cost benchmarks** — historical per-unit cost data for similar public works

### 5.4 Explainable Priority Score ("Glass-Box Ranking")
Each Need Cluster receives a composite, fully auditable score:

```
Priority Score =  w1·(Demand Intensity)  +  w2·(Objective Need Gap)
                +  w3·(Vulnerability Weight)  +  w4·(Feasibility / Cost-per-Beneficiary)
                −  w5·(Existing Plan Overlap Penalty)
```

Every factor is clickable — the MP's office can see exactly which data source produced which number, and adjust weights transparently (e.g., "weight vulnerability higher this quarter"). This directly answers the brief's example: comparing a school-upgrade cluster (high demand + real seat shortfall + long walk distance) against a proposed vocational centre (lower demand density, unclear land status) on the same objective scale.

### 5.5 Digital Twin Constituency Map
Interactive map with toggleable layers: demand heatmap, school/health/road infrastructure gaps, vulnerability index, satellite land-use — so the MP's office can visually spot hotspots, not just read a table.

### 5.6 Budget Simulation ("What-If Planner")
MP's staff can simulate: "If we fund Projects A + C this quarter, how many citizens/beneficiaries does that reach, and what's the score-weighted impact vs. funding B + D?" — turning prioritization into a plannable, defensible decision.

### 5.7 Transparency Ledger & Closed-Loop Feedback
- Public-facing (privacy-respecting) dashboard of all Need Clusters, their score, and status (Received → Under Review → Approved → In Progress → Completed).
- Every citizen who contributed to a cluster is notified via WhatsApp/SMS at each status change — closing the loop that CPGRAMS-style systems leave open.

### 5.8 Anti-Manipulation & Trust Safeguards
- Phone-number OTP verification per submission; duplicate-device/burst-submission detection.
- Authenticity scoring flags coordinated/bot-like submission spikes for human review before they affect ranking.
- Every AI-generated score is explainable and overridable by a human — AI recommends, MP's office decides.

## 6. User Stories

- *As a citizen*, I can call a toll-free number and describe my issue in Telugu; I get an SMS confirming it was logged and later, that it was acted on.
- *As an MP's aide*, I can open a dashboard each morning and see the top 10 ranked constituency needs, each with a one-paragraph evidence brief, instead of sorting through 500 messages.
- *As a district education officer*, I receive a ready-made brief: "Ward 12 school needs 3 new classrooms — enrollment exceeds capacity by 40%, nearest alternate school is 6.2 km away, 214 unique citizen requests over 90 days."
- *As a citizen who submitted a request*, I get a WhatsApp message when my cluster changes status, so I know I was heard.

## 7. Non-Functional Requirements

- **Multilingual-first**, not multilingual-added-on: all NLP pipelines run language detection → translation → canonical English processing → response back in source language.
- **Low-bandwidth & low-literacy friendly**: voice-first flows, WhatsApp (near-universal in India), no app-install requirement for base functionality.
- **Data privacy**: compliant with India's Digital Personal Data Protection (DPDP) Act 2023 — explicit consent capture, data minimization, right to erasure, PII encryption at rest.
- **Auditability**: every score must be reconstructable and explainable months later.
- **Scalability**: must handle a constituency of 15–25 lakh citizens and tens of thousands of submissions per year.

## 8. Out of Scope (Hackathon MVP)

- Direct fund disbursement / financial transactions
- Full IVR telephony integration (MVP will simulate/stub the telephony leg; architecture supports it)
- Native Android/iOS apps (MVP is a responsive PWA)

## 9. MVP Build Plan (2-Day Hackathon Scope)

**Day 1:** Citizen submission web/PWA (text, photo, voice-upload) → Gemini-based normalization + embedding + clustering pipeline → BigQuery storage → basic scoring engine.
**Day 2:** MP dashboard (ranked list + map + evidence drill-down) → what-if simulator → WhatsApp notification stub → polish, demo data seeding (synthetic constituency dataset), pitch deck.

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| AI misclassifies/duplicates submissions incorrectly | Human-in-the-loop review queue before a cluster affects final ranking |
| Public data (UDISE, Census) is stale or unavailable per-ward | Graceful degradation — score shows "data unavailable" rather than guessing |
| Political misuse of ranking as sole decision-maker | Score is explicitly advisory; MP/office retains override with logged justification |
| Low digital literacy citizens excluded | Voice/IVR-first design; community kiosk mode at MP's local office |

---
*JanSetu — built for the Code for Communities Hackathon (hack2skill), 2026.*

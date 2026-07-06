# JanSetu — Technical Design Document

**Author:** Mohammed Ayaan Adil Ahmed
**Hackathon:** Code for Communities (hack2skill) — People's Priorities track
**Build environment:** Google Antigravity (agentic IDE) + Gemini 3 / Gemini Enterprise Agent Platform

---

## 1. Architecture Overview

JanSetu is organized into five layers:

```
1. INGESTION LAYER      — where citizen input enters the system
2. AI PROCESSING LAYER  — multi-agent pipeline (ADK on Gemini Enterprise Agent Platform)
3. EVIDENCE FUSION LAYER — cross-referencing public/administrative datasets
4. INTELLIGENCE LAYER   — deduplication, clustering, explainable scoring
5. EXPERIENCE LAYER     — MP dashboard, citizen transparency portal, notifications
```

Data flows one direction (ingest → process → score → present) with a feedback channel back to citizens once a Need Cluster changes status.

### 1.1 High-Level Component Diagram (textual)

```
[Citizen Channels]                         [Public Data Sources]
 WhatsApp Business API                      UDISE+ / education data
 IVR + Speech-to-Text (Indic)               Census / SECC demographic data
 Web/PWA form + camera                      Google Maps Platform (Distance Matrix, Places)
 Bulk photo upload (durbar letters)         Earth Engine satellite imagery
        |                                   Local development plan (govt open data / CSV/PDF)
        v                                          |
+-------------------------+                        |
|  INGESTION GATEWAY      |                        |
|  Cloud Run webhooks +   |                        |
|  Cloud Storage (media)  |                        |
+-----------+-------------+                        |
            v                                      |
+-------------------------------------------------+ |
|      AI PROCESSING LAYER (ADK Multi-Agent)       | |
|  Intake & Normalization Agent (Gemini 3 Flash)   | |
|   - language detect -> Cloud Translation         | |
|   - Speech-to-Text for voice                     | |
|   - Vision/OCR for photos & handwritten letters  | |
|   - structured extraction (category, location)   | |
|              v                                    | |
|  Dedup & Clustering Agent                        | |
|   - Vertex AI text embeddings                    | |
|   - Vector Search nearest-neighbour clustering   | |
|   - authenticity/spam scoring                    | |
|              v                                    | |
|  Evidence Agent  <--------------------------------+-+
|   - calls public dataset APIs above
|   - geospatial join (BigQuery GIS)
|              v
|  Scoring Agent
|   - explainable weighted formula
|   - writes score + full evidence trail
|              v
|  Notification Agent
|   - WhatsApp/SMS status updates to citizens
+-------------------------+
            v
+-------------------------+
|   DATA LAYER            |
|  BigQuery (GIS-enabled) |  <- Need Clusters, scores, evidence trail
|  Firestore               |  <- live submission stream, session state
|  Cloud Storage           |  <- raw photos/audio
+-----------+-------------+
            v
+-------------------------+
|  EXPERIENCE LAYER        |
|  MP Dashboard (React)    |  ranked list, evidence drill-down, map, what-if simulator
|  Citizen Transparency PWA|  public status tracker
|  Looker Studio embed     |  trend analytics for district admin
+-------------------------+
```

## 2. Multi-Agent Design (Agent Development Kit on Gemini Enterprise Agent Platform)

JanSetu's core intelligence is a multi-agent pipeline built with Google's **Agent Development Kit (ADK)**, orchestrated on the **Gemini Enterprise Agent Platform** (formerly Vertex AI Agent Builder), using **Gemini 3 Pro** for reasoning-heavy steps and **Gemini 3 Flash** for high-volume normalization.

| Agent | Responsibility | Key Tools/APIs |
|---|---|---|
| **Intake & Normalization Agent** | Detects language, transcribes voice, OCRs photos/handwritten letters, extracts structured fields (category, location, description) | Speech-to-Text API, Cloud Translation API, Gemini 3 multimodal (vision), Document AI |
| **Dedup & Clustering Agent** | Embeds each submission, finds near-duplicates and thematically related submissions, merges into Need Clusters, scores submission authenticity | Vertex AI Embeddings, Vertex AI Vector Search |
| **Evidence Agent** | For each Need Cluster, fetches and joins relevant public datasets (enrollment, census, distance, satellite, existing plan) | BigQuery GIS, Google Maps Platform (Distance Matrix/Places), Earth Engine, Document AI (for scanned development-plan PDFs) |
| **Scoring Agent** | Computes the explainable Priority Score and writes the full evidence trail (every number cited to its source) | Custom scoring function (deterministic, not opaque ML) running as an ADK tool |
| **Notification Agent** | Sends status updates to citizens tied to a cluster when it changes state | WhatsApp Business API, Cloud Messaging/SMS gateway |

Agents communicate via the **A2A (Agent-to-Agent) protocol**, orchestrated by a supervising root agent. Each agent step is logged to Cloud Logging for auditability, and evaluated pre-launch using Agent Platform's Evaluation/simulation tools.

## 3. Explainable Priority Scoring Model

```
Priority Score = w1·D + w2·G + w3·V + w4·F − w5·O

D (Demand Intensity)      = normalized unique-citizen count behind the cluster (post-dedup)
G (Objective Need Gap)    = data-driven gap, e.g. (enrollment − seat capacity)/capacity,
                             or (avg travel distance − departmental norm)
V (Vulnerability Weight)  = SECC/Census-derived deprivation index of the ward
F (Feasibility)           = inverse of estimated cost-per-beneficiary, land status from Earth Engine
O (Overlap Penalty)       = deduction if an existing sanctioned project already covers this need
```

- Weights (w1–w5) are configurable by the MP's office and versioned — every historical score is reproducible with the weight-set that produced it.
- Every score renders as a **citation card**: "Demand: 214 unique citizens (source: 340 raw submissions, 61% deduplication). Need Gap: enrollment 612 vs capacity 440 (UDISE+, updated Mar 2026). Distance: avg 6.2 km to nearest alternate school (Google Maps Distance Matrix)."
- This is deliberately **not** a black-box ML ranking — it's a transparent, auditable formula, because government resource-allocation decisions must be defensible.

## 4. Technology Stack & Google Services

| Layer | Technology |
|---|---|
| Frontend (Citizen PWA + MP Dashboard) | React + Tailwind, hosted on Firebase Hosting |
| Backend / Orchestration | Cloud Run (containerized services), Cloud Functions (event triggers), Pub/Sub (event bus) |
| AI Models | Gemini 3 Pro, Gemini 3 Flash (multimodal reasoning, OCR, extraction) |
| Agent Orchestration | Agent Development Kit (ADK), Gemini Enterprise Agent Platform (Agent Engine, Agent Studio) |
| Speech | Cloud Speech-to-Text (Indic language models), Cloud Text-to-Speech (IVR responses) |
| Translation | Cloud Translation API |
| Semantic Search / Dedup | Vertex AI Embeddings + Vertex AI Vector Search |
| Geospatial | Google Maps Platform (Distance Matrix, Places, Maps JavaScript API), Google Earth Engine (satellite imagery/land verification), BigQuery GIS |
| Data Warehouse | BigQuery |
| Real-time/Transactional store | Firestore |
| Media Storage | Cloud Storage |
| Messaging Channels | WhatsApp Business API, SMS/IVR gateway |
| Auth | Firebase Authentication (phone OTP) |
| Analytics | Looker Studio (embedded dashboards) |
| Security | Cloud IAM, Model Armor (prompt-injection defense on agent tools), Cloud DLP (PII redaction) |
| Dev Environment | Google Antigravity (agentic IDE), Google AI Studio |

## 5. Data Model (simplified)

```
Submission { id, citizen_id(hashed), channel, raw_text, media_url, lang,
             lat, lng, ward_id, category, timestamp, authenticity_score }

NeedCluster { id, centroid_embedding, submission_ids[], ward_id, category,
              demand_count, priority_score, score_breakdown{D,G,V,F,O},
              evidence{udise_ref, census_ref, maps_ref, earth_engine_ref, plan_ref},
              status[Received|Review|Approved|InProgress|Completed], last_updated }

WardProfile { ward_id, population, literacy_rate, vulnerability_index,
              infra_inventory{schools[], health_centres[], roads[]} }
```

## 6. Security & Privacy

- **DPDP Act 2023 compliance**: explicit consent at submission, purpose limitation, right-to-erasure endpoint, PII (name/phone) stored hashed/encrypted and separated from public-facing cluster data.
- **Model Armor** guards agent tool-calls against prompt injection from malicious submission content (e.g., a photo caption trying to manipulate the scoring agent).
- **Human-in-the-loop**: clusters flagged with low authenticity scores or high political sensitivity route to a human review queue before affecting the public ranking.
- **Public transparency vs. privacy**: the public dashboard shows aggregated cluster data only — never individual citizen identities.

## 7. Scalability & Reliability

- Ingestion webhooks (WhatsApp/IVR) are stateless on Cloud Run, auto-scaling with traffic spikes (e.g., after a public meeting).
- Pub/Sub decouples ingestion from AI processing so a burst of 10,000 durbar-letter photos doesn't block real-time WhatsApp intake.
- BigQuery handles constituency-scale analytical queries (15–25 lakh citizens, multi-year history) cheaply via partitioned, clustered tables on ward_id and timestamp.
- Vector Search index is rebuilt incrementally, so new submissions are clustered within minutes, not batch-overnight.

## 8. Hackathon Build Plan (Google Antigravity)

Using **Google Antigravity** as the agent-first dev environment (exported directly from Google AI Studio prototypes):

1. **Scaffold** citizen PWA + MP dashboard shells in Antigravity from an AI Studio prototype export.
2. **Wire ingestion**: web form + file upload → Cloud Run → Cloud Storage/Firestore.
3. **Build the ADK agent pipeline** (Intake → Dedup → Evidence → Scoring → Notify) using Gemini 3 Flash for speed, Gemini 3 Pro for the scoring/evidence reasoning step.
4. **Seed synthetic data**: a demo constituency with ~500 synthetic submissions, mock UDISE/Census/plan data, real Google Maps distance calls.
5. **Build the ranked dashboard + map + what-if simulator** on top of BigQuery views.
6. **Stub WhatsApp notifications** (sandbox WhatsApp Business API) for the closed-loop demo.

## 9. Future Roadmap (Post-Hackathon)

- Full IVR telephony integration for feature-phone users.
- Native Android app with offline-first submission queueing for low-connectivity areas.
- Expansion to Gram Panchayat / municipal ward-level deployments.
- Integration with State Open Data Portals and PM Gati Shakti layers for infrastructure gap-mapping.
- Federated multi-constituency benchmarking (anonymized) for national-level policy insight.

---
*JanSetu — built for the Code for Communities Hackathon (hack2skill), 2026.*

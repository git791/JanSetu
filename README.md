# 🌉 JanSetu (जन-सेतु)
*AI-Powered Constituency Intelligence & Resource Allocation Platform*

JanSetu (meaning "People's Bridge") is a multi-agent AI platform designed to bridge the gap between citizens' unstructured civic complaints and an MP's (Member of Parliament) budget allocation decisions. 

## 🚨 The Problem
Elected representatives receive thousands of daily complaints across multiple channels (WhatsApp, Twitter, Voice, Web) in various regional languages. These requests are messy, unstructured, and often duplicate the same core issue (e.g., 50 people complaining about the same broken pipe). Without context on the severity of the issue or the demographics of the affected area, MPs struggle to allocate their MPLADS (Members of Parliament Local Area Development Scheme) funds effectively.

## 💡 The Solution
JanSetu automates the entire intake, clustering, and prioritization process:
1. **Omnichannel Intake:** Citizens can submit complaints via Text, Voice, or Photo in local languages.
2. **AI Categorization:** Google Gemini instantly translates the text, runs OCR on photos, and extracts the core issue and location.
3. **Semantic Deduplication:** Vertex AI converts the complaint into vector embeddings and mathematically merges it into existing "Need Clusters" if the same issue was already reported.
4. **Data Fusion:** The platform cross-references the cluster's location with government databases (UDISE+ for schools, Census for vulnerability) and Google Maps (distance to hospitals).
5. **Priority Scoring:** A mathematical algorithm calculates a final ROI/Priority score based on Demand, Vulnerability, and Infrastructure Gaps.

MPs receive a clean, ranked dashboard of highly-verified Need Clusters ready for immediate budget approval.

---

## ☁️ Google Cloud Features Highlight

This project is built heavily on the Google Cloud ecosystem, utilizing the latest AI and Serverless architectures:

*   🧠 **Gemini 3.5 Flash (Generative AI):** Used by the `Intake Agent` for lightning-fast translation of Hindi/regional languages, parsing unstructured text into JSON, and performing multimodal OCR on citizen photo uploads (e.g., recognizing a broken street light).
*   🧬 **Vertex AI Embeddings (Text-Embedding-004):** Used by the `Dedup Agent`. Every complaint is converted into semantic vector embeddings. Cosine similarity matching ensures that 50 different complaints about "water leaking on Main St" and "paani ki samasya" merge into a single actionable cluster.
*   🗺️ **Google Maps JavaScript API:** Powers the dynamic Constituency Map on the dashboard, rendering dark-mode styled geographic points, bounding box autoscaling, and real-time visual clustering of civic issues.
*   🚀 **Google Cloud Run:** The entire unified application (FastAPI backend + Vite/React frontend) is containerized and deployed as a scalable, serverless microservice on Cloud Run.

---

## 🛠️ How to Run Locally

### Prerequisites
- Node.js (v18+)
- Python (3.11+)
- Google Cloud API Keys (Gemini & Maps)

### 1. Set up Environment Variables
In the root directory, create a `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_key_here
```

### 2. Start the Backend
The backend is a FastAPI application that orchestrates the AI Multi-Agent pipeline.
```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*(The backend runs on http://localhost:8000)*

### 3. Start the Frontend
The frontend is a React application built with Vite and TailwindCSS.
```bash
cd frontend
npm install
npm run dev
```
*(The frontend runs on http://localhost:5173)*

### 4. Testing the Flow
1. Navigate to `http://localhost:5173/submit`.
2. Fill out a mock citizen complaint (try uploading a photo of a civic issue!).
3. Navigate to `http://localhost:5173/dashboard` to watch the AI automatically cluster, score, and map your submission in real-time.

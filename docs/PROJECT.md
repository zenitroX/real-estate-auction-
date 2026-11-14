# Project Overview: Indian Bank Auction Tracker (SKANDX)

This project is a decoupled 3-tier system designed to track, manage, and bid on Indian bank property auctions. The architecture separates the **Frontend SPA**, **Backend REST API**, and **Cloud Database** so each tier can be scaled and hosted independently.

## 1. Decoupled 3-Tier Architecture

### 1. Frontend (React 19 + Vite)
*   **Location:** `frontend/`
*   **Hosting Target:** Independent static hosting (Vercel, Netlify, Cloudflare Pages, S3/CloudFront).
*   **Features:** Luxury dark-navy & gold UI, 4 reference views (Home, Listings with Filters, Property Details & Bidding, Bidder Dashboard), live countdowns, search overlay, and modal flows.
*   **Environment Config:** `VITE_API_URL` pointing to the backend API domain.
*   **Build Target:** `frontend/dist/`.

### 2. Backend REST API & Ingestion Engine
*   **Location:** `backend/` and `auction-ingestion-engine/`
*   **Hosting Target:** Independent backend cloud hosting (Render, Railway, Fly.io, AWS ECS, or Docker).
*   **Features:**
    *   `backend/app.py`: High-performance REST API with full CORS support (`GET /api/auctions`, `GET /api/health`, `OPTIONS`).
    *   In-memory 60s cache with local fallback snapshot in `backend/data/auctions_data.json`.
    *   `auction-ingestion-engine/`: Automated web scrapers & Gemini Vision OCR pipeline.

### 3. Database (Managed Supabase)
*   **Platform:** Supabase Cloud PostgreSQL + REST API & Realtime.
*   **Tables:** `auction_properties` storing bank, borrower, property specs, reserve prices, and auction schedules.

---

## 2. Repository Layout

```text
.
├── backend/                  # Decoupled Python REST API service
│   ├── app.py                # Standalone API server with CORS
│   ├── requirements.txt      # Backend dependencies
│   ├── Dockerfile            # Container deployment (Render / Railway / Fly.io)
│   ├── .env.example          # Supabase config template
│   └── data/                 # Local snapshot cache (auctions_data.json)
├── frontend/                 # Decoupled React 19 SPA
│   ├── src/                  # Components, Views, Data layer
│   ├── public/               # Public assets & offline fallback
│   ├── dist/                 # Standalone production build
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example          # VITE_API_URL config
├── auction-ingestion-engine/ # Automated scrapers & OCR pipeline
├── serve.py                  # Local dev API entrypoint (delegates to backend/app.py)
├── run_web.bat               # Windows 1-click launcher for API server
└── docs/                     # Business documentation
```

---

## 3. Quick Start & Deployment Guide

### Run Backend API Locally
1. Run `python serve.py` or double-click `run_web.bat`.
2. Listening at `http://127.0.0.1:8000/api/auctions`.
3. Health check at `http://127.0.0.1:8000/api/health`.

### Run Frontend Locally
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Open [http://localhost:5173](http://localhost:5173).

### Deploying Frontend Separately (e.g., Vercel / Netlify)
1. Push `frontend/` to GitHub or link the `frontend/` subdirectory in Vercel/Netlify.
2. Build command: `npm run build`
3. Output directory: `dist`
4. Set Environment Variable: `VITE_API_URL=https://your-backend-api-domain.com`.

### Deploying Backend Separately (e.g., Render / Railway)
1. Deploy using `backend/Dockerfile` or as a Python Web Service.
2. Start command: `python app.py` (or `gunicorn -w 4 app:app`).
3. Set Environment Variables: `SUPABASE_URL` and `SUPABASE_KEY`.

---

## 4. Security & Compliance
*   **Keep Secrets Safe:** Never commit `.env` files or API keys (Supabase/Gemini) to version control.
*   **Data Privacy:** This project handles sensitive property/borrower information. Review the data before public deployment.
*   **Legal:** Ensure your use of scrapers complies with the target websites' terms of service.

# WindDesk

Day-ahead view of UK national wind generation: forecast available at decision time vs actual outturn, with simple accuracy metrics.

Data: Elexon BMRS `FUELHH` (actual wind) and `WINDFOR` (forecasts). Default range: January 2026.

AI tools: Cursor assisted scaffolding, API client code, UI, and docs.

## Live demo

- Frontend (Vercel): https://jkhrt.vercel.app
- API (Render): https://jkhrt.onrender.com
- Repo: https://github.com/Aniket512/jkhrt

## Layout

```
backend/           FastAPI
  app/
    main.py
    config.py
    schemas.py
    routers/       /api/health, /api/dashboard
    services/      Elexon client + analytics
  tests/
  Dockerfile
  requirements.txt

frontend/          React + Vite + TypeScript
  src/
  Dockerfile
  vercel.json

docker-compose.yml
```

## Decision logic

- **Day-ahead (default):** for delivery on day `D`, use the latest WINDFOR with `publishTime` on or before the gate on `D−1` (default `11:00` UTC).
- **Fixed cutoff:** one global `decision_cutoff` for every period.
- Metrics use periods with both forecast and actual. Nulls are not treated as zero.

| Dataset | Filters |
|---------|---------|
| FUELHH  | `settlementDateFrom`, `settlementDateTo`, `fuelType=WIND` |
| WINDFOR | `publishDateTimeFrom`, `publishDateTimeTo` |

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173 (`/api` proxies to port 8000)

### Docker

```bash
docker compose up --build
```

- UI: http://localhost:8080  
- API: http://localhost:8000/api/health  

### Tests

```bash
cd backend
pytest -q
```

## Deploy

### API (Render)

1. New Web Service from this repo.
2. Root directory: `backend`
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Env: `FRONTEND_ORIGIN=https://<your-vercel-app>.vercel.app`

### Frontend (Vercel)

1. Import this repo; root directory `frontend`.
2. Env: `VITE_API_BASE_URL=https://<your-api>.onrender.com` (no trailing slash).
3. Deploy, then set Render `FRONTEND_ORIGIN` to the Vercel URL.

## Example

```
GET /api/dashboard?start_date=2026-01-01&end_date=2026-02-01&mode=day_ahead&gate_hour_utc=11
```

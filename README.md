# EximJunction

> India's Import-Export Intelligence Platform

[![Live](https://img.shields.io/badge/Live-eximjunction.com-blue)](https://eximjunction.com)
[![API Docs](https://img.shields.io/badge/API-Docs-green)](https://api.eximjunction.com/docs)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)

---

## What is EximJunction?

EximJunction gives Indian importers, exporters, freight forwarders, and trade consultants
instant access to global trade intelligence — without paying Volza-level prices.

| Product | Description | Price |
|---|---|---|
| **Trade Data Portal** | Web UI — search trade data, download CSV | Free → ₹14,999/month |
| **Trade Data API** | REST API for developers and integrations | Free → ₹1,999/month |
| **EXIM Documentation** | IEC, RCMC, AD Code registration service | ₹1,999–₹9,999 fixed fee |

---

## Repository Structure

```
eximjunction/
├── trade-data-api/      Backend — Python, FastAPI, SQLAlchemy, PostgreSQL
├── trade-frontend/      Frontend — React, Vite, Tailwind CSS
├── test-suite-v2/       QA — pytest-bdd, Playwright, Locust
├── README.md            This file
└── .gitignore           Root ignore rules
```

---

## Quick Start

### Prerequisites

| Tool | Version | Download |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Git | Any | [git-scm.com](https://git-scm.com) |

### 1 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/eximjunction.git
cd eximjunction
```

### 2 — Start the backend

```bash
cd trade-data-api

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env with your values

# Initialize database and seed data
python -m app.db.init_db

# Start the server
uvicorn app.main:app --reload
```

Backend runs at: `http://localhost:8000`
API Docs at: `http://localhost:8000/docs`

### 3 — Start the frontend

```bash
# Open a new terminal
cd trade-frontend

# Install dependencies
npm install

# Set up environment variables
copy .env.example .env
# Edit .env with your values

# Start the dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

### 4 — Run the tests

```bash
# Open a new terminal
cd test-suite-v2

# Activate the same venv as backend
..\trade-data-api\venv\Scripts\activate    # Windows
source ../trade-data-api/venv/bin/activate  # Mac/Linux

# Install test dependencies
pip install -r requirements-test.txt

# Install Playwright browser
playwright install chromium

# Set Python path
# Windows PowerShell:
$env:PYTHONPATH = "..\trade-data-api;."

# Mac/Linux bash:
export PYTHONPATH=../trade-data-api:.

# Run backend smoke tests
pytest tests/backend -m smoke -v

# Run full backend suite
pytest tests/backend -v

# Run frontend tests (needs both servers running)
pytest tests/frontend -v

# Run everything with HTML report
pytest tests/backend tests/frontend -v --html=test-report.html --self-contained-html
```

---

## Environment Variables

### Backend — `trade-data-api/.env`

```env
DATABASE_URL=sqlite:///./trade_data.db
DATA_MODE=mock
API_PREFIX=/api/v1
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your_admin_password
RATE_LIMIT_FREE_PER_DAY=50
RATE_LIMIT_PAID_PER_DAY=10000
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
COMTRADE_API_KEY=
LOG_LEVEL=INFO
```

### Frontend — `trade-frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEMO_API_KEY=
```

> ⚠️ Never commit `.env` files. They are listed in `.gitignore`.

---

## API Overview

All data endpoints require an API key passed as `X-API-Key` header.

```bash
curl "https://api.eximjunction.com/api/v1/products/search?q=coffee" \
  -H "X-API-Key: tdk_YourKeyHere"
```

| Endpoint | Description |
|---|---|
| `GET /api/v1/products/search` | Search HS codes by keyword |
| `GET /api/v1/products/{hs_code}` | HS code detail with hierarchy |
| `GET /api/v1/products/{hs_code}/top-partners` | Top trading partners |
| `GET /api/v1/trade-flows` | Year-over-year trend with CAGR |
| `GET /api/v1/tariffs` | MFN and FTA preferential rates |
| `GET /api/v1/compliance` | Required documents per corridor |
| `GET /api/v1/countries` | Reference list of countries |
| `GET /api/v1/portal/search` | Portal search (authenticated) |
| `GET /api/v1/portal/export` | CSV export (Starter plan+) |

Full interactive docs: [api.eximjunction.com/docs](https://api.eximjunction.com/docs)

---

## Architecture

```
                    eximjunction.com
                         │
              ┌──────────┴──────────┐
              │                     │
         React SPA            FastAPI Backend
         (Vite + Tailwind)    (Python 3.11)
              │                     │
              │              SQLAlchemy ORM
              │                     │
              └──────────┬──────────┘
                         │
                   PostgreSQL (prod)
                   SQLite (dev)
```

**Tech stack:**

| Layer | Technology |
|---|---|
| Backend framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL 16 |
| Authentication | JWT + bcrypt |
| Payments | Razorpay |
| Frontend | React 18 + Vite 5 |
| Styling | Tailwind CSS 3.4 |
| Charts | Recharts |
| Web server (prod) | Caddy (auto HTTPS) |
| Trade data source | UN Comtrade+ API |

---

## Deployment

Production runs on Hostinger KVM 2 (India DC):

```
eximjunction.com         → React build (served by Caddy)
api.eximjunction.com     → FastAPI (uvicorn behind Caddy)
```

See [deployment guide](trade-data-api/DEPLOY.md) for full instructions.

---

## Testing

| Layer | Framework | Coverage |
|---|---|---|
| Backend API | pytest-bdd + httpx | 48 BDD scenarios |
| Frontend E2E | Playwright + pytest-bdd | 34 BDD scenarios |
| Performance | Locust | Load, spike, soak |
| Reporting | pytest-html + Allure | HTML reports |

```bash
# Quick smoke test (30 seconds)
pytest tests/backend -m smoke -v

# Full suite with coverage
pytest tests/backend -v --cov=app --cov-report=html

# Performance test
locust -f test-suite-v2/tests/performance/locustfile.py \
  --host http://localhost:8000 \
  --users 50 --spawn-rate 5 --run-time 2m --headless \
  --html load-test-report.html
```

---

## Roadmap

| Phase | Timeline | Milestone |
|---|---|---|
| ✅ Phase 1 | Complete | FastAPI backend + React frontend + Portal + QA suite |
| 🔄 Phase 2 | Month 1-2 | Deploy to eximjunction.com + real Comtrade data |
| 📅 Phase 3 | Month 3-4 | India shipment-level data (Cybex/Seair vendor) |
| 📅 Phase 4 | Month 5-6 | Global shipment data + dashboards |
| 📅 Phase 5 | Month 7-9 | Verified contacts + real-time alerts |
| 📅 Phase 6 | Month 10-12 | Competitor tracking + Volza feature parity |

---

## Contributing

This is a proprietary project. Please contact the maintainer before contributing.

---

## Support

- Email: support@eximjunction.com
- Docs: [eximjunction.com/docs](https://eximjunction.com/docs)
- API Reference: [api.eximjunction.com/docs](https://api.eximjunction.com/docs)

---

## License

Proprietary — All rights reserved © 2026 EximJunction

---

*Built in India 🇮🇳 for Indian import-export businesses*

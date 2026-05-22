# Trade Data API

A REST API for international trade data: HS code lookup, top trading partners, trade trends, tariffs, and compliance documents.

## Features

- **HS code search** — find products by keyword or code, navigate the 2/4/6-digit hierarchy
- **Top trading partners** — for any product, see the largest exporters/importers
- **Trade trends** — historical volume and value flows between countries
- **Tariff data** — MFN and preferential duty rates
- **Compliance docs** — required certificates and documents per country corridor

## Stack

- **FastAPI** — async Python web framework with auto-generated OpenAPI docs
- **PostgreSQL** — primary data store (SQLAlchemy ORM)
- **httpx** — async HTTP client for Comtrade ingestion
- **Pydantic v2** — request/response validation

## Data Sources

- [UN Comtrade+](https://comtradeplus.un.org/) — global trade flows (free, requires API key)
- [WITS](https://wits.worldbank.org/) — tariff data on top of Comtrade (free)
- Curated compliance reference data (manual, per corridor)

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

Key settings:

- `DATABASE_URL` — Postgres connection string
- `DATA_MODE` — `mock` (use seed data only) or `live` (call Comtrade)
- `COMTRADE_API_KEY` — required only when `DATA_MODE=live`

### 3. Set up the database

```bash
# Create the database (one-time)
createdb trade_data

# Create tables and load seed data
python -m app.db.init_db
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API explorer.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/products/search?q=coffee` | Search HS codes by keyword or code |
| GET | `/products/{hs_code}` | Product details + parent/child codes |
| GET | `/products/{hs_code}/top-partners` | Top trading partners for a product |
| GET | `/trade-flows` | Trade flow data with filters (reporter, partner, HS, years) |
| GET | `/tariffs` | Tariff rates between two countries for a product |
| GET | `/compliance` | Required documents for a trade corridor + product |
| GET | `/countries` | List supported countries with ISO codes |
| GET | `/health` | Liveness check |

## Modes

**Mock mode** (`DATA_MODE=mock`): All endpoints serve from the seeded Postgres database. Good for development, demos, and offline work. The seed data covers ~50 HS codes across major chapters and 30+ countries.

**Live mode** (`DATA_MODE=live`): Read endpoints fall back to Comtrade when data isn't cached locally. Successful responses are written to the DB so subsequent calls are fast. Requires `COMTRADE_API_KEY`.

## Getting a Comtrade API Key

1. Register at [https://comtradeplus.un.org/](https://comtradeplus.un.org/)
2. Go to your profile → API Keys
3. Free tier: 500 calls/day, sufficient for development

## Project Structure

```
app/
├── api/          # FastAPI route handlers
├── core/         # Config, settings, dependencies
├── db/           # Database session, init script
├── models/       # SQLAlchemy ORM models
├── schemas/      # Pydantic request/response schemas
├── services/     # Business logic, Comtrade client
└── seed/         # Seed data (JSON files)
```

## Roadmap

- [ ] Add WITS tariff ingestion
- [ ] Add DGFT/ICEGATE adapter for India shipment-level data
- [ ] Redis caching layer for hot queries
- [ ] Background ingestion jobs (Celery / APScheduler)
- [ ] Rate limiting per API key
- [ ] GraphQL endpoint as alternative to REST

## License

MIT

# CashAPI - an "API pharmacy"

One FastAPI shelf of micro-utilities - validators, converters, generators - served from a single endpoint and live on RapidAPI with free and paid plans. Next to it sits a demand scanner that watches what people actually search for, so the shelf stocks what sells.

## Layout

- `api_pharmacy/` - FastAPI service with an OpenAPI schema and a Postman collection
- `scanner/` - async demand scanner: aiohttp, worker pool, SQLite, one plugin per platform
- `scripts/` - server bootstrap
- `changelog.md` - project history

## Public points

- Health check: https://apiteka.pp.ua/healthz
- RapidAPI storefront: https://rapidapi.com/krisanovstas/api/cashapi-micro-utilities
- OpenAPI schema: /openapi.json

## Run

```bash
pip install -r api_pharmacy/requirements.txt
cd api_pharmacy && uvicorn app.main:app
```

Secrets live in `api_pharmacy/.env` (gitignored).

# CashAPI

Pharmacy price API: a scraper collects pharmacy prices and serves them through an API.

## Layout

- `api_pharmacy/` - FastAPI service, OpenAPI schema, Postman collection
- `scanner/` - price scraper
- `scripts/` - server bootstrap
- `changelog.md` - project history

## Run

```bash
pip install -r api_pharmacy/requirements.txt
cd api_pharmacy && uvicorn app.main:app
```

Secrets live in `api_pharmacy/.env` (gitignored).

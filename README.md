# WhatsApp File Pipeline

Event-driven pipeline for receiving files through the WhatsApp Cloud API and
storing them in Google Drive. The application is designed to run at low cost on
Oracle Cloud Infrastructure Always Free.

## Current status

The project is in its initial foundation phase. The FastAPI application,
development container, environment template, package structure, and health tests
are available. WhatsApp, OCI, database, queue, and Google Drive integrations are
planned for the next tasks.

## Target architecture

```text
WhatsApp Cloud API
        |
        v
FastAPI webhook on OCI
        |
        +--> PostgreSQL metadata
        |
        v
Redis queue --> Celery worker
                    |
                    +--> OCI Object Storage
                    |
                    +--> Google Drive
```

The MVP will receive files in a direct conversation with a WhatsApp Business
number. Support for the official Groups API remains a future enhancement because
it has separate eligibility and participant restrictions.

## Project structure

```text
src/
├── api/             # HTTP endpoints and webhook
├── application/     # Use cases and orchestration
├── integrations/    # WhatsApp, OCI, and Google clients
├── models/          # Domain and API schemas
├── repositories/    # Metadata persistence
└── storage/         # Storage abstractions

tests/               # Automated tests
docker/              # Production container configuration
terraform/           # OCI infrastructure as code
```

## Local setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Install the development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Start the API:

```bash
python -m uvicorn src.api.main:app --reload
```

Open:

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- OpenAPI documentation: http://localhost:8000/docs

## Docker

```bash
docker compose up --build
```

Stop the environment with:

```bash
docker compose down
```

## Tests and quality

```bash
pytest
ruff check .
```

## Configuration and secrets

Copy `.env.example` to `.env` and fill in only the values required for the
current development task. Never commit `.env`, OAuth tokens, API tokens, private
keys, or service account files.

Production secrets will be stored in OCI Vault.

## Roadmap

- [x] Create the initial repository foundation
- [x] Add FastAPI health endpoints
- [x] Add local Docker support
- [x] Add initial automated tests
- [ ] Implement WhatsApp webhook verification
- [ ] Validate webhook signatures
- [ ] Add PostgreSQL metadata persistence
- [ ] Add Redis and Celery processing
- [ ] Download WhatsApp media
- [ ] Add OCI Object Storage
- [ ] Upload files to Google Drive
- [ ] Provision OCI resources with Terraform
- [ ] Add CI/CD with GitHub Actions


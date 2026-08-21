# WhatsApp File Pipeline

Event-driven pipeline for receiving files through the WhatsApp Cloud API and
storing them in Google Drive. The application is designed to run at low cost on
Oracle Cloud Infrastructure Always Free.

## Current status

The FastAPI application exposes the health check and the WhatsApp webhook.
Validated document events are registered idempotently in Redis and sent to a
Celery worker. The worker records the complete processing lifecycle and retries
transient failures automatically. Database, OCI, and Google Drive integrations
are planned for the next tasks.

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
Redis broker --> Celery worker
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
├── repositories/    # Processing state and metadata persistence
└── storage/         # Storage abstractions

src/worker/          # Celery application and tasks

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

For the complete local environment, start the API, Redis, and worker with
Docker Compose:

```bash
docker compose up --build
```

Open:

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- OpenAPI documentation: http://localhost:8000/docs

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Application health check |
| GET | `/webhook` | Meta webhook verification |
| POST | `/webhook` | Receive signed WhatsApp events |

The POST endpoint validates and normalizes document events, registers each
`message_id` atomically in Redis, enqueues new messages, and returns immediately.
A repeated `message_id` is acknowledged but not enqueued again.

Example response:

```json
{
  "status": "accepted",
  "documents_received": 1,
  "documents_queued": 1,
  "duplicates_ignored": 0
}
```

## Asynchronous processing

Redis is used as both the Celery broker and the transient processing state
store. File contents are not placed on the queue; the task receives only the
normalized document metadata.

| Status | Meaning |
| --- | --- |
| `RECEIVED` | The webhook registered the message and reserved its `message_id` |
| `PROCESSING` | A worker started or retried the job |
| `COMPLETED` | The processing function completed successfully |
| `FAILED` | All automatic retry attempts were exhausted |

Tasks retry up to five times with exponential backoff, jitter, and a maximum
delay of 60 seconds. Processing records expire after seven days by default,
which keeps Redis storage bounded. The current processor is intentionally a
placeholder; media download and permanent storage are implemented in later
tasks.

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

The WhatsApp webhook requires these values during local integration testing:

```env
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=
```

The Celery project does not officially support native Windows workers. On
Windows, run the worker through Docker Compose instead of invoking `celery`
directly from Git Bash or PowerShell.

## Roadmap

- [x] Create the initial repository foundation
- [x] Add FastAPI health endpoints
- [x] Add local Docker support
- [x] Add initial automated tests
- [x] Implement WhatsApp webhook verification
- [x] Validate webhook signatures
- [x] Parse WhatsApp document messages
- [ ] Add PostgreSQL metadata persistence
- [x] Add Redis and Celery processing
- [ ] Download WhatsApp media
- [ ] Add OCI Object Storage
- [ ] Upload files to Google Drive
- [ ] Provision OCI resources with Terraform
- [ ] Add CI/CD with GitHub Actions

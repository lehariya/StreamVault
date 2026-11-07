# StreamVault — Subscription-Based Video Download Manager

A React + Flask full-stack application demonstrating plan-based video access, daily/monthly download quotas, download auditing, and user download history.

## Features

- User registration and JWT login; passwords are stored as Werkzeug password hashes.
- Free, Bronze, Silver and Gold plans with configurable daily and monthly quotas.
- Server-side video access checks and subscription-expiry checks.
- Download reservation records, idempotency keys, pending/completed/failed statuses.
- User download history with date, file size, plan, browser and status.
- IP address and user-agent audit metadata.
- Optional registered-device enforcement.
- Admin-only audit endpoint and video metadata creation endpoint.
- Responsive React dashboard, video library, subscription plans and download history.
- Pytest backend smoke tests.

## Starter plan limits

| Plan | Daily | Monthly |
|---|---:|---:|
| Free | 1 | 5 |
| Bronze | 3 | 30 |
| Silver | 5 | 100 |
| Gold | 10 | 300 |

Change these values in `backend/app/seed.py` before first startup, or update the Plan rows in the database. These are sample policy values.

## Requirements

- Python 3.10+
- Node.js 18+
- npm

## Run locally (Windows PowerShell)

### 1. Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Backend: http://127.0.0.1:5000  
Health check: http://127.0.0.1:5000/api/health

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again. Alternatively run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe run.py` without activating.

### 2. Frontend (new terminal)

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open http://127.0.0.1:5173

### Demo accounts

- User: `demo@streamvault.local` / `Demo@12345`
- Admin: `admin@streamvault.local` / `Admin@12345`

Change demo passwords and secrets before any deployment. The demo admin account is intentionally seeded for local evaluation.

## Add actual video files

The repository does not redistribute copyrighted media. Put MP4 files you own or are licensed to distribute in `backend/storage/videos/`. The seeded catalog expects these names:

- `sample-welcome.mp4`
- `python-fundamentals.mp4`
- `fullstack-architecture.mp4`
- `system-design.mp4`

If files are absent, catalog metadata still appears, but download requests correctly return HTTP 404 rather than pretending a file exists. File sizes are captured when seed data is first created; update the corresponding Video row or reseed a fresh local database after adding media.

To add a new video, sign in as admin and call `POST /api/admin/videos` with a JSON body such as:
```json
{"title":"My video","description":"Licensed learning content","filename":"my-video.mp4","required_plan":"bronze"}
```
The file must already exist in the storage directory. Admin audit: `GET /api/admin/downloads`.

## Optional device restriction

Default: `DEVICE_LIMIT_ENABLED=false`. To require a registered device, set it to `true` in `backend/.env` and restart the API. The frontend sends a browser-generated device ID, but a user must register it using `POST /api/downloads/devices` with `{"device_id":"<id>","label":"My laptop"}`. This starter implementation does not provide device-management UI. Browser local storage IDs can be cleared/spoofed; device registration is friction, not hardware-grade identity.

## API summary

All endpoints except `/api/health`, `/api/auth/register`, and `/api/auth/login` require `Authorization: Bearer <JWT>`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create user and Free subscription |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Profile, plan and quota |
| GET | `/api/videos` | Video catalog with access flags |
| GET | `/api/subscriptions/plans` | Plan catalogue |
| GET | `/api/subscriptions/me` | Current subscription |
| POST | `/api/subscriptions/activate-demo` | Simulated 30-day paid plan activation |
| GET | `/api/downloads/quota` | Current quota |
| POST | `/api/downloads/authorize` | Preflight authorization |
| POST | `/api/downloads/{video_id}` | Authorized file response; requires `Idempotency-Key` |
| GET | `/api/downloads/history` | User's own download history |
| POST | `/api/downloads/devices` | Register a device |
| GET | `/api/admin/downloads` | Admin audit log |
| POST | `/api/admin/videos` | Admin adds video metadata |

## Download lifecycle and important design notes

1. The browser asks the server to authorize the video.
2. The server resolves the active subscription, checks video access, optional device registration, daily/monthly quota, and confirms the media file exists.
3. The actual download endpoint repeats all checks. A preflight authorization is not a reusable permission token.
4. A unique idempotency key prevents a retry from creating a second record for the same logical request.
5. The server writes a `pending` reservation before sending bytes. Pending reservations count against quota. A process-local lock serializes reservations within one running API process; this is not sufficient across multiple workers or server instances.
6. The response close callback marks a streamed response completed. Interrupted responses are intended to remain pending or be marked failed by the close handler. Pending records should be reconciled by a production background job after a timeout.
7. A new date/month naturally starts a new quota window because counts are filtered by the server's UTC calendar boundary.

**Important production hardening:** For a multi-worker deployment, use PostgreSQL (or another transactional database), row-level locking/atomic quota reservations, a durable background reconciler for stale pending downloads, object storage with signed short-lived URLs, rate limiting, HTTPS, CSRF strategy appropriate to token storage, refresh-token rotation, account/device revocation, malware/content scanning, and centralized logs. The included SQLite starter is appropriate for local demonstration, not high-concurrency production.

### Limitations disclosed

- Payment processing is not integrated. The “Try demo activation” action simulates a 30-day plan; never treat a client-side selection as proof of payment. Production must activate plans only after a verified payment-provider webhook.
- No actual MP4 media is bundled. Add your own licensed media as described above.
- Browser download completion is best-effort in this starter. HTTP response closure is not proof that the user saved every byte to disk. Production-grade delivery should use a storage/CDN delivery service with server-side transfer telemetry.
- A process-local lock protects quota reservations only within one API process. It does not coordinate multiple workers or server instances. Production must use database-level atomic reservations/locking (for example PostgreSQL transactions with row locks or a dedicated quota-reservation table). SQLite is not the recommended database for a multi-instance production service.
- Device ID is an optional browser identifier, not a tamper-proof device fingerprint.

## Tests

```powershell
cd backend
pip install -r requirements.txt
pytest -q
```

Tests cover health, login/profile, registration validation, plan listing, and empty download history. They are smoke tests, not a complete security/concurrency test suite.

## Database reset

Stop the backend, delete `backend/streamvault.db`, and restart `python run.py`. The seed routine recreates plans, demo accounts, and catalog rows.

## Folder structure

```text
streamvault/
├── backend/
│   ├── app/
│   │   ├── routes/          # REST endpoints
│   │   ├── __init__.py      # Flask app factory and extensions
│   │   ├── models.py        # SQLAlchemy tables
│   │   ├── seed.py          # Demo data
│   │   └── services.py      # Subscription/quota business rules
│   ├── storage/videos/      # Add licensed MP4 files here
│   ├── tests/
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/pages/           # Login, dashboard, library, downloads, plans
│   ├── src/App.jsx
│   ├── src/api.js
│   └── package.json
├── docs/
└── README.md
```

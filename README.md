# 𝕏Dash
Authenticated X/Twitter analytics dashboard that compares performance, highlights best posting times, and visualizes engagement metrics from tweet datasets.

## Features

- Two-step authentication that checks paying subscribers in a WordPress/MySQL database and confirms the session via email-delivered OTP codes stored in MongoDB.
- Multi-tab Streamlit experience covering upload, time analysis, post summaries, comment leaderboards, golden connections visualized with `streamlit-agraph`, and timeframe-based performance comparisons.
- CSV ingestion workflow that persists the uploaded file as `source_data.csv`, deduplicates tweets, splits posts vs. comments, and powers metric aggregations such as impressions, engagements, profile clicks, likes, replies, retweets, and media views.
- Container-friendly deployment with a Python 3.10 Streamlit image, optional MongoDB service, and an nginx + certbot edge defined in `docker-compose.yaml`.
- Email utility built on `smtplib` for OTP delivery and reusable helper modules (`Authenticate.py`, `runxdash.py`, `database_handling.py`, `sendEmail.py`) that encapsulate login, analytics, database calls, and messaging.

## Getting Started

### Prerequisites
- Python 3.10+
- Pip
- Access to:
  - A MySQL instance that mirrors your WordPress `wp_users` and `wp_pms_member_subscriptions` tables.
  - A MongoDB instance for temporary OTP storage.
  - SMTP credentials (Gmail is used out of the box).

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration
The app expects credentials and connection details to be provided via environment variables (or `secrets.toml`). Create a `.env` file or export them in your shell before running Streamlit/Docker:

| Purpose | Suggested Variable |
| --- | --- |
| JWT signing key | `XDASH_JWT_SECRET` |
| Streamlit cookie names | `XDASH_COOKIE_NAME`, `XDASH_COOKIE_KEY` |
| WordPress DB connection | `WP_DB_HOST`, `WP_DB_NAME`, `WP_DB_USER`, `WP_DB_PASSWORD`, `WP_DB_PORT` |
| Mongo connection | `MONGO_URL` |
| SMTP | `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_SENDER_EMAIL`, `SMTP_SERVER`, `SMTP_PORT` |

Example `.env` snippet:
```env
XDASH_COOKIE_NAME=xdash-auth
XDASH_COOKIE_KEY=super-secret-jwt-key
WP_DB_HOST=your-mysql-host
WP_DB_NAME=your-wordpress-db
WP_DB_USER=your-user
WP_DB_PASSWORD=super-secret
WP_DB_PORT=3306
MONGO_URL=mongodb://username:password@mongo-host:27017/
SMTP_USERNAME=notifications@example.com
SMTP_PASSWORD=app-specific-password
SMTP_SENDER_EMAIL=notifications@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
```
Load it with `source .env` (Linux/macOS) or `set -a; source .env; set +a` so the Streamlit process inherits the configuration.

### Running Locally
```bash
streamlit run app.py
```
1. Authenticate with a subscriber email (must exist in WordPress DB and have an active plan).
2. Enter the OTP sent via email. Verified sessions receive a signed cookie for short-lived re-authentication.
3. Use the **Upload** tab to provide the X/Twitter CSV export. The file is stored as `source_data.csv` so subsequent tabs can use it.

### Demo Mode (No Authentication)
If you only want to explore the dashboard locally without connecting to MySQL, MongoDB, SMTP, or WordPress subscribers, enable demo mode. This skips the entire login/OTP workflow and signs you in with a placeholder email.

```bash
export XDASH_DEMO_MODE=1          # any truthy value works (1, true, yes, on)
export XDASH_DEMO_EMAIL=me@local  # optional label shown inside the app
streamlit run app.py
```

In demo mode the cookie, database, and SMTP environment variables are ignored, so you can upload a CSV immediately after the app loads.

### CSV Requirements
- Dates should be parseable by `pandas.to_datetime`.
- Remove personal data you do not wish to analyze prior to upload.

## Docker & Deployment

### Build Streamlit Image
```bash
docker build -t xdash-panel .
```

### Compose Stack
The provided `docker-compose.yaml` spins up:
- `mongodb` for OTP storage.
- `panel` (replace image with `xdash-panel` or push to a registry) exposing Streamlit on port 9090.
- `nginx` reverse-proxy with optional TLS certificates stored under `./certbot`.
- `certbot` helper container to issue certificates.

Run only what you need:
```bash
docker-compose up -d mongodb
docker-compose up -d panel
```
Or bring up the entire stack (includes nginx/certbot):
```bash
docker-compose up -d
```

Ensure environment variables/secrets are injected via compose overrides or an orchestration platform (e.g., Docker secrets, Kubernetes secrets).

## Project Structure

| File | Description |
| --- | --- |
| `app.py` | Streamlit entry point that initializes authentication and loads the dashboard. |
| `Authenticate.py` | Custom auth helper managing OTP flow, cookies, and session state. |
| `runxdash.py` | Core analytics experience with sidebar navigation and visualization logic. |
| `database_handling.py` | WordPress subscription lookup plus Mongo-backed OTP lifecycle. |
| `sendEmail.py` | Gmail SMTP helper for delivering OTP codes. |
| `Dockerfile` | Minimal image for running Streamlit on port 9090. |
| `docker-compose.yaml` | Multi-service stack (MongoDB, Streamlit panel, nginx, certbot). |
| `nginx.conf` | Example reverse-proxy configuration. |

## Development Tips
- Use `streamlit cache clear` or delete `source_data.csv` when switching datasets.
- Toggle the "Discard Outliers" switch inside the Time Analysis tab to see how IQR filtering affects charts.
- If the OTP email is throttled, `check_recent_otp` enforces a 90-second cooldown—surface the countdown via `st.error` to improve UX.
- Add tests or logging before touching `database_handling.py`; it opens live connections to external services.

## Troubleshooting
- **Authentication never succeeds** – Confirm the WordPress DB is reachable from your machine and the user has an active subscription that has not expired.
- **No OTP email** – Verify SMTP credentials and allow-list the sender address. Check MongoDB logs to ensure codes are written.
- **Charts empty** – Ensure your CSV columns match expected names (case sensitive) and the `time` column covers at least two dates for comparisons.

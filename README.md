# Alert Explainer API

## Purpose

Alert Explainer API is a FastAPI service for creating and retrieving alerts and generating rule-based explanations from alert severity, metric value, and threshold.

## Project structure

```text
.
├── main.py                 # FastAPI app setup and health endpoint
├── database.py             # SQLAlchemy engine, session, and DB dependency
├── models.py               # Alert database model
├── schemas.py              # Request and response schemas
├── routers/
│   └── alerts.py           # Alert API endpoints
├── services/
│   └── explainer.py        # Rule-based explanation generation
├── test_alerts.py          # API tests
├── requirements.txt        # Runtime dependencies
└── docs/
    └── adr/                # Architecture Decision Records
```

The service uses SQLite and creates `alerts.db` in the working directory when run.

## Alert fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | Database-generated alert identifier. |
| `title` | string | Alert title. |
| `severity` | string | One of `critical`, `warning`, or `info`. |
| `source` | string | Source that produced the alert. |
| `metric_name` | string | Name of the measured metric. |
| `metric_value` | number | Current metric value. |
| `threshold` | number | Comparison threshold. |
| `created_at` | datetime | Database-generated creation time. |

When creating an alert, provide `title`, `severity`, `source`, `metric_name`, `metric_value`, and `threshold`. The API assigns `id` and `created_at`.

## API endpoints

| Method | Path | Status codes | Description |
|---|---|---|---|
| `GET` | `/` | `200` | Health response indicating the API is running. |
| `POST` | `/alerts/` | `201`, `422` | Create an alert. `422` indicates an invalid request body. |
| `GET` | `/alerts/` | `200` | Return all alerts. |
| `GET` | `/alerts/{alert_id}` | `200`, `404`, `422` | Return one alert; `404` if it does not exist and `422` if the path ID is invalid. |
| `POST` | `/alerts/{alert_id}/explain` | `200`, `404`, `422` | Return an explanation for an alert; `404` if it does not exist and `422` if the path ID is invalid. |

## Install and run on Windows (PowerShell)

From the project directory, create and activate a virtual environment, then install the runtime dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the development server:

```powershell
python -m uvicorn main:app --reload
```

The API is available at <http://127.0.0.1:8000>. Interactive API documentation is available at <http://127.0.0.1:8000/docs>.

## Run the tests

Install the test tools in the activated virtual environment and run the test suite from the project directory:

```powershell
python -m pip install pytest httpx
python -m pytest -q
```

## Architecture Decision Records

- [0001 - Rule-Based Explanations](docs/adr/0001-rule-based-explanations.md)
- [0002 - Human Approval for Alert Summaries](docs/adr/0002-human-approval-for-alert-summaries.md)

# OceoGeo API

Backend API for OceoGeo built with FastAPI. The service currently provides:

- `POST /files/process` to upload and process ARGO NetCDF files into Neon PostgreSQL.
- `POST /chat/send_message` for chat message processing.

## Tech Stack

- Python
- FastAPI + Uvicorn
- PostgreSQL (Neon) via `psycopg2`
- `xarray`, `numpy`, `pandas` for NetCDF/data handling

## Project Structure

```text
.
|-- main.py                 # FastAPI app entry point, router wiring
|-- config.py               # Model/config constants
|-- requirements.txt
|-- api/
|   |-- chat.py             # Chat API routes
|   `-- process_files.py    # File upload + process API routes
|-- services/
|   |-- ChatService.py      # Chat business logic
|   |-- ProcessService.py   # NetCDF parse + persistence workflow
|   `-- NeondbService.py    # DB connection + inserts/ownership checks
`-- core/
    |-- processor.py        # NetCDF extraction helpers
    |-- chatbot.py
    `-- tools.py
```

## Prerequisites

- Python 3.10+ recommended
- A running Neon PostgreSQL database with required schema (`projects`, `files`, `profiles`, `measurements`)

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Configure environment variables.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS/Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file at the project root:

```env
NEON_DEV_DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
```

Notes:

- The code currently reads `NEON_DEV_DATABASE_URL`.
- `services/NeondbService.py` raises an error message mentioning `NEON_DATABASE_URL`, but the actual variable used is `NEON_DEV_DATABASE_URL`.

## Run The API

```bash
uvicorn main:app --reload
```

App URLs:

- Base URL: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Navigation

### Health/Root

- `GET /`
- Response: `{"message": "OceoGeo API is up !! "}`

### Chat Endpoints

- `POST /chat/send_message`

Request body:

```json
{
  "message": "Hello"
}
```

### File Processing Endpoints

- `POST /files/process`
- `multipart/form-data` fields:
- `file`: `.nc`, `.netcdf`, or `.nc4`
- `user_id`: string
- `project_id`: integer

Limits and validations:

- Max file size: `100 MB`
- Enforces project ownership (`project_id` must belong to `user_id`)

Sample `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/files/process" \
  -F "file=@C:/path/to/your/file.nc" \
  -F "user_id=user_test_001" \
  -F "project_id=1"
```

## Common Dev Commands

```bash
# Install/update dependencies
pip install -r requirements.txt

# Freeze current environment versions
pip freeze > requirements.txt
```

## Troubleshooting

- `RuntimeError: NEON_DATABASE_URL environment variable not set`
: Ensure `.env` includes `NEON_DEV_DATABASE_URL` and restart the app.
- DB permission/ownership errors (`403`/`404` on `/files/process`)
: Confirm `project_id` exists and belongs to the provided `user_id` in the `projects` table.
- Unsupported file type (`422`)
: Upload only `.nc`, `.netcdf`, or `.nc4` files.

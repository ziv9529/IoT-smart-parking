"""Settings read from the .env file."""

import os

from dotenv import load_dotenv


load_dotenv()

TB_HOST = os.getenv("TB_HOST", "https://eu.thingsboard.cloud").rstrip("/")
TB_TOKEN = os.getenv("TB_TOKEN")
TINKERCAD_URL = os.getenv("TINKERCAD_URL", "").strip()
BROWSER_CDP_URL = os.getenv(
    "BROWSER_CDP_URL",
    "http://127.0.0.1:9222"
).strip()

TELEMETRY_URL = f"{TB_HOST}/api/v1/{TB_TOKEN}/telemetry"
RPC_URL = f"{TB_HOST}/api/v1/{TB_TOKEN}/rpc"

SCAN_INTERVAL = 0.5

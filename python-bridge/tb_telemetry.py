import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()

TB_HOST = os.getenv("TB_HOST", "https://eu.thingsboard.cloud").rstrip("/")
TB_TOKEN = os.getenv("TB_TOKEN")
TELEMETRY_URL = f"{TB_HOST}/api/v1/{TB_TOKEN}/telemetry"

REQUIRED_KEYS = {
    "spot1",
    "spot2",
    "distance1",
    "distance2",
    "free",
    "light",
    "lamp",
    "gate"
}


def validate_data(data):
    missing = REQUIRED_KEYS - data.keys()

    if missing:
        raise ValueError(f"missing keys: {', '.join(sorted(missing))}")

    for key in ["spot1", "spot2", "lamp", "gate"]:
        if data[key] not in [0, 1]:
            raise ValueError(f"{key} must be 0 or 1")

    expected_free = 2 - data["spot1"] - data["spot2"]

    if data["free"] != expected_free:
        raise ValueError(
            f"free should be {expected_free}, but received {data['free']}"
        )

    if not 0 <= data["light"] <= 1023:
        raise ValueError("light must be between 0 and 1023")

    if data["distance1"] < 0 or data["distance2"] < 0:
        raise ValueError("distance values cannot be negative")


def send_telemetry(data):
    response = requests.post(
        TELEMETRY_URL,
        json=data,
        timeout=5
    )
    response.raise_for_status()
    print(f"sent successfully: {data}")


def main():
    if not TB_TOKEN:
        raise RuntimeError("TB_TOKEN is missing from the .env file")

    print("copy one JSON line from the Tinkercad serial monitor")
    print("type exit to stop")

    while True:
        try:
            line = input("json> ").strip()

            if line.lower() in ["exit", "quit"]:
                break

            if not line:
                continue

            data = json.loads(line)
            validate_data(data)
            send_telemetry(data)

        except json.JSONDecodeError:
            print("error: the line is not valid JSON")
        except (ValueError, requests.RequestException) as error:
            print("error:", error)
        except KeyboardInterrupt:
            break

    print("stopped")


if __name__ == "__main__":
    main()
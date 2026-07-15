"""Reading the JSON lines that the Arduino prints to the Serial Monitor."""

import json
import re


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


def extract_telemetry(text):
    records = []

    for line in text.splitlines():
        for raw_json in re.findall(r"\{[^{}\r\n]+\}", line):
            try:
                data = json.loads(raw_json)
                validate_data(data)
                records.append(data)
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

    return records


def record_key(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def get_new_records(previous, current):
    """Return the records that appeared since the last scan.

    The Serial Monitor keeps the old lines on screen, so every scan re-reads
    records we already sent. We look for the longest overlap between the tail
    of the previous scan and the head of the current one.
    """
    if not current:
        return []

    if not previous:
        return current[-1:]

    previous_keys = [record_key(item) for item in previous]
    current_keys = [record_key(item) for item in current]
    max_overlap = min(len(previous_keys), len(current_keys))

    for size in range(max_overlap, 0, -1):
        if previous_keys[-size:] == current_keys[:size]:
            return current[size:]

    return current[-1:]

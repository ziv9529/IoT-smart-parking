import json
import os
import queue
import re
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


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

PROFILE_DIR = Path(__file__).parent / ".tinkercad_profile"
SCAN_INTERVAL = 0.5

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

COMMANDS = {
    "openGate": "OPEN_GATE",
    "closeGate": "CLOSE_GATE"
}

COMMAND_LOGS = {
    "OPEN_GATE": [
        "LOG:GATE_OPENED",
        "LOG:GATE_BLOCKED_PARKING_FULL"
    ],
    "CLOSE_GATE": ["LOG:GATE_CLOSED"]
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
    print(
        "telemetry sent: "
        f"spot1={data['spot1']} "
        f"spot2={data['spot2']} "
        f"free={data['free']} "
        f"gate={data['gate']}"
    )


def send_rpc_reply(request_id, data):
    response = requests.post(
        f"{RPC_URL}/{request_id}",
        json=data,
        timeout=5
    )
    response.raise_for_status()


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


def read_page_text(page):
    texts = []

    for frame in page.frames:
        try:
            text = frame.locator("body").inner_text(timeout=1500)
            if text and text not in texts:
                texts.append(text)
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue

    return "\n".join(texts)


def visible_candidates(page):
    candidates = []
    selector = "input:not([type=hidden]), textarea, [contenteditable=true]"

    for frame in page.frames:
        locator = frame.locator(selector)
        count = min(locator.count(), 80)

        for index in range(count):
            item = locator.nth(index)

            try:
                if not item.is_visible() or not item.is_enabled():
                    continue

                box = item.bounding_box()
                if not box or box["width"] < 120 or box["height"] > 90:
                    continue

                readonly = item.get_attribute("readonly")
                if readonly is not None:
                    continue

                label = " ".join(filter(None, [
                    item.get_attribute("aria-label"),
                    item.get_attribute("placeholder"),
                    item.get_attribute("name"),
                    item.get_attribute("class")
                ])).lower()

                if "search" in label or "design name" in label:
                    continue

                score = box["y"] + box["x"] * 0.05

                if box["y"] > 500:
                    score += 1000

                candidates.append((score, frame, item, box))
            except Exception:
                continue

    candidates.sort(key=lambda entry: entry[0], reverse=True)
    return candidates


def find_serial_input(page):
    candidates = visible_candidates(page)

    if not candidates:
        return None

    return candidates[0][1], candidates[0][2], candidates[0][3]


def find_send_button(page, input_box):
    buttons = []

    for frame in page.frames:
        locator = frame.get_by_role("button", name="Send", exact=True)
        count = locator.count()

        for index in range(count):
            button = locator.nth(index)

            try:
                if not button.is_visible():
                    continue

                box = button.bounding_box()
                if not box:
                    continue

                distance = abs(box["y"] - input_box["y"])
                buttons.append((distance, button))
            except Exception:
                continue

    if not buttons:
        return None

    buttons.sort(key=lambda entry: entry[0])
    return buttons[0][1]


def try_open_serial_monitor(page):
    if find_serial_input(page):
        return True

    for frame in page.frames:
        try:
            label = frame.get_by_text("Serial Monitor", exact=True)

            for index in range(label.count()):
                item = label.nth(index)
                if item.is_visible():
                    item.click(timeout=1500)
                    time.sleep(0.5)
                    return find_serial_input(page) is not None
        except Exception:
            continue

    return False


def send_serial_command(page, command):
    if not try_open_serial_monitor(page):
        return {
            "success": False,
            "command": command,
            "error": "serial monitor input was not found"
        }

    found = find_serial_input(page)

    if not found:
        return {
            "success": False,
            "command": command,
            "error": "serial monitor input was not found"
        }

    _, serial_input, input_box = found
    before_text = read_page_text(page)
    expected_logs = COMMAND_LOGS.get(command, [])
    old_counts = {log: before_text.count(log) for log in expected_logs}

    try:
        serial_input.fill(command)
        send_button = find_send_button(page, input_box)

        if send_button:
            send_button.click(timeout=2000)
        else:
            serial_input.press("Enter")

        print(f"command sent to Tinkercad: {command}")
    except Exception as error:
        return {
            "success": False,
            "command": command,
            "error": str(error)
        }

    end_time = time.time() + 10

    while time.time() < end_time:
        time.sleep(0.4)
        current_text = read_page_text(page)

        for log in expected_logs:
            if current_text.count(log) > old_counts.get(log, 0):
                result = {
                    "success": True,
                    "command": command,
                    "arduinoLog": log
                }

                if log == "LOG:GATE_BLOCKED_PARKING_FULL":
                    result["gateOpened"] = False
                    result["reason"] = "parking full"

                return result

    return {
        "success": False,
        "command": command,
        "error": "Arduino response timeout"
    }


def rpc_worker(command_queue, stop_event):
    print("ThingsBoard RPC listener started")

    while not stop_event.is_set():
        try:
            response = requests.get(
                RPC_URL,
                params={"timeout": 20000},
                timeout=25
            )

            if response.status_code in [204, 408]:
                continue

            response.raise_for_status()

            if not response.text.strip():
                continue

            request = response.json()
            request_id = request.get("id")
            method = request.get("method")
            command = COMMANDS.get(method)

            if request_id is None or not method:
                print("invalid RPC request:", request)
                continue

            if not command:
                send_rpc_reply(request_id, {
                    "success": False,
                    "error": "unsupported method"
                })
                continue

            print(f"RPC received: {method}")
            result_queue = queue.Queue(maxsize=1)
            command_queue.put({
                "request_id": request_id,
                "command": command,
                "result_queue": result_queue
            })

            try:
                result = result_queue.get(timeout=15)
            except queue.Empty:
                result = {
                    "success": False,
                    "command": command,
                    "error": "browser bridge timeout"
                }

            send_rpc_reply(request_id, result)
            print("RPC reply sent")

        except requests.ReadTimeout:
            continue
        except requests.RequestException as error:
            print("RPC network error:", error)
            time.sleep(2)
        except ValueError as error:
            print("invalid RPC response:", error)
        except Exception as error:
            print("RPC worker error:", error)
            time.sleep(2)


def find_tinkercad_page(context):
    for page in context.pages:
        if "tinkercad.com" in page.url.lower():
            return page

    return None


def run_browser(command_queue, stop_event):
    previous_records = []
    last_input_warning = 0

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.connect_over_cdp(
                BROWSER_CDP_URL,
                timeout=10000
            )
        except Exception as error:
            raise RuntimeError(
                "could not connect to Google Chrome. "
                "run 2_start_chrome_gateway.bat first"
            ) from error

        if not browser.contexts:
            raise RuntimeError("Chrome opened without a browser context")

        context = browser.contexts[0]
        page = find_tinkercad_page(context)

        if page is None:
            page = context.new_page()

            if TINKERCAD_URL:
                page.goto(TINKERCAD_URL, wait_until="domcontentloaded")
            else:
                page.goto(
                    "https://www.tinkercad.com/",
                    wait_until="domcontentloaded"
                )
        elif TINKERCAD_URL and "circuits" not in page.url.lower():
            page.goto(TINKERCAD_URL, wait_until="domcontentloaded")

        print("connected to the existing Google Chrome window")
        print("open the Serial Monitor and press Start Simulation")

        try:
            while not stop_event.is_set():
                try:
                    page_text = read_page_text(page)
                    current_records = extract_telemetry(page_text)
                    new_records = get_new_records(previous_records, current_records)

                    for data in new_records:
                        try:
                            send_telemetry(data)
                        except requests.RequestException as error:
                            print("telemetry network error:", error)

                    if current_records:
                        previous_records = current_records

                    try:
                        rpc_request = command_queue.get_nowait()
                    except queue.Empty:
                        rpc_request = None

                    if rpc_request:
                        result = send_serial_command(
                            page,
                            rpc_request["command"]
                        )
                        rpc_request["result_queue"].put(result)

                    if not find_serial_input(page) and time.time() - last_input_warning > 10:
                        print("waiting for the Tinkercad Serial Monitor...")
                        last_input_warning = time.time()

                    time.sleep(SCAN_INTERVAL)

                except PlaywrightTimeoutError:
                    time.sleep(1)
                except Exception as error:
                    print("browser scan error:", error)
                    time.sleep(1)

        except KeyboardInterrupt:
            stop_event.set()


def main():
    if not TB_TOKEN:
        raise RuntimeError("TB_TOKEN is missing from the .env file")

    command_queue = queue.Queue()
    stop_event = threading.Event()

    rpc_thread = threading.Thread(
        target=rpc_worker,
        args=(command_queue, stop_event),
        daemon=True
    )
    rpc_thread.start()

    try:
        run_browser(command_queue, stop_event)
    finally:
        stop_event.set()
        print("bridge stopped")


if __name__ == "__main__":
    main()

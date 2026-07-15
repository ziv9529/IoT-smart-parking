"""The main loop: read the Serial Monitor, push telemetry, run queued commands."""

import queue
import time

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from config import BROWSER_CDP_URL, SCAN_INTERVAL, TINKERCAD_URL
from telemetry import extract_telemetry, get_new_records
from thingsboard import send_telemetry
from tinkercad_page import find_serial_input, find_tinkercad_page, read_page_text, send_serial_command


def connect_to_browser(playwright):
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

    return browser.contexts[0]


def open_tinkercad_page(context):
    page = find_tinkercad_page(context)

    if page is None:
        page = context.new_page()
        page.goto(
            TINKERCAD_URL or "https://www.tinkercad.com/",
            wait_until="domcontentloaded"
        )
    elif TINKERCAD_URL and "circuits" not in page.url.lower():
        page.goto(TINKERCAD_URL, wait_until="domcontentloaded")

    return page


def push_new_telemetry(page, previous_records):
    current_records = extract_telemetry(read_page_text(page))

    for data in get_new_records(previous_records, current_records):
        try:
            send_telemetry(data)
        except requests.RequestException as error:
            print("telemetry network error:", error)

    return current_records or previous_records


def run_pending_command(page, command_queue):
    try:
        rpc_request = command_queue.get_nowait()
    except queue.Empty:
        return

    result = send_serial_command(page, rpc_request["command"])
    rpc_request["result_queue"].put(result)


def run_browser(command_queue, stop_event):
    previous_records = []
    last_input_warning = 0

    with sync_playwright() as playwright:
        context = connect_to_browser(playwright)
        page = open_tinkercad_page(context)

        print("connected to the existing Google Chrome window")
        print("open the Serial Monitor and press Start Simulation")

        try:
            while not stop_event.is_set():
                try:
                    previous_records = push_new_telemetry(page, previous_records)
                    run_pending_command(page, command_queue)

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

"""Finding and driving the Tinkercad Serial Monitor inside the browser page."""

import time


# what the Arduino prints back after each command
COMMAND_LOGS = {
    "OPEN_GATE": [
        "LOG:GATE_OPENED",
        "LOG:GATE_BLOCKED_PARKING_FULL"
    ],
    "CLOSE_GATE": ["LOG:GATE_CLOSED"]
}


def find_tinkercad_page(context):
    for page in context.pages:
        if "tinkercad.com" in page.url.lower():
            return page

    return None


def read_page_text(page):
    texts = []

    for frame in page.frames:
        try:
            text = frame.locator("body").inner_text(timeout=1500)
            if text and text not in texts:
                texts.append(text)
        except Exception:
            continue

    return "\n".join(texts)


def visible_candidates(page):
    """Score every text box on the page by how likely it is the serial input.

    Tinkercad has no stable id for it, so we guess: it is wide, short, near
    the bottom of the page, and it is not the search or design-name box.
    """
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


def submit_command(page, serial_input, input_box, command):
    serial_input.fill(command)
    send_button = find_send_button(page, input_box)

    if send_button:
        send_button.click(timeout=2000)
    else:
        serial_input.press("Enter")

    print(f"command sent to Tinkercad: {command}")


def wait_for_log(page, command, old_counts):
    """Wait until one of the expected logs shows up more times than before."""
    end_time = time.time() + 10

    while time.time() < end_time:
        time.sleep(0.4)
        current_text = read_page_text(page)

        for log in COMMAND_LOGS.get(command, []):
            if current_text.count(log) > old_counts.get(log, 0):
                return log

    return None


def send_serial_command(page, command):
    found = find_serial_input(page) if try_open_serial_monitor(page) else None

    if not found:
        return {
            "success": False,
            "command": command,
            "error": "serial monitor input was not found"
        }

    _, serial_input, input_box = found

    # count the logs already on screen, so we only look at new ones
    before_text = read_page_text(page)
    old_counts = {
        log: before_text.count(log)
        for log in COMMAND_LOGS.get(command, [])
    }

    try:
        submit_command(page, serial_input, input_box, command)
    except Exception as error:
        return {
            "success": False,
            "command": command,
            "error": str(error)
        }

    log = wait_for_log(page, command, old_counts)

    if not log:
        return {
            "success": False,
            "command": command,
            "error": "Arduino response timeout"
        }

    result = {
        "success": True,
        "command": command,
        "arduinoLog": log
    }

    if log == "LOG:GATE_BLOCKED_PARKING_FULL":
        result["gateOpened"] = False
        result["reason"] = "parking full"

    return result

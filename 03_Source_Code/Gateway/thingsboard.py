"""Talking to ThingsBoard: sending telemetry and listening for RPC commands."""

import queue
import time

import requests

from config import RPC_URL, TELEMETRY_URL


# ThingsBoard RPC method -> the command we type into the Serial Monitor
COMMANDS = {
    "openGate": "OPEN_GATE",
    "closeGate": "CLOSE_GATE"
}


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


def handle_rpc_request(request, command_queue):
    """Pass one RPC request to the browser thread and reply with its result."""
    request_id = request.get("id")
    method = request.get("method")
    command = COMMANDS.get(method)

    if request_id is None or not method:
        print("invalid RPC request:", request)
        return

    if not command:
        send_rpc_reply(request_id, {
            "success": False,
            "error": "unsupported method"
        })
        return

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


def rpc_worker(command_queue, stop_event):
    """Long-poll ThingsBoard for RPC commands. Runs in its own thread."""
    print("ThingsBoard RPC listener started")

    while not stop_event.is_set():
        try:
            response = requests.get(
                RPC_URL,
                params={"timeout": 20000},
                timeout=25
            )

            # no command arrived before the long-poll expired
            if response.status_code in [204, 408]:
                continue

            response.raise_for_status()

            if not response.text.strip():
                continue

            handle_rpc_request(response.json(), command_queue)

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

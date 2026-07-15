"""Bridge between the Tinkercad simulation and ThingsBoard.

Reads the Arduino telemetry from the Tinkercad Serial Monitor in Chrome and
sends it to ThingsBoard, and sends gate commands from ThingsBoard back to the
Serial Monitor.

Run 2_start_chrome_gateway.bat first, then: python tinkercad_bridge.py
"""

import queue
import threading

from bridge import run_browser
from config import TB_TOKEN
from thingsboard import rpc_worker


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

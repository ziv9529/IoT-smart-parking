# reads the tinkercad serial monitor live and forwards each sample to thingsboard
# setup:
#   python -m venv venv
#   venv\Scripts\activate        (mac/linux: source venv/bin/activate)
#   pip install circuikit
# run:
#   python smart_parking_app.py

import requests

from circuikit import Circuikit
from circuikit.serial_monitor_interface import ThinkercadInterface
from circuikit.serial_monitor_interface.types import SerialMonitorOptions
from circuikit.services import Service, FileLogger
from circuikit.protocols import SendSmiInputFn

TOKEN = "PASTE_TOKEN_HERE"
HOST = "https://eu.thingsboard.cloud"
TINKERCAD_URL = "PASTE_YOUR_TINKERCAD_EDIT_URL_HERE"

SAMPLE_RATE_MS = 1000


# circuikit ships a ThingsBoardGateway, but it is hardcoded to
# http://thingsboard.cloud - wrong protocol and wrong region for us.
# so we write our own, it's the same idea.
class ThingsBoardEU(Service):
    def __init__(self, token, host):
        super().__init__()
        self.url = host + "/api/v1/" + token + "/telemetry"

    def on_message(self, message: dict) -> None:
        message.pop("time", None)   # circuikit adds its own timestamp, we don't need it

        try:
            r = requests.post(self.url, json=message, timeout=5)
            print(r.status_code, message)
        except Exception as e:
            print("error:", e)


def allocate_services(send_smi_input: SendSmiInputFn) -> list[Service]:
    return [
        ThingsBoardEU(token=TOKEN, host=HOST),
        FileLogger(file_path="./logs/serial_log.txt"),   # keeps a copy for the report
    ]


if __name__ == "__main__":
    options = SerialMonitorOptions(
        interface=ThinkercadInterface(
            thinkercad_url=TINKERCAD_URL,
            open_simulation_timeout=120,
        ),
        sample_rate_ms=SAMPLE_RATE_MS,
    )

    kit = Circuikit(
        serial_monitor_options=options,
        allocate_services_fn=allocate_services,
    )
    kit.start()

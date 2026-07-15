# smart parking - reads telemetry and sends it to thingsboard
# run: pip install requests pyserial

import json
import random
import time
import requests

TOKEN = "PASTE_TOKEN_HERE"
HOST = "https://eu.thingsboard.cloud"
URL = HOST + "/api/v1/" + TOKEN + "/telemetry"

# "mock"   - random values, for testing the connection
# "file"   - replay the serial monitor output captured from tinkercad
# "serial" - live arduino over usb
MODE = "file"

LOG_FILE = "serial_log.txt"
PORT = "COM6"
INTERVAL = 2
TOTAL_SPOTS = 2
DARK = 300


def read_mock():
    spot1 = random.randint(0, 1)
    spot2 = random.randint(0, 1)
    light = random.randint(0, 1023)
    return {
        "spot1": spot1,
        "spot2": spot2,
        "free": TOTAL_SPOTS - spot1 - spot2,
        "light": light,
        "lamp": 1 if light < DARK else 0
    }


def load_log(path):
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("{"):     # skip anything that isn't a json line
                lines.append(line)
    return lines


def send(data):
    r = requests.post(URL, json=data, timeout=5)
    print(r.status_code, data)


if MODE == "serial":
    import serial
    arduino = serial.Serial(PORT, 9600)
elif MODE == "file":
    log = load_log(LOG_FILE)
    print("loaded", len(log), "samples from", LOG_FILE)
    index = 0

print("running, ctrl+c to stop")

while True:
    try:
        if MODE == "serial":
            data = json.loads(arduino.readline().decode("utf-8").strip())
        elif MODE == "file":
            data = json.loads(log[index])
            index = (index + 1) % len(log)   # loop the log so the dashboard keeps moving
        else:
            data = read_mock()

        send(data)
        time.sleep(INTERVAL)

    except KeyboardInterrupt:
        break
    except Exception as e:
        print("error:", e)

if MODE == "serial":
    arduino.close()

print("stopped")

# smart parking - reads sensor data and sends it to thingsboard

import json
import random
import time
import requests

TOKEN = "j96kbmtym6297f2ieuek"
HOST  = "http://eu.thingsboard.cloud"   
URL   = f"{HOST}/api/v1/{TOKEN}/telemetry"

USE_ARDUINO = False     # switch to True once the tinkercad/arduino side is ready
PORT = "COM6"
INTERVAL = 2            # seconds between samples
TOTAL_SPOTS = 2
DARK = 300              # ldr value below this means it's dark
 
 
def read_mock():
    spot1 = random.randint(0, 1)
    spot2 = random.randint(0, 1)
    light = random.randint(0, 1023)
    return {
        "spot1": spot1,
        "spot2": spot2,
        "free": TOTAL_SPOTS - spot1 - spot2,
        "light": light,
        "lamp": 1 if light < DARK else 0,
        "temp": round(random.uniform(18, 34), 1)
    }
 
 
def read_serial(arduino):
    line = arduino.readline().decode("utf-8").strip()
    return json.loads(line)     # arduino prints one json line per cycle
 
 
def send(data):
    r = requests.post(URL, json=data, timeout=5)
    print(r.status_code, data)
 
 
arduino = None
if USE_ARDUINO:
    import serial
    arduino = serial.Serial(PORT, 9600)
 
print("running, ctrl+c to stop")
 
while True:
    try:
        if USE_ARDUINO:
            data = read_serial(arduino)
        else:
            data = read_mock()
        send(data)
        time.sleep(INTERVAL)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print("error:", e)      # bad line or network hiccup - keep the loop alive
 
if arduino:
    arduino.close()
 
print("stopped")
import requests

TOKEN = "j96kbmtym6297f2ieuek"
HOST  = "http://eu.thingsboard.cloud"   
URL   = f"{HOST}/api/v1/{TOKEN}/telemetry"

payload = {"spot1": 1, "spot2": 0, "free": 1, "light": 620, "lamp": 0}
r = requests.post(URL, json=payload)
print(r.status_code)   # 200 = הצלחה


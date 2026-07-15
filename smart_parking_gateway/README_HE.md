# Smart Parking - Tinkercad Gateway

ה-Gateway מחבר אוטומטית בין ה-Serial Monitor של Tinkercad לבין ThingsBoard.

הוא מבצע שני כיוונים:

```text
Tinkercad telemetry -> Python Gateway -> ThingsBoard
ThingsBoard RPC -> Python Gateway -> Tinkercad Serial Monitor
```

## 1. התקנה

מתוך Git Bash בתיקיית הפרויקט:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## 2. קובץ הגדרות

צור עותק של `.env.example` בשם `.env`:

```bash
cp .env.example .env
```

עדכן בקובץ `.env`:

```env
TB_HOST=https://eu.thingsboard.cloud
TB_TOKEN=הטוקן_של_ההתקן_ב-ThingsBoard
TINKERCAD_URL=הקישור_המלא_לפרויקט_ב-Tinkercad
```

אין להעלות את קובץ `.env` ל-Git.

## 3. הפעלה

```bash
python tinkercad_bridge.py
```

בפעם הראשונה ייפתח חלון Chromium חדש:

1. התחבר ל-Tinkercad אם צריך.
2. פתח את הפרויקט.
3. פתח את `Serial Monitor`.
4. לחץ `Start Simulation`.

מרגע זה, כל שורת JSON שה-Arduino מדפיס נשלחת אוטומטית ל-ThingsBoard.

לחיצה על `OPEN GATE` בדשבורד תשלח אוטומטית `OPEN_GATE` ל-Serial Monitor.

## 4. מה אמור להופיע בטרמינל

```text
ThingsBoard RPC listener started
browser opened
telemetry sent: spot1=0 spot2=0 free=2 gate=0
RPC received: openGate
command sent to Tinkercad: OPEN_GATE
RPC reply sent
```

## 5. הערה לגבי קוד Arduino

אין צורך לשנות כרגע את `smart_parking_ziv_ben.ino`.

הקוד כבר:

- מדפיס telemetry בפורמט JSON.
- מקבל `OPEN_GATE` ו-`CLOSE_GATE` דרך Serial.
- מדפיס לוג לאחר ביצוע פקודה.

## 6. אם ה-Gateway לא מזהה את Serial Monitor

ודא ש:

- הפרויקט פתוח באותו חלון Chromium שה-Gateway פתח.
- חלון `Serial Monitor` פתוח.
- הסימולציה התחילה.
- שורות JSON מופיעות ב-Serial Monitor.

אם עדיין מופיעה ההודעה:

```text
waiting for the Tinkercad Serial Monitor...
```

צריך להתאים את זיהוי שדה ה-Serial למבנה העמוד שמופיע אצלך.

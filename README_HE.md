# Smart Parking Gateway — Chrome version

גרסה זו לא מבצעת התחברות ל-Google מתוך Playwright.

## התקנה ראשונית

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

אין צורך להריץ `playwright install chromium`, כי ה-Gateway מתחבר ל-Google Chrome המותקן במחשב.

## 1. התחברות חד-פעמית

1. לחץ פעמיים על `1_login_chrome.bat`.
2. ייפתח Chrome עם פרופיל נפרד עבור הפרויקט.
3. התחבר ל-Tinkercad באמצעות Google.
4. ודא שאתה מצליח לפתוח את הפרויקט.
5. סגור את כל חלונות ה-Chrome שנפתחו על ידי הקובץ.

ההתחברות נשמרת מקומית בתיקייה:

```text
.chrome_gateway_profile/
```

אל תעלה את התיקייה הזו ל-Git ואל תשלח אותה לאחרים.

## 2. יצירת קובץ `.env`

```bash
cp .env.example .env
```

עדכן:

```env
TB_HOST=https://eu.thingsboard.cloud
TB_TOKEN=YOUR_THINGSBOARD_DEVICE_TOKEN
TINKERCAD_URL=YOUR_FULL_TINKERCAD_PROJECT_URL
BROWSER_CDP_URL=http://127.0.0.1:9222
```

## 3. הפעלה רגילה

בכל הרצה:

1. לחץ פעמיים על `2_start_chrome_gateway.bat`.
2. המתן עד ש-Chrome נפתח.
3. הרץ:

```bash
source .venv/Scripts/activate
python tinkercad_bridge.py
```

4. ב-Tinkercad פתח `Serial Monitor`.
5. לחץ `Start Simulation`.

כעת שינוי ה-Ultrasonic אמור לעדכן את ThingsBoard אוטומטית.

## סדר הפעלה מקוצר

```text
2_start_chrome_gateway.bat
→ python tinkercad_bridge.py
→ Serial Monitor
→ Start Simulation
```

## במקרה של שגיאה

### could not connect to Google Chrome

ודא שהפעלת קודם את:

```text
2_start_chrome_gateway.bat
```

### Address already in use / port 9222

סגור את חלון Chrome של ה-Gateway והפעל מחדש את הקובץ.

### waiting for the Tinkercad Serial Monitor

פתח ידנית את `Serial Monitor` בתוך הפרויקט.

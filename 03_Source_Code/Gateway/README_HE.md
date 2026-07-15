# Smart Parking Gateway

קורא את ה-Serial Monitor של Tinkercad מתוך Chrome, שולח טלמטריה ל-ThingsBoard ומקבל ממנו פקודות RPC לפתיחה וסגירה של השער.

ההתחברות ל-Google נעשית ידנית פעם אחת, ולא מתוך Playwright.

## התקנה

מתוך `03_Source_Code/Gateway`:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

אין צורך ב-`playwright install chromium`, כי ה-Gateway מתחבר ל-Chrome המותקן במחשב.

## הגדרות

```bash
cp .env.example .env
```

| משתנה | חובה | ברירת מחדל |
| --- | --- | --- |
| `TB_TOKEN` | כן | — |
| `TINKERCAD_URL` | מומלץ | דף הבית של Tinkercad |
| `TB_HOST` | לא | `https://eu.thingsboard.cloud` |
| `BROWSER_CDP_URL` | לא | `http://127.0.0.1:9222` |

## התחברות חד-פעמית

הרץ את `1_login_chrome.bat`, התחבר ל-Tinkercad דרך Google, ודא שהפרויקט נפתח, וסגור את חלונות ה-Chrome.

הפרופיל נשמר ב-`.chrome_gateway_profile/`. אל תעלה אותו ל-Git ואל תשלח אותו לאחרים.

## הפעלה

1. הרץ את `2_start_chrome_gateway.bat` והמתן שייפתח Chrome.
2. מתוך `03_Source_Code/Gateway`:

```bash
source .venv/Scripts/activate
python tinkercad_bridge.py
```

3. ב-Tinkercad פתח `Serial Monitor` ולחץ `Start Simulation`.

שינוי ה-Ultrasonic אמור לעדכן את ThingsBoard אוטומטית.

## מבנה הקוד

| קובץ | תפקיד |
| --- | --- |
| `tinkercad_bridge.py` | נקודת כניסה |
| `bridge.py` | הלולאה הראשית |
| `tinkercad_page.py` | איתור ה-Serial Monitor והקלדת פקודות אליו |
| `thingsboard.py` | שליחת טלמטריה וקבלת פקודות RPC |
| `telemetry.py` | פענוח ובדיקה של ה-JSON שה-Arduino מדפיס |
| `config.py` | קריאת `.env` |

## תקלות

| הודעה | פתרון |
| --- | --- |
| `could not connect to Google Chrome` | הרץ קודם את `2_start_chrome_gateway.bat` |
| `Address already in use / port 9222` | סגור את חלון ה-Chrome של ה-Gateway והרץ אותו מחדש |
| `waiting for the Tinkercad Serial Monitor` | פתח ידנית `Serial Monitor` בתוך הפרויקט |

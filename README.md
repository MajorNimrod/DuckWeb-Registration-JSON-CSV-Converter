# DuckWeb Registration JSON → CSV Converter

This tool converts the **DuckWeb weekly registration JSON** (the data behind your schedule) into a clean, Excel/Google Sheets–ready **CSV schedule** — with:

* One row per course (grouped by CRN)
* Clean titles
* Filtered exam / special long blocks
* Human‑readable meeting times

No JavaScript knowledge required. Users only need to **download one file from their browser** and run **one Python command**.

**NOTE: I created this for the purpose of club member and staff schedule management for the game dev UO club. I am not making any money off of this. I am not modifying any data on the registration page, and this is all accessed through DevOps. If the company who made the tool or the school wants to take this down, please send me an email.**

---

## What This Produces

A CSV like:

| Term   | CRN   | Subject | Course | Title                 | Meetings                                    |
| ------ | ----- | ------- | ------ | --------------------- | ------------------------------------------- |
| 202501 | 11587 | CS      | 314    | Computer Organization | Mon 1:00–1:50; Wed 1:00–1:50; Fri 1:00–1:50 |

Ready for:

* Excel
* Google Sheets
* Notion
* Calendar imports

---

## Requirements

* Python **3.9+**
* Any browser (Chrome, Edge, Firefox)

Check your Python version:

```bash
python --version
```

---

## Step 1 — Download Your Registration Data (NO Console Required)

1. Log into **DuckWeb**
2. Open your **Weekly Schedule / Registration** page
3. Press **F12** → click the **Network** tab
4. Refresh the page
5. In the Network list:

   * Click the filter **Fetch/XHR**
   * Click the request that returns JSON with fields like:
     `crn`, `subject`, `courseNumber`, `start`, `end`
6. Right‑click that request → **Save all as HAR with content**
7. Save it as:

```text
schedule.har
```
*or something similar*

This file contains your full registration data.

---

## Step 2 — Run the Python Converter

Place these in the same folder:

* `schedule_to_csv.py`
* `schedule.har` (or `schedule.json` if you copied raw JSON)

Run:

```bash
python schedule_to_csv.py schedule.har
```
*If it doesn't recognize the file, make sure to change 'schedule.har' to the name of the .har file.*

Output:

```text
schedule.csv
```

You can also choose a name:

```bash
python schedule_to_csv.py schedule.har -o winter_schedule.csv
```

---

## Step 3 — Open the CSV

Open `schedule.csv` with:

* Excel
* Google Sheets → File → Import → Upload
* Numbers (Mac)

Everything will already be in clean columns.

---

## Advanced Options

Inside `schedule_to_csv.py`:

```python
MAX_DURATION_MINUTES = 119
```

* Lower it to remove 90‑minute+ blocks
* Raise it if you WANT to keep exam periods

Title cleaning:

* `+ Dis` → `SUBJECT ### Discussion`
* `+ Lab` → `SUBJECT ### Lab`
* Prevents Excel formula bugs

---

## Common Issues

### “Excel shows `=+Dis` as a formula”
### fixed double opening file explorer on import
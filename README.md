# Lesson Project (منصة الدروس)

Quick steps to run on Windows (PowerShell). If `python` or `py` is not recognized, install Python and add it to PATH or use the Python installer option "Add to PATH".

1. Create virtual env and activate (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python app.py
```

4. Open http://127.0.0.1:5000 in your browser.

Notes about Python on Windows:
- If `python` is not found, install Python from https://www.python.org/downloads/windows/ and check "Add Python to PATH".
- Alternatively, find the full path to `python.exe` and use it instead of `python` in the commands above.

Default seeded admin account: email `admin@local` password `admin123` (change after first login).

---

Safety & production notes
- The app currently uses a default development secret when `LESSONS_SECRET` is not set. Set the environment variable `LESSONS_SECRET` in production to a strong secret before running.
- The Flask dev server runs with `debug=True` in `app.py` for convenience during development. Do NOT use this in production.
- Recommended simple production setup on Windows: install `waitress` and run the app with a production WSGI server. Example:

```powershell
pip install waitress
# If you prefer to keep app.py as-is, run via:
waitress-serve --port=8000 app:app
```

If you want me to add a proper `create_app()` factory and a `run_prod.ps1` script to ease production deployments, tell me and I'll add them (I will not commit without your approval).

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

## Render database persistence

The app defaults to `lessons.db` beside `app.py` for local development. Set
`DATABASE_PATH` to use another SQLite file; the app creates the parent folder
and, when the destination does not already exist, copies the existing local
database there without deleting or modifying the source. On Render, use
`DATABASE_PATH=/data/lessons.db` with a persistent disk mounted at `/data`.

This repository does not contain a Render Blueprint, so attaching a disk to
the existing service must be done in the Render dashboard:

1. Open the existing service in the Render dashboard and make a separate
   backup of its current `/app/lessons.db` before changing the service. Keep
   that backup outside the service (for example, download it using the
   service's Shell/SSH access). Do not continue if the existing database
   cannot be located or backed up.
2. Open the service's **Disks** page and choose **Add Disk**. Set a name (for
   example, `lessons-data`), mount path `/data`, and a size of at least 1 GB,
   then save. Render requires a paid service plan for persistent disks and
   will deploy the service after the disk is added.
3. If `/app/lessons.db` is still available after the disk deployment, the app
   will copy it to `/data/lessons.db` on startup when `DATABASE_PATH` is set
   and the destination does not exist. If the old file is missing, restore
   the backup from step 1 to `/data/lessons.db` using the service's Shell/SSH
   access before proceeding.
4. Open the service's **Environment** page and add `DATABASE_PATH` with value
   `/data/lessons.db`. Save and wait for the restart and deployment to become
   Live. If neither the old database nor a restored backup is available,
   startup stops with an error instead of creating a new database or seeding
   over missing data.

An ephemeral database that is already gone cannot be recovered from this
repository. Restore an available backup before setting `DATABASE_PATH`; do
not allow the service to start against an empty replacement database.

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

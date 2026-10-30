# GramaSathi Admin Dashboard — Flask + SQLite

This project connects the supplied `admindashboard.html` interface to a Python Flask backend and a local SQLite database.

## Features wired to the backend
- Dashboard counts and recent complaints
- Complaint list, filters, assigned officer, status and admin remarks
- User list, add user, block/unblock user
- Service list, add and edit services, activate/deactivate
- Notifications, mark read, mark all read, delete
- Admin profile saved in SQLite
- Activity log of admin actions

## Run on Windows
1. Install Python 3.10 or newer.
2. Extract this project folder.
3. Open Command Prompt in the `gramasathi_flask` folder.
4. Run:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
5. Open `http://127.0.0.1:5000` in your browser.

## Run on Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

The SQLite database `gramasathi.db` is created automatically on first run with a few sample records matching the supplied dashboard. Changes persist across restarts.

## Important
- This is a local development/demo project, not a production-secured deployment. Add authentication/authorization, CSRF protection, input validation, HTTPS and deployment configuration before exposing it to the internet.
- The existing dashboard's logout button still redirects to `login.html`; a login backend/page was not included in the supplied file.
- The profile picture and dark-mode preference still use browser local storage; the profile fields are stored in SQLite.

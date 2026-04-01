# Carpet Cleaning CRM

A working local Flask CRM for a carpet cleaning business.

## Included

- Dashboard
- Customers
- Jobs
- Quotes
- Invoices
- Printable quote view
- Printable invoice view
- Business settings
- SQLite database created automatically

## Run it in PowerShell

Open PowerShell in this folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

Then open:

```powershell
http://127.0.0.1:5000
```

## Notes

- The database file is `crm.db`
- The app creates the database automatically on first run
- Change the secret key in `app.py` before using this in a real environment
- This is designed as a strong working local foundation that can be expanded with PDF export, calendar sync, SMS, email templates, review links, and customer history

## Next upgrades

- PDF download instead of print only views
- Logo upload
- Customer history timeline
- SMS reminders
- Google Calendar sync
- Email templates and sending
- Recurring jobs
- Dashboard charts

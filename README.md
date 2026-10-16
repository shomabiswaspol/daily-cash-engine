# Daily Cash Transaction Engine

This repository contains a minimal scaffold for the Daily Cash Transaction Engine:
- FastAPI backend (backend/)
- React frontend scaffold (frontend/)
- DB migrations for Postgres (db/migrations/001_create_daily_cash_tables.sql)

Behavior notes
- "Cash Payment" is the primary cash account type the app records.
- Messages without an employee mobile are ignored (name-only messages are ignored).
- A WhatsApp message will only be considered for processing if BOTH:
  * It looks like a cash payment intent (amount, bkash/nagad/cash keywords)
  * The sender is the owner and the message appears to be addressed to the accountant number

See backend/README.md and frontend/README.md for development instructions.

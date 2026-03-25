# Form 230 Generator Web App

This is a Flask web application that helps gather user details to auto-generate the Romanian Form 230 ("Formular 230", used for redirecting up to 3.5% of income tax to an NGO).

## Features
- Collects personal data (Name, CNP, Address, Contact).
- Generates a valid Form 230 PDF by overlaying user data strictly on the designated `template.pdf` layout.
- Provides a bilingual interface (Romanian and English) with a modern toggle.
- Cloudflare Turnstile integration to stop spam.
- Simple admin panel for managing configured details, signatures, and to safely approve/generate PDFs.

## Setup and Installation

1. Prepare your Python environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Environment Configuration
Update your secret keys inside `app.py`, change `TURNSTILE_SECRET_KEY` if needed. Ensure `template.pdf` is present in the main directory. 

3. Start Server:
```bash
flask run
```

4. Go to `http://localhost:5000`. Login details (default test account inside `app.py`):

## Architecture 
- **app.py**: Core logic handling Routes, DB layout using SQLAlchemy, and precise text-coords drawing to map over the existing form layout in ReportLab.
- **template.pdf**: Needs to be maintained untouched as it functions as the base canvas for the generator.
- **generated_forms/**: All completed/approved PDFs are saved here. 

## Clean Ups Made
- Removed the old `java/` folder containing standalone (`.jar`) validators/PDF apps, as `app.py` now implements its own Python-native PDF writing integration via `reportlab` & `PyPDF2`; the external Java dependencies are entirely unused.
- Updated language translations across the site.
- Integrated a new pill-shaped design language switcher.

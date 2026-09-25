# Solar Documents Generator

A small local web app for RAYANI AGENCIES: fill in a customer's name, address/city and
electricity consumer number, and download a **Quotation** and a **Vendor Agreement** as
PDFs that look exactly like the original Word documents (same logo, colours, fonts and
layout) — only those four fields change, and the date is always filled in as today.

```
solar_document_generator/
├── server.py                    ← backend (Flask)
├── static/
│   ├── index.html               ← frontend
│   ├── styles.css
│   └── app.js
├── templates/
│   ├── vendor_agreement.doc     ← your original template (with {NAME} {ADDRESS} {BILL} {DATE} tags)
│   └── quotation.doc            ← your original template (with {NAME} {CITY} {DATE} tags)
├── examples/
│   ├── Vendor_Agreement_SAMPLE.pdf
│   └── Quotation_SAMPLE.pdf
├── requirements.txt
├── start.bat                    ← Windows start
├── start.sh                     ← macOS / Linux start
└── README.md
```

## How it works

1. The two files in `templates/` are your original Word documents, saved in modern
   Word format (`.docx`/OOXML) but kept with a `.doc` name to match this project's
   layout — they open fine in Word or LibreOffice. Everywhere the customer's name,
   address, city, consumer number and date used to be, there is now a placeholder
   tag: `{NAME}`, `{ADDRESS}`, `{CITY}`, `{BILL}`, `{DATE}`.
2. When you submit the form, `server.py` copies the right template, replaces those
   tags with what you typed (and today's date), and calls **LibreOffice** in
   headless mode to convert the filled document straight to PDF.
3. Because the conversion starts from the real Word document, the PDF keeps the
   exact original look — nothing is redrawn or approximated.

## Requirements

- **Python 3.9+**
- **LibreOffice** installed, with the `soffice` command available:
  - Windows: install from https://www.libreoffice.org/ (the default install path is
    already checked by `server.py`).
  - macOS: install LibreOffice.app (also auto-detected).
  - Linux: `sudo apt install libreoffice` (or your distro's equivalent).

## Running it

**Windows:** double-click `start.bat` (or run it from a command prompt).

**macOS / Linux:**
```bash
chmod +x start.sh   # first time only
./start.sh
```

Either script creates a virtual environment, installs Flask, and starts the server.
Then open **http://localhost:5000** in your browser.

## Using it

1. Enter the customer's **name**.
2. Enter the **full address** (used in the Vendor Agreement) and the **city** (used
   in the Quotation — the original quotation only ever showed the city).
3. Enter the 13-digit **electricity consumer number** (validated live).
4. Click **Download Quotation** or **Download Agreement** — the PDF is generated on
   the fly and downloaded straight to your computer.

The date is never typed in manually; both documents always use today's date,
formatted the way each original document used it (`25-09-2026` for the quotation,
`25-SEP-2026` for the agreement).

## Editing the templates

If you ever need to change the wording, pricing table, or letterhead, open the file
in `templates/` with Word or LibreOffice, edit it like any normal document, and save
it back over the same file — just make sure the five placeholder tags
(`{NAME}`, `{ADDRESS}`, `{CITY}`, `{BILL}`, `{DATE}`) stay in the document, spelled
exactly like that, wherever you want that value to appear.

## Troubleshooting

- **"LibreOffice was not found"** — install LibreOffice and make sure `soffice` is on
  your PATH, or edit the `candidates` list near the top of `server.py` to point at
  your installation.
- **Port 5000 already in use** — set a different port before starting, e.g.
  `PORT=5001 python server.py` (macOS/Linux) or `set PORT=5001 && python server.py`
  (Windows).

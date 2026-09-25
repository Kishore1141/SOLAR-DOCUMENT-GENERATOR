"""
Solar Documents Generator - backend server.

Fills the two Word templates in templates/ (quotation.doc and vendor_agreement.doc -
these are saved in modern .docx/OOXML format so they can be edited directly, but keep
the .doc name to match the requested project layout) with the customer's details,
then converts the result to PDF using LibreOffice (soffice) so the output keeps the
exact original look: logo, colours, fonts and layout.

Run with:  python server.py
Then open: http://localhost:5000
"""

import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, Response

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, static_folder=None)

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def today_dates():
    """Returns (quotation_date, agreement_date) as strings, always today's date."""
    now = datetime.date.today()
    quote_date = now.strftime("%d-%m-%Y")                      # e.g. 25-09-2026
    agreement_date = f"{now.day:02d}-{MONTHS[now.month - 1]}-{now.year}"  # e.g. 25-SEP-2026
    return quote_date, agreement_date


def escape_xml(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def fill_docx_template(template_path: Path, output_path: Path, replacements: dict):
    """
    Replace {PLACEHOLDER} tokens inside word/document.xml of a .docx (OOXML) file.
    The template files already have each placeholder sitting inside a single
    contiguous text run, so a plain string replace is safe and keeps every other
    part of the original document (logo, fonts, table, colours) untouched.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="solardoc_"))
    try:
        with zipfile.ZipFile(template_path, "r") as zin:
            zin.extractall(tmp_dir)

        doc_xml_path = tmp_dir / "word" / "document.xml"
        xml = doc_xml_path.read_text(encoding="utf-8")
        for key, value in replacements.items():
            xml = xml.replace("{%s}" % key, escape_xml(value))
        doc_xml_path.write_text(xml, encoding="utf-8")

        if output_path.exists():
            output_path.unlink()
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for root, _dirs, files in os.walk(tmp_dir):
                for f in files:
                    full = Path(root) / f
                    zout.write(full, full.relative_to(tmp_dir))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def find_soffice():
    """Locate the LibreOffice command-line binary across platforms."""
    candidates = [
        "soffice", "soffice.bin",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        path = shutil.which(c) if os.sep not in c else (c if Path(c).exists() else None)
        if path:
            return path
    return None


def convert_to_pdf(docx_path: Path, out_dir: Path) -> Path:
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice was not found. Please install LibreOffice and make sure "
            "'soffice' is on your PATH (see README.md)."
        )
    subprocess.run(
        [soffice, "--headless", "--norestore", "--convert-to", "pdf",
         "--outdir", str(out_dir), str(docx_path)],
        check=True, timeout=90,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    pdf_path = out_dir / (docx_path.stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError("PDF conversion did not produce an output file.")
    return pdf_path


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return cleaned or "customer"


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True, silent=True) or {}
    doc_type = data.get("docType")
    name = (data.get("name") or "").strip().upper()
    city = (data.get("city") or "").strip().upper()
    address = (data.get("address") or "").strip()
    bill = (data.get("bill") or "").strip()

    if not name:
        return jsonify({"error": "Customer name is required."}), 400

    quote_date, agreement_date = today_dates()
    work_dir = Path(tempfile.mkdtemp(prefix="solardoc_out_"))

    try:
        if doc_type == "quotation":
            if not city:
                return jsonify({"error": "City is required for the quotation."}), 400
            template = TEMPLATES_DIR / "quotation.doc"
            filled = work_dir / "quotation_filled.docx"
            fill_docx_template(template, filled, {
                "NAME": name, "CITY": city, "DATE": quote_date,
            })
            filename = f"Quotation-{safe_filename(name)}.pdf"

        elif doc_type == "agreement":
            if not address:
                return jsonify({"error": "Address is required for the agreement."}), 400
            if not re.fullmatch(r"\d{13}", bill):
                return jsonify({"error": "Electricity consumer number must be exactly 13 digits."}), 400
            template = TEMPLATES_DIR / "vendor_agreement.doc"
            filled = work_dir / "agreement_filled.docx"
            fill_docx_template(template, filled, {
                "NAME": name, "ADDRESS": address, "BILL": bill, "DATE": agreement_date,
            })
            filename = f"Vendor-Agreement-{safe_filename(name)}.pdf"

        else:
            return jsonify({"error": "Unknown document type."}), 400

        pdf_path = convert_to_pdf(filled, work_dir)
        pdf_bytes = pdf_path.read_bytes()

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "PDF conversion failed: " + e.stderr.decode(errors="ignore")[:500]}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "PDF conversion timed out."}), 500
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Solar Documents Generator running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

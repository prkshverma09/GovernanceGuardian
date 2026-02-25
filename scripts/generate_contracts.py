"""
Generate sample contract PDFs for Governance Guardian testing.
Uses PyMuPDF (fitz) so no extra dependency beyond ingest_contracts.py.
"""
import os
import fitz  # PyMuPDF

CONTRACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contracts")

# Sample contracts with compliance-relevant clauses (paragraphs for chunking)
CONTRACTS = [
    {
        "filename": "NDA_Partner_A.pdf",
        "title": "Non-Disclosure and Data Use Agreement - Partner A",
        "paragraphs": [
            "Non-Disclosure of PII. The Receiving Party shall not disclose, reveal, or otherwise make available any Personally Identifiable Information (PII) of the Disclosing Party's customers to any third party without express written consent.",
            "Marketing to Minors. The Receiving Party is strictly prohibited from using any dataset containing records of individuals under the age of eighteen (18) for marketing, promotional, or advertising purposes.",
            "Data Locality. Any data processing activities involving citizens of the European Union must comply with GDPR regulations. Storage in restricted zones is strictly prohibited.",
        ],
    },
    {
        "filename": "MSA_General_Compliance.pdf",
        "title": "Master Service Agreement - General Compliance Policy",
        "paragraphs": [
            "General Privacy Policy. All parties must ensure that data usage is limited to the specific purpose defined in the Work Order. Bulk emailing of customer lists is allowed only if the list has been scrubbed of opt-out records and minors.",
            "Definition of Minors. For the purposes of this agreement, a 'minor' is defined as any natural person under the age of 18 years old.",
            "Restricted Regions. No data originating from or involving residents of 'GDPR_Restricted_Zone' may be used for automated campaign targeting without enhanced legal review.",
        ],
    },
    {
        "filename": "DPA_Standard_v1.pdf",
        "title": "Data Processing Addendum (DPA) - Standard Version 1",
        "paragraphs": [
            "Processing Limits. The Processor shall only process personal data upon documented instructions from the Controller. Using the 'customer_leads_prod' dataset for email targeting requires prior verification of age and region compliance.",
            "Forbidden Fields. The Processor shall not collect or process sensitive data fields such as Social Security Numbers (SSN), medical history, or precise geolocation without explicit authorization.",
        ],
    },
]


def text_to_pdf(path: str, title: str, paragraphs: list[str]) -> None:
    """Write a simple PDF with title and paragraphs using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    margin = 50
    y = margin
    line_height = 14

    # Title
    page.insert_text((margin, y), title, fontsize=14, fontname="helv")
    y += line_height * 2

    for para in paragraphs:
        # Use textbox for long text / word wrap
        rect = fitz.Rect(margin, y, page.rect.width - margin, page.rect.height - margin)
        y = page.insert_textbox(rect, para, fontsize=11, fontname="helv")
        if y == fitz.TEXT_OVERFLOW:
            page = doc.new_page(width=595, height=842)
            rect = fitz.Rect(margin, margin, page.rect.width - margin, page.rect.height - margin)
            y = page.insert_textbox(rect, para, fontsize=11, fontname="helv")
        y += line_height

    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    doc.close()


def generate_all_contracts() -> None:
    os.makedirs(CONTRACTS_DIR, exist_ok=True)
    for c in CONTRACTS:
        path = os.path.join(CONTRACTS_DIR, c["filename"])
        text_to_pdf(path, c["title"], c["paragraphs"])
        print(f"Generated {c['filename']}")
    print(f"Done. {len(CONTRACTS)} contract PDFs in {CONTRACTS_DIR}")


if __name__ == "__main__":
    generate_all_contracts()

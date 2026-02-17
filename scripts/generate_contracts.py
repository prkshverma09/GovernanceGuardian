import os
from fpdf import FPDF

def create_contract_pdf(filename, title, clauses):
    """
    Generates a PDF contract with specific compliance clauses.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(190, 10, title, ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("helvetica", size=12)
    for i, (clause_title, content) in enumerate(clauses):
        pdf.set_font("helvetica", "B", 12)
        pdf.multi_cell(190, 10, f"{i+1}. {clause_title}")
        pdf.set_font("helvetica", size=12)
        pdf.multi_cell(190, 10, content)
        pdf.ln(5)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    pdf.output(filename)

def generate_all_contracts():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    contracts_dir = os.path.join(base_dir, "data", "contracts")

    # Contract 1: NDA Partner A (Referenced in PRD)
    create_contract_pdf(
        os.path.join(contracts_dir, "NDA_Partner_A.pdf"),
        "Non-Disclosure and Data Use Agreement - Partner A",
        [
            ("Non-Disclosure of PII", "The Receiving Party shall not disclose, reveal, or otherwise make available any Personally Identifiable Information (PII) of the Disclosing Party's customers to any third party without express written consent."),
            ("Marketing to Minors", "The Receiving Party is strictly prohibited from using any dataset containing records of individuals under the age of eighteen (18) for marketing, promotional, or advertising purposes."),
            ("Data Locality", "Any data processing activities involving citizens of the European Union must comply with GDPR regulations. Storage in restricted zones is strictly prohibited.")
        ]
    )

    # Contract 2: Master Service Agreement (General Policy)
    create_contract_pdf(
        os.path.join(contracts_dir, "MSA_General_Compliance.pdf"),
        "Master Service Agreement - General Compliance Policy",
        [
            ("General Privacy Policy", "All parties must ensure that data usage is limited to the specific purpose defined in the Work Order. Bulk emailing of customer lists is allowed only if the list has been scrubbed of opt-out records and minors."),
            ("Definition of Minors", "For the purposes of this agreement, a 'minor' is defined as any natural person under the age of 18 years old."),
            ("Restricted Regions", "No data originating from or involving residents of 'GDPR_Restricted_Zone' may be used for automated campaign targeting without enhanced legal review.")
        ]
    )

    # Contract 3: Data Processing Addendum
    create_contract_pdf(
        os.path.join(contracts_dir, "DPA_Standard_v1.pdf"),
        "Data Processing Addendum (DPA) - Standard Version 1",
        [
            ("Processing Limits", "The Processor shall only process personal data upon documented instructions from the Controller. Using the 'customer_leads_prod' dataset for email targeting requires prior verification of age and region compliance."),
            ("Forbidden Fields", "The Processor shall not collect or process sensitive data fields such as Social Security Numbers (SSN), medical history, or precise geolocation without explicit authorization.")
        ]
    )

    print(f"Generated 3 contract PDFs in {contracts_dir}")

if __name__ == "__main__":
    generate_all_contracts()

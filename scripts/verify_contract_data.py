"""
Verify contract test data without Elasticsearch.
Run from project root: python scripts/verify_contract_data.py
"""
import os
import glob
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
CONTRACTS_DIR = os.path.join(PROJECT_ROOT, "data", "contracts")


def main():
    if not os.path.isdir(CONTRACTS_DIR):
        print(f"Missing directory: {CONTRACTS_DIR}")
        sys.exit(1)

    txt_files = sorted(glob.glob(os.path.join(CONTRACTS_DIR, "*.txt")))
    pdf_files = sorted(glob.glob(os.path.join(CONTRACTS_DIR, "*.pdf")))

    if not txt_files and not pdf_files:
        print(f"No .txt or .pdf files in {CONTRACTS_DIR}")
        sys.exit(1)

    from scripts.chunker import chunk_text

    total_chunks = 0
    for path in txt_files:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = chunk_text(text)
        total_chunks += len(chunks)
        print(f"  {os.path.basename(path)}: {len(chunks)} chunks")

    for path in pdf_files:
        try:
            import fitz
            doc = fitz.open(path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
        except Exception as e:
            print(f"  {os.path.basename(path)}: skip ({e})")
            continue
        chunks = chunk_text(text)
        total_chunks += len(chunks)
        print(f"  {os.path.basename(path)}: {len(chunks)} chunks")

    print(f"Total: {len(txt_files) + len(pdf_files)} file(s), {total_chunks} chunks — ready for ingest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

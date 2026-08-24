"""Convert a NewVision BrowserView "Print Results" page (saved as text) into
a standard pipeline CSV. Stdlib only.

The print view is tab-delimited after a short preamble. Each DOCUMENT appears
once per party: rows whose first field is '*' are the From/plaintiff side,
unmarked rows are the To/defendant side (the leads). This script merges them
into one row per document with the standard column names the pipeline
already understands (so county csvColumns stay default), plus AllDefendants.

Status: 'V' (and 'B') are verified; anything else maps to the provisional
flag column 'U'.

Usage: python newvision_tsv_to_csv.py <print.txt> <out.csv>
"""
import csv
import sys

HEADER_MARKER = "Name\tDate\tType\tBook\tPage\tLegal\tFile#"
OUT_COLUMNS = ["U", "DirectName", "IndirectName", "AllDefendants", "RecordDate",
               "DocTypeDescription", "BookType", "BookPage", "InstrumentNumber",
               "Consideration", "DocLegalDescription", "Comments", "CaseNumber"]


def newvision_tsv_to_csv(tsv_path, csv_path):
    with open(tsv_path, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()

    start = next((i for i, l in enumerate(lines) if HEADER_MARKER in l), None)
    if start is None:
        raise SystemExit("not a NewVision print view (header row not found): " + tsv_path)

    docs = {}
    order = []
    for line in lines[start + 1:]:
        parts = line.split("\t")
        if len(parts) < 9 or not parts[7].strip():
            continue
        star, name, date, dtype, book, page, legal, file_num, status = \
            (p.strip() for p in parts[:9])
        doc = docs.get(file_num)
        if doc is None:
            doc = docs[file_num] = {
                "RecordDate": date, "DocTypeDescription": dtype,
                "BookType": "", "BookPage": f"{book}/{page}",
                "InstrumentNumber": file_num, "Consideration": "",
                "DocLegalDescription": legal, "Comments": "", "CaseNumber": "",
                "U": "" if status.upper() in ("V", "B") else "U",
                "DirectName": "", "IndirectName": "", "_defendants": [],
            }
            order.append(file_num)
        if star == "*":
            if not doc["DirectName"]:
                doc["DirectName"] = name
        else:
            doc["_defendants"].append(name)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        writer.writeheader()
        for file_num in order:
            doc = docs[file_num]
            defendants = doc.pop("_defendants")
            doc["IndirectName"] = defendants[0] if defendants else ""
            doc["AllDefendants"] = "; ".join(defendants)
            writer.writerow(doc)
    return csv_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    newvision_tsv_to_csv(sys.argv[1], sys.argv[2])
    print("wrote", sys.argv[2])

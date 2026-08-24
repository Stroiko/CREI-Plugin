"""Convert a Tyler Self-Service "Export as CSV" file (SearchResults.CSV) into
a standard pipeline CSV. Stdlib only.

Tyler SS quirks handled:
- line 1 is a search-description preamble; the real header is line 2
  (Document #, Description, Recording Date, Grantor, Grantee, Legal)
- Grantor/Grantee are comma-joined lists inside one cell; Grantees are the
  defendants (the leads)

Usage: python tylerss_csv_to_csv.py <SearchResults.CSV> <out.csv>
"""
import csv
import sys

OUT_COLUMNS = ["U", "DirectName", "IndirectName", "AllDefendants", "RecordDate",
               "DocTypeDescription", "BookType", "BookPage", "InstrumentNumber",
               "Consideration", "DocLegalDescription", "Comments", "CaseNumber"]


def _split_names(cell):
    return [n.strip() for n in (cell or "").split(",") if n.strip()]


def tylerss_csv_to_csv(src_path, csv_path):
    with open(src_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    header_idx = next((i for i, r in enumerate(rows)
                       if r and r[0].strip() == "Document #"), None)
    if header_idx is None:
        raise SystemExit("not a Tyler Self-Service export (no 'Document #' header): " + src_path)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        writer.writeheader()
        for r in rows[header_idx + 1:]:
            if len(r) < 6 or not r[0].strip():
                continue
            doc_num, description, rec_date, grantor, grantee, legal = (c.strip() for c in r[:6])
            plaintiffs = _split_names(grantor)
            defendants = _split_names(grantee)
            writer.writerow({
                "U": "", "DirectName": plaintiffs[0] if plaintiffs else "",
                "IndirectName": defendants[0] if defendants else "",
                "AllDefendants": "; ".join(defendants),
                "RecordDate": rec_date, "DocTypeDescription": description,
                "BookType": "", "BookPage": "", "InstrumentNumber": doc_num,
                "Consideration": "", "DocLegalDescription": legal,
                "Comments": "", "CaseNumber": "",
            })
    return csv_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    tylerss_csv_to_csv(sys.argv[1], sys.argv[2])
    print("wrote", sys.argv[2])

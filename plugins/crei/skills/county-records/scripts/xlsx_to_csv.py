"""Convert a Landmark Web export (.xlsx) to CSV using only the stdlib.

Landmark quirks handled:
- duplicate header names (two Location / DocLinks columns) -> suffixed _2, _3...
- structured legal cells prefixed "legalfield_" -> prefix stripped
- values may be shared strings, inline strings, or numbers

Usage: python xlsx_to_csv.py <in.xlsx> <out.csv>
"""
import csv
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _cell_text(cell, shared):
    t = cell.get("t")
    if t == "s":
        v = cell.find(M + "v")
        return shared[int(v.text)] if v is not None else ""
    if t == "inlineStr":
        return "".join(el.text or "" for el in cell.iter(M + "t"))
    v = cell.find(M + "v")
    return v.text if v is not None and v.text is not None else ""


def _rows(xlsx_path):
    with zipfile.ZipFile(xlsx_path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(M + "si"):
                shared.append("".join(el.text or "" for el in si.iter(M + "t")))
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        for row in sheet.iter(M + "row"):
            out = {}
            for cell in row.findall(M + "c"):
                out[_col_index(cell.get("r", "A1"))] = _cell_text(cell, shared)
            yield out


def xlsx_to_csv(xlsx_path, csv_path):
    rows = list(_rows(xlsx_path))
    if not rows:
        raise SystemExit("empty workbook: " + xlsx_path)

    width = max(max(r) for r in rows if r) + 1
    header_raw = [rows[0].get(i, "").strip() for i in range(width)]
    seen, headers = {}, []
    for name in header_raw:
        name = name or "col"
        seen[name] = seen.get(name, 0) + 1
        headers.append(name if seen[name] == 1 else f"{name}_{seen[name]}")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows[1:]:
            writer.writerow([re.sub(r"^legalfield_", "", r.get(i, ""))
                             for i in range(width)])
    return csv_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    xlsx_to_csv(sys.argv[1], sys.argv[2])
    print("wrote", sys.argv[2])

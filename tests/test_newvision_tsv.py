"""NewVision Print-Results TSV converter tests. Fixture mirrors the real Polk
print-view text (preamble lines, tab-delimited, '*' marks the From/plaintiff
party, same File# repeats across party rows); values synthetic."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from newvision_tsv_to_csv import newvision_tsv_to_csv

FIXTURE = "\n".join([
    "Some Clerk, CPA",
    "Document Type: LP,L PEN From: 8/14/2026 To: 8/20/2026",
    "Total Number of Records: 5",
    "\tName\tDate\tType\tBook\tPage\tLegal\tFile#\tStatus\tFlag",
    "*\tBIG BANK NA\t08/14/2026\tLP\t14116\t2049\tMADISON PLACE PHASE 2 LT 243\t2026196971\tV\t",
    "\tDOE JOHN\t08/14/2026\tLP\t14116\t2049\tMADISON PLACE PHASE 2 LT 243\t2026196971\tV\t",
    "\tDOE JANE\t08/14/2026\tLP\t14116\t2049\tMADISON PLACE PHASE 2 LT 243\t2026196971\tV\t",
    "*\tSOME HOA INC\t08/19/2026\tLP\t14121\t898\tHAMMOCK RESERVE PHASE 1 LT 142\t2026200879\tR\t",
    "\tROE RICHARD\t08/19/2026\tLP\t14121\t898\tHAMMOCK RESERVE PHASE 1 LT 142\t2026200879\tR\t",
])


def convert(tmp_path):
    src = tmp_path / "print.tsv"
    src.write_text(FIXTURE, encoding="utf-8")
    dst = tmp_path / "out.csv"
    newvision_tsv_to_csv(str(src), str(dst))
    with open(dst, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_one_row_per_document(tmp_path):
    rows = convert(tmp_path)
    assert len(rows) == 2
    assert {r["InstrumentNumber"] for r in rows} == {"2026196971", "2026200879"}


def test_party_roles_split(tmp_path):
    rows = convert(tmp_path)
    doc = next(r for r in rows if r["InstrumentNumber"] == "2026196971")
    assert doc["DirectName"] == "BIG BANK NA"
    assert doc["IndirectName"] == "DOE JOHN"
    assert doc["AllDefendants"] == "DOE JOHN; DOE JANE"


def test_fields_carried(tmp_path):
    rows = convert(tmp_path)
    doc = next(r for r in rows if r["InstrumentNumber"] == "2026196971")
    assert doc["RecordDate"] == "08/14/2026"
    assert doc["DocTypeDescription"] == "LP"
    assert doc["DocLegalDescription"] == "MADISON PLACE PHASE 2 LT 243"


def test_status_v_not_provisional(tmp_path):
    rows = convert(tmp_path)
    byid = {r["InstrumentNumber"]: r for r in rows}
    assert byid["2026196971"]["U"] == ""
    assert byid["2026200879"]["U"] == "U"

"""Tyler Self-Service CSV converter tests. Shape mirrors the real Orange
export (preamble line, quoted CSV, comma-joined party lists); values
synthetic."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from tylerss_csv_to_csv import tylerss_csv_to_csv

FIXTURE = "\n".join([
    '"Advanced Document Search  Recording Date is between Aug 14, 2026 and Aug 20, 2026 and Document types in Lis Pendens"',
    '"Document #","Description","Recording Date","Grantor","Grantee","Legal"',
    '"20260466476","Lis Pendens","08/20/2026 02:48 PM","BIG BANK NA","DOE JESSICA, DOE MARCELO, SECRETARY OF HOUSING AND URBAN DEVELOPMENT","Lot: 76    SOME CREEK TRACT 550"',
    '"20260465821","Lis Pendens","08/20/2026 12:30 PM","OTHER BANK NA, SOME TRUST 2024","ROE RONNIE, SOME INVESTMENTS LLC","Lot: 2 Block: C    SOME PINE HILLS"',
])


def convert(tmp_path):
    src = tmp_path / "SearchResults.CSV"
    src.write_text(FIXTURE, encoding="utf-8")
    dst = tmp_path / "out.csv"
    tylerss_csv_to_csv(str(src), str(dst))
    with open(dst, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_preamble_skipped_one_row_per_doc(tmp_path):
    rows = convert(tmp_path)
    assert len(rows) == 2
    assert rows[0]["InstrumentNumber"] == "20260466476"


def test_parties_mapped(tmp_path):
    rows = convert(tmp_path)
    assert rows[0]["DirectName"] == "BIG BANK NA"
    assert rows[0]["IndirectName"] == "DOE JESSICA"
    assert rows[0]["AllDefendants"] == "DOE JESSICA; DOE MARCELO; SECRETARY OF HOUSING AND URBAN DEVELOPMENT"
    assert rows[1]["DirectName"] == "OTHER BANK NA"


def test_fields_carried(tmp_path):
    rows = convert(tmp_path)
    assert rows[0]["RecordDate"] == "08/20/2026 02:48 PM"
    assert rows[0]["DocTypeDescription"] == "Lis Pendens"
    assert rows[1]["DocLegalDescription"] == "Lot: 2 Block: C    SOME PINE HILLS"

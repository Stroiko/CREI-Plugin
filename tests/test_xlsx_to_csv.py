"""xlsx converter tests. The fixture mirrors the real Landmark export shape
(duplicate headers, legalfield_ prefixes) with synthetic data - built in-test
so no PII ships in the repo."""
import csv
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from xlsx_to_csv import xlsx_to_csv

SHEET_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData>
<row r="1">
  <c r="A1" t="inlineStr"><is><t>Status</t></is></c>
  <c r="B1" t="inlineStr"><is><t>Direct Name</t></is></c>
  <c r="C1" t="inlineStr"><is><t>Location</t></is></c>
  <c r="D1" t="inlineStr"><is><t>Lot</t></is></c>
  <c r="E1" t="inlineStr"><is><t>Location</t></is></c>
  <c r="F1" t="s"><v>0</v></c>
</row>
<row r="2">
  <c r="A2" t="inlineStr"><is><t>V</t></is></c>
  <c r="B2" t="inlineStr"><is><t>SOME HOA INC</t></is></c>
  <c r="C2" t="inlineStr"><is><t>01,47,41,</t></is></c>
  <c r="D2" t="inlineStr"><is><t>legalfield_64</t></is></c>
  <c r="F2"><v>123</v></c>
</row>
</sheetData>
</worksheet>"""

SHARED_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1">
<si><t>Instrument #</t></si>
</sst>"""

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
</Types>"""

WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="s" sheetId="1"/></sheets></workbook>"""


def make_fixture(tmp_path):
    path = tmp_path / "sample.xlsx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("xl/workbook.xml", WORKBOOK)
        z.writestr("xl/sharedStrings.xml", SHARED_XML)
        z.writestr("xl/worksheets/sheet1.xml", SHEET_XML)
    return path


def convert(tmp_path):
    src = make_fixture(tmp_path)
    dst = tmp_path / "out.csv"
    xlsx_to_csv(str(src), str(dst))
    with open(dst, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_duplicate_headers_deduped(tmp_path):
    rows = convert(tmp_path)
    assert "Location" in rows[0] and "Location_2" in rows[0]


def test_legalfield_prefix_stripped(tmp_path):
    rows = convert(tmp_path)
    assert rows[0]["Lot"] == "64"


def test_shared_and_inline_strings(tmp_path):
    rows = convert(tmp_path)
    assert rows[0]["Status"] == "V"
    assert rows[0]["Instrument #"] == "123"


def test_missing_cells_are_empty(tmp_path):
    rows = convert(tmp_path)
    assert rows[0]["Location_2"] == ""

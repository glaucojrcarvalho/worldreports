"""Read-only BNM DPMC8 annual lending rate intake, never canonical data."""
import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://www.bnm.md/bdi/pages/reports/dpmc/DPMC8.xhtml?lang=en"
FIELDS = ("year", "weighted_nominal_rate_pct", "new_loan_volume_mdl_mn")
FILTER = {
    "report_id":"DPMC8",
    "publisher":"National Bank of Moldova",
    "indicator":"weighted_average_nominal_rate_new_loans",
    "frequency":"annual",
    "currency":"MDL",
    "borrower":"individuals_real_estate",
    "term":"total_by_terms",
    "interest_unit":"percent",
    "volume_unit":"million_MDL",
    "source_url":SOURCE,
}
EXTRAS = {"start_year","end_year","original_sha256","original_filename","reconciliation_note"}


def decimal(raw, minimum, maximum):
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?",raw or ""):
        raise AssertionError("Malformed decimal; no thousands/comma/NaN")
    value = Decimal(raw)
    if not minimum < value < maximum:
        raise AssertionError("Annual interest or volume outside bounds")
    return value


def audit(manifest, normalized_bytes, original_bytes):
    if set(manifest) != set(FILTER) | EXTRAS:
        raise AssertionError("Missing/unexpected DPMC8 selection fields")
    for key, value in FILTER.items():
        if manifest[key] != value:
            raise AssertionError("Wrong DPMC8 selection: " + key)
    start,end=manifest["start_year"],manifest["end_year"]
    if type(start) is not int or type(end) is not int or not (2006<=start<=end<=2025) or end-start<4:
        raise AssertionError("At least five consecutive completed years 2006-2025 required")
    sha=manifest["original_sha256"]
    if not isinstance(sha,str) or not re.fullmatch(r"[0-9a-f]{64}",sha):
        raise AssertionError("Original export digest must be SHA256")
    if not original_bytes or hashlib.sha256(original_bytes).hexdigest()!=sha:
        raise AssertionError("Original issuer export digest mismatch")
    if not isinstance(manifest["original_filename"],str) or not manifest["original_filename"].endswith((".csv",".xls",".xlsx")):
        raise AssertionError("Publisher export file identity required")
    if not isinstance(manifest["reconciliation_note"],str) or len(manifest["reconciliation_note"].strip())<30:
        raise AssertionError("Describe original-to-normalized row reconciliation")
    try:
        decoded=normalized_bytes.decode("utf-8-sig")
    except UnicodeError as ex:
        raise AssertionError("Normalized annual table must be UTF-8") from ex
    rd=csv.DictReader(io.StringIO(decoded,newline=""))
    if tuple(rd.fieldnames or ())!=FIELDS:
        raise AssertionError("Unexpected normalized annual table schema")
    rows=list(rd)
    if len(rows)!=end-start+1:
        raise AssertionError("Annual rows missing, repeated or outside selection")
    for i,row in enumerate(rows):
        if None in row or any(v is None for v in row.values()) or row["year"]!=str(start+i):
            raise AssertionError("Annual year order or CSV field corruption")
        decimal(row["weighted_nominal_rate_pct"],Decimal(0),Decimal(100))
        decimal(row["new_loan_volume_mdl_mn"],Decimal(0),Decimal(1000000))
    return {
        "status":"STRUCTURALLY_VALID_HUMAN_RECONCILIATION_REQUIRED",
        "source":SOURCE,
        "row_count":len(rows),
        "year_from":start,"year_to":end,
        "original_sha256":sha,
        "normalized_sha256":hashlib.sha256(normalized_bytes).hexdigest(),
        "publication_authorized":False,
        "canonical_rows_promoted":0,
        "human_approval_required":[
            "Check EACH rate and volume against original BNM DPMC8 output",
            "Confirm nominal weighted new-real-estate loans, MDL, individuals, annual frequency",
            "Check revisions, reporting breaks and territory",
            "Do not use December news quotes as annual means or DPMC10 stock rate",
        ],
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path)
    p.add_argument("--normalized",type=Path)
    p.add_argument("--original",type=Path)
    p.add_argument("--output",type=Path,default=Path("/tmp/moldova-dpmc8-intake.json"))
    args=p.parse_args()
    paths=[args.manifest,args.normalized,args.original]
    if any(paths) and not all(paths):
        p.error("Three inputs required together: manifest, normalized, original")
    if all(paths):
        result=audit(json.loads(args.manifest.read_text(encoding="utf-8")),
                     args.normalized.read_bytes(),args.original.read_bytes())
    else:
        result={"status":"AWAITING_OFFICIAL_DPMC8_ANNUAL_EXPORT",
                "publication_authorized":False,"canonical_rows_promoted":0,
                "needed":["Unmodified BNM annual export",
                          "Normalized yearly rate and yearly volume",
                          "Exact filter, source hash and independent human row review"]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Moldova DPMC8 review:",result["status"])

if __name__=="__main__":
    main()

# Moldova — annual DPMC8 new housing loan rate, proof-of-source intake

The official National Bank of Moldova report
https://www.bnm.md/bdi/pages/reports/dpmc/DPMC8.xhtml?lang=en
supports annual/monthly periods, nominal new-loan interest (%),
and loan volume (MDL millions). Select annual, national currency,
individuals: real-estate loans, total by terms, with completed
calendar years only.

The official DPMC10 report concerns outstanding-balance interest rates,
and must NEVER substitute for a newly issued housing loan rate.

To use this offline structural gate, retain the publisher ORIGINAL export.
Normalize the raw year/rate/volume records independently to a separate
UTF-8 CSV with columns year, weighted_nominal_rate_pct,
new_loan_volume_mdl_mn, and prepare a JSON manifest containing all
exact FILTER keys in the Python module plus integer start_year/end_year,
original_sha256, original_filename and reconciliation_note.

Example command (only after actual official export exists):
python -m countries.moldova.research.dpmc8_annual_intake --manifest selection.json --normalized rates_review.csv --original publisher_original.csv

This tool confirms the hash of the ORIGINAL file, year continuity,
expected currency/borrower/loan-purpose/term/frequency, numeric
units and zero/missing/incomplete-year errors. It CANNOT establish
that manually normalized values agree with the publisher original;
that needs independent source inspection and approval. Consequently
even a passing export always returns human-reconciliation-required
status and ZERO rows promoted into the country atlas.

No annual DPMC8 export has yet been obtained. The initial
interactive-browser attempt did not start because that provider's
wallet lacked credit. No user payment is required for existing static
GitHub CI; adding browser credit is optional for extraction.

No publication, upstream PR, merge, deployment, synthetic annual
series or country.yaml registration is authorized.

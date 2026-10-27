# Publisher-verified candidates — not atlas data

This directory contains original-publisher **source reconnaissance only**,
reviewed on 27 October 2026. Neither file is read by Moldova's plates.
The research branch has no active country.yaml and does not publish them.

## BNM mortgage new-loan interest

The National Bank of Moldova provides an annual/monthly report of
**weighted nominal interest rates AND volumes of newly granted loans**
at https://www.bnm.md/bdi/pages/reports/dpmc/DPMC8.xhtml?lang=en .
Its filters distinguish **national currency MDL**, **individuals'
new real-estate loans** and **all maturities** from businesses, consumer
credit and general banking-sector totals.

Issuer news reports independently state December 2024 mortgage MDL
interest **6.99%** (released 20 January 2025;
https://bnm.md/en/content/bank-loans-market-development-december-2024-0)
and December 2025 **8.24%** (released 20 January 2026;
https://www.bnm.md/en/content/developments-bank-loan-market-december-2025).
The evidence file nbm_mortgage_december.csv stores ONLY those monthly
values and publication dates. Do NOT use them as ANNUAL interest rates;
the NBM DPMC8 annual export must be retrieved with precise filters
and its weighted-rate methodology verified. NBM DPMC10 reports rates
on OUTSTANDING loans instead of new loans; it is the WRONG series.
Generic World Bank FR.INR.LEND is also not borrower/purpose-specific.

## Government fixed capital formation

The Ministry of Finance's January 2026 Economic Reform Programme
2026–2028, Annex Table 2/2b (printed p82, PDF index 81),
https://mf.gov.md/sites/default/files/ERP%202026-2028%20ENG.pdf,
identifies **sector S13, transaction P51, general-government gross
fixed capital formation**: historical programme baseline 2024
3.20 billion MDL and 1.0% GDP, 2025 programme estimate 5.20 billion
MDL and 1.0%, and 2026 projected 8.10 billion MDL and 1.4%. These
are NOT economy-wide investment (S1/P51) and must not be equated
with national public-budget cash purchases of nonfinancial assets.
The estimates/forecasts are NOT audited realized outcomes.

A compatible longer historical series and territorial/GDP checks
are required before the canonical government investment panel may
be filled. The nine original pending canonical panels remain
explicitly pending.

The associated offline test and audit script verify publisher URLs,
series definitions, category/currency, classification and vintage,
and produce a SHA-versioned JSON artifact. No made-up values,
interpolation, automatic external refresh, upload to upstream, merge
or deployment occurs.

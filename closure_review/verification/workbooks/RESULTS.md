# Workbook upgrade verification —23October2026

35 automated tests passed: existing28 plus7workbook tests. Independent reviewer rechecked Excel error cells, formula-cache blockers, explicit subtotal exclusion, no partial comparison, request races, provenance-only finding filtering and labels.

Browser desktop1440x1000 and mobile390x844 checked; mobile documentwidth390. Two constructed XLSX sample files imported via file chooser. Header4/columnsA–F suggested; subtotal13 blocked before explicit exclusion. Both then produced8validactivities. Comparison deltaUSD191830/fourfinancialfindings matched baseline fixture. Evidence drawer showed topsoilC8/E8/F8 cell references, saved values and bothSHA256fingerprints. Export readback verified2sources, mapping/provenance and4findings.

Real public FY25 sustainability workbook inspected:21worksheets includingClosure. This verifies reader compatibility for this file only, not engineering model interpretation.

Formula computation not implemented: saved values read as documented at https://openpyxl.readthedocs.io/en/stable/tutorial.html . AI key unavailable; no live AI generation claimed. Local only.

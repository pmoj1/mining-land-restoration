# AtlasIQ Closure Review

Local application for explicitly mapped Excel intake, input checks and source-linked closure cost comparison. Uses AtlasIQ's existing ink/ivory/amber palette, logo and Space Grotesk font.

## Open

Double-click **Start AtlasIQ.command**, then visit http://127.0.0.1:8765. Keep its terminal open. Stop with Control-C. If a server already occupies that port, stop it first. Alternatively, from the project root:

```sh
/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m closure_review
```

## Connect OpenAI

Double-click **Start with OpenAI.command** to open a separate AI-enabled workspace at http://127.0.0.1:8766. Enter your API key at the hidden prompt and a model ID enabled in your account. Credentials remain in that process environment and are not written into this project. The optional explanation button sends the displayed comparison to OpenAI. Local calculations and charts need no API key. Model access, billing and live generation must be verified using your account; no live API call was made during the build. AI explanations are drafts requiring review.

The integration uses the Responses API with `store:false`, which disables response storage for later API retrieval; this is not a promise of zero data retention. Documentation: https://developers.openai.com/api/docs/guides/conversation-state .

## Input contract

Download the baseline and scenario CSV templates from the application. Upload two UTF-8 CSVs with these columns, in order:

`id,activity,quantity,unit,rate,source`

Use stable unique activity IDs, consistent units, nonnegative quantities and rates, and a source reference for every row. All costs must be in USD on a consistent undiscounted basis. The importer does not convert currencies, discount estimates or infer missing numbers. Maximum 2,000 activities per file; combined request maximum 2 MB. An item absent from one file is explicitly added or removed, not proof the underlying physical work changed. CSVs can also be prepared in Excel. Native XLSX intake is available through Workbook intake, described below. PDF extraction is not implemented.

Quantity effect uses old rates, and rate effect uses new quantities. Added and removed scope is allocated to quantity effect. These effects reconcile to total movement. Review outcomes are browser-local annotations, not an authenticated approval audit trail. Export the review record to retain a portable copy. Uploads are processed in memory, not stored by the local server.

## Evidence and limits

The baseline reproduces eight published task totals in the February 2018 Yaouré conceptual closure plan: USD4,091,620. Hectare quantities are reconstructed from published totals and unit rates, not raw survey measurements. Monitoring and infrastructure removal are lump sums. See data/provenance.json and the source drawer.

The current scenario contains invented test changes. It is not a second company-approved estimate. The public historical estimate excludes uncertain long-term water treatment costs. This demonstration does not establish today's liability, model omissions, avoided losses or engineering correctness.

The local server binds only to 127.0.0.1. It is not a production cloud service, a multi-user approval system or a validated survey/GIS reconciliation tool. No automatic AI interpretation of arbitrary uploaded reports is claimed. XLSX import is an explicit user-confirmed mapping workflow.

## Verification

From the project root run `python -m unittest discover -s tests -v`. The included closure tests check arithmetic and rejected inputs. Existing corridor tests remain separate from closure functionality.

## Excel workbook intake (23 October 2026)

Open **Workbook intake** or **Import Excel**. For each file:

1. Choose an XLSX workbook. The preview identifies sheets and suggests a header row.
2. Confirm the sheet, header, data range and ID/activity/quantity/unit/rate columns. Map a stated-cost column to check its arithmetic too.
3. Explicitly exclude total, subtotal and note rows. Confirm the USD and undiscounted basis.
4. Run checks. Missing inputs, duplicate IDs, Excel error cells, missing formula caches and cost mismatches block comparison. Resolve these in the source or mapping.
5. Compare the checked workbooks. Inspect an activity to see exact source cells, saved values, formulas when present, and SHA256 file fingerprints. The evidence library and exported review include mapping scope, warnings and cell traces.

Header/column suggestions require confirmation. Stable IDs must already identify comparable activities; fuzzy matching, unit conversion and automatic engineering interpretation are not implemented. Hidden selected sheets and omitted cost scope are surfaced as warnings. File fingerprint changes alone are retained in provenance and do not create financial review findings.

The downloadable XLSX samples are constructed test files derived from the historical category totals, not original Perseus Excel workbooks. They deliberately include a total row so the reviewer must exclude it (row13). Both samples use header row4 and data rows5–12.

Formula cells use saved workbook results; AtlasIQ does not recalculate formulas or establish cache freshness. Missing saved results block import. External workbook links are not refreshed. See the [openpyxl documentation](https://openpyxl.readthedocs.io/en/stable/tutorial.html).

Limits: XLSX only, no encrypted or macro-enabled files;8MB per file;30MB expanded;30 sheets;10,000 rows/100 columns per sheet;2,000 valid mapped activities. Selected single-sheet scope only. File content remains in request memory, but exported source metadata may contain workbook values. Inputs and warnings are browser session state; refresh clears uploaded workbooks.

The bundled Python already includes openpyxl. For another environment install `closure_review/requirements.txt` and Python3.10+.

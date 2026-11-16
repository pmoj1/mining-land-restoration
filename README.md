# Mining Land Restoration and Closure Review

A mining rehabilitation project plan and a local prototype for reviewing closure-cost inputs and comparing scenarios.

## Explore

- `rehabilitation-plan/outputs/Mining_Rehabilitation_Project_Plan.docx` — the rehabilitation project plan.
- `rehabilitation-plan/work/` — the plan-generation source.
- `closure_review/` — the local CSV/XLSX intake and closure-cost comparison application.
- `research/` — research records, historical reports and source provenance.
- `tests/` — the closure-review tests copied from the original workspace.

## Run the local application

Use Python 3.10 or newer. From this repository root:

```sh
python3 -m pip install -r closure_review/requirements.txt
python3 -m closure_review
```

The default local address is http://127.0.0.1:8765. See `closure_review/README.md` for input requirements and optional AI explanations.

## Evidence and limits

The rehabilitation plan uses Nyanzaga as a case-study framing. The closure-cost demonstration uses published historical Yaouré category totals and constructed test scenarios. They are distinct inputs and must not be described as a verified current Nyanzaga liability or an implemented land-restoration programme.

The application checks explicitly mapped inputs and compares cost movements. It does not validate engineering assumptions, measure restored land, automatically interpret arbitrary reports, or establish current company-approved costs. Research archives preserve earlier ideas and statements in context.

Corridor/AtlasIQ transport monitoring is maintained separately in [atlasiq-corridor-lifeline](https://github.com/pmoj1/atlasiq-corridor-lifeline).

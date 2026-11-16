"""Deterministic closure cost comparison; all monetary arithmetic uses Decimal."""
from __future__ import annotations

import csv
import io
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

DATA = Path(__file__).with_name("data")
FIELDS = ("id", "activity", "quantity", "unit", "rate", "source")


def parse_csv(text: str) -> list[dict]:
    if not isinstance(text, str) or len(text) > 2_000_000:
        raise ValueError("Provide a CSV file smaller than 2 MB.")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    if reader.fieldnames != list(FIELDS):
        raise ValueError("CSV headers must be: " + ",".join(FIELDS))
    rows, seen = [], set()
    try:
        for line, raw in enumerate(reader, 2):
            if len(rows) >= 2000:
                raise ValueError("CSV supports at most 2,000 activities.")
            if None in raw or any(raw.get(k) is None for k in FIELDS):
                raise ValueError(f"Row {line}: column count does not match the header.")
            row = {k: raw[k].strip() for k in FIELDS}
            if any(not row[k] for k in FIELDS):
                raise ValueError(f"Row {line}: all fields are required, including source.")
            if any(len(v) > 2000 for v in row.values()):
                raise ValueError(f"Row {line}: field is too long.")
            if row['id'] in seen:
                raise ValueError(f"Row {line}: duplicate activity ID {row['id']}.")
            seen.add(row['id'])
            for key in ('quantity', 'rate'):
                try:
                    number = Decimal(row[key])
                except InvalidOperation:
                    raise ValueError(f"Row {line}: {key} must be a number.") from None
                if not number.is_finite() or number < 0 or number > Decimal('1000000000000'):
                    raise ValueError(f"Row {line}: {key} must be finite, nonnegative and no greater than 1 trillion.")
                if number.as_tuple().exponent < -6:
                    raise ValueError(f"Row {line}: {key} supports at most six decimal places.")
                row[key] = number
            rows.append(row)
    except csv.Error as error:
        raise ValueError(f"Invalid CSV: {error}") from None
    if not rows:
        raise ValueError("CSV has no activities. Missing data is not a zero estimate.")
    return rows


def _number(value: Decimal) -> float:
    return float(value)


def compare_csv(baseline_csv: str, current_csv: str) -> dict:
    return compare_rows(parse_csv(baseline_csv), parse_csv(current_csv))


def compare_rows(baseline: list[dict], current: list[dict]) -> dict:
    before = {r['id']: r for r in baseline}
    after = {r['id']: r for r in current}
    results, findings = [], []
    zero = Decimal(0)
    total_before = total_after = quantity_total = rate_total = zero
    for ident in dict.fromkeys([*before, *after]):
        old, new = before.get(ident), after.get(ident)
        present = new or old
        if old and new and old['unit'] != new['unit']:
            raise ValueError(f"Activity {ident}: units differ. Convert them explicitly before comparing.")
        q0, r0 = (old['quantity'], old['rate']) if old else (zero, new['rate'])
        q1, r1 = (new['quantity'], new['rate']) if new else (zero, old['rate'])
        c0, c1 = q0 * r0, q1 * r1
        quantity_effect, rate_effect = (q1 - q0) * r0, q1 * (r1 - r0)
        status = 'added' if old is None else 'removed' if new is None else 'changed' if (q0, r0, old['activity'], old['source']) != (q1, r1, new['activity'], new['source']) else 'unchanged'
        row = dict(id=ident, activity=present['activity'], unit=present['unit'],
                   baseline_quantity=_number(q0) if old else None,
                   current_quantity=_number(q1) if new else None,
                   baseline_rate=_number(r0) if old else None,
                   current_rate=_number(r1) if new else None,
                   baseline_cost=_number(c0), current_cost=_number(c1), delta=_number(c1-c0),
                   quantity_effect=_number(quantity_effect), rate_effect=_number(rate_effect), status=status,
                   source=present['source'], baseline_source=old['source'] if old else None,
                   current_source=new['source'] if new else None)
        results.append(row)
        if status != 'unchanged':
            if status in ('added', 'removed'):
                detail = f"Activity is {status} in the supplied current file. Confirm the scope change and its supporting evidence. Absence from a file does not prove the physical work disappeared."
            elif c0 != c1:
                detail = f"Cost changed by USD {c1-c0:,.2f}: quantity effect USD {quantity_effect:,.2f}; rate effect USD {rate_effect:,.2f}. Check the supplied evidence and approval for these changes."
            else:
                detail = "Cost is unchanged, but activity description, source or offsetting quantity/rate inputs changed. Review the supporting record."
            findings.append(dict(id=ident, title=present['activity'], detail=detail, source=present['source'], severity='review'))
        total_before += c0
        total_after += c1
        quantity_total += quantity_effect
        rate_total += rate_effect
    assert total_after-total_before == quantity_total+rate_total
    return dict(baseline_total=_number(total_before), current_total=_number(total_after),
                delta=_number(total_after-total_before), quantity_effect=_number(quantity_total),
                rate_effect=_number(rate_total), rows=results, findings=findings,
                currency='USD', basis='Undiscounted supplied activity costs',
                method='Quantity effect = (new quantity − old quantity) × old rate. Rate effect = new quantity × (new rate − old rate). Added/removed scope is allocated to quantity effect; absent values remain null.')


def template(version: str) -> str:
    if version not in ('baseline', 'current'):
        raise ValueError("Template version must be baseline or current.")
    return (DATA / f'{version}.csv').read_text()


def demo() -> dict:
    baseline, current = template('baseline'), template('current')
    def serial(rows):
        return [{k: _number(v) if isinstance(v, Decimal) else v for k, v in r.items()} for r in rows]
    return dict(baseline=dict(label='Yaouré · February 2018 public estimate', rows=serial(parse_csv(baseline))),
                current=dict(label='Illustrative test changes · not company data', rows=serial(parse_csv(current))),
                comparison=compare_csv(baseline, current),
                sources=[json.loads((DATA/'provenance.json').read_text())], mode='illustrative')

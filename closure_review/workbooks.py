"""Read-only, explicitly mapped XLSX ingestion with cell-level provenance.

No formula calculation, network retrieval, fuzzy identity matching or unit conversion.
"""
from __future__ import annotations
import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import io
from pathlib import PurePath
import re
import zipfile
import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter

MAX_FILE = 8_000_000
MAX_EXPANDED = 30_000_000
MAX_ROWS = 10000
MAX_COLS = 100
FIELDS = ('id', 'activity', 'quantity', 'unit', 'rate')
TOTAL = re.compile(r'\b(?:sub\s*total|subtotal|grand\s+total|total)\b', re.I)


def _clean_filename(filename):
    if not isinstance(filename, str) or not filename.strip() or len(filename) > 200:
        raise ValueError('A workbook filename of at most 200 characters is required.')
    return PurePath(filename.replace('\\', '/')).name


def _load(content, filename):
    filename = _clean_filename(filename)
    if not isinstance(content, bytes) or not content or len(content) > MAX_FILE:
        raise ValueError('Workbook must contain between 1 byte and 8 MB.')
    if not filename.lower().endswith('.xlsx'):
        raise ValueError('Only .xlsx workbooks are supported. Export older or macro-enabled files to .xlsx first.')
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 1500 or sum(x.file_size for x in entries) > MAX_EXPANDED:
                raise ValueError('Workbook expanded contents exceed the 30 MB or 1,500-part limit.')
            names = [x.filename for x in entries]
            if len(names) != len(set(names)):
                raise ValueError('Workbook ZIP contains duplicate parts.')
            if any(x.flag_bits & 1 for x in entries):
                raise ValueError('Encrypted workbooks are not supported.')
            if any('vbaProject' in name for name in names):
                raise ValueError('Macro-enabled workbook contents are not supported.')
            if '[Content_Types].xml' not in names or 'xl/workbook.xml' not in names:
                raise ValueError('File is not an XLSX workbook.')
            external = any(name.startswith('xl/externalLinks/') for name in names)
        formulas = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=False, keep_links=False)
        try:
            cached = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True, keep_links=False)
        except Exception:
            formulas.close()
            raise
    except ValueError:
        raise
    except Exception as error:
        raise ValueError('Workbook could not be read as a valid XLSX file.') from error
    for sheet in formulas:
        if (sheet.max_row or 0) > MAX_ROWS or (sheet.max_column or 0) > MAX_COLS:
            formulas.close(); cached.close()
            raise ValueError('Each worksheet must have at most 10,000 rows and 100 columns, including formatted cells.')
    if len(formulas.sheetnames) > 30:
        formulas.close(); cached.close()
        raise ValueError('Workbook supports at most 30 worksheets.')
    warnings = []
    if external:
        warnings.append('External workbook links were detected. They were not followed or refreshed. Formula caches may be stale.')
    return filename, hashlib.sha256(content).hexdigest(), formulas, cached, warnings


def _json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if value is None or isinstance(value, (str, bool, int, float)):
        # Error strings remain visible; non-finite floats must not break JSON serialization.
        if isinstance(value, float) and (value != value or abs(value) == float('inf')):
            return str(value)
        return value if not isinstance(value, str) else value[:2000]
    return str(value)[:2000]


def inspect_workbook(content: bytes, filename: str) -> dict:
    filename, digest, formulas, cached, warnings = _load(content, filename)
    result = {'sha256': digest, 'filename': filename, 'sheets': [], 'warnings': warnings}
    try:
        for sheet in formulas:
            values = cached[sheet.title]
            preview, candidates = [], []
            for number, (row, cached_row) in enumerate(zip(sheet.iter_rows(max_row=min(sheet.max_row or 1, 40)), values.iter_rows(max_row=min(sheet.max_row or 1, 40))), 1):
                cells, labels = [], []
                for col, (cell, cache) in enumerate(zip(row, cached_row), 1):
                    formula = str(cell.value) if cell.data_type == 'f' else None
                    value = cache.value if formula else cell.value
                    if cell.value is not None:
                        cells.append({'column': get_column_letter(col), 'value': _json_value(value),
                                      'formula': formula, 'coordinate': f'{get_column_letter(col)}{number}'})
                        if isinstance(value, str) and not formula:
                            labels.append({'column': get_column_letter(col), 'label': value[:200]})
                if cells:
                    preview.append({'row': number, 'cells': cells})
                recognized = sum(bool(re.search(r'\b(id|code|activity|description|task|quantity|qty|unit|rate|cost|amount)\b', x['label'], re.I)) for x in labels)
                if recognized >= 2:
                    candidates.append({'row': number, 'columns': labels})
            result['sheets'].append({'name': sheet.title, 'rows': sheet.max_row or 0,
                                     'columns': sheet.max_column or 0, 'preview': preview,
                                     'header_candidates': candidates, 'state': sheet.sheet_state})
        return result
    finally:
        formulas.close(); cached.close()


def _integer(value, label, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f'{label} must be an integer between {low} and {high}.')
    return value


def map_workbook(content: bytes, filename: str, mapping: dict) -> dict:
    filename, digest, formulas, cached, warnings = _load(content, filename)
    issues, provenance, rows, excluded, blocked = [], [], [], 0, 0
    def issue(severity, code, message, row=None, cell=None):
        issues.append(dict(severity=severity, code=code, message=message, row=row, cell=cell))
    try:
        if not isinstance(mapping, dict):
            raise ValueError('Provide a workbook column mapping.')
        if mapping.get('currency') != 'USD' or mapping.get('basis') != 'undiscounted':
            raise ValueError('Explicitly confirm USD currency and an undiscounted cost basis before mapping. No currency or discount conversion is performed.')
        if mapping.get('sheet') not in formulas.sheetnames:
            raise ValueError('Select an existing worksheet.')
        sheet = formulas[mapping['sheet']]
        cache = cached[sheet.title]
        max_row = sheet.max_row or 1
        header = _integer(mapping.get('header_row'), 'Header row', 1, max_row)
        start = _integer(mapping.get('start_row', header + 1), 'First data row', header + 1, MAX_ROWS)
        end = _integer(mapping.get('end_row', max_row), 'Last data row', start, MAX_ROWS)
        if end > max_row:
            raise ValueError('Last data row is outside the worksheet.')
        columns = mapping.get('columns')
        if not isinstance(columns, dict) or any(not columns.get(field) for field in FIELDS):
            raise ValueError('Map ID, activity, quantity, unit and rate columns.')
        selected = {}
        for field in (*FIELDS, 'cost'):
            value = columns.get(field)
            if field == 'cost' and not value:
                continue
            if not isinstance(value, str) or not re.fullmatch('[A-Za-z]{1,3}', value):
                raise ValueError(f'{field}: use a column letter such as A or B.')
            col = column_index_from_string(value.upper())
            if col > (sheet.max_column or 0):
                raise ValueError(f'{field}: selected column is outside the worksheet.')
            selected[field] = col
        if len(set(selected.values())) != len(selected):
            raise ValueError('Each mapped field must use a different column.')
        exclusions = mapping.get('exclude_rows', [])
        if not isinstance(exclusions, list):
            raise ValueError('Excluded rows must be a list of row numbers.')
        exclusions = set(_integer(x, 'Excluded row', start, end) for x in exclusions)
        for warning in warnings:
            issue('warning', 'external_links', warning)
        if 'cost' not in selected:
            issue('warning', 'cost_not_mapped', 'No stated-cost column mapped. Quantity × rate amounts cannot be checked against the workbook totals.')
        issue('warning', 'scope_not_verified', 'Mapping covers the selected worksheet and rows only. Omitted sheets, activities, contingency and other cost components have not been checked.')
        if sheet.sheet_state != 'visible':
            issue('warning', 'hidden_sheet', 'The selected worksheet is hidden in the workbook.')
        seen, formula_seen = set(), False
        formula_rows = sheet.iter_rows(min_row=start, max_row=end)
        cache_rows = cache.iter_rows(min_row=start, max_row=end)
        for number, (line, cached_line) in enumerate(zip(formula_rows, cache_rows), start):
            if number in exclusions:
                excluded += 1
                continue
            values, coords, formulae = {}, {}, {}
            row_issue_count = len(issues)
            for field, col in selected.items():
                cell, cached_cell = line[col - 1], cached_line[col - 1]
                coord = f'{get_column_letter(col)}{number}'
                coords[field] = coord
                formula = cell.data_type == 'f'
                values[field] = cached_cell.value if formula else cell.value
                if cell.data_type == 'e' or cached_cell.data_type == 'e':
                    issue('blocker', 'excel_error', f'{field}: Excel error {values[field]}. Repair the source workbook before importing.', number, coord)
                if formula:
                    formula_seen = True
                    formulae[field] = str(cell.value)
            if all(v is None or isinstance(v, str) and not v.strip() for v in values.values()) and not formulae:
                continue
            for field in formulae:
                if values[field] is None:
                    issue('blocker', 'missing_formula_cache', f'{field}: formula has no saved value. Recalculate and save in Excel before importing.', number, coords[field])
            row = {}
            for field in ('id', 'activity', 'unit'):
                value = values[field]
                if value is None or isinstance(value, bool) or isinstance(value, (date, datetime)) or not str(value).strip():
                    issue('blocker', 'missing_text', f'{field} is missing or invalid.', number, coords[field])
                else:
                    row[field] = str(value).strip()
                    if len(row[field]) > 1000:
                        issue('blocker', 'field_too_long', f'{field} exceeds 1,000 characters.', number, coords[field])
            if row.get('id') in seen:
                issue('blocker', 'duplicate_id', f'Duplicate activity ID {row["id"]}. Use stable unique IDs.', number, coords['id'])
            if 'id' in row:
                seen.add(row['id'])
            if any(TOTAL.search(str(values.get(field) or '')) for field in ('id', 'activity')):
                issue('blocker', 'subtotal_row', 'Possible subtotal or total. Explicitly exclude this row to avoid double counting, or correct the activity description.', number, coords['activity'])
            decimal_values = {}
            for field in ('quantity', 'rate', *(['cost'] if 'cost' in selected else [])):
                try:
                    value = values[field]
                    if value is None or isinstance(value, bool) or isinstance(value, (datetime, date)):
                        raise InvalidOperation
                    numeric = Decimal(str(value).strip())
                    if not numeric.is_finite() or numeric < 0 or numeric > Decimal('1000000000000') or numeric.as_tuple().exponent < -6:
                        raise InvalidOperation
                    decimal_values[field] = numeric
                    row[field] = float(numeric)
                except (InvalidOperation, ValueError):
                    issue('blocker', 'invalid_number', f'{field} must be a saved finite nonnegative number, at most 1 trillion and six decimal places. Missing values are not zero.', number, coords[field])
            if all(k in decimal_values for k in ('quantity', 'rate', 'cost')):
                calculated = decimal_values['quantity'] * decimal_values['rate']
                if abs(calculated - decimal_values['cost']) > Decimal('.01'):
                    issue('blocker', 'cost_mismatch', f'Stated cost {decimal_values["cost"]} differs from quantity × rate {calculated}. Check adjustments, rounding or the selected columns.', number, coords['cost'])
            row['source'] = f'{filename} | {sheet.title}!{",".join(coords.values())} | SHA256 {digest}'
            row['quantity'] = row.get('quantity')
            row['rate'] = row.get('rate')
            row_blockers = any(x['severity'] == 'blocker' for x in issues[row_issue_count:])
            if row_blockers:
                blocked += 1
            else:
                row.pop('cost', None)
                rows.append(row)
                provenance.append({'id': row['id'], 'sheet': sheet.title, 'row': number,
                                   'cells': coords, 'formulae': formulae, 'sha256': digest,
                                   'cached_values': {k: _json_value(values[k]) for k in selected},
                                   'stated_cost': float(decimal_values['cost']) if 'cost' in decimal_values else None})
        if formula_seen:
            issue('warning', 'formula_cache_unverified', 'Formula results are saved workbook caches, not recalculated by AtlasIQ. Their freshness and external dependencies have not been verified.')
        if not rows:
            issue('blocker', 'no_valid_activities', 'No valid activities remain in the selected mapping.')
        if len(rows) > 2000:
            issue('blocker', 'activity_limit', 'The comparison engine accepts at most 2,000 activities. Narrow the selected range.')
        can_compare = not any(x['severity'] == 'blocker' for x in issues)
        csv_text = None
        if can_compare:
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=(*FIELDS, 'source'))
            writer.writeheader()
            writer.writerows(rows)
            csv_text = out.getvalue()
        return {'rows': rows, 'csv': csv_text, 'issues': issues, 'provenance': provenance,
                'can_compare': can_compare, 'summary': {'included': len(rows), 'excluded': excluded, 'blocked': blocked},
                'sha256': digest, 'filename': filename, 'mapping': mapping}
    finally:
        formulas.close(); cached.close()

import os
import sys
import json
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
HANDOFF_DIR = os.path.join(ROOT_DIR, 'handoff')

# Catches oos2, 2024-2029 (including notes_2025, OOS2_2025, 2025Q3, 2024-02-01, pnl_2026)
FORBIDDEN_TOKEN_PATTERN = re.compile(r"(?:oos2|(?<!\d)202[4-9](?!\d))", re.IGNORECASE)

ALLOWED_ROOT_KEYS = {'export_tier', 'description', 'gate_criteria', 'total_leads', 'leads'}
ALLOWED_LEAD_KEYS = {
    'lead_id', 'source', 'original_id', 'name', 'family', 'symbol',
    'timeframe', 'direction', 'rule_description', 'source_verdict',
    'passes_all_5', 'data_quality_flags', 'replicability', 'evidence_tier',
    'gate_condition_met', 'verified_live_links', 'performance_metrics'
}
ALLOWED_METRIC_PERIODS = {'is_2004_2018', 'oos1_2019_2023'}
ALLOWED_PERIOD_KEYS = {'n', 'wr', 'years_pos', 'nam_duong'}
ALLOWED_IS_YEARS = {str(y) for y in range(2004, 2019)}
ALLOWED_OOS1_YEARS = {str(y) for y in range(2019, 2024)}

def recursive_check_holdout(obj, current_path="root"):
    violations = []
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            k_str = str(k)
            # Check key
            if FORBIDDEN_TOKEN_PATTERN.search(k_str):
                violations.append((f"{current_path}.key({k_str})", f"Forbidden holdout token in key: {k_str}"))
            # Recurse
            violations.extend(recursive_check_holdout(v, f"{current_path}.{k_str}"))
            
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            violations.extend(recursive_check_holdout(item, f"{current_path}[{idx}]"))
            
    elif isinstance(obj, str):
        if FORBIDDEN_TOKEN_PATTERN.search(obj):
            violations.append((current_path, f"Forbidden holdout token in string value: '{obj}'"))
            
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if 2024 <= obj <= 2099:
            violations.append((current_path, f"Forbidden holdout year numeric value: {obj}"))
            
    return violations

def _validate_pm(pm, prefix="performance_metrics"):
    errors = []
    extra_periods = set(pm.keys()) - ALLOWED_METRIC_PERIODS
    if extra_periods:
        errors.append(f"{prefix} periods violate allowlist: {extra_periods}")
    for period_name in ALLOWED_METRIC_PERIODS:
        if period_name in pm:
            p_data = pm[period_name]
            if not isinstance(p_data, dict):
                errors.append(f"{prefix}.{period_name} must be a dict")
                continue
            extra_pk = set(p_data.keys()) - ALLOWED_PERIOD_KEYS
            if extra_pk:
                errors.append(f"{prefix}.{period_name} keys violate allowlist: {extra_pk}")
            nd = p_data.get('nam_duong')
            if isinstance(nd, dict):
                allowed_years = ALLOWED_IS_YEARS if period_name == 'is_2004_2018' else ALLOWED_OOS1_YEARS
                invalid_years = set(str(y) for y in nd.keys()) - allowed_years
                if invalid_years:
                    errors.append(f"{prefix}.{period_name}.nam_duong years outside range {sorted(allowed_years)[0]}..{sorted(allowed_years)[-1]}: {invalid_years}")
    return errors

def validate_handoff_schema(data):
    schema_errors = []
    if isinstance(data, dict):
        if 'leads' in data:
            extra_root = set(data.keys()) - ALLOWED_ROOT_KEYS
            if extra_root:
                schema_errors.append(f"Root keys violate allowlist: {extra_root}")
            leads_list = data.get('leads', [])
        elif isinstance(data, list):
            leads_list = data
        else:
            leads_list = [data]

        for idx, item in enumerate(leads_list):
            if not isinstance(item, dict):
                continue
            # If item represents a lead
            if any(k in item for k in ('lead_id', 'original_id', 'performance_metrics')):
                extra_lead = set(item.keys()) - ALLOWED_LEAD_KEYS
                if extra_lead:
                    schema_errors.append(f"Lead [{idx}] keys violate allowlist: {extra_lead}")
                pm = item.get('performance_metrics')
                if isinstance(pm, dict):
                    schema_errors.extend(_validate_pm(pm, f"Lead [{idx}].performance_metrics"))
            elif 'performance_metrics' in item:
                pm = item.get('performance_metrics')
                if isinstance(pm, dict):
                    schema_errors.extend(_validate_pm(pm, f"Item [{idx}].performance_metrics"))
    return schema_errors

def sanitize_and_validate(data):
    v_tokens = recursive_check_holdout(data)
    v_schema = validate_handoff_schema(data)
    all_violations = v_tokens + [("schema", err) for err in v_schema]
    return (len(all_violations) == 0, all_violations)

def sanitize(handoff_dir=None):
    target_dir = handoff_dir or HANDOFF_DIR
    print(f"[*] Running holdout sanitizer check in: {target_dir}")
    if not os.path.exists(target_dir):
        print("[+] Handoff directory does not exist yet. Clean.")
        return True

    violations = []
    files_checked = 0

    for dirpath, _, filenames in os.walk(target_dir):
        for f in filenames:
            files_checked += 1
            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, ROOT_DIR).replace('\\', '/')
            
            # Check JSON files deeply
            if f.endswith('.json'):
                try:
                    with open(filepath, 'r', encoding='utf-8') as fp:
                        json_data = json.load(fp)
                    
                    # 1. Recursive token check
                    v_tokens = recursive_check_holdout(json_data, rel_path)
                    violations.extend(v_tokens)
                    
                    # 2. Strict allowlist schema validation if sanitized_master_leads.json
                    if f == 'sanitized_master_leads.json':
                        v_schema = validate_handoff_schema(json_data)
                        for err in v_schema:
                            violations.append((rel_path, err))
                except Exception as e:
                    violations.append((rel_path, f"JSON parse error: {e}"))
            else:
                # Text files (.md, etc.)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as fp:
                        content = fp.read()
                    matches = FORBIDDEN_TOKEN_PATTERN.findall(content)
                    if matches:
                        violations.append((rel_path, f"Forbidden holdout tokens in text: {matches[:3]}"))
                except Exception as e:
                    violations.append((rel_path, f"File read error: {e}"))

    if violations:
        print("[!] HOLDOUT LEAKAGE / SCHEMA VIOLATION DETECTED in handoff/ directory:")
        for path, err in violations:
            print(f"    - Location: {path}")
            print(f"      Violation: {err}")
        print("\n[FAIL] Holdout sanitizer check FAILED.")
        return False
    else:
        print(f"[+] Holdout Sanitizer: {files_checked} files checked. 0 leakage of Holdout data & 100% schema allowlist valid. PASS.")
        print("\n[SUCCESS] Holdout sanitizer PASSED.")
        return True

if __name__ == '__main__':
    ok = sanitize()
    if not ok:
        sys.exit(1)

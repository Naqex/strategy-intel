import os
import sys
import json
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
HANDOFF_DIR = os.path.join(ROOT_DIR, 'handoff')

FORBIDDEN_TOKEN_PATTERN = re.compile(r'\b(oos2|2024|2025|2026)\b', re.IGNORECASE)

ALLOWED_ROOT_KEYS = {'export_tier', 'description', 'gate_criteria', 'total_leads', 'leads'}
ALLOWED_LEAD_KEYS = {
    'lead_id', 'source', 'original_id', 'name', 'family', 'symbol',
    'timeframe', 'direction', 'rule_description', 'source_verdict',
    'passes_all_5', 'data_quality_flags', 'replicability', 'evidence_tier',
    'gate_condition_met', 'verified_live_links', 'performance_metrics'
}
ALLOWED_METRICS_PERIODS = {'is_2004_2018', 'oos1_2019_2023'}

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
            
    elif isinstance(obj, (int, float)):
        if obj in [2024, 2025, 2026]:
            violations.append((current_path, f"Forbidden holdout year numeric value: {obj}"))
            
    return violations

def validate_handoff_schema(data):
    schema_errors = []
    # Root keys
    extra_root = set(data.keys()) - ALLOWED_ROOT_KEYS
    if extra_root:
        schema_errors.append(f"Root keys violate allowlist: {extra_root}")
        
    for idx, lead in enumerate(data.get('leads', [])):
        extra_lead = set(lead.keys()) - ALLOWED_LEAD_KEYS
        if extra_lead:
            schema_errors.append(f"Lead [{idx}] keys violate allowlist: {extra_lead}")
        pm = lead.get('performance_metrics', {})
        extra_pm = set(pm.keys()) - ALLOWED_METRICS_PERIODS
        if extra_pm:
            schema_errors.append(f"Lead [{idx}] performance_metrics periods violate allowlist: {extra_pm}")
            
    return schema_errors

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

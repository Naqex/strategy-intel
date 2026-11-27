import argparse
import os
import sys
import json
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
HANDOFF_DIR = os.path.join(ROOT_DIR, 'handoff')

NOT_DISCLOSED = "NOT_DISCLOSED"

# Catches oos2, 2024-2029 (including notes_2025, OOS2_2025, 2025Q3, 2024-02-01, pnl_2026)
FORBIDDEN_TOKEN_PATTERN = re.compile(r"(?:oos2|(?<!\d)202[4-9](?!\d))", re.IGNORECASE)

ALLOWED_ROOT_KEYS = {'export_tier', 'description', 'gate_criteria', 'total_leads', 'leads'}
ALLOWED_LEAD_KEYS = {
    'lead_id', 'source', 'original_id', 'name', 'family', 'symbol',
    'timeframe', 'direction', 'rule_description', 'source_verdict',
    'passes_all_5', 'data_quality_flags', 'replicability', 'evidence_tier',
    'gate_condition_met', 'verified_live_links', 'performance_metrics'
}

# Offensive #3 extended cleanroom handoff allowlist (strict superset, zero holdout metrics)
ALLOWED_OFF3_ROOT_KEYS = ALLOWED_ROOT_KEYS | {
    'schema_version',
    'sources_merged',
    'dedup_summary',
    'prop_track_breakdown',
    'family_breakdown',
}
ALLOWED_OFF3_LEAD_KEYS = ALLOWED_LEAD_KEYS | {
    'source_origin',
    'source_url',
    'asset_class',
    'asset_universe',
    'prop_track',
    'family_tag',
    'economic_rationale',
    'counterparty_mechanism',
    'entry_rule',
    'exit_rule',
    'stop_loss_rule',
    'take_profit_rule',
    'verbatim_excerpt',
    'disqualifiers_checked',
    'dedup_status',
    'overlap_flags',
    'reported_winrate_pct',
    'reported_profit_factor',
    'reported_max_dd_pct',
}
OFF3_REQUIRED_LEAD_KEYS = {
    'lead_id',
    'source',
    'name',
    'symbol',
    'timeframe',
    'replicability',
    'evidence_tier',
}
ALLOWED_OFF3_REPLICABILITY = {
    'REPLICABLE_FROM_PUBLIC',
    'PARTIAL_RULE_SPEC',
    'PARTIAL_CONCEPT_ONLY',
    'CONCEPT_ONLY_NEEDS_SLTP_DESIGN',
    NOT_DISCLOSED,
}
ALLOWED_OFF3_EVIDENCE_TIERS = {
    'SOURCE_CLAIM_ONLY',
    'THIRD_PARTY_VERIFIED_REAL',
}
ALLOWED_OFF3_PROP_TRACKS = {
    'INTRADAY_SWAP0',
    'FTMO_SWING',
    'BOTH_INTRADAY_AND_SWING',
    NOT_DISCLOSED,
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

def validate_handoff_schema(data, schema_profile="master"):
    schema_errors = []
    if schema_profile == "offensive3":
        if not isinstance(data, dict):
            return ["Offensive #3 handoff payload must be a JSON object"]
        extra_root = set(data.keys()) - ALLOWED_OFF3_ROOT_KEYS
        if extra_root:
            schema_errors.append(f"Offensive3 root keys violate allowlist: {sorted(extra_root)}")
        leads_list = data.get('leads')
        if not isinstance(leads_list, list):
            schema_errors.append("Offensive3 root 'leads' must be a list")
            return schema_errors
        if data.get('total_leads') != len(leads_list):
            schema_errors.append(
                f"Offensive3 total_leads mismatch: {data.get('total_leads')} != len(leads)={len(leads_list)}"
            )
        seen_ids = set()
        for idx, item in enumerate(leads_list):
            if not isinstance(item, dict):
                schema_errors.append(f"Offensive3 Lead [{idx}] must be an object")
                continue
            extra_lead = set(item.keys()) - ALLOWED_OFF3_LEAD_KEYS
            if extra_lead:
                schema_errors.append(f"Offensive3 Lead [{idx}] keys violate allowlist: {sorted(extra_lead)}")
            missing_req = OFF3_REQUIRED_LEAD_KEYS - set(item.keys())
            if missing_req:
                schema_errors.append(f"Offensive3 Lead [{idx}] missing required keys: {sorted(missing_req)}")
            lid = item.get('lead_id')
            if not isinstance(lid, str) or not lid.strip():
                schema_errors.append(f"Offensive3 Lead [{idx}] has invalid lead_id: {lid!r}")
            elif lid in seen_ids:
                schema_errors.append(f"Offensive3 duplicate lead_id detected: {lid}")
            else:
                seen_ids.add(lid)
            ev_tier = item.get('evidence_tier')
            if ev_tier not in ALLOWED_OFF3_EVIDENCE_TIERS:
                schema_errors.append(f"Offensive3 Lead [{idx}] invalid evidence_tier: {ev_tier!r}")
            rep = item.get('replicability')
            if rep not in ALLOWED_OFF3_REPLICABILITY:
                schema_errors.append(f"Offensive3 Lead [{idx}] invalid replicability: {rep!r}")
            if 'prop_track' in item and item.get('prop_track') not in ALLOWED_OFF3_PROP_TRACKS:
                schema_errors.append(f"Offensive3 Lead [{idx}] invalid prop_track: {item.get('prop_track')!r}")
            pm = item.get('performance_metrics')
            if pm is not None:
                if not isinstance(pm, dict):
                    schema_errors.append(f"Offensive3 Lead [{idx}].performance_metrics must be a dict")
                elif pm:
                    schema_errors.extend(_validate_pm(pm, f"Offensive3 Lead [{idx}].performance_metrics"))
        return schema_errors

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


def scrub_holdout_tokens(obj):
    """Recursively strip all 2024..2029 / oos2 tokens and 2024..2099 numbers for cleanroom handoff."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            k_str = str(k)
            if FORBIDDEN_TOKEN_PATTERN.search(k_str):
                continue
            cleaned[k_str] = scrub_holdout_tokens(v)
        return cleaned
    if isinstance(obj, list):
        return [scrub_holdout_tokens(item) for item in obj]
    if isinstance(obj, str):
        return FORBIDDEN_TOKEN_PATTERN.sub("[REDACTED_HOLDOUT_PERIOD]", obj)
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if 2024 <= obj <= 2099:
            return NOT_DISCLOSED
        return obj
    return obj


def build_sanitized_offensive3_handoff(catalog_data):
    """Project catalog/auto_public_leads_v3.json onto strict Offensive #3 allowlist & scrub holdout tokens."""
    raw_leads = catalog_data.get('leads', []) if isinstance(catalog_data, dict) else []
    clean_leads = []

    for lead in raw_leads:
        if not isinstance(lead, dict):
            continue
        projected = {}
        for k in sorted(ALLOWED_OFF3_LEAD_KEYS):
            if k in lead:
                projected[k] = lead[k]
        # Cleanroom Offensive #3 handoff NEVER exports holdout or unverified performance tables
        projected['performance_metrics'] = {}
        if 'evidence_tier' not in projected:
            projected['evidence_tier'] = 'SOURCE_CLAIM_ONLY'
        if 'passes_all_5' not in projected:
            projected['passes_all_5'] = False
        if 'verified_live_links' not in projected:
            projected['verified_live_links'] = []

        # Flag transparently if source_url contained a redacted holdout year
        raw_url = str(projected.get('source_url', ''))
        if raw_url and FORBIDDEN_TOKEN_PATTERN.search(raw_url):
            dq = list(projected.get('data_quality_flags') or [])
            if 'URL_YEAR_REDACTED_IN_HANDOFF' not in dq:
                dq.append('URL_YEAR_REDACTED_IN_HANDOFF')
            projected['data_quality_flags'] = dq

        clean_leads.append(scrub_holdout_tokens(projected))

    handoff_payload = scrub_holdout_tokens({
        "schema_version": "off3-sanitized-handoff-v1",
        "export_tier": "CLEANROOM_HOLDOUT_SANITIZED_OFFENSIVE3",
        "description": (
            "Total Offensive #3 Cleanroom Handoff Package: deduplicated white-box Prop MT5 "
            "strategy specifications (Zero Hallucination, Zero Grid/Martingale, Holdout Sanitized)."
        ),
        "gate_criteria": {
            "condition_a": "Pure text/JSON public specification only (zero binary downloads, zero .mq5/.ex5 files)",
            "condition_b": (
                "Zero toxic Grid/Martingale/No-SL/Repaint/HFT mechanisms; deduplicated against 19 prior "
                "leads & cross-crawler overlaps; missing fields marked NOT_DISCLOSED; SOURCE_CLAIM_ONLY "
                "pending independent Dev M1 Bid/Ask backtest verification"
            ),
        },
        "sources_merged": catalog_data.get("sources_merged", []),
        "dedup_summary": catalog_data.get("dedup_summary", {}),
        "prop_track_breakdown": catalog_data.get("prop_track_breakdown", {}),
        "family_breakdown": catalog_data.get("family_breakdown", {}),
        "total_leads": len(clean_leads),
        "leads": clean_leads,
    })

    ok, violations = sanitize_and_validate(handoff_payload, schema_profile="offensive3")
    if not ok:
        raise ValueError(f"Sanitized Offensive #3 handoff failed validation: {violations[:10]}")
    return handoff_payload


def export_sanitized_offensive3(catalog_path=None, output_path=None):
    src_path = catalog_path or os.path.join(ROOT_DIR, 'catalog', 'auto_public_leads_v3.json')
    dst_path = output_path or os.path.join(HANDOFF_DIR, 'sanitized_offensive3_leads.json')
    with open(src_path, 'r', encoding='utf-8') as fp:
        catalog_data = json.load(fp)
    handoff_payload = build_sanitized_offensive3_handoff(catalog_data)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, 'w', encoding='utf-8', newline='\n') as fp:
        json.dump(handoff_payload, fp, ensure_ascii=False, indent=2)
        fp.write('\n')
    print(f"[+] Exported {handoff_payload['total_leads']} sanitized Offensive #3 leads to {dst_path}")
    return handoff_payload


def sanitize_and_validate(data, schema_profile="master"):
    v_tokens = recursive_check_holdout(data)
    v_schema = validate_handoff_schema(data, schema_profile=schema_profile)
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
        for f in sorted(filenames):
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
                    
                    # 2. Strict allowlist schema validation by handoff file profile
                    if f in ('sanitized_master_leads.json', 'sanitized_auto_leads.json'):
                        v_schema = validate_handoff_schema(json_data, schema_profile="master")
                        for err in v_schema:
                            violations.append((rel_path, err))
                    elif f == 'sanitized_offensive3_leads.json':
                        v_schema = validate_handoff_schema(json_data, schema_profile="offensive3")
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cleanroom Holdout Sanitizer & Handoff Validator")
    parser.add_argument(
        "--export-offensive3",
        action="store_true",
        help="Generate handoff/sanitized_offensive3_leads.json from catalog/auto_public_leads_v3.json before validating handoff/",
    )
    parser.add_argument(
        "--catalog-v3",
        default=None,
        help="Optional override path for auto_public_leads_v3.json",
    )
    parser.add_argument(
        "--output-off3",
        default=None,
        help="Optional override output path for sanitized_offensive3_leads.json",
    )
    parser.add_argument(
        "--handoff-dir",
        default=None,
        help="Optional override handoff directory to scan",
    )
    args = parser.parse_args(argv)

    if args.export_offensive3:
        export_sanitized_offensive3(catalog_path=args.catalog_v3, output_path=args.output_off3)

    ok = sanitize(handoff_dir=args.handoff_dir)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

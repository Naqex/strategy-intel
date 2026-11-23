import os
import json
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

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

def export_handoff():
    print("[*] Exporting sanitized cleanroom handoff package with strict recursive allowlist schema...")
    master_leads_path = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
    handoff_output_path = os.path.join(ROOT_DIR, 'handoff/sanitized_master_leads.json')

    with open(master_leads_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    clean_leads = []
    for lead in data.get('leads', []):
        # 1. Strict allowlist filter for lead keys
        clean_lead = {}
        for k in ALLOWED_LEAD_KEYS:
            if k in lead:
                clean_lead[k] = lead[k]
                
        # 2. Strict metric periods allowlist and recursive leaf pruning
        if 'performance_metrics' in clean_lead:
            raw_pm = clean_lead.get('performance_metrics', {})
            clean_pm = {}
            for period in ALLOWED_METRIC_PERIODS:
                if period in raw_pm and isinstance(raw_pm[period], dict):
                    raw_period = raw_pm[period]
                    clean_period = {}
                    for pk in ALLOWED_PERIOD_KEYS:
                        if pk in raw_period:
                            clean_period[pk] = raw_period[pk]
                    # Enforce strict years range inside nam_duong
                    if 'nam_duong' in clean_period and isinstance(clean_period['nam_duong'], dict):
                        allowed_years = ALLOWED_IS_YEARS if period == 'is_2004_2018' else ALLOWED_OOS1_YEARS
                        clean_period['nam_duong'] = {
                            str(yr): val for yr, val in clean_period['nam_duong'].items()
                            if str(yr) in allowed_years
                        }
                    clean_pm[period] = clean_period
            clean_lead['performance_metrics'] = clean_pm

        clean_leads.append(clean_lead)

    handoff_package = {
        "export_tier": "CLEANROOM_HOLDOUT_SANITIZED",
        "description": "Cleanroom Handoff Package for Internal Quant Research (Holdout Sanitized)",
        "gate_criteria": data.get("gate_criteria"),
        "total_leads": len(clean_leads),
        "leads": clean_leads
    }

    with open(handoff_output_path, 'w', encoding='utf-8') as f:
        json.dump(handoff_package, f, ensure_ascii=False, indent=2)

    print(f"[+] Exported {len(clean_leads)} sanitized leads to {handoff_output_path}")

if __name__ == '__main__':
    export_handoff()

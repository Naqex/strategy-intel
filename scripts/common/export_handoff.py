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

def export_handoff():
    print("[*] Exporting sanitized cleanroom handoff package with strict allowlist schema...")
    master_leads_path = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
    handoff_output_path = os.path.join(ROOT_DIR, 'handoff/sanitized_master_leads.json')

    with open(master_leads_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    clean_leads = []
    for lead in data.get('leads', []):
        # 1. Strict allowlist filter
        clean_lead = {}
        for k in ALLOWED_LEAD_KEYS:
            if k in lead:
                clean_lead[k] = lead[k]
                
        # 2. Strict metric periods allowlist
        if 'performance_metrics' in clean_lead:
            raw_pm = clean_lead['performance_metrics']
            clean_pm = {}
            for period in ALLOWED_METRIC_PERIODS:
                if period in raw_pm and raw_pm[period] is not None:
                    # Clean nam_duong to ensure no holdout year leakage
                    period_data = dict(raw_pm[period])
                    if 'nam_duong' in period_data:
                        clean_nd = {
                            yr: val for yr, val in period_data['nam_duong'].items()
                            if yr not in ['2024', '2025', '2026'] and int(yr) <= 2023
                        }
                        period_data['nam_duong'] = clean_nd
                    clean_pm[period] = period_data
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

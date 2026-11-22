import os
import json
import re
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

def export_handoff():
    print("[*] Exporting sanitized cleanroom handoff package...")
    master_leads_path = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
    handoff_output_path = os.path.join(ROOT_DIR, 'handoff/sanitized_master_leads.json')

    with open(master_leads_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    clean_leads = []
    for lead in data.get('leads', []):
        lead_copy = dict(lead)
        # Deep scrub any potential holdout fields
        if 'performance_metrics' in lead_copy:
            pm = dict(lead_copy['performance_metrics'])
            for k in list(pm.keys()):
                if '2025' in k or '2026' in k or 'oos2' in k.lower():
                    del pm[k]
            lead_copy['performance_metrics'] = pm

        for k in list(lead_copy.keys()):
            if '2025' in k or '2026' in k or 'oos2' in k.lower():
                del lead_copy[k]

        clean_leads.append(lead_copy)

    handoff_package = {
        "generated_at": datetime.now().isoformat(),
        "description": "Cleanroom Handoff Package for Internal Quant Research (Holdout 2025-2026 Sanitized)",
        "gate_criteria": data.get("gate_criteria"),
        "total_leads": len(clean_leads),
        "leads": clean_leads
    }

    with open(handoff_output_path, 'w', encoding='utf-8') as f:
        json.dump(handoff_package, f, ensure_ascii=False, indent=2)

    print(f"[+] Exported {len(clean_leads)} sanitized leads to {handoff_output_path}")

if __name__ == '__main__':
    export_handoff()

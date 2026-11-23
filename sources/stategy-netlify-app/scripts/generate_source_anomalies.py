import os
import json
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
REPORTS_DIR = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/raw/reports_json')
OUTPUT_PATH = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/extracted/source_anomalies.json')

def generate_anomalies():
    files = sorted([f for f in os.listdir(REPORTS_DIR) if f.endswith('.json')])
    mismatches = []
    missing_year_sets = []
    all_periods = {'IS': 15, 'OOS': 5, 'OOS2': 3}

    for fname in files:
        sid = fname.replace('.json', '')
        fpath = os.path.join(REPORTS_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as fp:
            d = json.load(fp)

        # Check years_pos vs True count
        for p in ['IS', 'OOS', 'OOS2']:
            part = d.get(p, {})
            nd = part.get('nam_duong')
            yp_str = part.get('years_pos')
            if nd and yp_str:
                true_count = sum(1 for v in nd.values() if v is True)
                try:
                    expected_pos = int(yp_str.split('/')[0])
                    if true_count != expected_pos:
                        mismatches.append({
                            'id': sid,
                            'period': p,
                            'years_pos_string': yp_str,
                            'expected_positive_years': expected_pos,
                            'actual_true_count_in_nam_duong': true_count,
                            'nam_duong': nd
                        })
                except Exception:
                    pass

        # Check missing year sets
        for p, exp_count in all_periods.items():
            nd = d.get(p, {}).get('nam_duong')
            if nd is None or len(nd) < exp_count:
                missing_year_sets.append({
                    'id': sid,
                    'period': p,
                    'years_present_count': len(nd) if nd else 0,
                    'expected_years_count': exp_count,
                    'missing_count': exp_count - (len(nd) if nd else 0),
                    'present_years': list(nd.keys()) if nd else []
                })

    unique_mismatch_ids = sorted(list(set(m['id'] for m in mismatches)))

    report = {
        "generated_at": datetime.now().isoformat(),
        "description": "Báo cáo kiểm toán độc lập các dị thường số liệu trong dữ liệu nguồn gốc raw/reports_json/ (242 chiến lược)",
        "audit_status": "WARN_SOURCE_ANOMALIES_LOGGED",
        "total_strategies_scanned": len(files),
        "mismatches_years_pos_count": len(unique_mismatch_ids),
        "mismatches_years_pos_ids": unique_mismatch_ids,
        "mismatches_detail": mismatches,
        "missing_years_in_nam_duong_count": len(missing_year_sets),
        "missing_years_detail": missing_year_sets
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)

    print(f"[+] Wrote source anomalies: {len(unique_mismatch_ids)} mismatches, {len(missing_year_sets)} missing year sets to {OUTPUT_PATH}")

if __name__ == '__main__':
    generate_anomalies()

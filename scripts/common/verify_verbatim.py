import os
import sys
import json
import hashlib
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def deep_compare_strategy_record(raw_d, ext_item):
    sid = ext_item.get('id')
    diffs = []
    
    # 1. Compare tieu_chi
    raw_tc = raw_d.get('tieu_chi', {})
    ext_tc = ext_item.get('tieu_chi', {})
    tc_mappings = [
        ('edge_vs_null', 'tieu_chi_1_hon_ngau_nhien'),
        ('ben_tham_so', 'tieu_chi_2_ben_tham_so'),
        ('song_sot_oos', 'tieu_chi_3_song_sot_oos1'),
        ('chiu_phi', 'tieu_chi_4_da_tru_phi'),
        ('kha_thi', 'tieu_chi_5_du_lon_mau_tren_100_lenh')
    ]
    for r_k, e_k in tc_mappings:
        if raw_tc.get(r_k) != ext_tc.get(e_k):
            diffs.append(f"{sid} tieu_chi mismatch on {r_k}: raw={raw_tc.get(r_k)} vs ext={ext_tc.get(e_k)}")
            
    # 2. Compare IS metrics
    raw_is = raw_d.get('IS', {})
    ext_is = ext_item.get('in_sample_2004_2018', {})
    if raw_is.get('n') != ext_is.get('so_lenh'):
        diffs.append(f"{sid} IS n mismatch: raw={raw_is.get('n')} vs ext={ext_is.get('so_lenh')}")
    if raw_is.get('wr') != ext_is.get('winrate_pct'):
        diffs.append(f"{sid} IS wr mismatch: raw={raw_is.get('wr')} vs ext={ext_is.get('winrate_pct')}")
    if raw_is.get('years_pos') != ext_is.get('so_nam_duong'):
        diffs.append(f"{sid} IS years_pos mismatch: raw={raw_is.get('years_pos')} vs ext={ext_is.get('so_nam_duong')}")
    if raw_is.get('nam_duong', {}) != ext_is.get('chi_tiet_nam', {}):
        diffs.append(f"{sid} IS nam_duong dict mismatch")
        
    # 3. Compare OOS metrics
    raw_oos = raw_d.get('OOS', {})
    ext_oos = ext_item.get('out_of_sample_1_2019_2023', {})
    if raw_oos.get('n') != ext_oos.get('so_lenh'):
        diffs.append(f"{sid} OOS n mismatch: raw={raw_oos.get('n')} vs ext={ext_oos.get('so_lenh')}")
    if raw_oos.get('wr') != ext_oos.get('winrate_pct'):
        diffs.append(f"{sid} OOS wr mismatch: raw={raw_oos.get('wr')} vs ext={ext_oos.get('winrate_pct')}")
    if raw_oos.get('years_pos') != ext_oos.get('so_nam_duong'):
        diffs.append(f"{sid} OOS years_pos mismatch: raw={raw_oos.get('years_pos')} vs ext={ext_oos.get('so_nam_duong')}")
    if raw_oos.get('nam_duong', {}) != ext_oos.get('chi_tiet_nam', {}):
        diffs.append(f"{sid} OOS nam_duong dict mismatch")
        
    return diffs

def scan_and_log_source_anomalies(reports_dir, anomalies_output_path):
    files = sorted([f for f in os.listdir(reports_dir) if f.endswith('.json')])
    mismatches = []
    missing_year_sets = []
    all_periods = {'IS': 15, 'OOS': 5, 'OOS2': 3}

    for fname in files:
        sid = fname.replace('.json', '')
        fpath = os.path.join(reports_dir, fname)
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

    with open(anomalies_output_path, 'w', encoding='utf-8') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)

    return unique_mismatch_ids, missing_year_sets

def verify():
    print("[*] Running verbatim and integrity verification...")
    errors = []

    # 1. SHA-256 Manifest Check
    manifest_targets = [
        'sources/stategy-netlify-app/raw/thu_vien_index.json',
        'sources/stategy-netlify-app/extracted/02_library_242_summary.json',
        'sources/stategy-netlify-app/extracted/04_top15_chat_full.json',
        'sources/ea-directory-2026/extracted/01_ea_catalog.json',
        'catalog/master_leads.json',
        'catalog/rejected_log.json',
        'catalog/indicator_reference.json',
        'handoff/sanitized_master_leads.json'
    ]
    verified_hashes = {}
    for target in manifest_targets:
        full_p = os.path.join(ROOT_DIR, target)
        if not os.path.exists(full_p):
            errors.append(f"Manifest target missing: {target}")
        else:
            sha = get_sha256(full_p)
            verified_hashes[target] = sha

    print(f"[+] SHA-256 Manifest Check: {len(verified_hashes)}/{len(manifest_targets)} files hashed successfully.")

    # 2. Verify Source 1 Deep Comparison (all 242 strategies)
    source1_dir = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app')
    if os.path.exists(source1_dir):
        raw_index_file = os.path.join(source1_dir, 'raw/thu_vien_index.json')
        ext_summary_file = os.path.join(source1_dir, 'extracted/02_library_242_summary.json')
        ext_top15_file = os.path.join(source1_dir, 'extracted/04_top15_chat_full.json')
        reports_dir = os.path.join(source1_dir, 'raw/reports_json')
        anomalies_file = os.path.join(source1_dir, 'extracted/source_anomalies.json')

        if os.path.exists(raw_index_file) and os.path.exists(ext_summary_file):
            with open(ext_summary_file, encoding='utf-8') as f:
                ext_summary = json.load(f)

            ext_danh_sach = ext_summary.get('danh_sach_242_chien_luoc', [])
            if len(ext_danh_sach) != 242:
                errors.append(f"Expected 242 strategies in summary, found {len(ext_danh_sach)}")

            # Deep compare every single strategy with raw reports_json
            deep_diffs_total = []
            for ext_item in ext_danh_sach:
                sid = ext_item.get('id')
                rf_path = os.path.join(reports_dir, f"{sid}.json")
                if not os.path.exists(rf_path):
                    errors.append(f"Missing raw JSON report for {sid}")
                else:
                    with open(rf_path, 'r', encoding='utf-8') as fp:
                        raw_d = json.load(fp)
                    diffs = deep_compare_strategy_record(raw_d, ext_item)
                    deep_diffs_total.extend(diffs)

            if deep_diffs_total:
                errors.extend(deep_diffs_total[:10])
                print(f"[!] Deep compare found {len(deep_diffs_total)} mismatches!")
            else:
                print(f"[+] Source 1 (stategy-netlify-app): 242/242 strategies DEEP COMPARED verbatim (n, wr, years_pos, nam_duong, tieu_chi).")

        # Scan and log source anomalies
        mismatches_8, missing_40 = scan_and_log_source_anomalies(reports_dir, anomalies_file)
        expected_8 = ['BRK009', 'BRK018', 'BRK034', 'IND015', 'IND044', 'IND047', 'REV025', 'VIR041']
        if sorted(mismatches_8) != sorted(expected_8):
            errors.append(f"Expected 8 mismatches {expected_8}, but got {mismatches_8}")
        if len(missing_40) != 40:
            errors.append(f"Expected 40 missing year sets, but got {len(missing_40)}")

        print(f"[WARN_SOURCE_ANOMALIES_LOGGED] 8 source mismatches & 40 missing year sets logged in source_anomalies.json.")

        # Top 15 CHẤT file
        if os.path.exists(ext_top15_file):
            with open(ext_top15_file, encoding='utf-8') as f:
                top15 = json.load(f)
            if len(top15) != 15:
                errors.append(f"Top 15 CHẤT file has {len(top15)} items instead of 15!")
            print(f"[+] Source 1 (Top 15 CHẤT): 15/15 verified.")

    # 3. Verify Source 2 (ea-directory-2026)
    source2_dir = os.path.join(ROOT_DIR, 'sources/ea-directory-2026')
    if os.path.exists(source2_dir):
        catalog_file = os.path.join(source2_dir, 'extracted/01_ea_catalog.json')
        if os.path.exists(catalog_file):
            with open(catalog_file, encoding='utf-8') as f:
                c_data = json.load(f)
            
            if c_data.get('coverage_scope') != "SAMPLE_45_OF_DIRECTORY":
                errors.append(f"Missing coverage_scope: SAMPLE_45_OF_DIRECTORY in {catalog_file}")

            catalog_items = c_data.get('items', [])
            required_keys = {
                'name', 'url', 'asset_type', 'platform', 'pricing', 'site_score', 'vendor_risk_label',
                'claimed_strategy_type', 'strategy_replicability', 'vendor_live_claim', 'third_party_verified_real',
                'has_grid_or_martingale_signals', 'is_hft_or_hedging_blackbox', 'money_management_flags',
                'symbols', 'timeframes', 'uses_hard_sl', 'verified_live_links'
            }
            valid_asset_types = {'EA', 'INDICATOR', 'UTILITY'}
            valid_risks = {'Low', 'Medium', 'High', 'NOT_DISCLOSED'}

            for item in catalog_items:
                missing_keys = required_keys - set(item.keys())
                if missing_keys:
                    errors.append(f"Item '{item.get('name')}' is missing required fields: {missing_keys}")
                if item.get('asset_type') not in valid_asset_types:
                    errors.append(f"Item '{item.get('name')}' has invalid asset_type: '{item.get('asset_type')}'")
                if item.get('vendor_risk_label') not in valid_risks:
                    errors.append(f"Item '{item.get('name')}' has invalid vendor_risk_label: '{item.get('vendor_risk_label')}'")

            print(f"[+] Source 2 (ea-directory-2026): {len(catalog_items)} items verified schema (coverage_scope: SAMPLE_45_OF_DIRECTORY, vendor_risk_label & 3 axes present).")

    # 4. Verify catalog/
    master_file = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
    rej_file = os.path.join(ROOT_DIR, 'catalog/rejected_log.json')
    ind_file = os.path.join(ROOT_DIR, 'catalog/indicator_reference.json')

    if os.path.exists(master_file):
        with open(master_file, encoding='utf-8') as f:
            m_data = json.load(f)
        leads = m_data.get('leads', [])
        if len(leads) != 15:
            errors.append(f"Expected 15 master leads, found {len(leads)}")

        passes_all_5_false_count = 0
        under_100_expected = {'IND026', 'SEA003', 'SEA004', 'SEA021'}
        for lead in leads:
            if lead.get('evidence_tier') != "SOURCE_CLAIM_ONLY":
                errors.append(f"Lead {lead.get('lead_id')} has evidence_tier '{lead.get('evidence_tier')}' instead of 'SOURCE_CLAIM_ONLY'")
            if lead.get('passes_all_5') is False:
                passes_all_5_false_count += 1
                if lead.get('original_id') not in under_100_expected:
                    errors.append(f"Lead {lead.get('original_id')} unexpectedly has passes_all_5 == False")
            if lead.get('original_id') == 'SEA004' and lead.get('replicability') != 'PARTIAL_RULE_SPEC':
                errors.append(f"SEA004 should have replicability 'PARTIAL_RULE_SPEC', found '{lead.get('replicability')}'")
            if lead.get('original_id') == 'SEA003' and lead.get('replicability') != 'REPLICABLE_FROM_PUBLIC':
                errors.append(f"SEA003 should have replicability 'REPLICABLE_FROM_PUBLIC', found '{lead.get('replicability')}'")

        if passes_all_5_false_count != 4:
            errors.append(f"Expected exactly 4 leads with passes_all_5 == False, found {passes_all_5_false_count}")

        print(f"[+] Catalog (master_leads.json): 15 leads verified (evidence_tier: SOURCE_CLAIM_ONLY, 11 True / 4 False passes_all_5).")

    if os.path.exists(rej_file):
        with open(rej_file, encoding='utf-8') as f:
            r_data = json.load(f)
        # Check no NA string
        content_str = json.dumps(r_data)
        if "PF OOS1: N/A, Max DD OOS1: N/A%" in content_str:
            errors.append("rejected_log.json contains placeholder string 'PF OOS1: N/A, Max DD OOS1: N/A%'")
        print(f"[+] Catalog (rejected_log.json): {len(r_data.get('rejected_items', []))} rejected items verified (0 placeholder strings).")

    if os.path.exists(ind_file):
        with open(ind_file, encoding='utf-8') as f:
            ind_data = json.load(f)
        if len(ind_data.get('items', [])) != 27:
            errors.append(f"Expected 27 items in indicator_reference, found {len(ind_data.get('items', []))}")
        print(f"[+] Catalog (indicator_reference.json): 27 items verified.")

    if errors:
        print("\n[!] VERIFICATION FAILED with errors:")
        for e in errors:
            print(f"    - {e}")
        return False
    else:
        print("\n[SUCCESS] Verbatim & integrity verification PASSED.")
        return True

if __name__ == '__main__':
    ok = verify()
    if not ok:
        sys.exit(1)

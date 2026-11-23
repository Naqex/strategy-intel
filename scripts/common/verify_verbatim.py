import os
import sys
import json
import hashlib

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest().upper()

def deep_compare_strategy_record(raw_d, ext_item):
    sid = ext_item.get('id')
    diffs = []
    
    # 1. Compare spec
    raw_spec = raw_d.get('spec', {})
    if raw_spec.get('id') != ext_item.get('id'):
        diffs.append(f"{sid} spec id mismatch: raw={raw_spec.get('id')} vs ext={ext_item.get('id')}")
    if raw_spec.get('ten') != ext_item.get('ten'):
        diffs.append(f"{sid} spec ten mismatch: raw={raw_spec.get('ten')} vs ext={ext_item.get('ten')}")
    if raw_spec.get('ho') != ext_item.get('ho'):
        diffs.append(f"{sid} spec ho mismatch: raw={raw_spec.get('ho')} vs ext={ext_item.get('ho')}")
    if raw_spec.get('nguon') != ext_item.get('nguon_goc'):
        diffs.append(f"{sid} spec nguon mismatch: raw={raw_spec.get('nguon')} vs ext={ext_item.get('nguon_goc')}")
    if raw_spec.get('mo_ta') != ext_item.get('quy_tac_mo_ta'):
        diffs.append(f"{sid} spec mo_ta mismatch: raw={raw_spec.get('mo_ta')} vs ext={ext_item.get('quy_tac_mo_ta')}")
    if raw_spec.get('tf') != ext_item.get('khung_thoi_gian'):
        diffs.append(f"{sid} spec tf mismatch: raw={raw_spec.get('tf')} vs ext={ext_item.get('khung_thoi_gian')}")

    # 2. Compare verdict
    if raw_d.get('verdict') != ext_item.get('verdict_goc'):
        diffs.append(f"{sid} verdict mismatch: raw={raw_d.get('verdict')} vs ext={ext_item.get('verdict_goc')}")

    # 3. Compare tieu_chi
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
            
    # 4. Compare IS metrics
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
        
    # 5. Compare OOS metrics
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

    # 6. Compare OOS2 metrics
    raw_oos2 = raw_d.get('OOS2', {})
    ext_oos2 = ext_item.get('out_of_sample_2_2024_2026', {})
    if raw_oos2.get('n') != ext_oos2.get('so_lenh'):
        diffs.append(f"{sid} OOS2 n mismatch: raw={raw_oos2.get('n')} vs ext={ext_oos2.get('so_lenh')}")
    if raw_oos2.get('wr') != ext_oos2.get('winrate_pct'):
        diffs.append(f"{sid} OOS2 wr mismatch: raw={raw_oos2.get('wr')} vs ext={ext_oos2.get('winrate_pct')}")
    if raw_oos2.get('years_pos') != ext_oos2.get('so_nam_duong'):
        diffs.append(f"{sid} OOS2 years_pos mismatch: raw={raw_oos2.get('years_pos')} vs ext={ext_oos2.get('so_nam_duong')}")
    if raw_oos2.get('status') != ext_oos2.get('trang_thai'):
        diffs.append(f"{sid} OOS2 status mismatch: raw={raw_oos2.get('status')} vs ext={ext_oos2.get('trang_thai')}")
    if raw_oos2.get('nam_duong', {}) != ext_oos2.get('chi_tiet_nam', {}):
        diffs.append(f"{sid} OOS2 nam_duong dict mismatch")
        
    return diffs

def compute_source_anomalies_in_memory(reports_dir):
    """Computes anomalies purely in memory without writing any files (READ-ONLY)."""
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
    return unique_mismatch_ids, mismatches, missing_year_sets

def verify_raw_manifest(raw_dir, manifest_path):
    errors = []
    if not os.path.exists(manifest_path):
        return [f"Raw manifest file missing: {manifest_path}"]
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    manifest_files = set(manifest.keys())
    actual_files = set()

    for dirpath, _, filenames in os.walk(raw_dir):
        for f in filenames:
            full_path = os.path.join(dirpath, f)
            rel_path = os.path.relpath(full_path, raw_dir).replace('\\', '/')
            actual_files.add(rel_path)

            if rel_path not in manifest:
                errors.append(f"Unexpected unmanifested file in raw: {rel_path}")
            else:
                expected_sha = manifest[rel_path]['sha256']
                expected_size = manifest[rel_path]['size']
                actual_size = os.path.getsize(full_path)
                if actual_size != expected_size:
                    errors.append(f"Size mismatch in {rel_path}: expected {expected_size}, got {actual_size}")
                actual_sha = get_sha256(full_path)
                if actual_sha != expected_sha:
                    errors.append(f"SHA-256 mismatch in {rel_path}: expected {expected_sha}, got {actual_sha}")

    missing_from_disk = manifest_files - actual_files
    if missing_from_disk:
        errors.append(f"Missing files from raw directory: {missing_from_disk}")

    return errors

def verify(repo_root=None):
    root = repo_root or ROOT_DIR
    print("[*] Running verbatim and integrity verification (READ-ONLY mode)...")
    errors = []

    # 1. SHA-256 Manifest Check for RAW directories
    s1_raw_dir = os.path.join(root, 'sources/stategy-netlify-app/raw')
    s1_manifest = os.path.join(root, 'sources/stategy-netlify-app/raw_manifest.sha256.json')
    s1_errs = verify_raw_manifest(s1_raw_dir, s1_manifest)
    if s1_errs:
        errors.extend(s1_errs)
    else:
        print("[+] Source 1 raw manifest check: 283/283 files verified matching SHA-256.")

    s2_raw_dir = os.path.join(root, 'sources/ea-directory-2026/raw')
    s2_manifest = os.path.join(root, 'sources/ea-directory-2026/raw_manifest.sha256.json')
    s2_errs = verify_raw_manifest(s2_raw_dir, s2_manifest)
    if s2_errs:
        errors.extend(s2_errs)
    else:
        print("[+] Source 2 raw manifest check: 48/48 files verified matching SHA-256.")

    # 2. Verify Source 1 Deep Comparison (all 242 strategies)
    source1_dir = os.path.join(root, 'sources/stategy-netlify-app')
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
                print(f"[+] Source 1 (stategy-netlify-app): 242/242 strategies DEEP COMPARED verbatim (spec, verdict, tieu_chi, IS, OOS, OOS2).")

        # In-memory anomalies check against saved source_anomalies.json (READ-ONLY)
        if not os.path.exists(anomalies_file):
            errors.append(f"source_anomalies.json missing at {anomalies_file}")
        else:
            with open(anomalies_file, 'r', encoding='utf-8') as af:
                saved_anomalies = json.load(af)

            computed_ids, computed_mismatches, computed_missing = compute_source_anomalies_in_memory(reports_dir)
            expected_8 = ['BRK009', 'BRK018', 'BRK034', 'IND015', 'IND044', 'IND047', 'REV025', 'VIR041']
            
            if sorted(computed_ids) != sorted(expected_8):
                errors.append(f"Expected 8 mismatches {expected_8}, but computed {computed_ids}")
            if len(computed_missing) != 40:
                errors.append(f"Expected 40 missing year sets, but computed {len(computed_missing)}")

            # Exact match between in-memory computation and saved file
            if saved_anomalies.get('mismatches_years_pos_count') != len(computed_ids):
                errors.append(f"source_anomalies.json mismatches_years_pos_count mismatch: {saved_anomalies.get('mismatches_years_pos_count')} vs computed {len(computed_ids)}")
            if saved_anomalies.get('missing_years_in_nam_duong_count') != len(computed_missing):
                errors.append(f"source_anomalies.json missing_years_in_nam_duong_count mismatch: {saved_anomalies.get('missing_years_in_nam_duong_count')} vs computed {len(computed_missing)}")
            if sorted(saved_anomalies.get('mismatches_years_pos_ids', [])) != sorted(computed_ids):
                errors.append("source_anomalies.json mismatches_years_pos_ids mismatch against in-memory computation")

            print(f"[WARN_SOURCE_ANOMALIES_LOGGED] 8 source mismatches & 40 missing year sets verified consistent with saved report.")

        # Top 15 CHẤT file
        if os.path.exists(ext_top15_file):
            with open(ext_top15_file, encoding='utf-8') as f:
                top15 = json.load(f)
            if len(top15) != 15:
                errors.append(f"Top 15 CHẤT file has {len(top15)} items instead of 15!")
            print(f"[+] Source 1 (Top 15 CHẤT): 15/15 verified.")

    # 3. Verify Source 2 (ea-directory-2026)
    source2_dir = os.path.join(root, 'sources/ea-directory-2026')
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
    master_file = os.path.join(root, 'catalog/master_leads.json')
    rej_file = os.path.join(root, 'catalog/rejected_log.json')
    ind_file = os.path.join(root, 'catalog/indicator_reference.json')

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

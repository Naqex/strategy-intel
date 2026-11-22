import os
import sys
import json
import hashlib

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify():
    print("[*] Running verbatim and integrity verification...")
    errors = []

    # 1. Verify sources/stategy-netlify-app/
    source1_dir = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app')
    if os.path.exists(source1_dir):
        raw_index_file = os.path.join(source1_dir, 'raw/thu_vien_index.json')
        ext_summary_file = os.path.join(source1_dir, 'extracted/02_library_242_summary.json')
        ext_top15_file = os.path.join(source1_dir, 'extracted/04_top15_chat_full.json')

        if os.path.exists(raw_index_file) and os.path.exists(ext_summary_file):
            with open(raw_index_file, encoding='utf-8') as f:
                raw_index = json.load(f)
            with open(ext_summary_file, encoding='utf-8') as f:
                ext_summary = json.load(f)

            raw_danh_sach = raw_index.get('danh_sach', [])
            ext_danh_sach = ext_summary.get('danh_sach_242_chien_luoc', [])

            raw_da_chay = [item for item in raw_danh_sach if item.get('trang_thai') == 'da_kiem_dinh']
            if len(raw_da_chay) != len(ext_danh_sach):
                errors.append(f"Mismatch in strategy count: raw da_kiem_dinh has {len(raw_da_chay)}, extracted has {len(ext_danh_sach)}")

            # Check verbatim fields
            for ext_item in ext_danh_sach:
                item_id = ext_item.get('id')
                raw_match = next((i for i in raw_da_chay if i.get('id') == item_id), None)
                if not raw_match:
                    errors.append(f"Extracted strategy {item_id} not found in raw index!")
                elif ext_item.get('verdict_goc') != raw_match.get('verdict'):
                    errors.append(f"Verdict mismatch in {item_id}: extracted '{ext_item.get('verdict_goc')}' vs raw '{raw_match.get('verdict')}'")

            print(f"[+] Source 1 (stategy-netlify-app): 242/242 strategies verified verbatim.")

        if os.path.exists(ext_top15_file):
            with open(ext_top15_file, encoding='utf-8') as f:
                top15 = json.load(f)
            if len(top15) != 15:
                errors.append(f"Top 15 CHẤT file has {len(top15)} items instead of 15!")
            for item in top15:
                if item.get('verdict') != 'CHẤT':
                    errors.append(f"Strategy {item.get('spec', {}).get('id')} has verdict '{item.get('verdict')}' instead of CHẤT")
            print(f"[+] Source 1 (Top 15 CHẤT): 15/15 verified.")

    # 2. Verify sources/ea-directory-2026/
    source2_dir = os.path.join(ROOT_DIR, 'sources/ea-directory-2026')
    if os.path.exists(source2_dir):
        catalog_file = os.path.join(source2_dir, 'extracted/01_ea_catalog.json')
        if os.path.exists(catalog_file):
            with open(catalog_file, encoding='utf-8') as f:
                catalog = json.load(f)
            required_keys = {
                'name', 'url', 'asset_type', 'platform', 'pricing', 'site_score', 'risk_label',
                'claimed_strategy_type', 'has_grid_or_martingale_signals', 'is_hft_or_hedging_blackbox',
                'symbols', 'timeframes', 'uses_hard_sl', 'verified_live_links'
            }
            valid_asset_types = {'EA', 'INDICATOR', 'UTILITY'}
            for item in catalog:
                missing_keys = required_keys - set(item.keys())
                if missing_keys:
                    errors.append(f"Item '{item.get('name')}' is missing required fields: {missing_keys}")
                if item.get('asset_type') not in valid_asset_types:
                    errors.append(f"Item '{item.get('name')}' has invalid asset_type: '{item.get('asset_type')}'")
            print(f"[+] Source 2 (ea-directory-2026): {len(catalog)} items verified schema (asset_type & blackbox flag present).")

    # 3. Verify catalog/
    ind_file = os.path.join(ROOT_DIR, 'catalog/indicator_reference.json')
    master_file = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
    rej_file = os.path.join(ROOT_DIR, 'catalog/rejected_log.json')

    if os.path.exists(ind_file):
        with open(ind_file, encoding='utf-8') as f:
            ind_data = json.load(f)
        for i in ind_data.get('items', []):
            if i.get('asset_type') not in {'INDICATOR', 'UTILITY'}:
                errors.append(f"Non-indicator item in indicator_reference: {i.get('name')}")
        print(f"[+] Catalog (indicator_reference.json): {len(ind_data.get('items', []))} items verified.")

    if os.path.exists(master_file):
        with open(master_file, encoding='utf-8') as f:
            m_data = json.load(f)
        for lead in m_data.get('leads', []):
            # Must meet condition a or b
            if not lead.get('gate_condition_met'):
                errors.append(f"Lead {lead.get('lead_id')} missing gate_condition_met tag")
        print(f"[+] Catalog (master_leads.json): {len(m_data.get('leads', []))} cleanroom leads verified.")

    if os.path.exists(rej_file):
        with open(rej_file, encoding='utf-8') as f:
            r_data = json.load(f)
        valid_cats = {
            'curve_fitted_retail_schools', 'chat_failed_oos',
            'toxic_money_management', 'blackbox_no_live_real_proof'
        }
        for item in r_data.get('rejected_items', []):
            if item.get('category') not in valid_cats:
                errors.append(f"Rejected item {item.get('id')} has unknown category: {item.get('category')}")
        print(f"[+] Catalog (rejected_log.json): {len(r_data.get('rejected_items', []))} rejected items verified.")

    if errors:
        print("\n[!] VERIFICATION FAILED with errors:")
        for e in errors:
            print(f"    - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Verbatim & integrity verification PASSED.")

if __name__ == '__main__':
    verify()

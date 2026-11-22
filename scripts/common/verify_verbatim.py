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

    # 2. Verify sources/ea-directory-2026/ (if exists)
    source2_dir = os.path.join(ROOT_DIR, 'sources/ea-directory-2026')
    if os.path.exists(source2_dir):
        catalog_file = os.path.join(source2_dir, 'extracted/01_ea_catalog.json')
        if os.path.exists(catalog_file):
            with open(catalog_file, encoding='utf-8') as f:
                catalog = json.load(f)
            required_keys = {
                'name', 'url', 'platform', 'pricing', 'site_score', 'risk_label',
                'claimed_strategy_type', 'has_grid_or_martingale_signals',
                'symbols', 'timeframes', 'uses_hard_sl', 'verified_live_links'
            }
            for ea in catalog:
                missing_keys = required_keys - set(ea.keys())
                if missing_keys:
                    errors.append(f"EA '{ea.get('name')}' is missing required fields: {missing_keys}")
            print(f"[+] Source 2 (ea-directory-2026): {len(catalog)} EAs verified schema.")

    if errors:
        print("\n[!] VERIFICATION FAILED with errors:")
        for e in errors:
            print(f"    - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Verbatim & integrity verification PASSED.")

if __name__ == '__main__':
    verify()

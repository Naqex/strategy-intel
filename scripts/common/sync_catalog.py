import os
import json
import re
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

def sync_catalog():
    print("[*] Synchronizing catalog with tightened clean-room criteria...")

    source1_top15_path = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/extracted/04_top15_chat_full.json')
    source2_catalog_path = os.path.join(ROOT_DIR, 'sources/ea-directory-2026/extracted/01_ea_catalog.json')
    source1_missing_path = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/extracted/07_missing_58_items.json')
    source1_summary_path = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/extracted/02_library_242_summary.json')

    # 1. Load Source 1 Top 15 CHẤT
    with open(source1_top15_path, 'r', encoding='utf-8') as f:
        top15_data = json.load(f)

    # 2. Load Source 2 extracted catalog
    with open(source2_catalog_path, 'r', encoding='utf-8') as f:
        s2_items = json.load(f)

    # 3. Load Source 1 failed/missing for rejected_log
    with open(source1_missing_path, 'r', encoding='utf-8') as f:
        missing_58 = json.load(f)
    with open(source1_summary_path, 'r', encoding='utf-8') as f:
        summary_242 = json.load(f)

    # Separate Source 2 items: Indicators & Utilities vs EAs
    indicators_and_utilities = []
    eas_source2 = []

    for item in s2_items:
        asset_type = item.get('asset_type', 'EA')
        if asset_type in ['INDICATOR', 'UTILITY']:
            indicators_and_utilities.append(item)
        else:
            eas_source2.append(item)

    # 4. Build catalog/indicator_reference.json
    ind_reference_path = os.path.join(ROOT_DIR, 'catalog/indicator_reference.json')
    indicator_package = {
        "generated_at": datetime.now().isoformat(),
        "source": "ea-directory-2026",
        "total_items": len(indicators_and_utilities),
        "indicators_count": sum(1 for i in indicators_and_utilities if i.get('asset_type') == 'INDICATOR'),
        "utilities_count": sum(1 for i in indicators_and_utilities if i.get('asset_type') == 'UTILITY'),
        "items": [
            {
                "id": i['url'].split('/')[-1],
                "name": i['name'],
                "asset_type": i['asset_type'],
                "url": i['url'],
                "platform": i['platform'],
                "pricing": i['pricing'],
                "site_score": i['site_score'],
                "claimed_strategy_type": i['claimed_strategy_type'],
                "symbols": i['symbols'],
                "timeframes": i['timeframes'],
                "description": f"Công cụ phân tích/hỗ trợ kỹ thuật ({i['asset_type']}) dựa trên {i['claimed_strategy_type']}."
            }
            for i in indicators_and_utilities
        ]
    }
    with open(ind_reference_path, 'w', encoding='utf-8') as f:
        json.dump(indicator_package, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved {ind_reference_path} ({len(indicators_and_utilities)} indicators & utilities)")

    # 5. Evaluate Source 2 EAs against Gate Criteria:
    # Condition (a): Live Real Verified link (NOT demo, NOT grid/hft/hedging)
    # Condition (b): Clearly stated independent trading mechanism (none of the closed commercial EAs)
    verified_real_eas = []
    rejected_grid_eas = []
    rejected_blackbox_eas = []

    for ea in eas_source2:
        has_grid = ea.get('has_grid_or_martingale_signals', False)
        live_links = ea.get('verified_live_links', [])
        
        # Check if real live proof exists (excluding demo)
        real_live_links = [link for link in live_links if 'demo' not in link.lower() and ('myfxbook.com' in link.lower() or 'mql5.com' in link.lower())]
        
        if has_grid:
            rejected_grid_eas.append(ea)
        elif real_live_links and not ea.get('is_hft_or_hedging_blackbox', False):
            verified_real_eas.append(ea)
        else:
            # Blackbox commercial EA without live real proof
            rejected_blackbox_eas.append(ea)

    print(f"[*] Source 2 EA Evaluation: {len(verified_real_eas)} Verified Real, {len(rejected_grid_eas)} Toxic Grid, {len(rejected_blackbox_eas)} Blackbox No Real Proof")

    # 6. Build catalog/master_leads.json
    # Only items satisfying Condition (a) or Condition (b)
    master_leads_list = []

    # Add Source 1 Top 15 CHẤT (Condition b)
    for strat in top15_data:
        spec = strat.get('spec', {})
        perf = strat.get('performance', {})
        audit = strat.get('replicability_audit', {})
        
        lead_id = f"LEAD-NETLIFY-{spec.get('id')}"
        master_leads_list.append({
            "lead_id": lead_id,
            "source": "stategy-netlify-app",
            "original_id": spec.get('id'),
            "name": spec.get('name'),
            "family": spec.get('family'),
            "symbol": spec.get('symbol', 'XAUUSD'),
            "timeframe": spec.get('timeframe'),
            "direction": spec.get('direction'),
            "rule_description": spec.get('rule_description'),
            "replicability": audit.get('status', 'PARTIAL_CONCEPT_ONLY'),
            "status": "VERIFIED_QUANT_EDGE",
            "gate_condition_met": "Condition (b): Independently verifiable quantitative mechanism with proven edge (Top 15 CHẤT)",
            "verified_live_links": [],
            "performance_metrics": {
                "is_2004_2018": perf.get('is_2004_2018'),
                "oos1_2019_2023": perf.get('oos1_2019_2023')
            }
        })

    # Add any Verified Real EAs from Source 2 (Condition a)
    for ea in verified_real_eas:
        lead_id = f"LEAD-EAFREE-{re.sub(r'[^a-zA-Z0-9]', '', ea['name'])[:16].upper()}"
        master_leads_list.append({
            "lead_id": lead_id,
            "source": "ea-directory-2026",
            "original_id": ea['url'].split('/')[-1],
            "name": ea['name'],
            "family": ea['claimed_strategy_type'],
            "symbol": ', '.join(ea['symbols']),
            "timeframe": ', '.join(ea['timeframes']),
            "direction": "Both",
            "rule_description": f"Chiến lược {ea['claimed_strategy_type']}. {ea['grid_martingale_rationale']}",
            "replicability": "CONCEPT_ONLY_COMMERCIAL_EA",
            "status": "VERIFIED_LIVE_REAL_PROOF",
            "gate_condition_met": "Condition (a): EA with Live Real Verified proof",
            "verified_live_links": ea['verified_live_links']
        })

    master_leads_path = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
    master_package = {
        "generated_at": datetime.now().isoformat(),
        "gate_criteria": {
            "condition_a": "EA with Live Real Verified link (strictly excluding demo, grid, HFT, hedging)",
            "condition_b": "Independently verifiable trading mechanism with quantified edge (Top 15 CHẤT from Source 1)"
        },
        "sources": ["stategy-netlify-app"] + (["ea-directory-2026"] if verified_real_eas else []),
        "total_leads": len(master_leads_list),
        "leads": master_leads_list
    }
    with open(master_leads_path, 'w', encoding='utf-8') as f:
        json.dump(master_package, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved {master_leads_path} ({len(master_leads_list)} leads)")

    # 7. Build catalog/rejected_log.json
    rejected_log_path = os.path.join(ROOT_DIR, 'catalog/rejected_log.json')
    
    # Source 1 rejected
    # 18 subjective retail items from missing 58 (chua_kiem_dinh)
    s1_retail = [item for item in missing_58.get('danh_sach_chi_tiet_58_muc', []) if item.get('trang_thai') == 'chua_kiem_dinh']
    # 188 OOS failed (CHÁT)
    s1_chat = [item for item in summary_242.get('danh_sach_242_chien_luoc', []) if item.get('verdict_goc') == 'CHÁT']

    rejected_rules = []
    # Add retail
    for r in s1_retail:
        rejected_rules.append({
            "id": r.get('id'),
            "source": "stategy-netlify-app",
            "name": r.get('ten'),
            "category": "curve_fitted_retail_schools",
            "reason": "Chiến lược vẽ tay cảm tính (trendlines, mô hình giá chủ quan), không đủ điều kiện định lượng bằng máy."
        })
    # Add CHÁT
    for c in s1_chat:
        rejected_rules.append({
            "id": c.get('id'),
            "source": "stategy-netlify-app",
            "name": c.get('ten'),
            "category": "chat_failed_oos",
            "reason": f"Sụp đổ hiệu suất Out-of-Sample (Verdict: CHÁT, PF OOS1: {c.get('pf_oos1', 'N/A')}, Max DD OOS1: {c.get('dd_oos1_pct', 'N/A')}%)."
        })
    # Add Source 2 Grid/Martingale EAs
    for g in rejected_grid_eas:
        rejected_rules.append({
            "id": g['url'].split('/')[-1],
            "source": "ea-directory-2026",
            "name": g['name'],
            "category": "toxic_money_management",
            "reason": f"GRID_MARTINGALE_TOXIC_RISK: {g['grid_martingale_rationale']}"
        })
    # Add Source 2 Blackbox EAs without Live Real Proof
    for b in rejected_blackbox_eas:
        rejected_rules.append({
            "id": b['url'].split('/')[-1],
            "source": "ea-directory-2026",
            "name": b['name'],
            "category": "blackbox_no_live_real_proof",
            "reason": "NO_LIVE_REAL_PROOF_BLACKBOX: EA thương mại đóng mã nguồn không có liên kết kiểm chứng tài khoản thật (Myfxbook/MQL5 Live Real), không đủ điều kiện đưa vào danh mục định lượng."
        })

    rejected_package = {
        "generated_at": datetime.now().isoformat(),
        "total_rejected": len(rejected_rules),
        "rejection_categories": {
            "curve_fitted_retail_schools": {
                "description": "Các trường phái bán lẻ vẽ tay cảm tính, không kiểm định được bằng máy",
                "count": len(s1_retail)
            },
            "chat_failed_oos": {
                "description": "Các chiến lược sụp đổ ở giai đoạn Out-of-Sample",
                "count": len(s1_chat)
            },
            "toxic_money_management": {
                "description": "Hệ thống sử dụng bẫy Grid, Martingale, nhồi lệnh rủi ro cao",
                "count": len(rejected_grid_eas)
            },
            "blackbox_no_live_real_proof": {
                "description": "EA thương mại hộp đen không có tài khoản thật Live Real kiểm chứng",
                "count": len(rejected_blackbox_eas)
            }
        },
        "rejected_items": rejected_rules
    }
    with open(rejected_log_path, 'w', encoding='utf-8') as f:
        json.dump(rejected_package, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved {rejected_log_path} ({len(rejected_rules)} rejected items)")

if __name__ == '__main__':
    sync_catalog()

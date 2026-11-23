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
    source1_index_path = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/raw/thu_vien_index.json')
    source1_reports_dir = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/raw/reports_json')

    # 1. Load Source 1 Top 15 CHẤT
    with open(source1_top15_path, 'r', encoding='utf-8') as f:
        top15_data = json.load(f)

    # 2. Load Source 2 extracted catalog
    with open(source2_catalog_path, 'r', encoding='utf-8') as f:
        s2_raw = json.load(f)
    s2_items = s2_raw.get('items', s2_raw) if isinstance(s2_raw, dict) else s2_raw

    # 3. Load Source 1 missing 58 items and raw index
    with open(source1_missing_path, 'r', encoding='utf-8') as f:
        missing_58 = json.load(f)
    with open(source1_index_path, 'r', encoding='utf-8') as f:
        raw_index = json.load(f)
    index_map = {item['id']: item for item in raw_index.get('danh_sach', [])}

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
        "coverage_scope": "SAMPLE_45_OF_DIRECTORY",
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
                "vendor_risk_label": i.get('vendor_risk_label', 'NOT_DISCLOSED'),
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
    verified_real_eas = []
    rejected_grid_eas = []
    rejected_blackbox_eas = []

    for ea in eas_source2:
        has_grid = ea.get('has_grid_or_martingale_signals', False)
        is_real = ea.get('third_party_verified_real', False)
        
        if has_grid:
            rejected_grid_eas.append(ea)
        elif is_real and not ea.get('is_hft_or_hedging_blackbox', False):
            verified_real_eas.append(ea)
        else:
            rejected_blackbox_eas.append(ea)

    print(f"[*] Source 2 EA Evaluation: {len(verified_real_eas)} Verified Real, {len(rejected_grid_eas)} Toxic Grid, {len(rejected_blackbox_eas)} Blackbox No Real Proof")

    # 6. Build catalog/master_leads.json
    master_leads_list = []

    for strat in top15_data:
        spec = strat.get('spec', {})
        strat_id = spec.get('id')
        tc = strat.get('tieu_chi', {})
        
        # Calculate passes_all_5 and feasibility flag purely dynamically from tieu_chi
        is_kha_thi = tc.get('kha_thi', True) if tc else False
        passes_all_5 = bool(all(tc.values())) if tc else False
        
        # Replicability classification
        if strat_id == 'SEA003':
            replicability = "REPLICABLE_FROM_PUBLIC"
        elif strat_id == 'SEA004':
            replicability = "PARTIAL_RULE_SPEC"
        else:
            replicability = "PARTIAL_CONCEPT_ONLY"
            
        # Data quality flags
        dq_flags = [
            "COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD",
            "MISSING_PF_AND_DD_IN_PUBLIC_JSON"
        ]
        if not is_kha_thi:
            dq_flags.append("FAILED_FEASIBILITY_UNDER_100_TRADES")
        if strat_id == 'SEA004':
            dq_flags.append("MISSING_DIRECTION_RULE_SPEC")

        # Dynamically derive direction from verbatim rule description
        mo_ta_lower = (spec.get('mo_ta') or '').lower()
        has_buy = bool(re.search(r'\bmua\b', mo_ta_lower))
        has_sell = bool(re.search(r'\bbán\b', mo_ta_lower))
        if has_buy and not has_sell:
            direction = "Long"
        elif has_sell and not has_buy:
            direction = "Short"
        else:
            direction = "Both"

        lead_id = f"LEAD-NETLIFY-{strat_id}"
        master_leads_list.append({
            "lead_id": lead_id,
            "source": "stategy-netlify-app",
            "original_id": strat_id,
            "name": spec.get('ten'),
            "family": spec.get('ho'),
            "symbol": "XAUUSD",
            "timeframe": spec.get('tf'),
            "direction": direction,
            "rule_description": spec.get('mo_ta'),
            "source_verdict": "CHẤT",
            "passes_all_5": passes_all_5,
            "data_quality_flags": dq_flags,
            "replicability": replicability,
            "evidence_tier": "SOURCE_CLAIM_ONLY",
            "gate_condition_met": "SOURCE_CONCEPT_CANDIDATE_QUARANTINED: source claim only, pending independent reproduction in Naqex/workspace",
            "verified_live_links": [],
            "performance_metrics": {
                "is_2004_2018": strat.get('IS'),
                "oos1_2019_2023": strat.get('OOS')
            }
        })

    # Add any Verified Real EAs from Source 2 (Condition a) - currently 0
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
            "source_verdict": "VENDOR_CLAIM",
            "passes_all_5": False,
            "data_quality_flags": [],
            "replicability": "CONCEPT_ONLY_COMMERCIAL_EA",
            "evidence_tier": "THIRD_PARTY_VERIFIED_REAL",
            "gate_condition_met": "Condition (a): EA with Live Real Verified proof",
            "verified_live_links": ea['verified_live_links']
        })

    master_leads_path = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
    master_package = {
        "generated_at": datetime.now().isoformat(),
        "gate_criteria": {
            "condition_a": "EA with Live Real Verified link (strictly excluding demo, grid, HFT, hedging)",
            "condition_b": "Public source concept lead (SOURCE_CLAIM_ONLY; quarantined pending independent white-box formalization & M1 Bid/Ask verification in Naqex/workspace)"
        },
        "sources": ["stategy-netlify-app"] + (["ea-directory-2026"] if verified_real_eas else []),
        "total_leads": len(master_leads_list),
        "leads": master_leads_list
    }
    with open(master_leads_path, 'w', encoding='utf-8') as f:
        json.dump(master_package, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved {master_leads_path} ({len(master_leads_list)} leads, evidence_tier: SOURCE_CLAIM_ONLY)")

    # 7. Build catalog/rejected_log.json
    rejected_log_path = os.path.join(ROOT_DIR, 'catalog/rejected_log.json')
    
    # 18 unverified items from missing 58
    s1_unverified = [item for item in missing_58.get('danh_sach_chi_tiet_58_muc', []) if item.get('trang_thai') == 'chua_kiem_dinh']
    
    # 188 OOS failed (CHÁT)
    s1_chat_ids = [item['id'] for item in raw_index.get('danh_sach', []) if item.get('trang_thai') == 'da_kiem_dinh' and item.get('verdict') == 'CHÁT']

    rejected_rules = []
    
    # Add 18 unverified items with exact sub-categories
    for u in s1_unverified:
        rejected_rules.append({
            "id": u.get('id'),
            "source": "stategy-netlify-app",
            "name": u.get('ten'),
            "category": "unverified_discretionary_or_missing_data",
            "sub_category": u.get('unverified_category', 'DISCRETIONARY_NOT_FORMALIZED'),
            "reason": u.get('ly_do_thieu_file_json', 'Chưa kiểm định do thiếu dữ liệu hoặc quy tắc cảm tính.'),
            "missing_evidence": "Không có tệp dữ liệu backtest định lượng do thiếu nguồn dữ liệu phụ trợ hoặc quy tắc chưa được thuật toán hóa khách quan."
        })

    # Add 188 CHÁT strategies with reasons directly from tieu_chi and index
    for cid in s1_chat_ids:
        idx_meta = index_map.get(cid, {})
        rf_path = os.path.join(source1_reports_dir, f"{cid}.json")
        tc = {}
        spec_meta = {}
        if os.path.exists(rf_path):
            with open(rf_path, 'r', encoding='utf-8') as rf:
                r_json = json.load(rf)
                tc = r_json.get('tieu_chi', {})
                spec_meta = r_json.get('spec', {})

        failed_reasons = []
        if tc.get('edge_vs_null') is False:
            failed_reasons.append("Không hơn ngẫu nhiên (p-value null model)")
        if tc.get('ben_tham_so') is False:
            failed_reasons.append("Không bền tham số (curve-fitting)")
        if tc.get('song_sot_oos') is False:
            failed_reasons.append("Thất bại sống sót OOS1")
        if tc.get('chiu_phi') is False:
            failed_reasons.append("Không chịu được ma sát chi phí giao dịch")
        if tc.get('kha_thi') is False:
            failed_reasons.append("Không khả thi thực tế (<100 lệnh)")

        failed_str = "; ".join(failed_reasons) if failed_reasons else "Thất bại kiểm định tiêu chí Out-of-Sample"
        oos_years = idx_meta.get('oos_years', 'N/A')
        oos_n = idx_meta.get('oos_n', 'N/A')

        rejected_rules.append({
            "id": cid,
            "source": "stategy-netlify-app",
            "name": idx_meta.get('ten') or spec_meta.get('ten') or cid,
            "category": "chat_failed_oos",
            "reason": f"Sụp đổ hiệu suất OOS (Verdict: CHÁT, Tiêu chí trượt: [{failed_str}], OOS1 Dương: {oos_years}, Số lệnh OOS1: {oos_n}).",
            "failed_criteria": failed_reasons,
            "missing_evidence": "Thiếu dữ liệu chi tiết Profit Factor và Max Drawdown nội nến trong tệp JSON công khai; không đạt các tiêu chuẩn kiểm định định lượng."
        })

    # Add Source 2 Grid/Martingale EAs
    for g in rejected_grid_eas:
        rejected_rules.append({
            "id": g['url'].split('/')[-1],
            "source": "ea-directory-2026",
            "name": g['name'],
            "category": "toxic_money_management",
            "reason": f"GRID_MARTINGALE_TOXIC_RISK: {g['grid_martingale_rationale']}",
            "missing_evidence": "Hệ thống sử dụng nhồi lệnh, hệ số nhân lot hoặc lưới giá rủi ro cháy tài khoản, vi phạm guardrails quản lý vốn định lượng."
        })

    # Add Source 2 Blackbox EAs without Live Real Proof
    for b in rejected_blackbox_eas:
        rejected_rules.append({
            "id": b['url'].split('/')[-1],
            "source": "ea-directory-2026",
            "name": b['name'],
            "category": "blackbox_no_live_real_proof",
            "reason": "NO_LIVE_REAL_PROOF_BLACKBOX: EA thương mại đóng mã nguồn không có liên kết kiểm chứng tài khoản thật (Myfxbook/MQL5 Live Real), không đủ điều kiện đưa vào danh mục định lượng.",
            "missing_evidence": "Thiếu mã nguồn thuật toán độc lập và thiếu hoàn toàn kiểm chứng độc lập trên tài khoản giao dịch tiền thật của bên thứ ba."
        })

    rejected_package = {
        "generated_at": datetime.now().isoformat(),
        "total_rejected": len(rejected_rules),
        "rejection_categories": {
            "unverified_discretionary_or_missing_data": {
                "description": "Chiến lược chưa kiểm định do thiếu dữ liệu phụ trợ hoặc quy tắc vẽ tay cảm tính (Source 1)",
                "count": len(s1_unverified),
                "sub_breakdown": {
                    "MISSING_AUXILIARY_DATA": sum(1 for r in rejected_rules if r.get('sub_category') == 'MISSING_AUXILIARY_DATA'),
                    "NOT_A_STANDALONE_STRATEGY": sum(1 for r in rejected_rules if r.get('sub_category') == 'NOT_A_STANDALONE_STRATEGY'),
                    "DISCRETIONARY_NOT_FORMALIZED": sum(1 for r in rejected_rules if r.get('sub_category') == 'DISCRETIONARY_NOT_FORMALIZED')
                }
            },
            "chat_failed_oos": {
                "description": "Các chiến lược sụp đổ ở giai đoạn Out-of-Sample theo kiểm định gốc (Source 1)",
                "count": len(s1_chat_ids)
            },
            "toxic_money_management": {
                "description": "Hệ thống sử dụng bẫy Grid, Martingale, nhồi lệnh rủi ro cao (Source 2)",
                "count": len(rejected_grid_eas)
            },
            "blackbox_no_live_real_proof": {
                "description": "EA thương mại hộp đen không có tài khoản thật Live Real kiểm chứng (Source 2)",
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

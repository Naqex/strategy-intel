import os
import sys
import json
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(ROOT_DIR, 'scripts/common'))
sys.path.insert(0, os.path.join(ROOT_DIR, 'sources/ea-directory-2026/scripts'))

from verify_verbatim import deep_compare_strategy_record
from holdout_sanitizer import recursive_check_holdout, validate_handoff_schema
from extract_catalog import extract_ea_from_html

class TestCleanroomGuards(unittest.TestCase):
    
    def test_a_verifier_catches_tampered_wr(self):
        """Negative test: Verifier must catch tampered winrate while verdict is untouched."""
        summary_path = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/extracted/02_library_242_summary.json')
        reports_dir = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/raw/reports_json')
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary = json.load(f)
            
        first_item = dict(summary['danh_sach_242_chien_luoc'][0])
        sid = first_item['id']
        raw_path = os.path.join(reports_dir, f"{sid}.json")
        with open(raw_path, 'r', encoding='utf-8') as f:
            raw_d = json.load(f)
            
        # Tamper winrate slightly
        tampered_item = json.loads(json.dumps(first_item))
        original_wr = tampered_item['in_sample_2004_2018']['winrate_pct']
        tampered_item['in_sample_2004_2018']['winrate_pct'] = (original_wr or 25.0) + 1.5
        
        diffs = deep_compare_strategy_record(raw_d, tampered_item)
        self.assertTrue(len(diffs) > 0, "Verifier failed to detect tampered winrate!")
        self.assertTrue(any("IS wr mismatch" in d for d in diffs), f"Expected 'IS wr mismatch' in diffs: {diffs}")
        print("\n[TEST A PASS] Verifier successfully caught tampered winrate.")

    def test_b_holdout_sanitizer_catches_deep_nested_and_2024(self):
        """Negative test: Sanitizer must fail on deeply nested holdout payload and year 2024."""
        # 1. Deeply nested forbidden payload
        nested_payload = {
            "version": "1.0",
            "nested": {
                "level1": {
                    "level2": {
                        "OOS2": {
                            "2025": {"pnl": 105.4}
                        }
                    }
                }
            }
        }
        violations_nested = recursive_check_holdout(nested_payload, "test_payload")
        self.assertTrue(len(violations_nested) > 0, "Sanitizer failed to detect deeply nested OOS2/2025!")
        tokens_found = [v[1] for v in violations_nested]
        self.assertTrue(any("OOS2" in t or "2025" in t for t in tokens_found))
        
        # 2. Year 2024 payload
        payload_2024 = {
            "leads": [
                {"id": "TEST01", "evaluated_year": 2024}
            ]
        }
        violations_2024 = recursive_check_holdout(payload_2024, "test_2024")
        self.assertTrue(len(violations_2024) > 0, "Sanitizer failed to detect year 2024!")
        print("[TEST B PASS] Sanitizer successfully caught nested holdout payload and year 2024.")

    def test_c_anomalies_recorded_and_passes_all_5(self):
        """Verify exactly 4/15 CHAT have passes_all_5 == False and 8 mismatches are logged."""
        # 1. Master leads check
        master_leads_path = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
        with open(master_leads_path, 'r', encoding='utf-8') as f:
            m_data = json.load(f)
            
        leads = m_data.get('leads', [])
        self.assertEqual(len(leads), 15, "Expected 15 leads in master_leads.json")
        
        false_leads = [l['original_id'] for l in leads if l.get('passes_all_5') is False]
        true_leads = [l['original_id'] for l in leads if l.get('passes_all_5') is True]
        
        self.assertEqual(len(false_leads), 4, f"Expected 4 false leads, got {len(false_leads)}")
        self.assertEqual(len(true_leads), 11, f"Expected 11 true leads, got {len(true_leads)}")
        self.assertEqual(sorted(false_leads), ['IND026', 'SEA003', 'SEA004', 'SEA021'])
        
        # Check SEA004 downgraded to PARTIAL_RULE_SPEC
        sea004 = next(l for l in leads if l['original_id'] == 'SEA004')
        self.assertEqual(sea004['replicability'], 'PARTIAL_RULE_SPEC')
        
        # 2. Anomalies file check
        anomalies_path = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/extracted/source_anomalies.json')
        with open(anomalies_path, 'r', encoding='utf-8') as f:
            anom_data = json.load(f)
            
        expected_8 = ['BRK009', 'BRK018', 'BRK034', 'IND015', 'IND044', 'IND047', 'REV025', 'VIR041']
        self.assertEqual(sorted(anom_data['mismatches_years_pos_ids']), expected_8)
        self.assertEqual(anom_data['missing_years_in_nam_duong_count'], 40)
        print("[TEST C PASS] 4/15 passes_all_5==False and 8 mismatches correctly recorded.")

    def test_d_eafree_parser_fixtures_regression(self):
        """Regression test for 3 EAFree fixture pages: quantum-titan, sunan-giri, scalping-robot."""
        fixtures_dir = os.path.join(ROOT_DIR, 'sources/ea-directory-2026/raw/details')
        
        # 1. Quantum Titan MT5
        qt = extract_ea_from_html(os.path.join(fixtures_dir, 'quantum-titan-mt5.html'))
        self.assertEqual(qt.vendor_risk_label, 'Low', f"Quantum Titan risk expected Low, got {qt.vendor_risk_label}")
        self.assertEqual(qt.pricing, 'POINTS (300 P-Points)')
        self.assertFalse(qt.third_party_verified_real)
        self.assertFalse(qt.has_grid_or_martingale_signals)
        
        # 2. Sunan Giri EA MT4
        sg = extract_ea_from_html(os.path.join(fixtures_dir, 'sunan-giri-ea-mt4.html'))
        self.assertEqual(sg.vendor_risk_label, 'Medium', f"Sunan Giri risk expected Medium, got {sg.vendor_risk_label}")
        self.assertEqual(sg.pricing, 'POINTS (30 Points)')
        self.assertTrue(sg.has_grid_or_martingale_signals)
        self.assertFalse(sg.third_party_verified_real)
        
        # 3. Scalping Robot Pro MT5
        srp = extract_ea_from_html(os.path.join(fixtures_dir, 'scalping-robot-pro-mt5.html'))
        self.assertEqual(srp.vendor_risk_label, 'High', f"Scalping Robot Pro risk expected High, got {srp.vendor_risk_label}")
        self.assertEqual(srp.pricing, 'POINTS (300 P-Points)')
        self.assertTrue(srp.has_grid_or_martingale_signals)
        self.assertFalse(srp.third_party_verified_real)
        
        # 4. Ghost AI EA MT5 (disclosed rule, not an HFT/Hedging blackbox)
        ghost = extract_ea_from_html(os.path.join(fixtures_dir, 'ghost-ai-ea-mt5.html'))
        self.assertEqual(ghost.vendor_risk_label, 'Low')
        self.assertEqual(ghost.strategy_replicability, 'REPLICABLE_RULE_SET')
        self.assertFalse(ghost.is_hft_or_hedging_blackbox)
        print("[TEST D PASS] EAFree parser regression passed for all 3 fixtures + Ghost AI.")

if __name__ == '__main__':
    unittest.main()

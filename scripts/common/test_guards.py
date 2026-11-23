import os
import sys
import json
import shutil
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(ROOT_DIR, 'scripts/common'))
sys.path.insert(0, os.path.join(ROOT_DIR, 'sources/ea-directory-2026/scripts'))

from verify_verbatim import verify, deep_compare_strategy_record
from holdout_sanitizer import sanitize_and_validate, recursive_check_holdout, validate_handoff_schema
from extract_catalog import extract_ea_from_html

class TestCleanroomGuards(unittest.TestCase):

    def test_holdout_sanitizer_negative_cases(self):
        """Negative tests for holdout_sanitizer: must catch (a) notes_2025 in oos1, (b) key OOS2_2025, (c) string 2025Q3, (d) number 2024."""
        # Case (a): performance_metrics with notes_2025 inside oos1
        payload_a = {
            "leads": [
                {
                    "lead_id": "TEST-01",
                    "performance_metrics": {
                        "oos1_2019_2023": {
                            "notes_2025": {"pnl": 123.45}
                        }
                    }
                }
            ]
        }
        valid_a, errs_a = sanitize_and_validate(payload_a)
        self.assertFalse(valid_a, "Sanitizer failed to catch 'notes_2025' in oos1_2019_2023")

        # Case (b): forbidden key OOS2_2025
        payload_b = {
            "leads": [
                {
                    "lead_id": "TEST-02",
                    "OOS2_2025": "forbidden_key"
                }
            ]
        }
        valid_b, errs_b = sanitize_and_validate(payload_b)
        self.assertFalse(valid_b, "Sanitizer failed to catch key 'OOS2_2025'")

        # Case (c): string value '2025Q3'
        payload_c = {
            "leads": [
                {
                    "lead_id": "TEST-03",
                    "period_tag": "2025Q3"
                }
            ]
        }
        valid_c, errs_c = sanitize_and_validate(payload_c)
        self.assertFalse(valid_c, "Sanitizer failed to catch string value '2025Q3'")

        # Case (d): numeric year 2024
        payload_d = {
            "leads": [
                {
                    "lead_id": "TEST-04",
                    "holdout_year": 2024
                }
            ]
        }
        valid_d, errs_d = sanitize_and_validate(payload_d)
        self.assertFalse(valid_d, "Sanitizer failed to catch numeric year 2024")
        print("\n[TEST PASS] holdout_sanitizer negative test cases (a, b, c, d) all caught.")

    def test_verify_verbatim_end_to_end_negative_cases(self):
        """Negative tests for verify_verbatim.verify(): must catch (a) OOS2.wr, (b) spec.ten, (c) 1 byte raw mismatch, (d) anomalies mismatch."""
        with tempfile.TemporaryDirectory() as td:
            # Copy relevant folders to tempdir
            shutil.copytree(os.path.join(ROOT_DIR, 'catalog'), os.path.join(td, 'catalog'))
            shutil.copytree(os.path.join(ROOT_DIR, 'handoff'), os.path.join(td, 'handoff'))
            shutil.copytree(os.path.join(ROOT_DIR, 'sources'), os.path.join(td, 'sources'))

            # Baseline check: must pass on clean copy
            clean_pass = verify(repo_root=td)
            self.assertTrue(clean_pass, "Baseline verify() on clean temp copy should PASS")

            # Case (a): Tamper OOS2.wr in extracted summary
            sum_path = os.path.join(td, 'sources/stategy-netlify-app/extracted/02_library_242_summary.json')
            with open(sum_path, 'r', encoding='utf-8') as f:
                sum_data = json.load(f)
            orig_wr = sum_data['danh_sach_242_chien_luoc'][0]['out_of_sample_2_2024_2026']['winrate_pct']
            sum_data['danh_sach_242_chien_luoc'][0]['out_of_sample_2_2024_2026']['winrate_pct'] = 99.9
            with open(sum_path, 'w', encoding='utf-8') as f:
                json.dump(sum_data, f)
            self.assertFalse(verify(repo_root=td), "verify() failed to catch tampered OOS2.wr")
            # Restore
            sum_data['danh_sach_242_chien_luoc'][0]['out_of_sample_2_2024_2026']['winrate_pct'] = orig_wr
            with open(sum_path, 'w', encoding='utf-8') as f:
                json.dump(sum_data, f)

            # Case (b): Tamper spec.ten in extracted summary
            orig_ten = sum_data['danh_sach_242_chien_luoc'][0]['ten']
            sum_data['danh_sach_242_chien_luoc'][0]['ten'] = "Tampered Strategy Name"
            with open(sum_path, 'w', encoding='utf-8') as f:
                json.dump(sum_data, f)
            self.assertFalse(verify(repo_root=td), "verify() failed to catch tampered spec.ten")
            # Restore
            sum_data['danh_sach_242_chien_luoc'][0]['ten'] = orig_ten
            with open(sum_path, 'w', encoding='utf-8') as f:
                json.dump(sum_data, f)

            # Case (c): Tamper 1 byte in raw/ (raw_manifest mismatch)
            raw_target = os.path.join(td, 'sources/stategy-netlify-app/raw/thu_vien_index.json')
            with open(raw_target, 'ab') as f:
                f.write(b" ")
            self.assertFalse(verify(repo_root=td), "verify() failed to catch 1-byte raw_manifest mismatch")
            # Restore by recopying raw_target
            shutil.copy2(os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/raw/thu_vien_index.json'), raw_target)

            # Case (d): Tamper source_anomalies.json
            anom_path = os.path.join(td, 'sources/stategy-netlify-app/extracted/source_anomalies.json')
            with open(anom_path, 'r', encoding='utf-8') as f:
                anom_data = json.load(f)
            orig_m_count = anom_data['mismatches_years_pos_count']
            anom_data['mismatches_years_pos_count'] = 999
            with open(anom_path, 'w', encoding='utf-8') as f:
                json.dump(anom_data, f)
            self.assertFalse(verify(repo_root=td), "verify() failed to catch tampered source_anomalies.json")
            # Restore
            anom_data['mismatches_years_pos_count'] = orig_m_count
            with open(anom_path, 'w', encoding='utf-8') as f:
                json.dump(anom_data, f)

            # Verify that verify() did NOT modify or overwrite source_anomalies.json
            mtime_before = os.path.getmtime(anom_path)
            verify(repo_root=td)
            mtime_after = os.path.getmtime(anom_path)
            self.assertEqual(mtime_before, mtime_after, "verify() should be READ-ONLY and not touch source_anomalies.json")

        print("[TEST PASS] verify_verbatim end-to-end negative cases (a, b, c, d) all caught.")

    def test_doc_consistency(self):
        """Assert consistency across README.md, 05_replicability_audit.md, and master_leads.json."""
        # 1. README.md checks
        readme_path = os.path.join(ROOT_DIR, 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('**8 chiến lược** có số năm dương', content, "README must state exactly 8 year mismatches")
        self.assertIn('**40 chu kỳ kiểm định** thiếu', content, "README must state exactly 40 missing year sets")
        self.assertNotIn('REV028 (CHẤT)', content, "README must not contain stale REV028 (CHẤT)")
        self.assertIn('SEA003', content, "README must reference SEA003 for REV029")
        self.assertNotIn('Toàn bộ kết quả backtest trên trang là MT5', content, "README must not contain stale backtest claim")
        self.assertIn('Backtest vendor trên mẫu 45 EAFree gồm cả MetaTrader 4', content, "README must contain updated vendor backtest description")

        # 2. 05_replicability_audit.md vs master_leads.json
        leads_path = os.path.join(ROOT_DIR, 'catalog/master_leads.json')
        with open(leads_path, 'r', encoding='utf-8') as f:
            leads = json.load(f)['leads']
        rep_leads_count = sum(1 for l in leads if l.get('replicability') == 'REPLICABLE_FROM_PUBLIC')
        self.assertEqual(rep_leads_count, 1, "Expected exactly 1 REPLICABLE_FROM_PUBLIC lead (SEA003)")

        audit_path = os.path.join(ROOT_DIR, 'sources/stategy-netlify-app/extracted/05_replicability_audit.md')
        with open(audit_path, 'r', encoding='utf-8') as f:
            audit_text = f.read()

        table_rep_rows = [line for line in audit_text.splitlines() if line.startswith('|') and '`REPLICABLE_FROM_PUBLIC`' in line]
        self.assertEqual(len(table_rep_rows), rep_leads_count, "Audit table REPLICABLE_FROM_PUBLIC count must match master_leads.json")
        self.assertIn('1 / 15 chiến lược (6.7%)', audit_text, "Audit summary must state 1/15 (6.7%) REPLICABLE_FROM_PUBLIC")
        print("[TEST PASS] Document consistency assertions all verified.")

    def test_eafree_fixtures_regression(self):
        """Regression test for 3 EAFree fixture pages + Ghost AI."""
        fixtures_dir = os.path.join(ROOT_DIR, 'sources/ea-directory-2026/raw/details')

        # 1. Quantum Titan MT5
        qt = extract_ea_from_html(os.path.join(fixtures_dir, 'quantum-titan-mt5.html'))
        self.assertEqual(qt.vendor_risk_label, 'Low')
        self.assertEqual(qt.pricing, 'POINTS (300 P-Points)')
        self.assertFalse(qt.third_party_verified_real)
        self.assertFalse(qt.has_grid_or_martingale_signals)

        # 2. Sunan Giri EA MT4
        sg = extract_ea_from_html(os.path.join(fixtures_dir, 'sunan-giri-ea-mt4.html'))
        self.assertEqual(sg.vendor_risk_label, 'Medium')
        self.assertEqual(sg.pricing, 'POINTS (30 Points)')
        self.assertTrue(sg.has_grid_or_martingale_signals)
        self.assertFalse(sg.third_party_verified_real)

        # 3. Scalping Robot Pro MT5
        srp = extract_ea_from_html(os.path.join(fixtures_dir, 'scalping-robot-pro-mt5.html'))
        self.assertEqual(srp.vendor_risk_label, 'High')
        self.assertEqual(srp.pricing, 'POINTS (300 P-Points)')
        self.assertTrue(srp.has_grid_or_martingale_signals)
        self.assertFalse(srp.third_party_verified_real)

        # 4. Ghost AI EA MT5 (disclosed concept, not HFT/blackbox, third_party_verified_real=False)
        ghost = extract_ea_from_html(os.path.join(fixtures_dir, 'ghost-ai-ea-mt5.html'))
        self.assertEqual(ghost.vendor_risk_label, 'Low')
        self.assertEqual(ghost.strategy_replicability, 'CONCEPT_DISCLOSED_UNVERIFIED')
        self.assertFalse(ghost.is_hft_or_hedging_blackbox)
        self.assertFalse(ghost.third_party_verified_real)
        self.assertEqual(ghost.live_proof_verification_status, 'NO_LIVE_LINK')
        print("[TEST PASS] EAFree fixtures regression passed for all 3 fixtures + Ghost AI.")

if __name__ == '__main__':
    unittest.main()

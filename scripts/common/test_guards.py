import os
import subprocess
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts/common"))
sys.path.insert(0, os.path.join(ROOT_DIR, "sources/ea-directory-2026/scripts"))

from verify_verbatim import verify, verify_raw_manifest, deep_compare_strategy_record  # noqa: E402, F401
from holdout_sanitizer import (  # noqa: E402, F401
    sanitize,
    sanitize_and_validate,
    recursive_check_holdout,
    validate_handoff_schema,
)
from repo_hygiene_check import audit_repo_hygiene, check_hygiene  # noqa: E402
try:
    from extract_catalog import extract_ea_from_html  # noqa: E402
except ModuleNotFoundError:
    extract_ea_from_html = None
import auto_intel_ingest  # noqa: E402


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
            shutil.copytree(os.path.join(ROOT_DIR, "catalog"), os.path.join(td, "catalog"))
            shutil.copytree(os.path.join(ROOT_DIR, "handoff"), os.path.join(td, "handoff"))
            shutil.copytree(os.path.join(ROOT_DIR, "sources"), os.path.join(td, "sources"))

            # Baseline check: must pass on clean copy
            clean_pass = verify(repo_root=td)
            self.assertTrue(clean_pass, "Baseline verify() on clean temp copy should PASS")

            # Case (a): Tamper OOS2.wr in extracted summary
            sum_path = os.path.join(td, "sources/stategy-netlify-app/extracted/02_library_242_summary.json")
            with open(sum_path, "r", encoding="utf-8") as f:
                sum_data = json.load(f)
            orig_wr = sum_data["danh_sach_242_chien_luoc"][0]["out_of_sample_2_2024_2026"]["winrate_pct"]
            sum_data["danh_sach_242_chien_luoc"][0]["out_of_sample_2_2024_2026"]["winrate_pct"] = 99.9
            with open(sum_path, "w", encoding="utf-8") as f:
                json.dump(sum_data, f)
            self.assertFalse(verify(repo_root=td), "verify() failed to catch tampered OOS2.wr")
            # Restore
            sum_data["danh_sach_242_chien_luoc"][0]["out_of_sample_2_2024_2026"]["winrate_pct"] = orig_wr
            with open(sum_path, "w", encoding="utf-8") as f:
                json.dump(sum_data, f)

            # Case (b): Tamper spec.ten in extracted summary
            orig_ten = sum_data["danh_sach_242_chien_luoc"][0]["ten"]
            sum_data["danh_sach_242_chien_luoc"][0]["ten"] = "Tampered Strategy Name"
            with open(sum_path, "w", encoding="utf-8") as f:
                json.dump(sum_data, f)
            self.assertFalse(verify(repo_root=td), "verify() failed to catch tampered spec.ten")
            # Restore
            sum_data["danh_sach_242_chien_luoc"][0]["ten"] = orig_ten
            with open(sum_path, "w", encoding="utf-8") as f:
                json.dump(sum_data, f)

            # Case (c): Tamper 1 byte in raw/ (raw_manifest mismatch)
            raw_target = os.path.join(td, "sources/stategy-netlify-app/raw/thu_vien_index.json")
            with open(raw_target, "ab") as f:
                f.write(b" ")
            self.assertFalse(verify(repo_root=td), "verify() failed to catch 1-byte raw_manifest mismatch")
            # Restore by recopying raw_target
            shutil.copy2(os.path.join(ROOT_DIR, "sources/stategy-netlify-app/raw/thu_vien_index.json"), raw_target)

            # Case (d): Tamper source_anomalies.json
            anom_path = os.path.join(td, "sources/stategy-netlify-app/extracted/source_anomalies.json")
            with open(anom_path, "r", encoding="utf-8") as f:
                anom_data = json.load(f)
            orig_m_count = anom_data["mismatches_years_pos_count"]
            anom_data["mismatches_years_pos_count"] = 999
            with open(anom_path, "w", encoding="utf-8") as f:
                json.dump(anom_data, f)
            self.assertFalse(verify(repo_root=td), "verify() failed to catch tampered source_anomalies.json")
            # Restore
            anom_data["mismatches_years_pos_count"] = orig_m_count
            with open(anom_path, "w", encoding="utf-8") as f:
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
        readme_path = os.path.join(ROOT_DIR, "README.md")
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("**8 chiến lược** có số năm dương", content, "README must state exactly 8 year mismatches")
        self.assertIn("**40 chu kỳ kiểm định** thiếu", content, "README must state exactly 40 missing year sets")
        self.assertNotIn("REV028 (CHẤT)", content, "README must not contain stale REV028 (CHẤT)")
        self.assertIn("SEA003", content, "README must reference SEA003 for REV029")
        self.assertNotIn("Toàn bộ kết quả backtest trên trang là MT5", content, "README must not contain stale backtest claim")
        self.assertIn("Backtest vendor trên mẫu 45 EAFree gồm cả MetaTrader 4", content, "README must contain updated vendor backtest description")

        # 2. 05_replicability_audit.md vs master_leads.json
        leads_path = os.path.join(ROOT_DIR, "catalog/master_leads.json")
        with open(leads_path, "r", encoding="utf-8") as f:
            leads = json.load(f)["leads"]
        rep_leads_count = sum(1 for l in leads if l.get("replicability") == "REPLICABLE_FROM_PUBLIC")
        self.assertEqual(rep_leads_count, 1, "Expected exactly 1 REPLICABLE_FROM_PUBLIC lead (SEA003)")

        audit_path = os.path.join(ROOT_DIR, "sources/stategy-netlify-app/extracted/05_replicability_audit.md")
        with open(audit_path, "r", encoding="utf-8") as f:
            audit_text = f.read()

        table_rep_rows = [line for line in audit_text.splitlines() if line.startswith("|") and "`REPLICABLE_FROM_PUBLIC`" in line]
        self.assertEqual(len(table_rep_rows), rep_leads_count, "Audit table REPLICABLE_FROM_PUBLIC count must match master_leads.json")
        self.assertIn("1 / 15 chiến lược (6.7%)", audit_text, "Audit summary must state 1/15 (6.7%) REPLICABLE_FROM_PUBLIC")
        self.assertNotIn("1:2 đến 1:3", audit_text, "Audit summary must not contain hallucinated R:R claims")

        # 3. Verify 5 Long-only leads have direction == 'Long' and 0 unproven DUPLICATE_EXACT
        long_only_ids = {"IND026", "MTF020", "SEA003", "SEA011", "SEA021"}
        for lead in leads:
            if lead.get("original_id") in long_only_ids:
                self.assertEqual(lead.get("direction"), "Long", f"{lead.get('original_id')} must be Long-only")
        with open(os.path.join(ROOT_DIR, "sources/stategy-netlify-app/extracted/07_missing_58_items.json"), "r", encoding="utf-8") as f:
            m58 = json.load(f)
        self.assertEqual(m58["phan_loai_thieu"]["phan_loai_gop"]["DUPLICATE_EXACT"], 0, "No unproven DUPLICATE_EXACT allowed")
        with open(os.path.join(ROOT_DIR, "handoff/sanitized_master_leads.json"), "r", encoding="utf-8") as f:
            handoff = json.load(f)
        self.assertNotIn("Independently verifiable", handoff["gate_criteria"]["condition_b"])
        print("[TEST PASS] Document consistency assertions all verified.")

    @unittest.skipIf(extract_ea_from_html is None, "beautifulsoup4 not installed in active interpreter")
    def test_eafree_fixtures_regression(self):
        """Regression test for 3 EAFree fixture pages + Ghost AI."""
        fixtures_dir = os.path.join(ROOT_DIR, "sources/ea-directory-2026/raw/details")

        # 1. Quantum Titan MT5
        qt = extract_ea_from_html(os.path.join(fixtures_dir, "quantum-titan-mt5.html"))
        self.assertEqual(qt.vendor_risk_label, "Low")
        self.assertEqual(qt.pricing, "POINTS (300 P-Points)")
        self.assertFalse(qt.third_party_verified_real)
        self.assertFalse(qt.has_grid_or_martingale_signals)

        # 2. Sunan Giri EA MT4
        sg = extract_ea_from_html(os.path.join(fixtures_dir, "sunan-giri-ea-mt4.html"))
        self.assertEqual(sg.vendor_risk_label, "Medium")
        self.assertEqual(sg.pricing, "POINTS (30 Points)")
        self.assertTrue(sg.has_grid_or_martingale_signals)
        self.assertFalse(sg.third_party_verified_real)

        # 3. Scalping Robot Pro MT5
        srp = extract_ea_from_html(os.path.join(fixtures_dir, "scalping-robot-pro-mt5.html"))
        self.assertEqual(srp.vendor_risk_label, "High")
        self.assertEqual(srp.pricing, "POINTS (300 P-Points)")
        self.assertTrue(srp.has_grid_or_martingale_signals)
        self.assertFalse(srp.third_party_verified_real)

        # 4. Ghost AI EA MT5 (disclosed concept, not HFT/blackbox, third_party_verified_real=False)
        ghost = extract_ea_from_html(os.path.join(fixtures_dir, "ghost-ai-ea-mt5.html"))
        self.assertEqual(ghost.vendor_risk_label, "Low")
        self.assertEqual(ghost.strategy_replicability, "CONCEPT_DISCLOSED_UNVERIFIED")
        self.assertFalse(ghost.is_hft_or_hedging_blackbox)
        self.assertFalse(ghost.third_party_verified_real)
        self.assertEqual(ghost.live_proof_verification_status, "NO_LIVE_LINK")
        print("[TEST PASS] EAFree fixtures regression passed for all 3 fixtures + Ghost AI.")

    def test_auto_ingest_binary_url_and_payload_blocker(self):
        """Binary URL & payload blocker must reject all forbidden binary/executable/archive extensions."""
        blocked_urls = [
            "https://example.org/files/bot.ex4",
            "https://example.org/files/bot.ex5",
            "https://example.org/src/ea.mq4",
            "https://example.org/src/ea.mq5",
            "https://example.org/bin/helper.dll",
            "https://example.org/setup/installer.exe",
            "https://example.org/setup/pkg.msi",
            "https://example.org/scripts/run.bat",
            "https://example.org/scripts/run.ps1",
            "https://example.org/archive/ea-pack.zip",
            "https://example.org/archive/ea-pack.rar",
            "https://example.org/archive/ea-pack.7z",
            "https://example.org/archive/ea-pack.tar.gz",
            "https://example.org/download?file=secret_bot.ex5",
            "ftp://example.org/readme.txt",
        ]
        for bad_url in blocked_urls:
            with self.assertRaises(
                auto_intel_ingest.BinaryDownloadBlockedError,
                msg=f"Failed to block forbidden URL: {bad_url}",
            ):
                auto_intel_ingest.validate_safe_public_url(bad_url)

        # Safe text/HTML/JSON URLs must pass
        self.assertEqual(
            auto_intel_ingest.validate_safe_public_url("https://quantpedia.com/strategies/dual-momentum-model/"),
            "https://quantpedia.com/strategies/dual-momentum-model/",
        )

        # Binary payload checks (magic bytes & content-type)
        with self.assertRaises(auto_intel_ingest.BinaryDownloadBlockedError):
            auto_intel_ingest.validate_text_payload(b"MZ\x90\x00binary", content_type="text/plain")
        with self.assertRaises(auto_intel_ingest.BinaryDownloadBlockedError):
            auto_intel_ingest.validate_text_payload(b"PK\x03\x04zip", content_type="text/plain")
        with self.assertRaises(auto_intel_ingest.BinaryDownloadBlockedError):
            auto_intel_ingest.validate_text_payload(b"hello", content_type="application/octet-stream")
        with self.assertRaises(auto_intel_ingest.BinaryDownloadBlockedError):
            auto_intel_ingest.validate_text_payload(b"hello", content_type="text/plain", filename_hint='attachment; filename="ea.ex5"')
        print("[TEST PASS] auto_intel_ingest binary URL & payload blocker verified.")

    def test_auto_ingest_zero_hallucination_and_toxic_rejection(self):
        """Missing fields must become NOT_DISCLOSED; Grid/Martingale/No-SL rejected; negations preserved."""
        sparse_raw = {
            "original_id": "SPARSE-01",
            "url": "https://example.org/spec.html",
            "name": "Minimal Trend Spec",
            "raw_text": "Public trend concept using hard stop loss. Strictly avoids martingale and avoids grid.",
        }
        extracted = auto_intel_ingest.extract_spec_from_raw(sparse_raw, raw_rel_path="sources/public-auto-ingest/raw/sparse.json")
        self.assertEqual(extracted["timeframe"], auto_intel_ingest.NOT_DISCLOSED)
        self.assertEqual(extracted["symbol"], auto_intel_ingest.NOT_DISCLOSED)
        self.assertEqual(extracted["stop_loss_rule"], auto_intel_ingest.NOT_DISCLOSED)
        self.assertEqual(extracted["reported_winrate_pct"], auto_intel_ingest.NOT_DISCLOSED)
        self.assertEqual(extracted["reported_profit_factor"], auto_intel_ingest.NOT_DISCLOSED)
        self.assertEqual(extracted["reported_max_dd_pct"], auto_intel_ingest.NOT_DISCLOSED)
        self.assertIn("Public trend concept", extracted["verbatim_excerpt"])
        self.assertFalse(extracted["is_toxic"], "Negated martingale/grid phrasing must not false-positive")

        toxic_raw = {
            "original_id": "TOXIC-99",
            "url": "https://example.org/toxic.html",
            "name": "Danger Grid EA",
            "raw_text": "Uses grid trading with 2.0x lot multiplier martingale and trades without stop loss.",
        }
        toxic_ext = auto_intel_ingest.extract_spec_from_raw(toxic_raw, raw_rel_path="sources/public-auto-ingest/raw/toxic.json")
        self.assertTrue(toxic_ext["is_toxic"])
        self.assertIn("TOXIC_MARTINGALE", toxic_ext["toxic_flags"])
        self.assertIn("TOXIC_GRID", toxic_ext["toxic_flags"])
        self.assertIn("TOXIC_NO_STOP_LOSS", toxic_ext["toxic_flags"])

        # Cross-category & hard-stop negation bypasses MUST still be caught as toxic
        bypass_cases = [
            ("Uses martingale recovery with a mandatory hard stop.", "TOXIC_MARTINGALE"),
            ("Opens grid trading layers every 50 points with no martingale.", "TOXIC_GRID"),
            ("Doubles the lot on loss (martingale) with zero grid.", "TOXIC_MARTINGALE"),
            ("Uses strict hard stop with cost-averaging grid system.", "TOXIC_GRID"),
        ]
        for text, expected_flag in bypass_cases:
            is_tox, flags, _ = auto_intel_ingest.detect_toxic_signals(text)
            self.assertTrue(is_tox, f"Cross-category/hard-stop negation bypassed toxic detector: {text}")
            self.assertIn(expected_flag, flags, f"Missing {expected_flag} for: {text}")

        # Decimal-dot SL=0.5 / TP=1.5 MUST NOT trigger false-positive TOXIC_NO_STOP_LOSS
        clean_sl_tox, clean_sl_flags, _ = auto_intel_ingest.detect_toxic_signals(
            "Breakout strategy with SL=0.5 ATR and TP=1.5 ATR."
        )
        self.assertFalse(clean_sl_tox, f"False positive on decimal SL=0.5: {clean_sl_flags}")

        # Explicit SL=0 / SL=0.0 MUST still trigger TOXIC_NO_STOP_LOSS, and 1.8x rationale must stay intact
        zero_sl_tox, zero_sl_flags, zero_rationale = auto_intel_ingest.detect_toxic_signals(
            "Uses 1.8x lot multiplier with SL=0.0 until recovery."
        )
        self.assertTrue(zero_sl_tox)
        self.assertIn("TOXIC_NO_STOP_LOSS", zero_sl_flags)
        self.assertIn("TOXIC_MARTINGALE", zero_sl_flags)
        self.assertIn("1.8x lot multiplier", zero_rationale)
        print("[TEST PASS] auto_intel_ingest NOT_DISCLOSED & toxic rejection (incl. cross-negation & decimal SL) verified.")

    def test_auto_ingest_offline_pipeline_and_holdout_scrub(self):
        """Offline auto-ingest writes valid SHA-256 manifest, rejects toxic specs, and emits 0-leakage handoff."""
        scratch_parent = os.path.join(ROOT_DIR, ".scratch")
        os.makedirs(scratch_parent, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch_parent) as td:
            td_path = Path(td)
            summary = auto_intel_ingest.run_ingest(root_dir=td_path, mode="offline")
            self.assertEqual(summary["raw_files"], 6)
            self.assertEqual(summary["accepted_leads"], 4)
            self.assertEqual(summary["rejected_toxic"], 2)

            # Verify raw manifest integrity using verify_verbatim.verify_raw_manifest
            raw_dir = td_path / "sources" / "public-auto-ingest" / "raw"
            manifest_path = td_path / "sources" / "public-auto-ingest" / "raw_manifest.sha256.json"
            self.assertEqual(verify_raw_manifest(str(raw_dir), str(manifest_path)), [])

            # Verify handoff/sanitized_auto_leads.json passes holdout_sanitizer with 0 leakage
            handoff_dir = td_path / "handoff"
            self.assertTrue(sanitize(handoff_dir=str(handoff_dir)))
            handoff_data = json.loads((handoff_dir / "sanitized_auto_leads.json").read_text(encoding="utf-8"))
            ok, violations = sanitize_and_validate(handoff_data)
            self.assertTrue(ok, f"Sanitized auto handoff had violations: {violations}")
            self.assertEqual(handoff_data["total_leads"], 4)

            # Ensure scrubbed payload rejects numeric 2025/2026 and string 2024..2029/oos2
            dirty = {
                "lead_id": "X-1",
                "rule_description": "Strong OOS2 performance in 2025 and 2026",
                "year_2025": 2025,
                "nested": [2024, 2026, "2029-01-01"],
            }
            scrubbed = auto_intel_ingest.scrub_holdout_tokens(dirty)
            self.assertEqual(recursive_check_holdout(scrubbed), [])
        print("[TEST PASS] auto_intel_ingest offline end-to-end & holdout scrub verified.")

    def test_repo_hygiene_tracked_vs_gitignored_inbox_split(self):
        """repo_hygiene_check must pass gitignored inbox/ binaries (without deleting) and fail tracked/workspace binaries."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=td, check=True)
            (td_path / ".gitignore").write_text("inbox/**\n!inbox/\n!inbox/README.md\n", encoding="utf-8")
            (td_path / "inbox").mkdir()
            (td_path / "inbox" / "README.md").write_text("# inbox\n", encoding="utf-8")
            (td_path / "scripts" / "common").mkdir(parents=True)
            (td_path / "scripts" / "common" / "test_guards.py").write_text("# ok\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore", "inbox/README.md", "scripts/common/test_guards.py"], cwd=td, check=True)

            # 1. Owner drops local binary + archive inside gitignored inbox/
            drop_ex5 = td_path / "inbox" / "vendor" / "sample.ex5"
            drop_rar = td_path / "inbox" / "vendor" / "pack.rar"
            drop_ex5.parent.mkdir(parents=True)
            drop_ex5.write_bytes(b"EX5_LOCAL_DROP")
            drop_rar.write_bytes(b"RAR_LOCAL_DROP")

            audit_clean = audit_repo_hygiene(repo_root=td)
            self.assertTrue(audit_clean["clean"], f"Gitignored inbox/ drops must not fail hygiene: {audit_clean}")
            self.assertEqual(
                audit_clean["gitignored_inbox_binaries"],
                ["inbox/vendor/pack.rar", "inbox/vendor/sample.ex5"],
            )
            self.assertTrue(drop_ex5.exists() and drop_rar.exists(), "Hygiene check must NEVER delete owner inbox files")

            # 2. Untracked non-gitignored binary outside inbox/ MUST FAIL
            bad_ws_bin = td_path / "sources" / "leak.ex5"
            bad_ws_bin.parent.mkdir(parents=True)
            bad_ws_bin.write_bytes(b"LEAK")
            audit_bad = audit_repo_hygiene(repo_root=td)
            self.assertFalse(audit_bad["clean"], "Non-gitignored binary in sources/ MUST fail hygiene")
            self.assertIn("sources/leak.ex5", audit_bad["binary_found"])
            bad_ws_bin.unlink()

            # 3. Force-tracked binary inside inbox/ MUST FAIL
            subprocess.run(["git", "add", "-f", "inbox/vendor/sample.ex5"], cwd=td, check=True)
            audit_forced = audit_repo_hygiene(repo_root=td)
            self.assertFalse(audit_forced["clean"], "Force-tracked binary inside inbox/ MUST fail hygiene")
            self.assertIn("inbox/vendor/sample.ex5", audit_forced["binary_found"])
            subprocess.run(["git", "rm", "--cached", "-q", "inbox/vendor/sample.ex5"], cwd=td, check=True)

            # 4. Loose test_*.py outside scripts/common/test_guards.py MUST FAIL
            loose_test = td_path / "scripts" / "test_extra.py"
            loose_test.write_text("# forbidden\n", encoding="utf-8")
            audit_scratch = audit_repo_hygiene(repo_root=td)
            self.assertFalse(audit_scratch["clean"], "Loose test_*.py must fail hygiene")
            self.assertIn("scripts/test_extra.py", audit_scratch["loose_scratch"])
            loose_test.unlink()

            self.assertTrue(check_hygiene(repo_root=td))
        print("[TEST PASS] repo_hygiene_check tracked vs gitignored inbox/ split verified.")


if __name__ == "__main__":
    unittest.main()

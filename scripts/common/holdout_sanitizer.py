import os
import sys
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
HANDOFF_DIR = os.path.join(ROOT_DIR, 'handoff')

# Patterns that indicate 2025 or 2026 performance / PnL / holdout results
FORBIDDEN_PATTERNS = [
    r'2025\s*(?:pnl|winrate|return|lãi|lỗ|trades|lệnh)',
    r'2026\s*(?:pnl|winrate|return|lãi|lỗ|trades|lệnh)',
    r'"2025":\s*(?:true|false|\d+)',
    r'"2026":\s*(?:true|false|\d+)',
    r'OOS2\s*(?:status|trạng thái|kỳ 2)',
    r'2024-02-01\s*→\s*2026',
]

def sanitize():
    print(f"[*] Running holdout sanitizer check in: {HANDOFF_DIR}")
    if not os.path.exists(HANDOFF_DIR):
        print("[+] Handoff directory does not exist yet. Clean.")
        return

    violations = []
    files_checked = 0

    for dirpath, _, filenames in os.walk(HANDOFF_DIR):
        for f in filenames:
            files_checked += 1
            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, ROOT_DIR).replace('\\', '/')
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    for pattern in FORBIDDEN_PATTERNS:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            violations.append((rel_path, pattern, matches[:3]))
            except Exception as e:
                print(f"[!] Warning reading {rel_path}: {e}")

    if violations:
        print("[!] HOLDOUT LEAKAGE DETECTED in handoff/ directory:")
        for path, pat, m in violations:
            print(f"    - File: {path}")
            print(f"      Pattern: {pat}")
            print(f"      Matches: {m}")
        print("\n[FAIL] Holdout sanitizer check FAILED. Remove 2025/2026 data from handoff files.")
        sys.exit(1)
    else:
        print(f"[+] Holdout Sanitizer: {files_checked} files checked. 0 leakage of 2025/2026 Holdout data. PASS.")
        print("\n[SUCCESS] Holdout sanitizer PASSED.")

if __name__ == '__main__':
    sanitize()

import os
import sys

# Target root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

FORBIDDEN_EXTENSIONS = {
    '.ex4', '.ex5', '.mq4', '.mq5', '.dll', '.exe', '.msi',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bin'
}

SCRATCH_PATTERNS = {
    'temp', 'tmp', 'test_', 'check_', 'inspect_', 'scratch'
}

def check_hygiene():
    print(f"[*] Running repo hygiene check in: {ROOT_DIR}")
    violations = []
    binary_found = []
    loose_scratch = []

    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        # Skip git and .scratch directory
        rel_dir = os.path.relpath(dirpath, ROOT_DIR).replace('\\', '/')
        if rel_dir == '.git' or rel_dir.startswith('.git/'):
            continue
        if rel_dir == '.scratch' or rel_dir.startswith('.scratch/'):
            continue
        if rel_dir == 'node_modules' or rel_dir.startswith('node_modules/'):
            continue

        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            full_path = os.path.join(dirpath, f)
            rel_path = os.path.relpath(full_path, ROOT_DIR).replace('\\', '/')

            # 1. Check forbidden binaries
            if ext in FORBIDDEN_EXTENSIONS:
                binary_found.append(rel_path)

            # 2. Check loose scratch/temporary files outside .scratch/
            # If a file in root or scripts matches scratch patterns and isn't standard
            if (f.startswith(('test_', 'inspect_', 'check_', 'tmp_')) or
                (f.endswith(('.tmp', '.scratch')))):
                loose_scratch.append(rel_path)

    clean = True

    if binary_found:
        print("[!] FORBIDDEN BINARY FILES FOUND:")
        for b in binary_found:
            print(f"    - {b}")
        clean = False
    else:
        print("[+] Binary Check: 0 forbidden binary files found. PASS.")

    if loose_scratch:
        print("[!] LOOSE SCRATCH FILES FOUND OUTSIDE .scratch/:")
        for s in loose_scratch:
            print(f"    - {s}")
        clean = False
    else:
        print("[+] Scratch Check: 0 loose scratch files found outside .scratch/. PASS.")

    if not clean:
        print("\n[FAIL] Repo hygiene check FAILED.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Repo hygiene check PASSED completely.")

if __name__ == '__main__':
    check_hygiene()

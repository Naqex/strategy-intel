import os
import subprocess
import sys

# Target root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

FORBIDDEN_EXTENSIONS = {
    ".ex4",
    ".ex5",
    ".mq4",
    ".mq5",
    ".dll",
    ".exe",
    ".msi",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bin",
}

SCRATCH_PATTERNS = {
    "temp",
    "tmp",
    "test_",
    "check_",
    "inspect_",
    "scratch",
}

SKIP_DIR_PREFIXES = (".git", ".scratch", "node_modules", "__pycache__")


def is_forbidden_binary(filename: str) -> bool:
    lower = filename.lower()
    if lower.endswith(".tar.gz"):
        return True
    ext = os.path.splitext(lower)[1]
    return ext in FORBIDDEN_EXTENSIONS


def _is_skipped_relpath(rel_path: str) -> bool:
    parts = rel_path.split("/")
    for part in parts[:-1]:
        if part in SKIP_DIR_PREFIXES:
            return True
    return parts[0] in SKIP_DIR_PREFIXES if parts else False


def _git_list_nul(root: str, args: list[str]) -> list[str] | None:
    try:
        proc = subprocess.run(
            ["git", "-C", root, *args],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    raw = proc.stdout.decode("utf-8", errors="surrogateescape")
    return [entry.replace("\\", "/") for entry in raw.split("\x00") if entry]


def _collect_workspace_files(root: str) -> tuple[bool, list[str]]:
    """Return (used_git, rel_paths) for tracked + non-gitignored workspace files."""
    has_git_marker = os.path.exists(os.path.join(root, ".git"))
    if has_git_marker:
        tracked = _git_list_nul(root, ["ls-files", "-z"])
        untracked = _git_list_nul(root, ["ls-files", "--others", "--exclude-standard", "-z"])
        if tracked is not None and untracked is not None:
            combined = set(tracked) | set(untracked)
            existing = [
                rel
                for rel in sorted(combined)
                if not _is_skipped_relpath(rel) and os.path.isfile(os.path.join(root, rel))
            ]
            return True, existing

    # Fail-closed fallback when not inside a Git repository: walk everything except skipped dirs.
    walked: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if rel_dir != "." and _is_skipped_relpath(rel_dir + "/_"):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PREFIXES]
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root).replace("\\", "/")
            if not _is_skipped_relpath(rel_path):
                walked.append(rel_path)
    return False, sorted(walked)


def _collect_gitignored_inbox_binaries(root: str, workspace_set: set[str], used_git: bool) -> list[str]:
    """Read-only inventory of gitignored binary files quarantined inside inbox/."""
    if not used_git:
        return []
    inbox_dir = os.path.join(root, "inbox")
    if not os.path.isdir(inbox_dir):
        return []

    quarantined: list[str] = []
    for dirpath, dirnames, filenames in os.walk(inbox_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PREFIXES]
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root).replace("\\", "/")
            # Only classify as informational quarantine if gitignored (NOT tracked & NOT non-ignored).
            if rel_path in workspace_set:
                continue
            if is_forbidden_binary(fname):
                quarantined.append(rel_path)
    return sorted(quarantined)


def audit_repo_hygiene(repo_root: str | None = None) -> dict:
    root = os.path.abspath(repo_root or ROOT_DIR)
    used_git, workspace_files = _collect_workspace_files(root)
    workspace_set = set(workspace_files)

    binary_found: list[str] = []
    loose_scratch: list[str] = []

    for rel_path in workspace_files:
        fname = os.path.basename(rel_path)

        # 1. Check forbidden binaries across tracked + non-gitignored workspace files
        if is_forbidden_binary(fname):
            binary_found.append(rel_path)

        # 2. Check loose scratch/temporary files outside .scratch/
        if rel_path == "scripts/common/test_guards.py":
            continue

        if fname.startswith(("test_", "inspect_", "check_", "tmp_")) or fname.endswith((".tmp", ".scratch")):
            loose_scratch.append(rel_path)

    gitignored_inbox_binaries = _collect_gitignored_inbox_binaries(root, workspace_set, used_git)
    clean = (len(binary_found) == 0) and (len(loose_scratch) == 0)

    return {
        "root": root,
        "git_mode": used_git,
        "workspace_files_checked": len(workspace_files),
        "binary_found": sorted(binary_found),
        "loose_scratch": sorted(loose_scratch),
        "gitignored_inbox_binaries": gitignored_inbox_binaries,
        "clean": clean,
    }


def check_hygiene(repo_root: str | None = None) -> bool:
    result = audit_repo_hygiene(repo_root=repo_root)
    mode_label = "git-tracked + non-gitignored workspace" if result["git_mode"] else "full-walk fallback (no .git)"
    print(f"[*] Running repo hygiene check in: {result['root']} ({mode_label}, {result['workspace_files_checked']} files)")

    if result["binary_found"]:
        print("[!] FORBIDDEN BINARY FILES FOUND (tracked or non-gitignored):")
        for b in result["binary_found"]:
            print(f"    - {b}")
    else:
        print("[+] Binary Check (tracked + non-gitignored): 0 forbidden binary files found. PASS.")

    if result["loose_scratch"]:
        print("[!] LOOSE SCRATCH FILES FOUND OUTSIDE .scratch/:")
        for s in result["loose_scratch"]:
            print(f"    - {s}")
    else:
        print("[+] Scratch Check: 0 loose scratch files found outside .scratch/. PASS.")

    quarantined = result["gitignored_inbox_binaries"]
    if quarantined:
        print(
            f"[i] Gitignored inbox/ binary quarantine inventory: {len(quarantined)} local file(s) "
            "(untracked, gitignored, preserved read-only — NOT a repo hygiene failure):"
        )
        for q in quarantined:
            print(f"    - [QUARANTINED_LOCAL_INBOX] {q}")
    else:
        print("[i] Gitignored inbox/ binary quarantine inventory: 0 local binary files.")

    if not result["clean"]:
        print("\n[FAIL] Repo hygiene check FAILED.")
        return False

    print("\n[SUCCESS] Repo hygiene check PASSED completely.")
    return True


if __name__ == "__main__":
    ok = check_hygiene()
    if not ok:
        sys.exit(1)

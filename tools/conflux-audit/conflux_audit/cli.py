from __future__ import annotations

import argparse
import json
from .audit import audit_repo

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Conflux Audit: a conservative repository quality preflight.")
    parser.add_argument("path", nargs="?", default=".", help="Repository path (default: current directory).")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument("--fail-on", choices=("error", "warning", "never"), default="error", help="Exit non-zero at this severity.")
    args = parser.parse_args(argv)
    result = audit_repo(args.path)
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"Conflux Audit | score={result.score} | files={result.files_scanned} | errors={result.errors} | warnings={result.warnings}")
        for f in result.findings:
            suffix = f" | {f.evidence}" if f.evidence else ""
            print(f"[{f.severity.upper()}] {f.rule} {f.path}: {f.message}{suffix}")
    if args.fail_on == "never":
        return 0
    if args.fail_on == "warning" and (result.errors or result.warnings):
        return 1
    return 1 if result.errors else 0

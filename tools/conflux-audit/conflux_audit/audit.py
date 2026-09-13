from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import re
from typing import Iterable

DEFAULT_EXCLUDES = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}
TEXT_EXTENSIONS = {".md", ".txt", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sh"}

@dataclass
class Finding:
    rule: str
    severity: str
    path: str
    message: str
    evidence: str | None = None

    def to_dict(self):
        return asdict(self)

@dataclass
class AuditResult:
    root: str
    files_scanned: int
    findings: list[Finding]

    @property
    def score(self) -> int:
        penalties = {"error": 20, "warning": 8, "info": 0}
        return max(0, 100 - sum(penalties[f.severity] for f in self.findings))

    @property
    def errors(self) -> int:
        return sum(f.severity == "error" for f in self.findings)

    @property
    def warnings(self) -> int:
        return sum(f.severity == "warning" for f in self.findings)

    def to_dict(self):
        return {"root": self.root, "files_scanned": self.files_scanned, "score": self.score,
                "errors": self.errors, "warnings": self.warnings,
                "findings": [f.to_dict() for f in self.findings]}

def iter_files(root: Path, max_bytes: int = 1_000_000) -> Iterable[tuple[Path, str]]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in DEFAULT_EXCLUDES for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS or path.stat().st_size > max_bytes:
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

def audit_repo(root: str | Path) -> AuditResult:
    root = Path(root).resolve()
    findings: list[Finding] = []
    files = list(iter_files(root))
    rel = lambda p: str(p.relative_to(root))

    readme = next((p for p in (root / "README.md", root / "README.rst", root / "README.txt") if p.exists()), None)
    if not readme:
        findings.append(Finding("DOC-001", "error", "", "Repository has no README."))
    else:
        text = readme.read_text(encoding="utf-8", errors="replace")
        if len(text.strip()) < 200:
            findings.append(Finding("DOC-002", "warning", rel(readme), "README is very short; usage and scope may be unclear."))
        if re.search(r"\bTODO\b|\bTBD\b|coming soon", text, re.I):
            findings.append(Finding("DOC-003", "warning", rel(readme), "README contains unresolved placeholder language."))

    test_files = [p for p, _ in files if p.name.startswith("test_") or p.name.endswith("_test.py") or "/tests/" in str(p)]
    if not test_files:
        findings.append(Finding("TEST-001", "error", "", "No recognizable test files found."))

    package_markers = [root / "pyproject.toml", root / "package.json", root / "Cargo.toml", root / "go.mod"]
    if not any(p.exists() for p in package_markers):
        findings.append(Finding("PKG-001", "warning", "", "No common package/build manifest found."))

    ci = root / ".github" / "workflows"
    if not ci.exists() or not any(ci.glob("*.y*ml")):
        findings.append(Finding("CI-001", "warning", "", "No GitHub Actions workflow found."))

    for path, text in files:
        if path.name.lower() == "changelog.md":
            continue
        claims = re.findall(r"(?im)^\s*(?:[-*]\s*)?(?:status|tested|tests?|coverage|benchmark|performance|secure|verified|guarantee)\s*[:=-]\s*(.+)$", text)
        for claim in claims:
            value = claim.strip()
            if re.search(r"(?:\b100%|\ball tests pass\b|\bfully tested\b|\bproduction[- ]ready\b|\bsecure\b|\bguaranteed\b|\bverified\b)", value, re.I):
                findings.append(Finding("EVID-001", "warning", rel(path), "Strong verification claim found; confirm it is backed by reproducible evidence.", value[:180]))

    link_pattern = re.compile(r"https?://[^\s)\]}>]+")
    for path, text in files:
        for url in link_pattern.findall(text):
            if "example.com" in url or "localhost" in url:
                continue
            if path.name.lower() == "readme.md":
                findings.append(Finding("LINK-001", "info", rel(path), "External URL present; network reachability is not checked by default.", url))

    return AuditResult(str(root), len(files), findings)

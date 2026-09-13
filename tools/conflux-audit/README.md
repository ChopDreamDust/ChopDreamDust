# Conflux Audit

A small, dependency-free repository preflight tool based on practical parts of the Conflux quality kernel.

## Checks

- README, tests, package metadata, and CI workflow presence.
- Strong verification claims that should be backed by reproducible evidence.
- External links as review points; network reachability is intentionally not claimed.
- JSON output for automation.
- Conservative exit codes: errors fail by default; warnings can also fail CI.

This is a preflight tool. It does not prove that a project works or replace human review.

## Usage

Run directly from the tool directory:

```bash
cd tools/conflux-audit
python -m conflux_audit .
python -m conflux_audit . --format json
python -m conflux_audit . --fail-on warning
```

Or install the local package:

```bash
cd tools/conflux-audit
python -m pip install -e .
conflux-audit .
```

No network access is required at runtime.

## Development

```bash
cd tools/conflux-audit
python -m unittest discover -s tests -v
```

The runtime uses only the Python standard library.

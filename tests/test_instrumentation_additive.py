"""Static accuracy guardrails for the VICE instrumentation branch."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).parents[1]

def diff_files():
    out = subprocess.check_output(["git", "diff", "--name-only",
                                   "upstream/v3.10.0...HEAD"], cwd=ROOT, text=True)
    return {Path(x) for x in out.splitlines() if x}

def test_only_allowlisted_areas_are_modified():
    changed = diff_files()
    forbidden = ("src/cpu/", "src/maincpu/", "src/memory/", "src/raster/")
    assert not any(str(p).replace("\\", "/").startswith(forbidden) for p in changed)

def test_observer_changes_are_additive():
    changed = {str(p).replace("\\", "/") for p in diff_files()}
    for path in ("src/iecbus/iecbus.c", "src/c128/c128.c", "src/vdc/vdc.c",
                 "src/monitor/monitor_binary.c"):
        assert path in changed

def test_pristine_branch_is_ancestor():
    subprocess.check_call(["git", "merge-base", "--is-ancestor",
                           "upstream/v3.10.0", "HEAD"], cwd=ROOT)

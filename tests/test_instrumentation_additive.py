"""Static accuracy guardrails for the VICE instrumentation branch."""
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).parents[1]

def diff_files():
    if subprocess.call(["git", "rev-parse", "--verify", "upstream/v3.10.0"], cwd=ROOT,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
        pytest.skip("upstream branch is available in the development checkout only")
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

def test_iec_recorder_exposes_raw_drive_context_and_inferred_semantics():
    source = (ROOT / "src" / "iecbus" / "iecbus.c").read_text(encoding="utf-8")
    for field in ("drive_context", "semantic", "cpu_regs.pc", "cpu_regs.a",
                  "cpu_regs.x", "cpu_regs.y"):
        assert field in source
    # The implementation must document that labels are hints, not ROM symbols.
    docs = (ROOT / "doc" / "iec-jsonl-recorder.txt").read_text(encoding="utf-8")
    assert "line-level hints" in docs

def test_pristine_branch_is_ancestor():
    if subprocess.call(["git", "rev-parse", "--verify", "upstream/v3.10.0"], cwd=ROOT,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
        pytest.skip("upstream branch is available in the development checkout only")
    subprocess.check_call(["git", "merge-base", "--is-ancestor",
                           "upstream/v3.10.0", "HEAD"], cwd=ROOT)

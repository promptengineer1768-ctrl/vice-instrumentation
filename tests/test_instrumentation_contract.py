from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_keyboard_extension_contract():
    source = read("src/monitor/monitor_binary.c")
    docs = read("doc/binary-monitor-keyboard-matrix.txt")
    assert "e_MON_CMD_KEYBOARD_MATRIX = 0x74" in source
    assert "keyboard_set_keyarr_any" in source
    assert "0x74" in docs


def test_iec_observer_contract():
    header = read("src/iecbus.h")
    source = read("src/c64/c64iec.c")
    assert "iecbus_observer_t" in header
    assert "iecbus_set_observer" in header
    assert "iecbus_observer(&iecbus)" in source


def test_c128_and_vdc_timing_contracts():
    c128 = read("src/c128/c128.h")
    vdc = read("src/vdc/vdc.h")
    vdc_docs = read("doc/vdc-timing-sample.txt")
    assert "c128_get_timing_sample" in c128
    assert "vdc_get_timing_sample" in vdc
    assert "busy_until" in vdc_docs

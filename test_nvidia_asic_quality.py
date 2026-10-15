"""Regression tests using selected driver response bytes; no GPU or NvAPI is required."""
import ctypes
import json
from pathlib import Path
import struct
import unittest

import nvidia_asic_quality as n


FIXTURE = json.loads((Path(__file__).parent / "tests/fixtures/blackwell-595.99.02.json").read_text())


def buffers(gpu_index):
    gpu = FIXTURE["gpus"][gpu_index]
    layout = FIXTURE["layout"]
    info, control = bytearray(n.INFO_SIZE), bytearray(n.CTRL_SIZE)
    info[0x24] = gpu["die_count"]
    mask = sum(1 << variable["var"] for variable in gpu["variables"])
    info[4:0x24] = control[4:0x24] = mask.to_bytes(32, "little")
    for variable in gpu["variables"]:
        e = layout["info_base"] + variable["var"] * layout["info_stride"]
        c = layout["control_base"] + variable["var"] * layout["control_stride"]
        for offset, data in variable["info"].items():
            offset, data = int(offset, 16), bytes.fromhex(data)
            info[e + offset:e + offset + len(data)] = data
        data = bytes.fromhex(variable["control"])
        control[c:c + len(data)] = data
    return info, control


class CapturedApi:
    def __init__(self, gpu_index, info=None, control=None):
        self.name = FIXTURE["gpus"][gpu_index]["name"]
        captured_info, captured_control = buffers(gpu_index)
        self.info = captured_info if info is None else info
        self.control = captured_control if control is None else control

    def call(self, key, handle, buffer):
        data = {"GetFullName": self.name.encode() + b"\0",
                "VfeVarGetInfo": self.info, "VfeVarGetControl": self.control}[key]
        ctypes.memmove(buffer.raw, bytes(data), len(data))
        return 0


def read(gpu_index, **kwargs):
    return n.read_gpu(CapturedApi(gpu_index, **kwargs), None, gpu_index, gpu_index + 1, False)


class FuseTests(unittest.TestCase):
    def test_gb300_has_two_independent_die_readings(self):
        gpu = read(1)
        self.assertNotIn("error", gpu)
        self.assertEqual([die["die"] for die in gpu["dies"]], [0, 1])
        for die, speedo, quality, nvvdd, nvvdd_raw, msvdd, msvdd_raw in [
                (0, 2170, 49.5, 30400, 608, 12100, 242),
                (1, 2182, 55.6, 32900, 658, 13200, 264)]:
            with self.subTest(die=die):
                fuses = gpu["dies"][die]["fuses"]
                self.assertEqual(fuses["speedo"]["value"], speedo)
                self.assertEqual(fuses["speedo"]["raw"], speedo)
                self.assertEqual(fuses["speedo"]["quality"], quality)
                self.assertEqual(fuses["speedo"]["range"], [2071.03, 2270.77])
                self.assertEqual((fuses["nvvdd"]["value"], fuses["nvvdd"]["raw"]), (nvvdd, nvvdd_raw))
                self.assertEqual((fuses["msvdd"]["value"], fuses["msvdd"]["raw"]), (msvdd, msvdd_raw))
                self.assertTrue(all(f["valid"] for f in fuses.values()))
                self.assertFalse(any(f["override"] for f in fuses.values()))

    def test_rtx_scalar_json_is_preserved(self):
        gpu = read(0)
        self.assertNotIn("dies", gpu)
        self.assertNotIn("error", gpu)
        self.assertEqual(gpu["fuses"]["speedo"], {
            "var": 14, "value": 2181, "raw": 2181, "valid": True, "override": False,
            "range": [2056.93, 2284.87], "quality": 54.4})
        self.assertEqual(gpu["fuses"]["nvvdd"]["value"], 58650)
        self.assertEqual(gpu["fuses"]["msvdd"]["value"], 18700)

    def test_ada_type_7_remains_supported(self):
        info, control = buffers(0)
        e = n.INFO_BASE + 14 * n.INFO_STRIDE
        struct.pack_into("<I", info, e, 7)
        info[e + 0x654] = 7
        self.assertEqual(n.parse_fuses(info, control)["speedo"]["value"], 2181)

    def test_missing_control_preserves_each_die_without_quality(self):
        info, _ = buffers(1)
        for die, expected in [(0, 2170), (1, 2182)]:
            speedo = n.parse_fuses(info, None, die)["speedo"]
            self.assertEqual(speedo["value"], expected)
            self.assertNotIn("quality", speedo)
            self.assertIsNone(speedo["override"])

    def test_version_bytes_do_not_replace_completion_flags(self):
        info, control = buffers(1)
        e = n.INFO_BASE + 16 * n.INFO_STRIDE
        info[e + 0x138] = 0
        info[e + 0x145] = 0
        first = n.parse_fuses(info, control, 0)["speedo"]
        second = n.parse_fuses(info, control, 1)["speedo"]
        self.assertTrue(first["valid"])
        self.assertEqual(first["quality"], 49.5)
        self.assertFalse(second["valid"])
        self.assertNotIn("quality", second)
        output = n.table([read(1, info=info, control=control)], n.TEXT["en"], False)
        self.assertNotIn("2182", output)

    def test_control_override_is_shared_without_overwriting_raw_values(self):
        info, control = buffers(1)
        control[n.CTRL_BASE + 16 * n.CTRL_STRIDE + 0x2C] = 1
        for die, raw in [(0, 2170), (1, 2182)]:
            speedo = n.parse_fuses(info, control, die)["speedo"]
            self.assertTrue(speedo["override"])
            self.assertEqual(speedo["raw"], raw)

    def test_unknown_ids_are_not_identified_from_plausible_values(self):
        info, control = buffers(1)
        e = n.INFO_BASE + 16 * n.INFO_STRIDE
        info[e + 0x114:e + 0x116] = b"\xfe\xfe"
        gpu = read(1, info=info, control=control)
        for die in gpu["dies"]:
            self.assertNotIn("speedo", die["fuses"])
        self.assertIn("no Speedo", gpu["error"])
        self.assertIn((14, 254, 59), n.variable_summary(info))
        self.assertIn((14, 254, 109), n.variable_summary(info))

    def test_mask_excludes_a_populated_speedo_slot(self):
        info, control = buffers(1)
        mask = int.from_bytes(info[4:0x24], "little") & ~(1 << 16)
        info[4:0x24] = mask.to_bytes(32, "little")
        self.assertNotIn("speedo", n.parse_fuses(info, control, 0))

    def test_speedo_is_identified_by_fields_after_slot_relocation(self):
        info, control = buffers(1)
        source = n.INFO_BASE + 16 * n.INFO_STRIDE
        target = n.INFO_BASE + 70 * n.INFO_STRIDE
        info[target:target + n.INFO_STRIDE] = info[source:source + n.INFO_STRIDE]
        c_source = n.CTRL_BASE + 16 * n.CTRL_STRIDE
        c_target = n.CTRL_BASE + 70 * n.CTRL_STRIDE
        control[c_target:c_target + n.CTRL_STRIDE] = control[c_source:c_source + n.CTRL_STRIDE]
        mask = (int.from_bytes(info[4:0x24], "little") & ~(1 << 16)) | (1 << 70)
        info[4:0x24] = mask.to_bytes(32, "little")
        for die, expected in [(0, 2170), (1, 2182)]:
            speedo = n.parse_fuses(info, control, die)["speedo"]
            self.assertEqual((speedo["var"], speedo["value"]), (70, expected))

    def test_signed_values_and_raw_values_have_independent_flags(self):
        info, control = buffers(1)
        e = n.INFO_BASE + 16 * n.INFO_STRIDE
        info[e + 0x120] = info[e + 0x130] = 1
        struct.pack_into("<i", info, e + 0x124, -6)
        struct.pack_into("<i", info, e + 0x134, -7)
        first = n.parse_fuses(info, control, 0)["speedo"]
        second = n.parse_fuses(info, control, 1)["speedo"]
        self.assertEqual(first["value"], 2170)
        self.assertEqual((second["value"], second["raw"]), (-6, -7))
        self.assertNotIn("quality", second)

    def test_unknown_die_count_does_not_decode_paired_values(self):
        for count in (0, 1, 3):
            with self.subTest(count=count):
                info, control = buffers(1)
                info[0x24] = count
                gpu = read(1, info=info, control=control)
                self.assertNotIn("dies", gpu)
                self.assertIn("no Speedo", gpu["error"])

    def test_duplicate_matches_are_rejected_per_die(self):
        info, control = buffers(1)
        source = n.INFO_BASE + 16 * n.INFO_STRIDE
        target = n.INFO_BASE + 17 * n.INFO_STRIDE
        info[target:target + n.INFO_STRIDE] = info[source:source + n.INFO_STRIDE]
        info[target + 0x115] = 0xFE
        mask = int.from_bytes(info[4:0x24], "little") | (1 << 17)
        info[4:0x24] = mask.to_bytes(32, "little")
        self.assertNotIn("speedo", n.parse_fuses(info, control, 0))
        self.assertEqual(n.parse_fuses(info, control, 1)["speedo"]["value"], 2182)

    def test_nonfinite_or_zero_width_range_does_not_produce_quality(self):
        info, control = buffers(1)
        for bounds in [(float("nan"), 2270.77), (2071.03, float("inf")), (0.0, 0.0)]:
            with self.subTest(bounds=bounds):
                struct.pack_into("<ff", control, n.CTRL_BASE + 16 * n.CTRL_STRIDE + 4, *bounds)
                self.assertNotIn("quality", n.parse_fuses(info, control, 0)["speedo"])

    def test_mixed_gpu_table_has_three_rows_and_no_false_override(self):
        for lang in ("en", "es"):
            output = n.table([read(0), read(1)], n.TEXT[lang], False)
            rows = output.splitlines()[2:5]
            self.assertEqual(len(rows), 3)
            self.assertIn("RTX PRO 6000", rows[0])
            self.assertIn("2170", rows[1])
            self.assertIn("2182", rows[2])
            self.assertNotIn("*", output)
            self.assertIn(n.TEXT[lang]["per_die"], output)

    def test_scalar_table_keeps_its_columns(self):
        output = n.table([read(0)], n.TEXT["en"], False)
        self.assertNotIn("Die", output.splitlines()[0])
        self.assertIn("54.4 %", output)


if __name__ == "__main__":
    unittest.main()

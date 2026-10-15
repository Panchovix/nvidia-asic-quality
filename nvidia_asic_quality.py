#!/usr/bin/env python3
"""Show NVIDIA GPU Speedo, ASIC quality and IDDQ (read-only).

Uses only NvAPI GET functions from the NVIDIA driver (libnvidia-api.so.1 on Linux,
nvapi64.dll on Windows). Nothing on the GPU is changed.
ASIC quality = 100 * (Speedo - min) / (max - min), with the model range the driver reports.
"""
import argparse
import ctypes as C
import json
import math
import os
import struct
import sys

IDS = {"Initialize": 0x0150E828, "EnumPhysicalGPUs": 0xE5AC921F, "GetBusId": 0x1BE0B8E5,
       "GetFullName": 0xCEEE8E9F, "ManufacturingInfo": 0xA4218928,
       "VfeVarGetInfo": 0xB9DA41D6, "VfeVarGetControl": 0x5D387298}
MFG_VER, MFG_SIZE = 0x10018, 0x18
INFO_VER, INFO_SIZE, INFO_BASE, INFO_STRIDE = 0x2F9568, 0x2B9568, 0x128, 0x2BC0
CTRL_VER, CTRL_SIZE, CTRL_BASE, CTRL_STRIDE = 0x29FC8, 0x9FC8, 0x68, 0xA0
# Fuse variables: type 0xD (Blackwell) by (fuse id, version field id); type 7 (Ada and older) by field id.
FUSE_D = {(0x00, 1): "speedo", (0x18, 3): "nvvdd", (0x19, 3): "msvdd", (0x1B, 1): "oc_bin"}
FUSE_7 = {0x07: "speedo", 0x10: "nvvdd", 0x11: "msvdd"}
# Type 0xE uses two VFIELD ID/version pairs, observed on GB300 with driver 595.99.02.
FUSE_E = {(0x3A, 0x3B): "speedo", (0x6C, 0x6D): "speedo",
          (0x4B, 0x3D): "nvvdd", (0x7D, 0x6F): "nvvdd",
          (0x4C, 0x3D): "msvdd", (0x7E, 0x6F): "msvdd",
          (0x4E, 0x3B): "oc_bin", (0x80, 0x6D): "oc_bin"}
FOUNDRY = {1: "TSMC", 2: "UMC", 3: "Chartered", 5: "IBM", 6: "SMIC", 7: "TOSHIBA", 8: "SONY"}
B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GUARD = 4096
NVAPI_STATUS = {-3: "no implementation", -5: "invalid argument", -6: "device not found",
                -9: "incompatible struct version", -104: "not supported"}

TEXT = {
    "en": {"device": "#", "bus": "Bus", "gpu": "GPU", "speedo": "Speedo", "range": "Model range", "quality": "ASIC quality",
           "nvvdd": "IDDQ NVVDD", "msvdd": "IDDQ MSVDD", "ecid": "ECID", "die": "Die", "na": "n/a",
           "note": "ASIC quality: where the Speedo sits inside its model's range (same as HWiNFO and mVolt+).\n"
                   "Compare only cards of the same model; each model has its own range.",
           "override": "* Fuse override active: a value may differ from the chip's fuses.",
           "per_die": "Dual-die GPUs: one row per die; ASIC quality is calculated separately for each die.",
           "none": "No NVIDIA GPU found.",
           "missing": "n/a: the driver does not report a Speedo for this GPU here; --json shows why."},
    "es": {"device": "#", "bus": "Bus", "gpu": "GPU", "speedo": "Speedo", "range": "Rango del modelo", "quality": "Calidad ASIC",
           "nvvdd": "IDDQ NVVDD", "msvdd": "IDDQ MSVDD", "ecid": "ECID", "die": "Die", "na": "n/d",
           "note": "Calidad ASIC: dónde cae el Speedo dentro del rango de su modelo (igual que HWiNFO y mVolt+).\n"
                   "Compara solo tarjetas del mismo modelo; cada modelo tiene su propio rango.",
           "override": "* Override de fusible activo: un valor puede diferir del grabado en fábrica.",
           "per_die": "GPUs de dos dies: una fila por die; la calidad ASIC se calcula por separado para cada die.",
           "none": "No se encontró ninguna GPU NVIDIA.",
           "missing": "n/d: el driver no entrega un Speedo para esta GPU; --json muestra el motivo."},
}


class Buffer:
    """Zeroed buffer with guard bytes after it, checked after every call."""
    def __init__(self, size, version=None, seed=b""):
        self.size = size
        self.raw = C.create_string_buffer(size + GUARD)
        C.memset(C.addressof(self.raw) + size, 0xCD, GUARD)
        C.memmove(self.raw, seed, len(seed))
        if version is not None:
            struct.pack_into("<I", self.raw, 0, version)

    def data(self):
        if self.raw.raw[self.size:] != b"\xcd" * GUARD:
            sys.exit("ABORT: NvAPI wrote past its buffer (unexpected driver ABI)")
        return self.raw.raw[:self.size]


class NvApi:
    def __init__(self):
        name = "nvapi64.dll" if os.name == "nt" else "libnvidia-api.so.1"
        try:
            query = C.CDLL(name).nvapi_QueryInterface
        except (OSError, AttributeError) as error:
            sys.exit(f"Cannot load {name}: {error}")
        query.restype, query.argtypes = C.c_void_p, [C.c_uint32]
        self.functions = {}
        for key, ident in IDS.items():
            address = query(ident)
            args = [] if key == "Initialize" else [C.c_void_p, C.c_void_p]
            self.functions[key] = C.CFUNCTYPE(C.c_int, *args)(address) if address else None
        if not self.functions["Initialize"] or self.functions["Initialize"]() != 0:
            sys.exit("NvAPI initialization failed")

    def call(self, key, handle, buffer):
        function = self.functions[key]
        if function is None:
            return -3  # NVAPI_NO_IMPLEMENTATION
        status = function(handle, C.c_void_p(C.addressof(buffer.raw)))
        buffer.data()
        return status

    def gpus(self):
        handles, count = Buffer(64 * 8), Buffer(4)
        if self.functions["EnumPhysicalGPUs"](C.c_void_p(C.addressof(handles.raw)),
                                              C.c_void_p(C.addressof(count.raw))) != 0:
            return []
        n = struct.unpack_from("<I", count.data())[0]
        return [C.c_void_p(h) for h in struct.unpack_from(f"<{n}Q", handles.data())]


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def signed_value(data, offset, flag_offset):
    raw = u32(data, offset)
    return raw - (1 << 32) if data[flag_offset] and raw >> 31 else raw


def ecid_text(q0, q1):
    lot = B36[q1 & 63] + "".join(B36[(q0 >> shift) & 63] for shift in range(58, 9, -6))
    x = (q1 >> 12) & 0x1FF
    x = x - 0x200 if x & 0x100 else x
    return "%s-%s%s-%02d_x%d_y%d" % (FOUNDRY.get(q0 & 0xF, "?"), B36[(q0 >> 4) & 63], lot,
                                     (q1 >> 6) & 63, x, (q1 >> 21) & 0x1FF)


def variable_summary(info):
    """(type, field id, version field id) of every listed VFE variable, for chips this script does not know."""
    mask = int.from_bytes(info[4:0x24], "little")
    summary = set()
    for i in range(255):
        if not mask >> i & 1:
            continue
        e = INFO_BASE + i * INFO_STRIDE
        var_type = u32(info, e)
        if var_type == 0xE:
            summary.update((var_type, info[e + 0x114 + die], info[e + 0x116 + die]) for die in range(2))
        else:
            summary.add((var_type, info[e + 0x654], info[e + 0x655]))
    return sorted(summary)


def parse_fuses(info, ctrl, die=None):
    """Read scalar fuses, or one die of type 0xE fuses, from INFO and optional CONTROL."""
    mask = int.from_bytes(info[4:0x24], "little")
    matches = {}
    for i in range(255):
        if not mask >> i & 1:
            continue
        e = INFO_BASE + i * INFO_STRIDE
        var_type = u32(info, e)
        if die is not None:
            if var_type != 0xE or die not in (0, 1):
                continue
            name = FUSE_E.get((info[e + 0x114 + die], info[e + 0x116 + die]))
            if not name:
                continue
            # Two signed-value structs precede two hardware-value structs. The bytes
            # at 0x138 are fuse versions; version-check completion is at 0x144.
            d = die * 8
            reading = {"var": i, "value": signed_value(info, e + 0x11C + d, e + 0x118 + d),
                       "raw": signed_value(info, e + 0x12C + d, e + 0x128 + d),
                       "valid": bool(info[e + 0x144 + die]), "override": None}
        else:
            field, version = info[e + 0x654], info[e + 0x655]
            name = (FUSE_D.get((field, version)) if var_type == 0xD
                    else FUSE_7.get(field) if var_type == 7 else None)
            if not name:
                continue
            reading = {"var": i, "value": signed_value(info, e + 0x11C, e + 0x118),
                       "raw": signed_value(info, e + 0x124, e + 0x120),
                       "valid": bool(info[e + 0x138]), "override": bool(info[e + 0x134])}
        if ctrl is not None:
            c = CTRL_BASE + i * CTRL_STRIDE
            low, high = struct.unpack_from("<ff", ctrl, c + 4)
            if math.isfinite(low) and math.isfinite(high) and low < high and high - low < 1e9:
                reading["range"] = [round(low, 2), round(high, 2)]
            reading["override"] = bool(reading["override"] or u32(ctrl, c + 0x2C))
        matches.setdefault(name, []).append(reading)
    fuses = {name: found[0] for name, found in matches.items() if len(found) == 1}
    speedo = fuses.get("speedo")
    if speedo and speedo["valid"] and "range" in speedo:
        low, high = speedo["range"]
        if low <= speedo["value"] <= high:
            speedo["quality"] = round(100 * (speedo["value"] - low) / (high - low), 1)
    return fuses


def read_gpu(api, handle, device, bus, with_ecid):
    name = Buffer(64)
    api.call("GetFullName", handle, name)
    gpu = {"device": device, "bus": "%02x" % bus,
           "name": name.data().split(b"\0")[0].decode(errors="replace").removeprefix("NVIDIA ")}
    if with_ecid:
        mfg = Buffer(MFG_SIZE, MFG_VER)
        if api.call("ManufacturingInfo", handle, mfg) == 0:
            q0, q1 = struct.unpack_from("<QI", mfg.data(), 8)
            gpu["ecid"] = ecid_text(q0, q1)
    info = Buffer(INFO_SIZE, INFO_VER)
    status = api.call("VfeVarGetInfo", handle, info)
    if status != 0:
        gpu["error"] = f"PerfVfeVarGetInfo returned NvAPI status {status} ({NVAPI_STATUS.get(status, 'other')})"
        return gpu
    info_data = info.data()
    ctrl = Buffer(CTRL_SIZE, CTRL_VER, seed=bytes(4) + info_data[4:0x24])
    ctrl_data = ctrl.data() if api.call("VfeVarGetControl", handle, ctrl) == 0 else None
    gpu["fuses"] = parse_fuses(info_data, ctrl_data)
    if info_data[0x24] == 2:  # Only the two-die INFO layout has been decoded.
        dies = [{"die": die, "fuses": parse_fuses(info_data, ctrl_data, die)} for die in range(2)]
        if any(die["fuses"] for die in dies):
            gpu["dies"] = dies
    if "speedo" not in gpu["fuses"] and not any("speedo" in die["fuses"] for die in gpu.get("dies", [])):
        gpu["error"] = "no Speedo fuse variable matched; variables found: " + json.dumps(variable_summary(info_data))
    return gpu


def table(gpus, text, with_ecid):
    na = text["na"]
    with_dies = any(gpu.get("dies") for gpu in gpus)
    header = ["device", "bus", "gpu"] + (["die"] if with_dies else [])
    header += ["speedo", "range", "quality", "nvvdd", "msvdd"] + (["ecid"] if with_ecid else [])
    rows, overridden = [], False
    for gpu in gpus:
        for die in gpu.get("dies", [{"fuses": gpu.get("fuses", {})}]):
            fuses = die["fuses"]
            speedo = fuses.get("speedo", {})
            mark = "*" if any(f.get("override") for f in fuses.values()) else ""
            overridden |= bool(mark)
            quality = speedo.get("quality")
            value = lambda key: str(fuses[key]["value"]) if fuses.get(key, {}).get("valid") else na
            rows.append([str(gpu["device"]), gpu["bus"], gpu["name"]]
                        + ([str(die.get("die", "-"))] if with_dies else [])
                        + [f"{value('speedo')}{mark}" if speedo.get("valid") else na,
                           "%.1f-%.1f" % tuple(speedo["range"]) if "range" in speedo else na,
                           f"{quality:.1f} %" if quality is not None else na, value("nvvdd"), value("msvdd")]
                        + ([gpu.get("ecid", na)] if with_ecid else []))
    titles = [text[key] for key in header]
    widths = [max(len(row[i]) for row in rows + [titles]) for i in range(len(titles))]
    right = {i for i, key in enumerate(header) if key in {"device", "die", "speedo", "quality", "nvvdd", "msvdd"}}
    line = lambda cells: "  ".join(c.rjust(w) if i in right else c.ljust(w)
                                   for i, (c, w) in enumerate(zip(cells, widths))).rstrip()
    out = [line(titles), line(["-" * w for w in widths])] + [line(row) for row in rows]
    out += ["", text["note"]] + ([text["override"]] if overridden else [])
    out += [text["per_die"]] if with_dies else []
    out += [text["missing"]] if any("error" in gpu for gpu in gpus) else []
    return "\n".join(out)


def main():
    default_lang = "es" if os.environ.get("LC_ALL", os.environ.get("LANG", "")).startswith("es") else "en"
    parser = argparse.ArgumentParser(description="NVIDIA Speedo / ASIC quality / IDDQ (read-only)")
    parser.add_argument("--lang", choices=sorted(TEXT), default=default_lang)
    parser.add_argument("--device", type=int, help="only this GPU, by its number in the # column (PCI order, normally the same as nvidia-smi)")
    parser.add_argument("--bus", type=lambda value: int(value, 16), help="only this PCI bus (hex), e.g. 09")
    parser.add_argument("--ecid", action="store_true", help="also show the chip ECID (wafer, lot, x/y)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    api = NvApi()
    found = []
    for handle in api.gpus():
        bus = Buffer(4)
        if api.call("GetBusId", handle, bus) == 0:
            found.append((u32(bus.data(), 0), handle))
    found.sort(key=lambda item: item[0])  # PCI order, normally the nvidia-smi numbering
    gpus = [read_gpu(api, handle, device, bus, args.ecid) for device, (bus, handle) in enumerate(found)
            if (args.device is None or device == args.device) and (args.bus is None or bus == args.bus)]
    if args.json:
        print(json.dumps(gpus, indent=1))
    elif not gpus:
        print(TEXT[args.lang]["none"])
    else:
        print(table(gpus, TEXT[args.lang], args.ecid))


if __name__ == "__main__":
    main()

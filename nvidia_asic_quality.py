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
FOUNDRY = {1: "TSMC", 2: "UMC", 3: "Chartered", 5: "IBM", 6: "SMIC", 7: "TOSHIBA", 8: "SONY"}
B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GUARD = 4096

TEXT = {
    "en": {"bus": "Bus", "gpu": "GPU", "speedo": "Speedo", "range": "Model range", "quality": "ASIC quality",
           "nvvdd": "IDDQ NVVDD", "msvdd": "IDDQ MSVDD", "ecid": "ECID", "na": "n/a",
           "note": "ASIC quality: where the Speedo sits inside its model's range (same as HWiNFO and mVolt+).\n"
                   "Compare only cards of the same model; each model has its own range.",
           "override": "* Speedo override active: the value is not the fused one.",
           "none": "No NVIDIA GPU found."},
    "es": {"bus": "Bus", "gpu": "GPU", "speedo": "Speedo", "range": "Rango del modelo", "quality": "Calidad ASIC",
           "nvvdd": "IDDQ NVVDD", "msvdd": "IDDQ MSVDD", "ecid": "ECID", "na": "n/d",
           "note": "Calidad ASIC: dónde cae el Speedo dentro del rango de su modelo (igual que HWiNFO y mVolt+).\n"
                   "Compara solo tarjetas del mismo modelo; cada modelo tiene su propio rango.",
           "override": "* Override de Speedo activo: el valor no es el de fábrica.",
           "none": "No se encontró ninguna GPU NVIDIA."},
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


def parse_fuses(info, ctrl):
    """Fuse readings from a VFE variable INFO buffer and its CONTROL buffer (or None)."""
    mask = int.from_bytes(info[4:0x24], "little")
    matches = {}
    for i in range(255):
        if not mask >> i & 1:
            continue
        e = INFO_BASE + i * INFO_STRIDE
        var_type, field, version = u32(info, e), info[e + 0x654], info[e + 0x655]
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
            reading["override"] |= u32(ctrl, c + 0x2C) != 0
        matches.setdefault(name, []).append(reading)
    fuses = {name: found[0] for name, found in matches.items() if len(found) == 1}
    speedo = fuses.get("speedo")
    if speedo and speedo["valid"] and "range" in speedo:
        low, high = speedo["range"]
        if low <= speedo["value"] <= high:
            speedo["quality"] = round(100 * (speedo["value"] - low) / (high - low), 1)
    return fuses


def read_gpu(api, handle, with_ecid):
    bus, name = Buffer(4), Buffer(64)
    api.call("GetBusId", handle, bus)
    api.call("GetFullName", handle, name)
    gpu = {"bus": "%02x" % u32(bus.data(), 0),
           "name": name.data().split(b"\0")[0].decode(errors="replace").removeprefix("NVIDIA ")}
    if with_ecid:
        mfg = Buffer(MFG_SIZE, MFG_VER)
        if api.call("ManufacturingInfo", handle, mfg) == 0:
            q0, q1 = struct.unpack_from("<QI", mfg.data(), 8)
            gpu["ecid"] = ecid_text(q0, q1)
    info = Buffer(INFO_SIZE, INFO_VER)
    if api.call("VfeVarGetInfo", handle, info) != 0:
        return gpu
    info_data = info.data()
    ctrl = Buffer(CTRL_SIZE, CTRL_VER, seed=bytes(4) + info_data[4:0x24])
    ctrl_data = ctrl.data() if api.call("VfeVarGetControl", handle, ctrl) == 0 else None
    gpu["fuses"] = parse_fuses(info_data, ctrl_data)
    return gpu


def table(gpus, text, with_ecid):
    na = text["na"]
    header = ["bus", "gpu", "speedo", "range", "quality", "nvvdd", "msvdd"] + (["ecid"] if with_ecid else [])
    rows, overridden = [], False
    for gpu in gpus:
        fuses = gpu.get("fuses", {})
        speedo = fuses.get("speedo", {})
        mark = "*" if any(f.get("override") for f in fuses.values()) else ""
        overridden |= bool(mark)
        quality = speedo.get("quality")
        rows.append([gpu["bus"], gpu["name"], f"{speedo['value']}{mark}" if speedo else na,
                     "%.1f-%.1f" % tuple(speedo["range"]) if "range" in speedo else na,
                     f"{quality:.1f} %" if quality is not None else na,
                     str(fuses["nvvdd"]["value"]) if "nvvdd" in fuses else na,
                     str(fuses["msvdd"]["value"]) if fuses.get("msvdd", {}).get("value") else na]
                    + ([gpu.get("ecid", na)] if with_ecid else []))
    titles = [text[key] for key in header]
    widths = [max(len(row[i]) for row in rows + [titles]) for i in range(len(titles))]
    right = {2, 4, 5, 6}
    line = lambda cells: "  ".join(c.rjust(w) if i in right else c.ljust(w)
                                   for i, (c, w) in enumerate(zip(cells, widths))).rstrip()
    out = [line(titles), line(["-" * w for w in widths])] + [line(row) for row in rows]
    out += ["", text["note"]] + ([text["override"]] if overridden else [])
    return "\n".join(out)


def main():
    default_lang = "es" if os.environ.get("LC_ALL", os.environ.get("LANG", "")).startswith("es") else "en"
    parser = argparse.ArgumentParser(description="NVIDIA Speedo / ASIC quality / IDDQ (read-only)")
    parser.add_argument("--lang", choices=sorted(TEXT), default=default_lang)
    parser.add_argument("--bus", type=lambda value: int(value, 16), help="only this PCI bus (hex), e.g. 09")
    parser.add_argument("--ecid", action="store_true", help="also show the chip ECID (wafer, lot, x/y)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    api = NvApi()
    gpus = []
    for handle in api.gpus():
        bus = Buffer(4)
        if args.bus is not None and (api.call("GetBusId", handle, bus) != 0 or u32(bus.data(), 0) != args.bus):
            continue
        gpus.append(read_gpu(api, handle, args.ecid))
    gpus.sort(key=lambda gpu: int(gpu["bus"], 16))
    if args.json:
        print(json.dumps(gpus, indent=1))
    elif not gpus:
        print(TEXT[args.lang]["none"])
    else:
        print(table(gpus, TEXT[args.lang], args.ecid))


if __name__ == "__main__":
    main()

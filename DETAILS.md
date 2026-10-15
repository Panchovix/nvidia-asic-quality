# NVIDIA ASIC quality: details

English | [Español](DETAILS_es.md)

**How much does it matter?** Usually a few percent at most at stock settings. The driver already builds each
card's V/F curve from its own Speedo, and every card has the same boost clock cap, so a card that is not power or
thermal limited reaches that cap either way. It shows up under a power limit (for example a 300 W Max-Q or a long
compute load): there the better chip holds a slightly higher clock at the same watts. From the VBIOS equations it
looks like about 1 MHz per Speedo point at a given voltage; that is our estimate, not a measurement. Going from
35 % to 60 % is about 57 Speedo points, so roughly 50–60 MHz, or about 2 % core clock. Memory-bound work such as
LLM inference barely changes, higher IDDQ (more leakage) partly cancels it under a power limit, and for manual
overclocking a higher Speedo often means more headroom, but it is still silicon lottery.

**Methodology.** Reading a factory value and normalizing it are different from validating a performance
predictor. Cross-check the fuse IDs, per-die mapping and units with an independent decoder or matching fuse/VBIOS
definitions, and repeat captures to confirm that raw fuse values remain stable. The `valid` flag requires a
completed driver version check and, when enabled, a matching fuse version; mismatches are excluded even if the
driver permits a fallback default. Driver overrides still require separate inspection.

To test predictive value, collect multiple matching cards after warm-up. At fixed clocks, compare power or energy
per unit of work; at a fixed power cap, compare sustained clocks and throughput. Repeat measurements while
recording temperature, memory clocks, throttling reasons and software versions, and include both compute-bound
and memory-bound workloads. NVIDIA describes these controls in its
[performance measurement guide](https://docs.nvidia.com/deeplearning/tensorrt/10.x.x/performance/hw-sw-environment.html).
For Grace Blackwell, also record CPU/module power budgets because
[power steering can change the GPU budget](https://docs.nvidia.com/dccpu/grace-perf-tuning-guide/power-thermals.html).
The 1 MHz per point figure above is an estimate; this project has not measured a MHz-per-Speedo conversion,
an expected performance gain or a statistical percentile.

**Precision and collection.** Quality uses the unrounded float32 bounds from the driver. JSON preserves those
bounds; the table rounds only for display. More decimal places do not increase the precision of an integer fuse.
`--diagnostics` implies JSON and returns an object containing driver/architecture/ABI information and a `gpus`
array. Each GPU includes VBIOS version, call status codes, variable indices, fuse IDs and version-check metadata.
The NvAPI driver-version query can be unavailable; on Linux the kernel module version line is included when
readable. Use `python3 nvidia_asic_quality.py --device 1 --diagnostics > gb300.json` for a reproducible report.

**Datacenter GPUs.** Experimental GB300 support reads paired type `0xE` VFE fuse variables and shows one row
per die. Each die gets its own Speedo, ASIC quality and IDDQ readings; no package-wide quality is calculated.
For example, one GB300 reports Speedo 2170 / 2182, quality 49.5 % / 55.6 %, NVVDD IDDQ 30400 / 32900 and
MSVDD IDDQ 12100 / 13200, with a shared model range of 2071.03–2270.77.

The GB300 fuse IDs and layout were inferred from driver responses and NvAPI conversion code on Linux aarch64
with driver 595.99.02. Other dual-die GPUs, Windows and registry overrides are untested. The override flag for
paired variables comes from GetControl and is `null` in JSON if that call is unavailable. Other datacenter
models or unknown fuse IDs can still show `n/a`.

Single-die JSON keeps its `fuses` object. Dual-die GPUs additionally have a `dies` array, with a zero-based `die`
index and a `fuses` object for each die. `--device` and `--bus` select the GPU and include both dies. The `Die`
column appears only when at least one selected GPU has paired readings.

**Read-only.** It calls only NvAPI GET functions from the NVIDIA driver (`libnvidia-api.so.1`): Initialize,
EnumPhysicalGPUs, GetBusId, GetFullName, ManufacturingInfo, PerfVfeVarGetInfo and PerfVfeVarGetControl.
Diagnostics additionally call GetVbiosVersionString and SYS_GetDriverAndBranchVersion.
Nothing on the GPU is changed. It needs Python 3.9+ and no extra packages. Depending on the permissions of
`/dev/nvidia*` it may need `sudo`.

Tested on Linux with driver 615.78.08: RTX 5090, 5080, 5070 Ti, RTX PRO 6000 Blackwell Max-Q, RTX PRO 4000
Blackwell SFF and RTX 2000 Ada. On Windows it loads `nvapi64.dll` instead; confirmed working on Windows.
Older GPUs, or drivers with a different structure layout, show `n/a`.

Run `python3 -m unittest -v` for regression tests using selected driver response bytes; no GPU or NvAPI library
is required. The fixtures contain no ECIDs.

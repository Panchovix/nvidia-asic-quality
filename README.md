# NVIDIA ASIC quality

[English](#english) · [Español](#español)

## English

A small read-only script that shows, for each NVIDIA GPU, the **Speedo**, its **ASIC quality** and the **IDDQ**
(leakage) of the NVVDD and MSVDD rails. This is the same data HWiNFO and mVolt+ show on Windows.

```
$ sudo python3 nvidia_asic_quality.py --lang en
Bus  GPU                                               Speedo  Model range    ASIC quality  IDDQ NVVDD  IDDQ MSVDD
---  ------------------------------------------------  ------  -------------  ------------  ----------  ----------
03   RTX PRO 6000 Blackwell Max-Q Workstation Edition    2169  2056.9-2284.9        49.2 %       61800       20400
06   GeForce RTX 5090                                    2113  2018.9-2284.9        35.4 %       43750       14450
07   GeForce RTX 5080                                    2247  2054.8-2287.0        82.8 %       35250       13650
13   RTX 2000 Ada Generation                             2008  1901.6-2122.9        48.1 %        9200         n/a
```

- **Speedo**: a speed value written into the chip's fuses at the factory. Higher means faster silicon.
- **ASIC quality**: `100 × (Speedo − min) / (max − min)`. The range comes from the driver (the card's VBIOS) and
  is fixed for each model. Only compare cards of the same model.
- **IDDQ**: leakage current per rail, also from the fuses. It is larger on bigger chips.
- `--ecid` also shows the chip ID: foundry, lot, wafer and x/y position on the wafer.
- `--bus 07` reads only one GPU; `--json` prints machine-readable output.

**Read-only.** It calls only NvAPI GET functions from the NVIDIA driver (`libnvidia-api.so.1`): Initialize,
EnumPhysicalGPUs, GetBusId, GetFullName, ManufacturingInfo, PerfVfeVarGetInfo and PerfVfeVarGetControl.
Nothing on the GPU is changed. It needs Python 3.9+ and no extra packages. Depending on the permissions of
`/dev/nvidia*` it may need `sudo`.

Tested on Linux with driver 615.78.08: RTX 5090, 5080, 5070 Ti, RTX PRO 6000 Blackwell Max-Q, RTX PRO 4000
Blackwell SFF and RTX 2000 Ada. On Windows it loads `nvapi64.dll` instead; that path is untested.
Older GPUs, or drivers with a different structure layout, show `n/a`.

## Español

Un script pequeño, solo de lectura, que muestra para cada GPU NVIDIA el **Speedo**, su **calidad ASIC** y la
**IDDQ** (fuga) de los rieles NVVDD y MSVDD. Son los mismos datos que muestran HWiNFO y mVolt+ en Windows.

```
$ sudo python3 nvidia_asic_quality.py --lang es
Bus  GPU                                               Speedo  Rango del modelo  Calidad ASIC  IDDQ NVVDD  IDDQ MSVDD
---  ------------------------------------------------  ------  ----------------  ------------  ----------  ----------
03   RTX PRO 6000 Blackwell Max-Q Workstation Edition    2169  2056.9-2284.9           49.2 %       61800       20400
06   GeForce RTX 5090                                    2113  2018.9-2284.9           35.4 %       43750       14450
07   GeForce RTX 5080                                    2247  2054.8-2287.0           82.8 %       35250       13650
13   RTX 2000 Ada Generation                             2008  1901.6-2122.9           48.1 %        9200         n/d
```

- **Speedo**: un valor de velocidad grabado en fábrica en los fusibles del chip. Más alto significa silicio más rápido.
- **Calidad ASIC**: `100 × (Speedo − mín) / (máx − mín)`. El rango lo entrega el driver (sale de la VBIOS de la
  tarjeta) y es fijo para cada modelo. Compara solo tarjetas del mismo modelo.
- **IDDQ**: corriente de fuga por riel, también de los fusibles. Es mayor en chips más grandes.
- `--ecid` muestra además el ID del chip: fundición, lote, oblea y posición x/y en la oblea.
- `--bus 07` lee solo una GPU; `--json` entrega la salida en JSON.

**Solo lectura.** Usa únicamente funciones GET de NvAPI del driver de NVIDIA (`libnvidia-api.so.1`): Initialize,
EnumPhysicalGPUs, GetBusId, GetFullName, ManufacturingInfo, PerfVfeVarGetInfo y PerfVfeVarGetControl.
No cambia nada en la GPU. Necesita Python 3.9+ y ningún paquete extra. Según los permisos de `/dev/nvidia*`
puede requerir `sudo`.

Probado en Linux con el driver 615.78.08: RTX 5090, 5080, 5070 Ti, RTX PRO 6000 Blackwell Max-Q, RTX PRO 4000
Blackwell SFF y RTX 2000 Ada. En Windows carga `nvapi64.dll`; ese camino no está probado.
GPUs más antiguas, o drivers con otra estructura, muestran `n/d`.

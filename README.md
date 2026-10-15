# NVIDIA ASIC quality

[English](#english) · [Español](#español)

## English

A small read-only script that shows, for each NVIDIA GPU, the **Speedo**, its **ASIC quality** and the **IDDQ**
(leakage) of the NVVDD and MSVDD rails, using factory characterization values exposed through NvAPI.

```
$ sudo python3 nvidia_asic_quality.py --lang en
#  Bus  GPU                                               Speedo  Driver range   ASIC quality  IDDQ NVVDD  IDDQ MSVDD
-  ---  ------------------------------------------------  ------  -------------  ------------  ----------  ----------
0  03   RTX PRO 6000 Blackwell Max-Q Workstation Edition    2169  2056.9-2284.9        49.2 %       61800       20400
3  06   GeForce RTX 5090                                    2113  2018.9-2284.9        35.4 %       43750       14450
4  07   GeForce RTX 5080                                    2247  2054.8-2287.0        82.8 %       35250       13650
7  13   RTX 2000 Ada Generation                             2008  1901.6-2122.9        48.1 %        9200         n/a
```

- **Speedo**: factory silicon characterization stored in fuses. Interpret it within the same GPU design and
  calibration; it is not a measured clock speed.
- **ASIC quality**: `100 × (Speedo − min) / (max − min)`, using the bounds returned by VFE GetControl. It is a
  normalized position in that range, not a percentile or performance score. The bounds have not been established
  as manufacturing population minima/maxima. Compare matching GPU models, VBIOS versions and drivers.
- **IDDQ**: factory leakage characterization per rail, also from fuses. It is not a live current measurement;
  units and calibration depend on the GPU design.
- `--ecid` also shows the chip ID: foundry, lot, wafer and x/y position on the wafer.
- By default it reads every GPU. `--device 4` reads only one, by its number in the `#` column (PCI order,
  normally the same as `nvidia-smi`); `--bus 07` selects by PCI bus instead. `--json` prints machine-readable output.

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
This project has not established a MHz-per-Speedo conversion, expected performance gain, or statistical percentile.

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
Blackwell SFF and RTX 2000 Ada. On Windows it loads `nvapi64.dll` instead; that path is untested.
Older GPUs, or drivers with a different structure layout, show `n/a`.

Run `python3 -m unittest -v` for regression tests using selected driver response bytes; no GPU or NvAPI library
is required. The fixtures contain no ECIDs.

## Español

Un script pequeño, solo de lectura, que muestra para cada GPU NVIDIA el **Speedo**, su **calidad ASIC** y la
**IDDQ** (fuga) de los rieles NVVDD y MSVDD, usando valores de caracterización de fábrica expuestos por NvAPI.

```
$ sudo python3 nvidia_asic_quality.py --lang es
#  Bus  GPU                                               Speedo  Límites driver    Calidad ASIC  IDDQ NVVDD  IDDQ MSVDD
-  ---  ------------------------------------------------  ------  ----------------  ------------  ----------  ----------
0  03   RTX PRO 6000 Blackwell Max-Q Workstation Edition    2169  2056.9-2284.9           49.2 %       61800       20400
3  06   GeForce RTX 5090                                    2113  2018.9-2284.9           35.4 %       43750       14450
4  07   GeForce RTX 5080                                    2247  2054.8-2287.0           82.8 %       35250       13650
7  13   RTX 2000 Ada Generation                             2008  1901.6-2122.9           48.1 %        9200         n/d
```

- **Speedo**: caracterización del silicio grabada en fábrica en los fusibles. Se interpreta dentro del mismo
  diseño de GPU y calibración; no es una frecuencia medida.
- **Calidad ASIC**: `100 × (Speedo − mín) / (máx − mín)`, usando los límites de VFE GetControl. Es la posición
  normalizada en ese rango, no un percentil ni una medida de rendimiento. No se ha establecido que esos límites
  sean los extremos de la población de fabricación. Compara el mismo modelo de GPU, VBIOS y driver.
- **IDDQ**: caracterización de fuga de fábrica por riel, también de los fusibles. No es una medida de corriente
  en tiempo real; las unidades y la calibración dependen del diseño de la GPU.
- `--ecid` muestra además el ID del chip: fundición, lote, oblea y posición x/y en la oblea.
- Por defecto lee todas las GPUs. `--device 4` lee solo una, según su número en la columna `#` (orden PCI,
  normalmente el mismo de `nvidia-smi`); `--bus 07` la elige por bus PCI. `--json` entrega la salida en JSON.

**Metodología.** Leer un valor de fábrica y normalizarlo es distinto de validar una predicción de rendimiento.
Contrasta los IDs, la asignación de dies y las unidades con otro decodificador o definiciones de fusibles/VBIOS
correspondientes, y repite las capturas para confirmar que los valores crudos sean estables. La marca `valid`
requiere que el driver haya completado la comprobación de versión y, si está habilitada, que la versión coincida;
las discrepancias se excluyen aunque el driver permita un valor por defecto. Los overrides requieren inspección
por separado.

Para evaluar el valor predictivo, reúne varias tarjetas equivalentes y caliéntalas antes de medir. A frecuencia
fija, compara potencia o energía por unidad de trabajo; a límite de potencia fijo, compara frecuencia sostenida y
rendimiento. Repite las medidas registrando temperatura, frecuencia de memoria, motivos de throttling y versiones
de software, con cargas limitadas tanto por cómputo como por memoria. NVIDIA describe estos controles en su
[guía de medición de rendimiento](https://docs.nvidia.com/deeplearning/tensorrt/10.x.x/performance/hw-sw-environment.html).
En Grace Blackwell, registra también los presupuestos de potencia de CPU y módulo porque
[la distribución de potencia puede cambiar el presupuesto de la GPU](https://docs.nvidia.com/dccpu/grace-perf-tuning-guide/power-thermals.html).
Este proyecto no ha establecido una conversión de MHz por Speedo, una mejora esperada de rendimiento ni un percentil.

**Precisión y captura.** La calidad usa los límites float32 sin redondear del driver. JSON conserva esos límites;
la tabla solo redondea al mostrar. Más decimales no aumentan la precisión de un fusible entero. `--diagnostics`
implica JSON y entrega un objeto con datos del driver, arquitectura y ABI, y un arreglo `gpus`. Cada GPU incluye
versión de VBIOS, códigos de estado, índices e IDs de variables y datos de comprobación de versión. La consulta de
versión del driver por NvAPI puede no estar disponible; en Linux se incluye la línea de versión del módulo cuando
es legible. Usa `python3 nvidia_asic_quality.py --device 1 --diagnostics > gb300.json` para un informe reproducible.

**GPUs de datacenter.** El soporte experimental de GB300 lee variables VFE de tipo `0xE` con valores para dos
dies y muestra una fila por die. Cada die tiene su propio Speedo, calidad ASIC e IDDQ; no se calcula una calidad
para todo el encapsulado. Por ejemplo, una GB300 entrega Speedo 2170 / 2182, calidad 49.5 % / 55.6 %, IDDQ NVVDD
30400 / 32900 e IDDQ MSVDD 12100 / 13200, con un rango del modelo compartido de 2071.03–2270.77.

Los IDs de fusibles y la estructura de GB300 se dedujeron de las respuestas del driver y del código de conversión
de NvAPI en Linux aarch64 con el driver 595.99.02. No se han probado otras GPUs de dos dies, Windows ni overrides
por registro. La marca de override de las variables pareadas viene de GetControl y es `null` en JSON si esa
llamada no está disponible. Otros modelos de datacenter o IDs desconocidos todavía pueden mostrar `n/d`.

El JSON de las GPUs de un die conserva su objeto `fuses`. Las GPUs de dos dies agregan un arreglo `dies`, con
un índice `die` desde cero y un objeto `fuses` para cada die. `--device` y `--bus` seleccionan la GPU e incluyen
ambos dies. La columna `Die` aparece solo cuando alguna GPU seleccionada tiene lecturas pareadas.

**Solo lectura.** Usa únicamente funciones GET de NvAPI del driver de NVIDIA (`libnvidia-api.so.1`): Initialize,
EnumPhysicalGPUs, GetBusId, GetFullName, ManufacturingInfo, PerfVfeVarGetInfo y PerfVfeVarGetControl.
Los diagnósticos también llaman a GetVbiosVersionString y SYS_GetDriverAndBranchVersion.
No cambia nada en la GPU. Necesita Python 3.9+ y ningún paquete extra. Según los permisos de `/dev/nvidia*`
puede requerir `sudo`.

Probado en Linux con el driver 615.78.08: RTX 5090, 5080, 5070 Ti, RTX PRO 6000 Blackwell Max-Q, RTX PRO 4000
Blackwell SFF y RTX 2000 Ada. En Windows carga `nvapi64.dll`; ese camino no está probado.
GPUs más antiguas, o drivers con otra estructura, muestran `n/d`.

Ejecuta `python3 -m unittest -v` para probar respuestas seleccionadas del driver; no requiere GPU ni biblioteca
NvAPI. Los datos de prueba no contienen ECIDs.

## Community results / Resultados de la comunidad

Shared by users; ECIDs are left out. ASIC quality only compares cards of the same model.
Compartidos por usuarios; sin ECID. La calidad ASIC solo compara tarjetas del mismo modelo.

### RTX PRO 6000 Blackwell (Workstation and Max-Q, range 2056.9–2284.9)

| User | GPU | Speedo | ASIC quality | IDDQ NVVDD | IDDQ MSVDD |
|---|---|---:|---:|---:|---:|
| Panchovix | Max-Q Workstation Edition | 2197 | 61.5 % | 56450 | 18550 |
| Panchovix | Max-Q Workstation Edition | 2197 | 61.5 % | 60800 | 20000 |
| aimark42 | Workstation Edition | 2195 | 60.6 % | 67900 | 22650 |
| aimark42 | Max-Q Workstation Edition | 2191 | 58.8 % | 55800 | 18500 |
| crowbill | Workstation Edition | 2171 | 50.0 % | 56100 | 17250 |
| Panchovix | Max-Q Workstation Edition | 2169 | 49.2 % | 61800 | 20400 |
| crowbill | Workstation Edition | 2159 | 44.8 % | 58250 | 19350 |
| crowbill | Workstation Edition | 2151 | 41.3 % | 50150 | 16150 |
| aimark42 | Max-Q Workstation Edition | 2138 | 35.6 % | 52000 | 17050 |
| crowbill | Workstation Edition | 2135 | 34.3 % | 45150 | 14300 |

Jack Zampolin, two machines with four GPUs each (ASIC quality only, model not stated):
workstation-1 41.3 %, 27.7 %, 47.4 %, 43.5 %; workstation-2 53.6 %, 46.1 %, 31.6 %, 66.7 %.

### Other models / Otros modelos (Panchovix)

| GPU | Speedo | Model range | ASIC quality | IDDQ NVVDD | IDDQ MSVDD |
|---|---:|---|---:|---:|---:|
| GeForce RTX 5090 | 2113 | 2018.9–2284.9 | 35.4 % | 43750 | 14450 |
| GeForce RTX 5080 | 2247 | 2054.8–2287.0 | 82.8 % | 35250 | 13650 |
| GeForce RTX 5070 Ti | 2176 | 2054.8–2287.0 | 52.2 % | 27450 | 11150 |
| RTX PRO 4000 Blackwell SFF Edition | 2161 | 2054.8–2287.0 | 45.7 % | 21100 | 8450 |
| RTX 2000 Ada Generation | 2008 | 1901.6–2122.9 | 48.1 % | 9200 | n/a |

## License / Licencia

MIT. See [LICENSE](LICENSE). / Ver [LICENSE](LICENSE).

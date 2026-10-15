# NVIDIA ASIC quality: details / detalles

[English](#english) · [Español](#español)

## English

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
Blackwell SFF and RTX 2000 Ada. On Windows it loads `nvapi64.dll` instead; that path is untested.
Older GPUs, or drivers with a different structure layout, show `n/a`.

Run `python3 -m unittest -v` for regression tests using selected driver response bytes; no GPU or NvAPI library
is required. The fixtures contain no ECIDs.

## Español

**¿Cuánto importa?** Normalmente unos pocos por ciento como mucho, con la configuración de fábrica. El driver ya
arma la curva V/F de cada tarjeta con su propio Speedo, y todas tienen el mismo tope de boost, así que una tarjeta
que no está limitada por potencia o temperatura llega a ese tope igual. Se nota bajo un límite de potencia (por
ejemplo una Max-Q de 300 W o una carga de cómputo larga): ahí el chip mejor mantiene un reloj algo más alto con los
mismos watts. Según las ecuaciones de la VBIOS parece ser cerca de 1 MHz por punto de Speedo a un mismo voltaje;
es una estimación nuestra, no una medición. Pasar de 35 % a 60 % son unos 57 puntos de Speedo, o sea unos
50–60 MHz, cerca de 2 % de reloj del núcleo. El trabajo limitado por memoria, como la inferencia de LLM, casi no
cambia; una IDDQ más alta (más fuga) lo compensa en parte bajo un límite de potencia; y para overclock manual un
Speedo más alto suele dar más margen, pero sigue siendo lotería del silicio.

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
La cifra de 1 MHz por punto de arriba es una estimación; este proyecto no ha medido una conversión de MHz por Speedo,
una mejora esperada de rendimiento ni un percentil.

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

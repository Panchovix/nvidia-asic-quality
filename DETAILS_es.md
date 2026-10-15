# NVIDIA ASIC quality: detalles

[English](DETAILS.md) | Español

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
Blackwell SFF y RTX 2000 Ada. En Windows carga `nvapi64.dll`; confirmado que funciona en Windows.
GPUs más antiguas, o drivers con otra estructura, muestran `n/d`.

Ejecuta `python3 -m unittest -v` para probar respuestas seleccionadas del driver; no requiere GPU ni biblioteca
NvAPI. Los datos de prueba no contienen ECIDs.

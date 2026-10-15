# NVIDIA ASIC quality

[English](README.md) | Español

Script de solo lectura que muestra el Speedo, la calidad ASIC y la IDDQ (fuga) de cada GPU NVIDIA.

```
$ sudo python3 nvidia_asic_quality.py --lang es
#  Bus  GPU                                               Speedo  Límites driver    Calidad ASIC  IDDQ NVVDD  IDDQ MSVDD
-  ---  ------------------------------------------------  ------  ----------------  ------------  ----------  ----------
0  03   RTX PRO 6000 Blackwell Max-Q Workstation Edition    2169  2056.9-2284.9           49.2 %       61800       20400
3  06   GeForce RTX 5090                                    2113  2018.9-2284.9           35.4 %       43750       14450
4  07   GeForce RTX 5080                                    2247  2054.8-2287.0           82.8 %       35250       13650
7  13   RTX 2000 Ada Generation                             2008  1901.6-2122.9           48.1 %        9200         n/d
```

### Cómo usarlo

Funciona en Linux y Windows. Necesita Python 3.9+ y el driver de NVIDIA; ningún paquete extra. En Linux, según
los permisos de `/dev/nvidia*`, puede requerir `sudo`.

```
python3 nvidia_asic_quality.py              # todas las GPUs
python3 nvidia_asic_quality.py --device 0   # una GPU, según la columna #
python3 nvidia_asic_quality.py --json       # salida JSON
```

Otras opciones: `--bus 07` (elegir por bus PCI), `--ecid` (ID del chip: fundición, lote, oblea, x/y),
`--diagnostics` (informe para compartir cuando una GPU muestra `n/d`), `--lang en|es`.

- **Speedo**: valor de velocidad grabado en fábrica en los fusibles del chip. Más alto significa silicio más rápido.
- **Calidad ASIC**: dónde cae el Speedo dentro del rango de su modelo, `100 × (Speedo − mín) / (máx − mín)`. Es el
  mismo valor que muestran HWiNFO y mVolt+. Compara solo tarjetas del mismo modelo.
- **IDDQ**: fuga de fábrica por riel (NVVDD núcleo, MSVDD), también de los fusibles.

Más detalle (cuánto importa, metodología, GPUs de datacenter, llamadas de solo lectura): [DETAILS_es.md](DETAILS_es.md).

## Resultados de la comunidad

Las tablas con los resultados compartidos por usuarios están en el [README en inglés](README.md#community-results).

## Licencia

MIT. Ver [LICENSE](LICENSE).

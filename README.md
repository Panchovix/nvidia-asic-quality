# NVIDIA ASIC quality

English | [Español](README_es.md)

Read-only script that shows each NVIDIA GPU's Speedo, ASIC quality and IDDQ (leakage).

```
$ sudo python3 nvidia_asic_quality.py --lang en
#  Bus  GPU                                               Speedo  Driver range   ASIC quality  IDDQ NVVDD  IDDQ MSVDD
-  ---  ------------------------------------------------  ------  -------------  ------------  ----------  ----------
0  03   RTX PRO 6000 Blackwell Max-Q Workstation Edition    2169  2056.9-2284.9        49.2 %       61800       20400
3  06   GeForce RTX 5090                                    2113  2018.9-2284.9        35.4 %       43750       14450
4  07   GeForce RTX 5080                                    2247  2054.8-2287.0        82.8 %       35250       13650
7  13   RTX 2000 Ada Generation                             2008  1901.6-2122.9        48.1 %        9200         n/a
```

### How to use

Needs Python 3.9+ and the NVIDIA driver; no extra packages. Depending on `/dev/nvidia*` permissions it may need `sudo`.

```
python3 nvidia_asic_quality.py              # every GPU
python3 nvidia_asic_quality.py --device 0   # one GPU, by the # column
python3 nvidia_asic_quality.py --json       # JSON output
```

Other options: `--bus 07` (select by PCI bus), `--ecid` (chip ID: foundry, lot, wafer, x/y), `--diagnostics`
(report to share when a GPU shows `n/a`), `--lang en|es`.

- **Speedo**: factory speed value stored in the chip's fuses. Higher means faster silicon.
- **ASIC quality**: where the Speedo sits inside its model's range, `100 × (Speedo − min) / (max − min)`. It is the
  same value HWiNFO and mVolt+ show. Only compare cards of the same model.
- **IDDQ**: factory leakage per rail (NVVDD core, MSVDD), also from the fuses.

More detail (how much it matters, methodology, datacenter GPUs, read-only calls): [DETAILS.md](DETAILS.md).

## Community results

Shared by users; ECIDs are left out. ASIC quality only compares cards of the same model.

### RTX PRO 6000 Blackwell (Workstation, Max-Q and Server, range 2056.9–2284.9)

| User | GPU | Speedo | ASIC quality | IDDQ NVVDD | IDDQ MSVDD |
|---|---|---:|---:|---:|---:|
| Shieldstar | Max-Q Workstation Edition | 2213 | 68.5 % | 64350 | 20750 |
| ufear | Server Edition | 2207 | 65.8 % | 63300 | 20150 |
| ufear | Max-Q Workstation Edition | 2202 | 63.6 % | 56550 | 18350 |
| ufear | Server Edition | 2200 | 62.8 % | 61650 | 20000 |
| Panchovix | Max-Q Workstation Edition | 2197 | 61.5 % | 56450 | 18550 |
| Panchovix | Max-Q Workstation Edition | 2197 | 61.5 % | 60800 | 20000 |
| aimark42 | Workstation Edition | 2195 | 60.6 % | 67900 | 22650 |
| aimark42 | Max-Q Workstation Edition | 2191 | 58.8 % | 55800 | 18500 |
| Shieldstar | Workstation Edition | 2190 | 58.4 % | 59200 | 19150 |
| el8 | Max-Q Workstation Edition | 2181 | 54.4 % | 58650 | 18700 |
| Shieldstar | Workstation Edition | 2179 | 53.6 % | 53900 | 17600 |
| Shieldstar | Max-Q Workstation Edition | 2176 | 52.2 % | 49500 | 16750 |
| ufear | Server Edition | 2174 | 51.4 % | 60350 | 19200 |
| ufear | Max-Q Workstation Edition | 2173 | 50.9 % | 52350 | 17050 |
| Shieldstar | Max-Q Workstation Edition | 2172 | 50.5 % | 58200 | 19000 |
| crowbill | Workstation Edition | 2171 | 50.0 % | 56100 | 17250 |
| ufear | Server Edition | 2170 | 49.6 % | 55200 | 17950 |
| Panchovix | Max-Q Workstation Edition | 2169 | 49.2 % | 61800 | 20400 |
| crowbill | Workstation Edition | 2159 | 44.8 % | 58250 | 19350 |
| ufear | Max-Q Workstation Edition | 2159 | 44.8 % | 50700 | 16900 |
| ufear | Max-Q Workstation Edition | 2157 | 43.9 % | 51200 | 17200 |
| Shieldstar | Workstation Edition | 2156 | 43.5 % | 53200 | 16800 |
| ufear | Server Edition | 2155 | 43.0 % | 53150 | 17550 |
| Shieldstar | Max-Q Workstation Edition | 2153 | 42.1 % | 49900 | 16400 |
| ufear | Server Edition | 2152 | 41.7 % | 50650 | 16850 |
| crowbill | Workstation Edition | 2151 | 41.3 % | 50150 | 16150 |
| Shieldstar | Workstation Edition | 2149 | 40.4 % | 51050 | 16450 |
| ufear | Max-Q Workstation Edition | 2148 | 40.0 % | 61650 | 21000 |
| Shieldstar | Workstation Edition | 2145 | 38.6 % | 46350 | 15450 |
| ufear | Server Edition | 2145 | 38.6 % | 55650 | 17800 |
| Shieldstar | Max-Q Workstation Edition | 2144 | 38.2 % | 51750 | 16550 |
| Shieldstar | Max-Q Workstation Edition | 2143 | 37.8 % | 49450 | 16450 |
| ufear | Max-Q Workstation Edition | 2143 | 37.8 % | 50550 | 16700 |
| Shieldstar | Workstation Edition | 2142 | 37.3 % | 45850 | 14850 |
| aimark42 | Max-Q Workstation Edition | 2138 | 35.6 % | 52000 | 17050 |
| crowbill | Workstation Edition | 2135 | 34.3 % | 45150 | 14300 |
| Shieldstar | Workstation Edition | 2120 | 27.7 % | 53750 | 17350 |
| ufear | Server Edition | 2119 | 27.2 % | 45000 | 14700 |
| Shieldstar | Max-Q Workstation Edition | 2117 | 26.4 % | 44450 | 14600 |
| Shieldstar | Max-Q Workstation Edition | 2116 | 25.9 % | 52300 | 17050 |
| Shieldstar | Workstation Edition | 2109 | 22.8 % | 58450 | 18900 |

Jack Zampolin, two machines with four GPUs each (ASIC quality only, model not stated):
workstation-1 41.3 %, 27.7 %, 47.4 %, 43.5 %; workstation-2 53.6 %, 46.1 %, 31.6 %, 66.7 %.

### Spark (GB10, range 2130.86–2390.00)

| User | GPU | Speedo | ASIC quality | IDDQ NVVDD | IDDQ MSVDD |
|---|---|---:|---:|---:|---:|
| el8 | GB10 | 2310 | 69.1 % | 13294 | 4632 |
| el8 | GB10 | 2270 | 53.7 % | 10678 | 3962 |
| el8 | GB10 | 2259 | 49.4 % | 10326 | 3690 |
| el8 | GB10 | 2201 | 27.1 % | 12120 | 4162 |

### Ada

| User | GPU | Speedo | Driver range | ASIC quality | IDDQ NVVDD | IDDQ MSVDD |
|---|---|---:|---|---:|---:|---:|
| el8 | GeForce RTX 4070 Ti SUPER | 1954 | 1871.07–2109.30 | 34.8 % | 17800 | 97700 |

### Blackwell B300 (GB300, experimental, range 2071.03–2270.77, one row per die)

| User | GPU | Speedo | ASIC quality | IDDQ NVVDD | IDDQ MSVDD |
|---|---|---:|---:|---:|---:|
| el8 | GB300, die 0 | 2170 | 49.5 % | 30400 | 12100 |
| el8 | GB300, die 1 | 2182 | 55.6 % | 32900 | 13200 |

### Other models (Panchovix)

| GPU | Speedo | Model range | ASIC quality | IDDQ NVVDD | IDDQ MSVDD |
|---|---:|---|---:|---:|---:|
| GeForce RTX 5090 | 2113 | 2018.9–2284.9 | 35.4 % | 43750 | 14450 |
| GeForce RTX 5080 | 2247 | 2054.8–2287.0 | 82.8 % | 35250 | 13650 |
| GeForce RTX 5070 Ti | 2176 | 2054.8–2287.0 | 52.2 % | 27450 | 11150 |
| RTX PRO 4000 Blackwell SFF Edition | 2161 | 2054.8–2287.0 | 45.7 % | 21100 | 8450 |
| RTX 2000 Ada Generation | 2008 | 1901.6–2122.9 | 48.1 % | 9200 | n/a |

## License

MIT. See [LICENSE](LICENSE).

#!/usr/bin/env python3
"""Versión secuencial (línea a línea) de la misma pregunta.
Uso: python3 secuencial.py ventas.csv > salida_secuencial.txt
Reutiliza parse_linea del mapper para que ambas versiones validen igual."""
import csv
import sys
import time
from collections import defaultdict
from decimal import Decimal

from mapper import HEADER_PREFIX, parse_linea

CENT = Decimal("0.01")


def main(ruta):
    t0 = time.perf_counter()
    totales, malas = defaultdict(Decimal), 0
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.lower().startswith(HEADER_PREFIX):
                continue
            try:
                clave, monto = parse_linea(next(csv.reader([linea])))
            except (ValueError, csv.Error, StopIteration):
                malas += 1
                continue
            totales[clave] += monto
    for clave in sorted(totales):
        hora, cat = clave.split("|", 1)
        print(f"{hora}\t{cat}\t{totales[clave].quantize(CENT)}")
    sys.stderr.write(f"malformadas={malas} tiempo={time.perf_counter()-t0:.2f}s\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("uso: secuencial.py archivo.csv")
    main(sys.argv[1])

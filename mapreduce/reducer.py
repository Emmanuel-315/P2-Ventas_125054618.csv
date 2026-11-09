#!/usr/bin/env python3
"""Reducer: suma los montos por clave 'HH|categoria' (la entrada llega ordenada).
Salida: hora <TAB> categoria <TAB> ingreso_total"""
import sys
from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")


def emitir(clave, total):
    hora, categoria = clave.split("|", 1)
    print(f"{hora}\t{categoria}\t{total.quantize(CENT)}")


def main():
    actual, total = None, Decimal(0)
    for linea in sys.stdin:
        try:
            clave, valor = linea.rstrip("\n").rsplit("\t", 1)
            monto = Decimal(valor)
        except (ValueError, InvalidOperation):
            sys.stderr.write("reporter:counter:DataMart,ReducerMalformadas,1\n")
            continue
        if clave != actual:
            if actual is not None:
                emitir(actual, total)
            actual, total = clave, Decimal(0)
        total += monto
    if actual is not None:
        emitir(actual, total)


if __name__ == "__main__":
    main()

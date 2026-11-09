#!/usr/bin/env python3
"""Mapper: ingreso por (hora del día, categoría).

Esquema CSV de ventas_125054618.csv (índices desde 0; sobreescribibles con las
variables de entorno COL_FECHA, COL_CATEGORIA, COL_CANTIDAD, COL_PRECIO):
    id,fecha_hora,tienda,categoria,producto,cantidad,precio_unitario,metodo_pago
    1,2025-09-12 02:34:57,T007,Abarrotes,ABA-0013,2,72.36,Transferencia

Salida:  HH|categoria <TAB> cantidad*precio
"""
import csv
import os
import sys
from decimal import Decimal, InvalidOperation

IDX_FECHA = int(os.environ.get("COL_FECHA", 1))
IDX_CATEGORIA = int(os.environ.get("COL_CATEGORIA", 3))
IDX_CANTIDAD = int(os.environ.get("COL_CANTIDAD", 5))
IDX_PRECIO = int(os.environ.get("COL_PRECIO", 6))
HEADER_PREFIX = os.environ.get("HEADER_PREFIX", "id,").lower()


def parse_linea(campos):
    """Devuelve (clave, monto). Lanza ValueError si la fila es inválida."""
    try:
        fecha = campos[IDX_FECHA].strip().replace("T", " ")
        hora = int(fecha.split()[1].split(":")[0])
        categoria = campos[IDX_CATEGORIA].strip().replace("|", "/").replace("\t", " ")
        cantidad = Decimal(campos[IDX_CANTIDAD].strip())
        precio = Decimal(campos[IDX_PRECIO].strip())
    except (IndexError, InvalidOperation) as e:
        raise ValueError(str(e))
    if not 0 <= hora <= 23:
        raise ValueError("hora fuera de rango")
    if not categoria:
        raise ValueError("categoria vacia")
    if cantidad < 0 or precio < 0:
        raise ValueError("valores negativos")
    return f"{hora:02d}|{categoria}", cantidad * precio


def contar_malformada():
    # Contador de Hadoop Streaming (aparece en la salida del job)
    sys.stderr.write("reporter:counter:DataMart,LineasMalformadas,1\n")


def main():
    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        if linea.lstrip("\ufeff").lower().startswith(HEADER_PREFIX):
            continue  # encabezado
        try:
            campos = next(csv.reader([linea]))
            clave, monto = parse_linea(campos)
        except (ValueError, csv.Error, StopIteration):
            contar_malformada()
            continue
        print(f"{clave}\t{monto}")


if __name__ == "__main__":
    main()

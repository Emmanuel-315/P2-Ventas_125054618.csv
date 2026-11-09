#!/usr/bin/env python3
"""Carga la salida del job (part-00000) a la tabla 'resultados' de PostgreSQL.
Se ejecuta en el contenedor api:
  docker compose exec api python /scripts/cargar_resultados.py
Es idempotente: si (hora, categoria) ya existe, actualiza el total."""
import os
import sys
import time

import psycopg2

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/data/output/resultado/part-00000"

DDL = """
CREATE TABLE IF NOT EXISTS resultados (
    id SERIAL PRIMARY KEY,
    hora SMALLINT NOT NULL CHECK (hora BETWEEN 0 AND 23),
    categoria TEXT NOT NULL,
    ingreso_total NUMERIC(16,2) NOT NULL,
    UNIQUE (hora, categoria)
)"""

UPSERT = """
INSERT INTO resultados (hora, categoria, ingreso_total) VALUES (%s, %s, %s)
ON CONFLICT (hora, categoria) DO UPDATE SET ingreso_total = EXCLUDED.ingreso_total"""


def conectar():
    for _ in range(15):
        try:
            return psycopg2.connect(
                host=os.environ.get("DB_HOST", "db"), port=os.environ.get("DB_PORT", 5432),
                dbname=os.environ["POSTGRES_DB"], user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"])
        except psycopg2.OperationalError:
            time.sleep(2)
    sys.exit("No se pudo conectar a la base de datos")


def main():
    filas, malas = [], 0
    with open(RUTA, encoding="utf-8") as f:
        for linea in f:
            if not linea.strip():
                continue
            try:
                hora, categoria, total = linea.rstrip("\n").split("\t")
                filas.append((int(hora), categoria, total))
            except ValueError:
                malas += 1
    conn = conectar()
    with conn, conn.cursor() as cur:
        cur.execute(DDL)
        cur.executemany(UPSERT, filas)
    conn.close()
    print(f"Cargadas {len(filas)} filas (omitidas {malas}) desde {RUTA}")


if __name__ == "__main__":
    main()

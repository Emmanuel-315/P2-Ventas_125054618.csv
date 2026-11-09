"""API CRUD de DataMart: ingreso total por hora (0-23) y categoría."""
import os
import time

import psycopg2
from psycopg2 import errors
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS resultados (
    id SERIAL PRIMARY KEY,
    hora SMALLINT NOT NULL CHECK (hora BETWEEN 0 AND 23),
    categoria TEXT NOT NULL,
    ingreso_total NUMERIC(16,2) NOT NULL,
    UNIQUE (hora, categoria)
)"""
COLS = "id, hora, categoria, ingreso_total::float8 AS ingreso_total"


def conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"), port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ["POSTGRES_DB"], user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"])


def run(sql, params=(), fetch="all"):
    c = conn()
    try:
        with c, c.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            return cur.rowcount
    finally:
        c.close()


def init_db():
    for _ in range(15):
        try:
            run(DDL, fetch=None)
            return
        except psycopg2.OperationalError:
            time.sleep(2)
    raise RuntimeError("DB no disponible")


init_db()


def validar(data, parcial=False):
    """Valida el JSON; devuelve (dict_limpio, error)."""
    if not isinstance(data, dict):
        return None, "JSON inválido"
    out = {}
    try:
        if "hora" in data or not parcial:
            out["hora"] = int(data["hora"])
            if not 0 <= out["hora"] <= 23:
                return None, "hora debe estar entre 0 y 23"
        if "categoria" in data or not parcial:
            out["categoria"] = str(data["categoria"]).strip()
            if not out["categoria"]:
                return None, "categoria vacía"
        if "ingreso_total" in data or not parcial:
            out["ingreso_total"] = round(float(data["ingreso_total"]), 2)
    except (KeyError, TypeError, ValueError):
        return None, "campos requeridos: hora (int), categoria (str), ingreso_total (número)"
    return out, None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/resultados")
def listar():
    return jsonify(run(f"SELECT {COLS} FROM resultados ORDER BY hora, categoria"))


@app.get("/resultados/<clave>")
def por_categoria(clave):
    """clave = categoría. Opcional: ?hora=14 para filtrar también por hora."""
    sql, params = f"SELECT {COLS} FROM resultados WHERE lower(categoria) = lower(%s)", [clave]
    if "hora" in request.args:
        sql += " AND hora = %s"
        params.append(request.args.get("hora", type=int))
    rows = run(sql + " ORDER BY hora", params)
    if not rows:
        return {"error": "sin resultados para esa clave"}, 404
    return jsonify(rows)


@app.post("/resultados")
def crear():
    d, err = validar(request.get_json(silent=True))
    if err:
        return {"error": err}, 400
    try:
        row = run(f"INSERT INTO resultados (hora, categoria, ingreso_total) "
                  f"VALUES (%(hora)s, %(categoria)s, %(ingreso_total)s) RETURNING {COLS}", d, "one")
    except errors.UniqueViolation:
        return {"error": "ya existe ese par hora/categoria"}, 409
    return jsonify(row), 201


@app.put("/resultados/<int:rid>")
def actualizar(rid):
    d, err = validar(request.get_json(silent=True), parcial=True)
    if err or not d:
        return {"error": err or "nada que actualizar"}, 400
    sets = ", ".join(f"{k} = %({k})s" for k in d)
    d["id"] = rid
    try:
        row = run(f"UPDATE resultados SET {sets} WHERE id = %(id)s RETURNING {COLS}", d, "one")
    except errors.UniqueViolation:
        return {"error": "ya existe ese par hora/categoria"}, 409
    return (jsonify(row), 200) if row else ({"error": "no encontrado"}, 404)


@app.delete("/resultados/<int:rid>")
def borrar(rid):
    n = run("DELETE FROM resultados WHERE id = %s", (rid,), None)
    return ("", 204) if n else ({"error": "no encontrado"}, 404)

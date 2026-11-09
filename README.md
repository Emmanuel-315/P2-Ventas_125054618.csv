# Examen Segundo Parcial — Pipeline de datos contenerizado

**Matrícula:** 125054618 · **Pregunta de negocio (dígito 8):** ingreso total por hora del día (0–23) y categoría.

## Arquitectura
`hadoop` (Debian + OpenJDK + Hadoop standalone + sshd) → salida `part-00000` en volumen `hadoop_out` → `cargar_resultados.py` → `db` (PostgreSQL, volumen `pgdata`) → `api` (Flask, puerto 8000). Los tres servicios están en la red `datamart_net`.

## Esquema del CSV
`id,fecha_hora,tienda,categoria,producto,cantidad,precio_unitario,metodo_pago` (ingreso = cantidad × precio_unitario). El mapper lee fecha (col 1), categoría (col 3), cantidad (col 5) y precio (col 6); ajustable con las variables `COL_*` o en `mapreduce/mapper.py`.

## Cómo levantar
```bash
cp .env.example .env            # edita la contraseña
bash scripts/gen_keys.sh        # par de llaves SSH para api -> hadoop
mkdir -p data && cp /ruta/ventas_125054618.csv data/   # el CSV está en .gitignore
docker compose up -d --build
docker compose exec hadoop hadoop version                  # A1
```

## Ejecución del pipeline
```bash
# 1) Job MapReduce (Hadoop Streaming) + tiempo
docker compose exec -u hadoop hadoop bash -c 'time /scripts/run_job.sh /data/input/ventas_125054618.csv'

# 2) Versión secuencial + tiempo + comparación
docker compose exec -u hadoop hadoop bash -c '
  cd /home/hadoop/mapreduce
  time python3 secuencial.py /data/input/ventas_125054618.csv > /tmp/seq.txt
  diff /tmp/seq.txt /data/output/resultado/part-00000 && echo "RESULTADOS IDÉNTICOS"'

# 3) Cargar a la BD (desde el contenedor api)
docker compose exec api python /scripts/cargar_resultados.py

# 4) Probar la API
curl localhost:8000/resultados
curl localhost:8000/resultados/Electronica            # clave = categoría
curl "localhost:8000/resultados/Electronica?hora=14"
curl -X POST localhost:8000/resultados -H 'Content-Type: application/json' \
     -d '{"hora":3,"categoria":"Prueba","ingreso_total":123.45}'
curl -X PUT localhost:8000/resultados/1 -H 'Content-Type: application/json' -d '{"ingreso_total":999.99}'
curl -X DELETE localhost:8000/resultados/1
```
Datos de prueba (si aún no tienes el CSV): `python3 scripts/generar_dataset.py 100000 data/ventas_prueba.csv`.

## SSH (Parte B)
```bash
docker compose exec -u hadoop hadoop ssh localhost hostname      # sin contraseña
docker compose exec api ssh hadoop@hadoop hostname               # api -> hadoop por nombre de servicio
```
Las llaves nunca están en la imagen ni hay contraseñas en los Dockerfile: el usuario `hadoop` tiene la contraseña bloqueada (`usermod -p '*'`), `sshd` solo acepta llaves; la llave de `hadoop` se genera al arrancar y la de `api` se genera en el host con `gen_keys.sh` (`ssh_keys/` está en `.gitignore`).

## Persistencia (Parte D)
```bash
docker compose down && docker compose up -d
curl localhost:8000/resultados      # los datos siguen ahí (volumen pgdata)
```

## Evidencias
Guardar en `evidencias/`: `hadoop version`, salida del job (con contadores), `time` de ambas versiones y el `diff`, `ssh localhost`, `ssh hadoop@hadoop` desde api, `curl` de los endpoints, y el antes/después de `down`/`up`.

## Comparativa de rendimiento (C2)
| Versión | Tiempo real |
|---|---|
| Hadoop Streaming (standalone) | _<completar con tu `time`>_ |
| Secuencial Python | _<completar>_ |

_<Ajusta el párrafo con tus tiempos>_ En este escenario el script secuencial fue más rápido porque Hadoop standalone corre en una sola máquina y un solo proceso (LocalJobRunner): no hay paralelismo real ni HDFS, y aun así paga costos fijos que no compensa: arrancar la JVM, preparar el job, lanzar procesos Python para mapper y reducer, serializar cada registro por pipes (stdin/stdout), y hacer la fase de shuffle/sort escribiendo a disco. El script secuencial hace una sola pasada en memoria sobre un archivo que cabe en una máquina y cuyo resultado final es diminuto (24 horas × categorías), así que casi todo su tiempo es lectura útil.

## Parte E – Teoría

**1. Modos de Hadoop.** *Standalone*: un solo proceso Java, sin daemons, usa el sistema de archivos local; sirve para desarrollo y depuración. *Pseudo-distribuido*: todos los daemons (NameNode, DataNode, ResourceManager, NodeManager) corren en una máquina como procesos separados, simulando un clúster; requiere SSH sin contraseña para los scripts de arranque. *Totalmente distribuido*: los daemons se reparten en varios nodos reales. HDFS se usa en los modos pseudo-distribuido y totalmente distribuido (en standalone se usa el FS local).

**2. Volumen vs `COPY` del dataset.** (a) El dataset pesa cientos de MB: copiarlo infla la imagen, las capas y los tiempos de build/push, y lo duplica en cada imagen. (b) Los datos cambian más que el código: con un volumen se reemplaza el CSV sin reconstruir la imagen y la misma imagen sirve para distintos datasets. (c) Los datos no deberían quedar embebidos ni distribuirse en un registro (privacidad, versionado en git/`.gitignore`), y montarlo `:ro` protege el original de modificaciones accidentales.

**3. `docker compose down` vs `down -v`.** `down` elimina contenedores y redes, pero los volúmenes nombrados se conservan; la base de datos mantiene sus datos al volver a hacer `up`. `down -v` además borra los volúmenes nombrados (`pgdata`, `hadoop_out`), por lo que los datos de la base se pierden definitivamente.

**4. MapReduce vs secuencial en 400 MB.** Un archivo de 400 MB se procesa en segundos en una sola máquina; el overhead fijo de MapReduce (JVM, planificación, shuffle/sort a disco, pipes con Python) puede superar el tiempo útil de cómputo, y en standalone no hay paralelismo real. Conviene cuando los datos exceden la memoria/disco de un nodo (decenas de GB a TB), cuando hay un clúster con HDFS y localidad de datos que permite muchos mappers en paralelo, cuando el cómputo por registro es pesado o se requiere tolerancia a fallos y escalado horizontal.

**5. `CMD` vs `ENTRYPOINT`; `COPY` vs `ADD`.** `ENTRYPOINT` define el ejecutable fijo del contenedor y los argumentos de `docker run` se le agregan; `CMD` define el comando/argumentos por defecto, que se reemplazan fácilmente al ejecutar `docker run imagen otro-comando`. Suelen combinarse (ENTRYPOINT = programa, CMD = argumentos por defecto). `COPY` solo copia archivos/directorios del contexto de build a la imagen; `ADD` hace lo mismo pero además descomprime automáticamente tar locales y acepta URLs, por lo que su comportamiento es menos predecible y se recomienda `COPY` salvo que se necesite esa extracción.

## Notas
- Hadoop 3.3.6 sobre OpenJDK 17 (misma combinación que funcionó en la práctica anterior; Debian bookworm solo ofrece Java 17); `HADOOP_OPTS` abre módulos de Java necesarios. Versión configurable con `--build-arg HADOOP_VERSION=...`.
- `GET /resultados/<clave>` filtra por categoría (sin distinguir mayúsculas); `?hora=` es opcional.
- `PUT`/`DELETE` operan por `id` de la tabla `resultados`; `cargar_resultados.py` es idempotente (upsert por hora+categoría).

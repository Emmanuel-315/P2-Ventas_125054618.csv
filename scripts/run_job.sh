#!/bin/bash
# Ejecutar DENTRO del contenedor hadoop:  /scripts/run_job.sh /data/input/ventas_XXXX.csv
set -euo pipefail
CSV="${1:?uso: run_job.sh /data/input/ventas_<matricula>.csv}"
OUT=/data/output/resultado
cd /home/hadoop/mapreduce
rm -rf "$OUT"   # Hadoop falla si el directorio de salida ya existe
hadoop jar "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -files mapper.py,reducer.py \
  -input "$CSV" \
  -output "$OUT" \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py"
echo "Resultado en $OUT/part-00000"

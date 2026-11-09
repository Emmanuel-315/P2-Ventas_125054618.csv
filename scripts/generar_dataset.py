#!/usr/bin/env python3
"""Genera un CSV de prueba (con algunas líneas malformadas a propósito).
Uso: python3 generar_dataset.py 100000 data/ventas_prueba.csv"""
import random, sys
n, out = int(sys.argv[1]), sys.argv[2]
cats = ["Electronica", "Hogar", "Ropa", "Alimentos", "Juguetes", "Deportes"]
random.seed(42)
with open(out, "w") as f:
    f.write("id,fecha_hora,tienda,categoria,producto,cantidad,precio_unitario,metodo_pago\n")
    for i in range(1, n + 1):
        if i % 997 == 0:
            f.write("linea,rota\n"); continue
        if i % 1499 == 0:
            f.write(f"{i},2024-03-15 99:99:99,T01,Ropa,P,x,y,Efectivo\n"); continue
        h, m, s = random.randint(0, 23), random.randint(0, 59), random.randint(0, 59)
        f.write(f"{i},2024-03-{random.randint(1,28):02d} {h:02d}:{m:02d}:{s:02d},"
                f"T{random.randint(1,20):03d},{random.choice(cats)},P{random.randint(1,500)},"
                f"{random.randint(1,5)},{random.randint(5,2000)}.{random.randint(0,99):02d},Efectivo\n")

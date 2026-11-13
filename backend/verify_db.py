"""
Script de Verificación en Base de Datos MySQL
Permite comprobar en consola la data limpia y los 2 campos calculados (monto_total e igv)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

# Asegurar codificación UTF-8 en consolas de Windows para tildes y caracteres especiales
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "MySQL")
DB_NAME = os.getenv("DB_NAME", "tienda_db")


def verificar():
    print("=" * 70)
    print("   VERIFICACIÓN DE BASE DE DATOS (MySQL - TIENDA_DB)")
    print("=" * 70)
    
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor(dictionary=True)

    # 1. Conteo total
    cursor.execute("SELECT COUNT(*) AS total FROM ventas;")
    total = cursor.fetchone()["total"]
    print(f"-> Total de registros almacenados en la tabla 'ventas': {total}\n")

    # 2. Muestra de registros con campos calculados
    print("-> Muestra de los primeros 5 registros limpios con campos calculados:")
    cursor.execute("""
        SELECT id_transaccion, categoria, producto, cantidad, precio_unitario,
               fecha_venta, monto_total, igv
        FROM ventas
        LIMIT 5;
    """)
    filas = cursor.fetchall()
    header = f"{'ID':<10} | {'CATEGORIA':<12} | {'PRODUCTO':<22} | {'CANT':<5} | {'PRECIO':<10} | {'FECHA':<11} | {'MONTO TOTAL':<12} | {'IGV':<10}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for f in filas:
        print(f"{f['id_transaccion']:<10} | {f['categoria']:<12} | {f['producto'][:22]:<22} | {f['cantidad']:<5} | {float(f['precio_unitario']):<10.2f} | {str(f['fecha_venta']):<11} | {float(f['monto_total']):<12.2f} | {float(f['igv']):<10.2f}")
    print("-" * len(header))

    # 3. Resumen agrupado por categoría
    print("\n-> Resumen agrupado por categoría (monto_total vs igv):")
    cursor.execute("""
        SELECT categoria, 
               COUNT(*) AS total_ventas,
               SUM(cantidad) AS unidades_vendidas,
               SUM(monto_total) AS total_ingresos,
               SUM(igv) AS total_igv
        FROM ventas
        GROUP BY categoria
        ORDER BY total_ingresos DESC;
    """)
    resumen = cursor.fetchall()
    res_header = f"{'CATEGORIA':<15} | {'VENTAS':<8} | {'UNIDADES':<10} | {'TOTAL INGRESOS (S/)':<20} | {'TOTAL IGV (S/)':<15}"
    print("-" * len(res_header))
    print(res_header)
    print("-" * len(res_header))
    for r in resumen:
        print(f"{r['categoria']:<15} | {r['total_ventas']:<8} | {r['unidades_vendidas']:<10} | {float(r['total_ingresos']):<20.2f} | {float(r['total_igv']):<15.2f}")
    print("-" * len(res_header))

    cursor.close()
    conn.close()
    print("\n[OK] Verificación completada con éxito.")


if __name__ == "__main__":
    verificar()


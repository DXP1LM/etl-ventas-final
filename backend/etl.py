"""
Pipeline ETL (Extracción, Limpieza, Transformación y Carga) con Pandas y MySQL
Caso de Estudio: Opción B - Ventas de Tienda por Departamentos
"""
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import mysql.connector

# Asegurar codificación UTF-8 en consolas de Windows para tildes y caracteres especiales
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from logic import (
    normalizar_categoria,
    normalizar_producto,
    limpiar_precio
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "MySQL")
DB_NAME = os.getenv("DB_NAME", "tienda_db")

CSV_CANDIDATE_PATHS = [
    BASE_DIR / "ventas_departamentos_sucio_v2.csv",
    BASE_DIR.parent / "ventas_departamentos_sucio_v2.csv",
    Path("ventas_departamentos_sucio_v2.csv")
]


def encontrar_csv() -> Path:
    for path in CSV_CANDIDATE_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError("No se encontró el archivo ventas_departamentos_sucio_v2.csv")


def obtener_conexion(crear_bd_si_no_existe: bool = True):
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    if crear_bd_si_no_existe:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.database = DB_NAME
    return conn


def asegurar_tabla_ventas(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id_transaccion VARCHAR(15) PRIMARY KEY,
        categoria VARCHAR(50) NOT NULL,
        producto VARCHAR(100) NOT NULL,
        cantidad INT NOT NULL,
        precio_unitario DECIMAL(10,2) NOT NULL,
        fecha_venta DATE NOT NULL,
        stock_actual INT NOT NULL,
        monto_total DECIMAL(10,2) NOT NULL,
        igv DECIMAL(10,2) NOT NULL
    );
    """)
    conn.commit()


def vaciar_tabla_ventas(conn):
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE ventas;")
    conn.commit()
    print("-> Tabla 'ventas' vaciada con éxito (0 registros).")


def procesar_dataframe(csv_path: Path):
    """
    Realiza la extracción, limpieza y transformación utilizando Pandas DataFrames.
    """
    # 1. Extracción
    df_raw = pd.read_csv(csv_path, dtype=str)
    total_leidos = len(df_raw)

    # 2. Descarte de registros duplicados por clave primaria (id_transaccion)
    df = df_raw.drop_duplicates(subset=['id_transaccion'], keep='first').copy()
    duplicados_descartados = total_leidos - len(df)

    # Limpieza de espacios en blanco en todas las columnas
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # Reemplazo de cadenas vacías por NaN
    df = df.replace('', np.nan)
    despues_duplicados = len(df)

    # 3. Descarte de filas con valores nulos o vacíos
    cols_requeridas = ['id_transaccion', 'categoria', 'producto', 'cantidad', 'precio_unitario', 'fecha_venta', 'stock_actual']
    df = df.dropna(subset=cols_requeridas)
    nulos_descartados = despues_duplicados - len(df)

    despues_nulos = len(df)

    # 4. Filtrado de valores fuera de rango o corruptos
    # - Fechas inválidas (ej. 'FECHA_INVALIDA', '2026/99/99')
    df['fecha_valida'] = pd.to_datetime(df['fecha_venta'], format='%Y-%m-%d', errors='coerce')
    df = df[df['fecha_valida'].notna()].copy()

    # - Cantidades (debe ser numérico entero > 0)
    df['cantidad_num'] = pd.to_numeric(df['cantidad'], errors='coerce')
    df = df[(df['cantidad_num'].notna()) & (df['cantidad_num'] > 0)].copy()
    df['cantidad'] = df['cantidad_num'].astype(int)

    # - Stock (debe ser numérico entero >= 0)
    df['stock_num'] = pd.to_numeric(df['stock_actual'], errors='coerce')
    df = df[(df['stock_num'].notna()) & (df['stock_num'] >= 0)].copy()
    df['stock_actual'] = df['stock_num'].astype(int)

    # - Precio unitario (limpieza de símbolos de moneda 'S/' y filtrado > 0)
    def parse_precio(p):
        try:
            return limpiar_precio(p)
        except Exception:
            return np.nan

    df['precio_num'] = df['precio_unitario'].apply(parse_precio)
    df = df[df['precio_num'].notna() & (df['precio_num'] > 0)].copy()
    df['precio_unitario'] = df['precio_num'].round(2)

    invalidos_descartados = despues_nulos - len(df)

    # 5. Estandarización de textos (mayúsculas/minúsculas y categorías oficiales)
    df['categoria'] = df['categoria'].apply(normalizar_categoria)
    df['producto'] = df['producto'].apply(normalizar_producto)

    # 6. Transformación con Pandas: Creación de 2 Campos Calculados obligatorios
    df['monto_total'] = (df['cantidad'] * df['precio_unitario']).round(2)
    df['igv'] = (df['monto_total'] * 0.18).round(2)

    metricas = {
        "total_leidos": total_leidos,
        "duplicados": duplicados_descartados,
        "nulos": nulos_descartados,
        "invalidos": invalidos_descartados,
        "total_limpios": len(df)
    }

    # Seleccionar columnas finales en el orden de la tabla MySQL
    columnas_ordenadas = [
        'id_transaccion', 'categoria', 'producto', 'cantidad', 'precio_unitario',
        'fecha_venta', 'stock_actual', 'monto_total', 'igv'
    ]
    df_final = df[columnas_ordenadas].copy()
    return df_final, metricas


def ejecutar_etl(vaciar_antes: bool = True):
    print("=" * 65)
    print("   INICIANDO PROCESO ETL CON PANDAS (VENTAS DE TIENDA)")
    print("=" * 65)

    csv_path = encontrar_csv()
    print(f"[1] FASE DE EXTRACCIÓN: Leyendo '{csv_path.name}' con Pandas...")

    conn = obtener_conexion()
    asegurar_tabla_ventas(conn)

    if vaciar_antes:
        vaciar_tabla_ventas(conn)

    print("[2] FASE DE LIMPIEZA Y TRANSFORMACIÓN: Procesando DataFrame...")
    df_limpio, metricas = procesar_dataframe(csv_path)

    print("\n   RESUMEN DE CALIDAD DE DATOS (PANDAS):")
    print(f"   - Registros brutos leídos      : {metricas['total_leidos']}")
    print(f"   - Duplicados eliminados        : {metricas['duplicados']}")
    print(f"   - Filas con nulos descartadas  : {metricas['nulos']}")
    print(f"   - Filas con valores inválidos  : {metricas['invalidos']}")
    print(f"   - Registros limpios y válidos  : {metricas['total_limpios']}")

    print("\n[3] FASE DE CARGA (SQL): Insertando DataFrame en tabla 'ventas' (MySQL)...")
    cursor = conn.cursor()
    query_insert = """
    INSERT INTO ventas (
        id_transaccion, categoria, producto, cantidad, precio_unitario,
        fecha_venta, stock_actual, monto_total, igv
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    # Convertir DataFrame a lista de tuplas para inserción masiva de alto rendimiento
    registros = [tuple(row) for row in df_limpio.itertuples(index=False, name=None)]
    cursor.executemany(query_insert, registros)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM ventas;")
    total_en_bd = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    print(f"   - Inserción completada con éxito.")
    print(f"   - Total confirmado en base de datos: {total_en_bd} registros.")
    print("=" * 65)
    print("   PROCESO ETL CON PANDAS FINALIZADO SATISFACTORIAMENTE")
    print("=" * 65)
    return total_en_bd


if __name__ == "__main__":
    ejecutar_etl(vaciar_antes=True)

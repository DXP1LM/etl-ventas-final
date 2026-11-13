"""
Microservicio API REST en Python (Flask)
Caso de Estudio: Ventas de Tienda por Departamentos
Conexión exclusiva a la base de datos MySQL (tienda_db)
"""
import os
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "MySQL")
DB_NAME = os.getenv("DB_NAME", "tienda_db")
API_PORT = int(os.getenv("API_PORT", "5000"))

app = Flask(__name__)
# Evitar que caracteres con tildes (como Tecnología) se escapen como \u00ed
app.json.ensure_ascii = False
# Habilitar CORS para permitir consumo desde el Frontend (Angular en http://localhost:4200)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def serialize_row(row: dict) -> dict:
    """Convierte tipos Decimal y Date a formato nativo JSON."""
    result = {}
    for key, val in row.items():
        if isinstance(val, Decimal):
            result[key] = float(val)
        elif isinstance(val, (date, datetime)):
            result[key] = val.isoformat()
        else:
            result[key] = val
    return result


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "proyecto": "Arquitectura de Datos End-to-End",
        "servicio": "Microservicio REST de Ventas por Departamento",
        "version": "1.0.0",
        "endpoints": [
            "/api/health",
            "/api/ventas",
            "/api/dashboard/kpis",
            "/api/dashboard/totales-por-categoria",
            "/api/dashboard/unidades-por-categoria"
        ]
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """Verifica estado de salud del API y conexión con MySQL."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ventas;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({
            "status": "online",
            "database": "connected",
            "db_name": DB_NAME,
            "total_registros_ventas": count,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "database": "error",
            "error": str(e)
        }), 500


@app.route("/api/ventas", methods=["GET"])
def listar_ventas():
    """
    Retorna la lista de transacciones de ventas almacenadas en la BD limpia.
    Permite filtrar opcionalmente por categoría o búsqueda de texto.
    """
    categoria = request.args.get("categoria", "").strip()
    busqueda = request.args.get("q", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT id_transaccion, categoria, producto, cantidad, precio_unitario,
               fecha_venta, stock_actual, monto_total, igv
        FROM ventas
        WHERE 1=1
    """
    params = []

    if categoria:
        query += " AND LOWER(categoria) = LOWER(%s)"
        params.append(categoria)

    if busqueda:
        query += " AND (id_transaccion LIKE %s OR producto LIKE %s OR categoria LIKE %s)"
        like_term = f"%{busqueda}%"
        params.extend([like_term, like_term, like_term])

    query += " ORDER BY fecha_venta DESC, id_transaccion ASC;"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    data = [serialize_row(r) for r in rows]
    return jsonify({
        "total": len(data),
        "data": data
    }), 200


@app.route("/api/dashboard/kpis", methods=["GET"])
def dashboard_kpis():
    """Retorna indicadores clave de rendimiento (KPIs) para las tarjetas del Dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            COUNT(*) AS total_transacciones,
            COALESCE(SUM(cantidad), 0) AS total_unidades,
            COALESCE(SUM(monto_total), 0) AS total_ingresos,
            COALESCE(SUM(igv), 0) AS total_igv,
            COUNT(DISTINCT categoria) AS total_categorias
        FROM ventas;
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    res = {
        "total_transacciones": int(row["total_transacciones"] or 0),
        "total_unidades": int(row["total_unidades"] or 0),
        "total_ingresos": round(float(row["total_ingresos"] or 0), 2),
        "total_igv": round(float(row["total_igv"] or 0), 2),
        "total_categorias": int(row["total_categorias"] or 0)
    }
    return jsonify(res), 200


@app.route("/api/dashboard/totales-por-categoria", methods=["GET"])
def dashboard_totales_por_categoria():
    """
    Datos para Gráfico de Barras Verticales:
    Comparativa de ingresos por categoría mostrando los dos campos calculados (monto_total vs igv).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            categoria,
            ROUND(SUM(monto_total), 2) AS monto_total,
            ROUND(SUM(igv), 2) AS igv
        FROM ventas
        GROUP BY categoria
        ORDER BY monto_total DESC;
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    categorias = []
    montos = []
    igvs = []

    for r in rows:
        categorias.append(r["categoria"])
        montos.append(float(r["monto_total"]))
        igvs.append(float(r["igv"]))

    return jsonify({
        "categorias": categorias,
        "monto_total": montos,
        "igv": igvs,
        "detalles": [serialize_row(r) for r in rows]
    }), 200


@app.route("/api/dashboard/unidades-por-categoria", methods=["GET"])
def dashboard_unidades_por_categoria():
    """
    Datos para Gráfico de Torta / Dona:
    Participación porcentual de unidades vendidas por departamento
    (Tecnología, Electro, Calzado, Hogar, Ropa).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            categoria,
            SUM(cantidad) AS unidades
        FROM ventas
        GROUP BY categoria
        ORDER BY unidades DESC;
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    total_unidades = int(sum(int(r["unidades"]) for r in rows)) if rows else 1

    categorias = []
    unidades = []
    porcentajes = []

    for r in rows:
        categorias.append(r["categoria"])
        cant = int(r["unidades"])
        unidades.append(cant)
        pct = round((cant / total_unidades) * 100, 2)
        porcentajes.append(float(pct))

    return jsonify({
        "categorias": categorias,
        "unidades": unidades,
        "porcentajes": porcentajes,
        "total_unidades": int(total_unidades)
    }), 200


if __name__ == "__main__":
    print(f"-> Servidor REST iniciado en http://localhost:{API_PORT}")
    app.run(host="0.0.0.0", port=API_PORT, debug=False)

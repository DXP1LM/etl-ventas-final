"""
Pruebas Unitarias para Lógica de Negocio y ETL de Ventas
Validación de casos normales, casos borde y excepciones
"""
import unittest
import sys
from pathlib import Path

# Agregar directorio padre al PATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logic import (
    calcular_monto_total,
    calcular_igv,
    limpiar_precio,
    normalizar_categoria,
    normalizar_producto,
    validar_registro
)


class TestCalculosVentas(unittest.TestCase):
    """Pruebas unitarias para los 2 campos calculados obligatorios y funciones auxiliares."""

    # ---------------------------------------------------------
    # 1. Pruebas para cálculo de monto_total
    # ---------------------------------------------------------
    def test_calcular_monto_total_caso_normal(self):
        """Caso normal: producto de cantidad estándar y precio unitario."""
        cantidad = 5
        precio_unitario = 120.50
        resultado = calcular_monto_total(cantidad, precio_unitario)
        self.assertEqual(resultado, 602.50)

    def test_calcular_monto_total_caso_borde_unidad_minima(self):
        """Caso borde: cantidad mínima válida (1) y precio con decimales periódicos."""
        cantidad = 1
        precio_unitario = 99.999
        resultado = calcular_monto_total(cantidad, precio_unitario)
        self.assertEqual(resultado, 100.00)

    def test_calcular_monto_total_caso_borde_precio_cero(self):
        """Caso borde: precio unitario 0.0 (promoción total)."""
        cantidad = 10
        precio_unitario = 0.0
        resultado = calcular_monto_total(cantidad, precio_unitario)
        self.assertEqual(resultado, 0.0)

    def test_calcular_monto_total_cantidad_invalida_lanza_error(self):
        """Caso de error: cantidad menor o igual a cero lanza ValueError."""
        with self.assertRaises(ValueError):
            calcular_monto_total(0, 50.0)
        with self.assertRaises(ValueError):
            calcular_monto_total(-3, 50.0)

    def test_calcular_monto_total_precio_negativo_lanza_error(self):
        """Caso de error: precio negativo lanza ValueError."""
        with self.assertRaises(ValueError):
            calcular_monto_total(2, -15.0)

    def test_calcular_monto_total_tipo_no_numerico_lanza_error(self):
        """Caso de error: tipos no numéricos lanzan TypeError."""
        with self.assertRaises(TypeError):
            calcular_monto_total("3", 50.0) # type: ignore
        with self.assertRaises(TypeError):
            calcular_monto_total(3, "50.0") # type: ignore

    # ---------------------------------------------------------
    # 2. Pruebas para cálculo de igv (18%)
    # ---------------------------------------------------------
    def test_calcular_igv_caso_normal(self):
        """Caso normal: cálculo de 18% sobre monto positivo."""
        monto_total = 1000.00
        resultado = calcular_igv(monto_total)
        self.assertEqual(resultado, 180.00)

    def test_calcular_igv_caso_borde_monto_cero(self):
        """Caso borde: monto total de 0.0 debe producir IGV 0.0."""
        resultado = calcular_igv(0.0)
        self.assertEqual(resultado, 0.0)

    def test_calcular_igv_caso_borde_redondeo_centimos(self):
        """Caso borde: monto con fracciones que requieren redondeo preciso."""
        monto_total = 129.20
        # 129.20 * 0.18 = 23.256 -> 23.26
        resultado = calcular_igv(monto_total)
        self.assertEqual(resultado, 23.26)

    def test_calcular_igv_monto_negativo_lanza_error(self):
        """Caso de error: monto negativo lanza ValueError."""
        with self.assertRaises(ValueError):
            calcular_igv(-100.0)

    def test_calcular_igv_tasa_invalida_lanza_error(self):
        """Caso de error: tasa fuera del rango [0, 1] lanza ValueError."""
        with self.assertRaises(ValueError):
            calcular_igv(100.0, tasa=1.5)

    def test_calcular_igv_tipo_invalido_lanza_error(self):
        """Caso de error: tipo no numérico lanza TypeError."""
        with self.assertRaises(TypeError):
            calcular_igv("100.0") # type: ignore

    # ---------------------------------------------------------
    # 3. Pruebas para limpieza de precios y normalizaciones
    # ---------------------------------------------------------
    def test_limpiar_precio_con_simbolos_y_espacios(self):
        """Limpia cadenas como 'S/ 1826.7' o '$ 250.00'."""
        self.assertEqual(limpiar_precio("S/ 1826.7"), 1826.70)
        self.assertEqual(limpiar_precio("S/. 500.5"), 500.50)
        self.assertEqual(limpiar_precio(" $ 99.90 "), 99.90)

    def test_limpiar_precio_invalido(self):
        """Verifica excepciones con precios nulos, vacíos o menores o iguales a 0."""
        with self.assertRaises(ValueError):
            limpiar_precio(None) # type: ignore
        with self.assertRaises(ValueError):
            limpiar_precio("   ")
        with self.assertRaises(ValueError):
            limpiar_precio("0.0")

    def test_normalizar_categoria(self):
        """Valida que categorías en minúsculas o con espacios se estandaricen."""
        self.assertEqual(normalizar_categoria("  tecnología "), "Tecnología")
        self.assertEqual(normalizar_categoria("calzado"), "Calzado")
        self.assertEqual(normalizar_categoria("ELECTRO"), "Electro")
        self.assertEqual(normalizar_categoria("ropa"), "Ropa")
        self.assertEqual(normalizar_categoria("hogar"), "Hogar")
        self.assertEqual(normalizar_categoria(""), "")

    def test_normalizar_producto(self):
        """Valida estandarización de nombres de productos."""
        self.assertEqual(normalizar_producto("  ZAPATILLAS DEPORTIVAS  "), "Zapatillas Deportivas")
        self.assertEqual(normalizar_producto("laptop core i5"), "Laptop Core i5")
        self.assertEqual(normalizar_producto("laptop core i7"), "Laptop Core i7")
        self.assertEqual(normalizar_producto("TABLET 10\"\""), "Tablet 10\"")
        self.assertEqual(normalizar_producto(""), "")

    def test_validar_registro_errores_no_numericos(self):
        """Valida rechazo de valores no numéricos en cantidad, stock o precio."""
        fila_cant = {
            "id_transaccion": "TRX-0010", "categoria": "Ropa", "producto": "Polo",
            "cantidad": "abc", "precio_unitario": "50.0", "fecha_venta": "2026-05-10", "stock_actual": "10"
        }
        valido, motivo = validar_registro(fila_cant)
        self.assertFalse(valido)
        self.assertIn("Cantidad no numérica", motivo)

        fila_stock = {
            "id_transaccion": "TRX-0011", "categoria": "Ropa", "producto": "Polo",
            "cantidad": "2", "precio_unitario": "50.0", "fecha_venta": "2026-05-10", "stock_actual": "xyz"
        }
        valido, motivo = validar_registro(fila_stock)
        self.assertFalse(valido)
        self.assertIn("Stock no numérico", motivo)

        fila_precio = {
            "id_transaccion": "TRX-0012", "categoria": "Ropa", "producto": "Polo",
            "cantidad": "2", "precio_unitario": "S/ NINGUNO", "fecha_venta": "2026-05-10", "stock_actual": "10"
        }
        valido, motivo = validar_registro(fila_precio)
        self.assertFalse(valido)
        self.assertIn("Precio inválido", motivo)

        fila_precio_cero = {
            "id_transaccion": "TRX-0013", "categoria": "Ropa", "producto": "Polo",
            "cantidad": "2", "precio_unitario": "0.0", "fecha_venta": "2026-05-10", "stock_actual": "10"
        }
        valido, motivo = validar_registro(fila_precio_cero)
        self.assertFalse(valido)
        self.assertIn("Precio", motivo)

    # ---------------------------------------------------------
    # 4. Pruebas para validación de filas completas del CSV
    # ---------------------------------------------------------
    def test_validar_registro_correcto(self):
        """Fila completa y válida pasa la validación."""
        fila = {
            "id_transaccion": "TRX-0001",
            "categoria": "Electro",
            "producto": "Televisor 50\"",
            "cantidad": "3",
            "precio_unitario": "S/ 1200.00",
            "fecha_venta": "2026-05-10",
            "stock_actual": "25"
        }
        valido, motivo = validar_registro(fila)
        self.assertTrue(valido)
        self.assertEqual(motivo, "OK")

    def test_validar_registro_descarte_por_campo_vacio(self):
        """Fila con campo vacío es descartada."""
        fila = {
            "id_transaccion": "TRX-0002",
            "categoria": "",
            "producto": "Microondas",
            "cantidad": "2",
            "precio_unitario": "900.0",
            "fecha_venta": "2026-05-10",
            "stock_actual": "10"
        }
        valido, motivo = validar_registro(fila)
        self.assertFalse(valido)
        self.assertIn("nulo o vacío", motivo)

    def test_validar_registro_descarte_por_cantidad_invalida(self):
        """Fila con cantidad <= 0 es descartada."""
        fila = {
            "id_transaccion": "TRX-0003",
            "categoria": "Calzado",
            "producto": "Botines",
            "cantidad": "0",
            "precio_unitario": "200.0",
            "fecha_venta": "2026-05-10",
            "stock_actual": "10"
        }
        valido, motivo = validar_registro(fila)
        self.assertFalse(valido)
        self.assertIn("Cantidad", motivo)

    def test_validar_registro_descarte_por_stock_negativo(self):
        """Fila con stock < 0 es descartada."""
        fila = {
            "id_transaccion": "TRX-0004",
            "categoria": "Hogar",
            "producto": "Cortina",
            "cantidad": "1",
            "precio_unitario": "150.0",
            "fecha_venta": "2026-05-10",
            "stock_actual": "-5"
        }
        valido, motivo = validar_registro(fila)
        self.assertFalse(valido)
        self.assertIn("Stock negativo", motivo)

    def test_validar_registro_descarte_por_fecha_invalida(self):
        """Fila con fecha inválida es descartada."""
        fila = {
            "id_transaccion": "TRX-0005",
            "categoria": "Ropa",
            "producto": "Jeans",
            "cantidad": "2",
            "precio_unitario": "120.0",
            "fecha_venta": "FECHA_INVALIDA",
            "stock_actual": "20"
        }
        valido, motivo = validar_registro(fila)
        self.assertFalse(valido)
        self.assertIn("fecha inválido", motivo)


if __name__ == "__main__":
    unittest.main()

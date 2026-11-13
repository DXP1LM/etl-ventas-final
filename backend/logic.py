"""
Módulo de Lógica de Negocio y Transformación de Datos para Ventas
"""
import re
from datetime import datetime

VALID_CATEGORIES = {
    'tecnología': 'Tecnología',
    'tecnologia': 'Tecnología',
    'electro': 'Electro',
    'ropa': 'Ropa',
    'hogar': 'Hogar',
    'calzado': 'Calzado'
}


def calcular_monto_total(cantidad: int, precio_unitario: float) -> float:
    """
    Calcula el monto total multiplicando cantidad por precio unitario.
    Valida que la cantidad sea mayor a 0 y el precio no sea negativo.
    """
    if not isinstance(cantidad, (int, float)) or not isinstance(precio_unitario, (int, float)):
        raise TypeError("La cantidad y el precio unitario deben ser valores numéricos")
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a 0")
    if precio_unitario < 0:
        raise ValueError("El precio unitario no puede ser negativo")
    
    return round(float(cantidad) * float(precio_unitario), 2)


def calcular_igv(monto_total: float, tasa: float = 0.18) -> float:
    """
    Calcula el IGV (18%) a partir del monto total.
    Valida que el monto total no sea negativo.
    """
    if not isinstance(monto_total, (int, float)):
        raise TypeError("El monto total debe ser un valor numérico")
    if monto_total < 0:
        raise ValueError("El monto total no puede ser negativo")
    if tasa < 0 or tasa > 1:
        raise ValueError("La tasa impositiva debe estar entre 0 y 1")
    
    return round(float(monto_total) * float(tasa), 2)


def limpiar_precio(precio_raw: str) -> float:
    """
    Limpia símbolos de moneda ('S/', '$', etc.) y espacios de campos numéricos.
    """
    if precio_raw is None:
        raise ValueError("El precio no puede ser nulo")
    
    texto = str(precio_raw).strip()
    texto = texto.replace("S/.", "").replace("S/", "").replace("$", "").replace(" ", "")
    
    if not texto:
        raise ValueError("El precio no contiene un valor numérico válido")
    
    valor = float(texto)
    if valor <= 0:
        raise ValueError("El precio unitario debe ser mayor a 0")
    
    return round(valor, 2)


def normalizar_categoria(cat: str) -> str:
    """
    Elimina espacios en blanco y normaliza el nombre del departamento/categoría.
    """
    if not cat:
        return ""
    cat_limpia = cat.strip().lower()
    return VALID_CATEGORIES.get(cat_limpia, cat.strip().title())


def normalizar_producto(prod: str) -> str:
    """
    Estandariza los nombres de productos (espacios excesivos, formato título).
    """
    if not prod:
        return ""
    # Quitar comillas dobles excesivas y espacios sobrantes
    texto = re.sub(r'\s+', ' ', prod.strip())
    # Mantener nomenclatura estándar
    texto = texto.replace('""', '"')
    partes = texto.split(" ")
    partes_formateadas = []
    for p in partes:
        p_clean = p.strip()
        if p_clean.lower() == "core":
            partes_formateadas.append("Core")
        elif p_clean.lower() == "i5":
            partes_formateadas.append("i5")
        elif p_clean.lower() == "i7":
            partes_formateadas.append("i7")
        else:
            partes_formateadas.append(p_clean.capitalize())
    return " ".join(partes_formateadas)


def validar_registro(registro: dict) -> tuple[bool, str]:
    """
    Valida un registro crudo del CSV contra todas las reglas de calidad de datos.
    Retorna (es_valido, motivo_descarte).
    """
    campos_requeridos = ['id_transaccion', 'categoria', 'producto', 'cantidad', 'precio_unitario', 'fecha_venta', 'stock_actual']
    
    for campo in campos_requeridos:
        valor = registro.get(campo)
        if valor is None or str(valor).strip() == "":
            return False, f"Campo nulo o vacío: {campo}"

    # Validar fecha
    fecha = str(registro['fecha_venta']).strip()
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        return False, f"Formato de fecha inválido: {fecha}"

    # Validar cantidad
    try:
        cantidad = int(str(registro['cantidad']).strip())
        if cantidad <= 0:
            return False, f"Cantidad no es mayor a 0: {cantidad}"
    except ValueError:
        return False, f"Cantidad no numérica: {registro.get('cantidad')}"

    # Validar stock
    try:
        stock = int(str(registro['stock_actual']).strip())
        if stock < 0:
            return False, f"Stock negativo ilógico: {stock}"
    except ValueError:
        return False, f"Stock no numérico: {registro.get('stock_actual')}"

    # Validar precio
    try:
        precio = limpiar_precio(registro['precio_unitario'])
    except (ValueError, TypeError) as err:
        return False, f"Precio inválido: {err}"

    return True, "OK"

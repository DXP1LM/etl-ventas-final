CREATE DATABASE IF NOT EXISTS tienda_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tienda_db;

DROP TABLE IF EXISTS ventas;

CREATE TABLE ventas (
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


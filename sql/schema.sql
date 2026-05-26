-- ============================================================
--  SIF-Bancario — Esquema MySQL completo
--  Ejecutar solo si se prefiere crear las tablas manualmente
--  (SQLAlchemy las crea automáticamente al correr el ETL)
-- ============================================================

CREATE DATABASE IF NOT EXISTS sif_bancario
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sif_bancario;

-- ── Captaciones ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS captaciones (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    fecha            DATE,
    entidad          VARCHAR(100),
    tipo_entidad     VARCHAR(10),
    localidad        VARCHAR(100),
    moneda           VARCHAR(10),
    sector           VARCHAR(100),
    tipo_depositante VARCHAR(100),
    monto            DOUBLE,
    numero_cuentas   INT,
    fuente_endpoint  VARCHAR(80),
    cargado_en       DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_cap_fecha_entidad (fecha, entidad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Cartera de Créditos ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS cartera_creditos (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    fecha                DATE,
    entidad              VARCHAR(100),
    tipo_entidad         VARCHAR(10),
    clasificacion_riesgo VARCHAR(50),
    genero               VARCHAR(20),
    localidad            VARCHAR(100),
    moneda               VARCHAR(10),
    sector_economico     VARCHAR(100),
    tipo_cartera         VARCHAR(80),
    saldo                DOUBLE,
    numero_deudores      INT,
    fuente_endpoint      VARCHAR(80),
    cargado_en           DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_cart_fecha_entidad (fecha, entidad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Estados Financieros ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS estados_financieros (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    fecha        DATE,
    entidad      VARCHAR(100),
    tipo_entidad VARCHAR(10),
    cuenta       VARCHAR(20),
    descripcion  VARCHAR(200),
    monto        DOUBLE,
    tipo_estado  VARCHAR(20),
    cargado_en   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_ef_fecha_entidad (fecha, entidad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Indicadores ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS indicadores (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    fecha           DATE,
    entidad         VARCHAR(100),
    tipo_entidad    VARCHAR(10),
    tipo_indicador  VARCHAR(80),
    nombre          VARCHAR(200),
    valor           DOUBLE,
    fuente_endpoint VARCHAR(80),
    cargado_en      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_ind_fecha_tipo (fecha, tipo_indicador)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Solvencia ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS solvencia (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    fecha        DATE,
    entidad      VARCHAR(100),
    tipo_entidad VARCHAR(10),
    componente   VARCHAR(100),
    valor        DOUBLE,
    cargado_en   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_sol_fecha_entidad (fecha, entidad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Log de Cargas ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS log_cargas (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    endpoint  VARCHAR(100),
    registros INT,
    estado    VARCHAR(20),
    mensaje   TEXT,
    inicio    DATETIME,
    fin       DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

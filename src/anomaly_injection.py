"""
anomaly_injection.py

Módulo para inyectar anomalías realistas en el dataset de movimientos.
Simula problemas comunes de calidad de datos que el pipeline de limpieza
debe ser capaz de detectar y corregir.

Anomalías inyectadas:
1. Valores nulos aleatorios (10-25% por columna crítica)
2. Duplicados parciales (misma transacción registrada múltiples veces)
3. Valores atípicos fuera de rango (cantidades negativas, fechas inversas)
4. Inconsistencias lógicas (producto OUT antes de IN, etc.)
5. Errores de tipo de dato (fechas malformadas, números como strings)

Uso:
    python src/anomaly_injection.py --input data/raw/movements_raw.csv \
                                   --output data/interim/movements_with_anomalies.csv \
                                   --seed 42 \
                                   --null_ratio 0.15
"""

import pandas as pd
import numpy as np
import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def inject_nulls(df, null_ratio=0.15, critical_cols=None, seed=42):
    """
    Inyecta valores nulos aleatorios en columnas no críticas.

    Args:
        df: DataFrame con movimientos
        null_ratio: Proporción de valores a hacer NULL (0.0-0.5)
        critical_cols: Columnas que NO deben tener NULLs
        seed: Para reproducibilidad

    Returns:
        DataFrame con NULLs inyectados
    """
    np.random.seed(seed)
    df_copy = df.copy()

    if critical_cols is None:
        critical_cols = {'event_id', 'household_id', 'product_id', 'timestamp', 'event_type'}

    nullable_cols = [col for col in df_copy.columns if col not in critical_cols]

    logger.info(f"Inyectando NULLs en {null_ratio*100:.1f}% de valores...")
    for col in nullable_cols:
        if col in df_copy.columns:
            null_count = int(len(df_copy) * null_ratio)
            null_indices = np.random.choice(len(df_copy), size=null_count, replace=False)
            df_copy.loc[null_indices, col] = np.nan
            logger.info(f"  {col}: {null_count} NULLs")

    return df_copy


def inject_duplicates(df, duplicate_ratio=0.05, seed=42):
    """
    Inyecta registros duplicados (misma transacción registrada 2-3 veces).

    Args:
        df: DataFrame original
        duplicate_ratio: Proporción de registros a duplicar
        seed: Para reproducibilidad

    Returns:
        DataFrame con duplicados
    """
    np.random.seed(seed)
    df_copy = df.copy()

    dup_count = int(len(df_copy) * duplicate_ratio)
    dup_indices = np.random.choice(len(df_copy), size=dup_count, replace=False)

    logger.info(f"Inyectando {dup_count} registros duplicados ({duplicate_ratio*100:.1f}%)...")

    duplicates = []
    for idx in dup_indices:
        row = df_copy.iloc[idx].copy()
        # Variar ligeramente (timestamp +/- 1 minuto)
        ts = pd.to_datetime(row['timestamp'])
        ts_variation = ts + timedelta(minutes=np.random.randint(-1, 2))
        row['timestamp'] = ts_variation.strftime('%Y-%m-%d %H:%M:%S')
        duplicates.append(row)

    df_duplicates = pd.concat(
        [df_copy, pd.DataFrame(duplicates)],
        ignore_index=True
    )
    logger.info(f"  Total registros después: {len(df_duplicates)}")

    return df_duplicates


def inject_outliers(df, outlier_ratio=0.08, seed=42):
    """
    Inyecta valores atípicos en columnas numéricas:
    - Cantidades negativas
    - Valores extremadamente grandes
    - Fechas de vencimiento en el pasado

    Args:
        df: DataFrame
        outlier_ratio: Proporción de outliers
        seed: Para reproducibilidad

    Returns:
        DataFrame con outliers
    """
    np.random.seed(seed)
    df_copy = df.copy()

    logger.info(f"Inyectando outliers en {outlier_ratio*100:.1f}% de registros...")

    # Outliers en 'quantity'
    if 'quantity' in df_copy.columns:
        outlier_indices = np.random.choice(
            len(df_copy),
            size=int(len(df_copy) * outlier_ratio),
            replace=False
        )
        for idx in outlier_indices:
            choice = np.random.choice(['negative', 'extreme'])
            if choice == 'negative':
                df_copy.loc[idx, 'quantity'] = -np.random.randint(1, 100)
            else:
                df_copy.loc[idx, 'quantity'] = np.random.randint(1000, 10000)
        logger.info(f"  quantity: {len(outlier_indices)} outliers")

    # Outliers en 'expiry_date': fechas muy antiguas o muy futuras
    if 'expiry_date' in df_copy.columns:
        outlier_indices = np.random.choice(
            len(df_copy),
            size=int(len(df_copy) * outlier_ratio * 0.5),
            replace=False
        )
        for idx in outlier_indices:
            choice = np.random.choice(['past', 'future'])
            if choice == 'past':
                old_date = datetime.now() - timedelta(days=np.random.randint(1, 365))
                df_copy.loc[idx, 'expiry_date'] = old_date.strftime('%Y-%m-%d')
            else:
                future_date = datetime.now() + timedelta(days=np.random.randint(365, 730))
                df_copy.loc[idx, 'expiry_date'] = future_date.strftime('%Y-%m-%d')
        logger.info(f"  expiry_date: {len(outlier_indices)} outliers")

    return df_copy


def inject_logical_inconsistencies(df, seed=42):
    """
    Inyecta inconsistencias lógicas:
    - Timestamps inversas
    - Timestamps posteriores a expiry_date

    Args:
        df: DataFrame
        seed: Para reproducibilidad

    Returns:
        DataFrame con inconsistencias
    """
    np.random.seed(seed)
    df_copy = df.copy()

    logger.info("Inyectando inconsistencias lógicas...")

    if 'timestamp' in df_copy.columns and 'expiry_date' in df_copy.columns:
        inconsistent_indices = np.random.choice(
            len(df_copy),
            size=int(len(df_copy) * 0.03),
            replace=False
        )
        for idx in inconsistent_indices:
            # Hacer que el timestamp sea posterior al expiry_date
            df_copy.loc[idx, 'timestamp'] = df_copy.loc[idx, 'expiry_date'] + ' 23:59:59'

        logger.info(f"  Timestamp > Expiry_date: {len(inconsistent_indices)} registros")

    return df_copy


def inject_type_errors(df, type_error_ratio=0.05, seed=42):
    """
    Inyecta errores de tipo de dato:
    - Números como strings
    - Fechas malformadas
    - Valores inválidos en categorías

    Args:
        df: DataFrame
        type_error_ratio: Proporción de errores
        seed: Para reproducibilidad

    Returns:
        DataFrame con errores de tipo
    """
    np.random.seed(seed)
    df_copy = df.copy()

    logger.info(f"Inyectando errores de tipo en {type_error_ratio*100:.1f}% de registros...")

    # Convertir algunas cantidades a strings
    if 'quantity' in df_copy.columns:
        error_indices = np.random.choice(
            len(df_copy),
            size=int(len(df_copy) * type_error_ratio),
            replace=False
        )
        for idx in error_indices:
            df_copy.loc[idx, 'quantity'] = str(df_copy.loc[idx, 'quantity'])
        logger.info(f"  quantity como string: {len(error_indices)}")

    # Fechas malformadas (cambiar formato o agregar caracteres)
    if 'timestamp' in df_copy.columns:
        error_indices = np.random.choice(
            len(df_copy),
            size=int(len(df_copy) * type_error_ratio * 0.3),
            replace=False
        )
        malformed_dates = ['2024-13-45', 'not-a-date', '20240115', '2024/01/15 25:61:00']
        for idx in error_indices:
            df_copy.loc[idx, 'timestamp'] = np.random.choice(malformed_dates)
        logger.info(f"  timestamp malformado: {len(error_indices)}")

    return df_copy


def run_anomaly_injection(input_path, output_path, seed=42, null_ratio=0.15):
    """
    Ejecuta el pipeline completo de inyección de anomalías.

    Args:
        input_path: Ruta al CSV de movimientos original
        output_path: Ruta donde guardar los movimientos con anomalías
        seed: Seed para reproducibilidad
        null_ratio: Proporción de valores nulos
    """
    logger.info(f"Leyendo movimientos desde: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Registros leídos: {len(df)}")

    # Crear bitácora de inyección
    injection_log = {
        "timestamp_execution": datetime.now().isoformat(),
        "input_file": input_path,
        "input_record_count": len(df),
        "seed": seed,
        "anomalies": {}
    }

    # Inyectar anomalías
    df = inject_nulls(df, null_ratio=null_ratio, seed=seed)
    injection_log["anomalies"]["nulls"] = f"{null_ratio*100:.1f}% ratio"

    df = inject_duplicates(df, duplicate_ratio=0.05, seed=seed)
    injection_log["anomalies"]["duplicates"] = "5% ratio"

    df = inject_outliers(df, outlier_ratio=0.08, seed=seed)
    injection_log["anomalies"]["outliers"] = "8% ratio"

    df = inject_logical_inconsistencies(df, seed=seed)
    injection_log["anomalies"]["logical"] = "3% timestamp/expiry inconsistencies"

    df = inject_type_errors(df, type_error_ratio=0.05, seed=seed)
    injection_log["anomalies"]["type_errors"] = "5% type errors"

    # Guardar resultado
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"✅ Movimientos con anomalías guardados en: {output_path}")
    logger.info(f"   Total registros después de inyección: {len(df)}")

    # Guardar bitácora
    injection_log["output_record_count"] = len(df)
    injection_log["output_file"] = output_path

    log_path = output_path.replace('.csv', '_injection_log.json')
    with open(log_path, 'w') as f:
        json.dump(injection_log, f, indent=2, default=str)
    logger.info(f"📋 Bitácora de inyección guardada: {log_path}")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inyectar anomalías realistas en dataset de movimientos"
    )
    parser.add_argument(
        "--input",
        default="data/raw/movements_raw.csv",
        help="Ruta al CSV de movimientos original"
    )
    parser.add_argument(
        "--output",
        default="data/interim/movements_with_anomalies.csv",
        help="Ruta donde guardar los movimientos con anomalías"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed para reproducibilidad"
    )
    parser.add_argument(
        "--null_ratio",
        type=float,
        default=0.15,
        help="Proporción de valores nulos (0.0-0.5)"
    )

    args = parser.parse_args()

    run_anomaly_injection(
        args.input,
        args.output,
        seed=args.seed,
        null_ratio=args.null_ratio
    )

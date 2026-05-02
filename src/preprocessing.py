"""
preprocessing.py

Pipeline de limpieza y corrección de datos con detección de anomalías.
Detecta y corrige:
- Valores nulos
- Duplicados
- Valores atípicos
- Inconsistencias lógicas
- Errores de tipo

Genera bitácora detallada de transformaciones y validación QA.

Uso:
    python src/preprocessing.py --input data/interim/movements_with_anomalies.csv \
                               --catalog data/raw/catalog_raw.csv \
                               --output data/processed/inventory_v1.csv
"""

import pandas as pd
import polars as pl
import numpy as np
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCleaner:
    """Pipeline de limpieza y validación de datos con bitácora."""

    def __init__(self, movements_path, catalog_path, seed=42):
        self.movements_path = movements_path
        self.catalog_path = catalog_path
        self.seed = seed
        self.cleaning_log = {
            "timestamp": datetime.now().isoformat(),
            "input_file": movements_path,
            "catalog_file": catalog_path,
            "steps": []
        }
        self.df = None
        self.df_catalog = None

    def load_data(self):
        """Carga datos de movimientos y catálogo."""
        logger.info("📂 Cargando datos...")

        if not os.path.exists(self.movements_path):
            raise FileNotFoundError(f"No se encuentra {self.movements_path}")
        if not os.path.exists(self.catalog_path):
            raise FileNotFoundError(f"No se encuentra {self.catalog_path}")

        self.df = pd.read_csv(self.move
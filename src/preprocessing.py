"""
preprocessing.py - Pipeline de limpieza y preparacion (Entrega 2, revisado)
"""

import argparse
import polars as pl
import json
import os
from datetime import datetime

CATEGORY_MAP = {
    4:  "Frutas y Verduras",
    16: "Lacteos y Refrigerados",
    7:  "Bebidas",
    3:  "Panaderia y Granos",
    1:  "Despensa General",
    20: "Congelados",
}

LOCATION_MAP = {
    4:  "Refrigerador",
    16: "Refrigerador",
    7:  "Estante",
    3:  "Despensa",
    1:  "Despensa",
    20: "Refrigerador",
}

CALORIE_THRESHOLD = 900


def run_preprocessing(
    movements_path="data/raw/movements_raw.csv",
    catalog_path="data/raw/catalog_raw.csv",
    output_path="data/interim/inventory_v1.csv",
    log_path="data/interim/transformations_log.json",
):
    """Los defaults reproducen exactamente el comportamiento historico del
    pipeline (el que genero los data/processed/*.csv y docs/data_dictionary.md
    documentados). Los parametros existen para poder reutilizar esta misma
    logica de limpieza sobre otra entrada, ej. el dataset con anomalias
    inyectadas de notebooks/00_data_pipeline.ipynb, sin duplicar codigo."""
    print("=" * 60)
    print("PIPELINE DE LIMPIEZA --- Smart Kitchen Intelligence")
    print("Ejecucion: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)

    for p in [movements_path, catalog_path]:
        if not os.path.exists(p):
            raise FileNotFoundError("Archivo no encontrado: " + p)

    # CARGA
    df_mov = pl.read_csv(movements_path)
    df_cat = pl.read_csv(catalog_path)
    n_mov_inicial = len(df_mov)
    n_cat_inicial = len(df_cat)
    print("[CARGA] movements: " + str(n_mov_inicial) + " | catalog: " + str(n_cat_inicial))

    # P4 -- Tipos de dato explicitos
    df_mov = df_mov.with_columns([
        pl.col("product_id").cast(pl.Int64),
        pl.col("household_id").cast(pl.Int64),
        pl.col("quantity").cast(pl.Int64),
        pl.col("timestamp").str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False),
        pl.col("expiry_date").str.to_date("%Y-%m-%d", strict=False),
        pl.col("event_type").cast(pl.Categorical),
        pl.col("classification").cast(pl.Categorical),
    ])

    df_cat = df_cat.with_columns([
        pl.col("product_id").cast(pl.Int64),
        pl.col("calories_100g").cast(pl.Float64),
        pl.col("proteins_100g").cast(pl.Float64),
        pl.col("carbs_100g").cast(pl.Float64),
        pl.col("category").cast(pl.Int64),
        pl.when(pl.col("nutriscore") == "Falta Dato")
          .then(None)
          .otherwise(pl.col("nutriscore"))
          .alias("nutriscore"),
    ])

    # P1 -- Outlier calorico
    cat_outliers = df_cat.filter(pl.col("calories_100g") > CALORIE_THRESHOLD)
    n_outliers = len(cat_outliers)
    df_cat = df_cat.filter(
        pl.col("calories_100g").is_null() | (pl.col("calories_100g") <= CALORIE_THRESHOLD)
    )
    n_cat_post_p1 = len(df_cat)
    print("[P1] Outliers caloricos: " + str(n_outliers) + " -> catalogo: " + str(n_cat_inicial) + "->" + str(n_cat_post_p1))

    # P2 -- Categorias numericas -> category_name + location
    cat_vals  = df_cat["category"].to_list()
    cat_names = [CATEGORY_MAP.get(v, "Categoria_" + str(v)) for v in cat_vals]
    loc_names = [LOCATION_MAP.get(v, "Estante") for v in cat_vals]
    df_cat = df_cat.with_columns([
        pl.Series("category_name", cat_names),
        pl.Series("location", loc_names),
    ])
    n_cats_distintas = df_cat["category_name"].n_unique()
    print("[P2] Categorias: " + str(df_cat["category"].n_unique()) + " dept_ids -> " + str(n_cats_distintas) + " category_name")

    # P5 -- Nutriscore faltante (ya convertido en P4)
    n_nutriscore_nulos_cat = df_cat["nutriscore"].null_count()
    print("[P5] Nutriscore nulos en catalogo: " + str(n_nutriscore_nulos_cat) + " productos")

    # P6 -- Deduplicacion
    n_antes_dedup = len(df_mov)
    df_mov = df_mov.unique(subset=["event_id"], keep="first")
    n_duplicados = n_antes_dedup - len(df_mov)
    print("[P6] Duplicados eliminados: " + str(n_duplicados))

    # P3 -- Integridad referencial
    cat_pids = df_cat["product_id"].to_list()
    mask_validos = df_mov["product_id"].is_in(cat_pids)
    n_huerfanos = int((~mask_validos).sum())
    df_mov = df_mov.filter(mask_validos)
    n_mov_post_p3 = len(df_mov)
    print("[P3] Huerfanos eliminados: " + str(n_huerfanos) + " -> movements: " + str(n_mov_inicial) + "->" + str(n_mov_post_p3))

    # JOIN
    catalog_join = df_cat.select([
        "product_id", "nutriscore", "calories_100g",
        "proteins_100g", "carbs_100g", "category_name", "location",
    ])
    df_inv = df_mov.join(catalog_join, on="product_id", how="left")

    # Columnas derivadas
    df_inv = df_inv.with_columns(
        pl.col("event_type").cast(pl.String).alias("action_type")
    )
    df_inv = df_inv.with_columns(
        (pl.col("expiry_date").cast(pl.Date) - pl.col("timestamp").cast(pl.Date))
        .dt.total_days()
        .alias("dias_para_vencer")
    )

    # Orden final de columnas
    columnas_finales = [
        "event_id", "household_id", "stock_id",
        "product_id", "product_name",
        "action_type", "quantity", "timestamp", "expiry_date",
        "classification", "location", "category_name", "dias_para_vencer",
        "nutriscore", "calories_100g", "proteins_100g", "carbs_100g",
    ]
    df_inv = df_inv.select(columnas_finales)

    # Guardar
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df_inv.write_csv(output_path)

    n_final     = len(df_inv)
    n_cols      = len(df_inv.columns)
    n_nut_nulos = int(df_inv["nutriscore"].null_count())
    n_dpv_neg   = int((df_inv["dias_para_vencer"] < 0).sum())
    ts_min      = str(df_inv["timestamp"].min())
    ts_max      = str(df_inv["timestamp"].max())

    dist_action = df_inv["action_type"].value_counts().sort("action_type")
    dist_class  = df_inv["classification"].cast(pl.String).value_counts().sort("classification")
    dist_loc    = df_inv["location"].value_counts().sort("location")
    dist_cat    = df_inv["category_name"].value_counts().sort("category_name")

    print("")
    print("[OUTPUT] " + output_path)
    print("  Filas: " + str(n_final) + " | Columnas: " + str(n_cols))
    print("  Rango temporal: " + ts_min + " -> " + ts_max)
    print("  Nutriscore nulo en inventario: " + str(n_nut_nulos))
    print("  Eventos vencidos al momento del evento: " + str(n_dpv_neg))
    for row in dist_action.iter_rows(named=True):
        print("  action_type " + str(row["action_type"]) + ": " + str(row["count"]))
    for row in dist_class.iter_rows(named=True):
        print("  classification " + str(row["classification"]) + ": " + str(row["count"]))
    for row in dist_loc.iter_rows(named=True):
        print("  location " + str(row["location"]) + ": " + str(row["count"]))
    for row in dist_cat.iter_rows(named=True):
        print("  category_name " + str(row["category_name"]) + ": " + str(row["count"]))

    # Transformations log
    action_dist = {row["action_type"]: row["count"] for row in dist_action.iter_rows(named=True)}
    class_dist  = {row["classification"]: row["count"] for row in dist_class.iter_rows(named=True)}
    loc_dist    = {row["location"]: row["count"] for row in dist_loc.iter_rows(named=True)}
    cat_dist    = {row["category_name"]: row["count"] for row in dist_cat.iter_rows(named=True)}

    log = {
        "timestamp_ejecucion": datetime.now().isoformat(),
        "esquema": "multi-hogar v2 (10 hogares, 90 dias, clasificacion OUT detallada)",
        "registros_iniciales": {
            "catalog":   n_cat_inicial,
            "movements": n_mov_inicial,
        },
        "transformaciones": {
            "P1_outlier_calorico": {
                "umbral_calories_100g":      CALORIE_THRESHOLD,
                "outliers_detectados":       n_outliers,
                "outliers_removidos":        n_outliers,
                "registros_catalog_despues": n_cat_post_p1,
            },
            "P2_homologacion_categorias": {
                "dept_ids_distintos":     int(df_cat["category"].n_unique()),
                "category_names_finales": n_cats_distintas,
                "mapeo_category_name":    CATEGORY_MAP,
                "mapeo_location":         LOCATION_MAP,
                "location_derivada":      True,
            },
            "P3_integridad_referencial": {
                "huerfanos_detectados":        n_huerfanos,
                "huerfanos_removidos":         n_huerfanos,
                "registros_movements_despues": n_mov_post_p3,
            },
            "P4_tipos_de_dato": {
                "product_id":    "Int64",
                "household_id":  "Int64",
                "quantity":      "Int64",
                "timestamp":     "Datetime",
                "expiry_date":   "Date",
                "event_type":    "Categorical",
                "classification": "Categorical",
            },
            "P5_nutriscore_faltante": {
                "valor_original":      "Falta Dato",
                "accion":              "convertido a null (nulo estructural preservado)",
                "productos_afectados": n_nutriscore_nulos_cat,
            },
            "P6_deduplicacion": {
                "duplicados_removidos": n_duplicados,
                "registros_despues":    n_mov_post_p3,
            },
            "join": {
                "tabla_izquierda":  "movements",
                "tabla_derecha":    "catalog",
                "tipo_join":        "left",
                "clave":            "product_id",
                "registros_resultado": n_final,
            },
            "derivadas": {
                "action_type":      "alias de event_type (IN/OUT)",
                "category_name":    "mapeada desde category/dept_id",
                "location":         "derivada desde dept_id via LOCATION_MAP",
                "dias_para_vencer": "expiry_date - timestamp en dias (neg = vencido)",
                "columnas_finales": n_cols,
            },
        },
        "registros_finales": {
            "catalog":      n_cat_post_p1,
            "movements":    n_mov_post_p3,
            "inventory_v1": n_final,
        },
        "calidad_datos": {
            "nulos_nutriscore_eventos":    n_nut_nulos,
            "eventos_vencidos_al_momento": n_dpv_neg,
            "cardinalidad_category_name":  n_cats_distintas,
            "cardinalidad_location":       int(df_inv["location"].n_unique()),
            "distribucion_action_type":    action_dist,
            "distribucion_classification": class_dist,
            "distribucion_location":       loc_dist,
            "distribucion_category_name":  cat_dist,
            "rango_temporal": {
                "min": ts_min,
                "max": ts_max,
            },
        },
    }

    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print("")
    print("[LOG] " + log_path + " actualizado.")
    print("=" * 60)
    print("Pipeline completado sin errores.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de limpieza SKI")
    parser.add_argument("--input", dest="movements_path", default="data/raw/movements_raw.csv",
                         help="CSV de movimientos a limpiar (default: movements_raw.csv; "
                              "pasar el CSV con anomalias inyectadas para reusar esta misma "
                              "logica sobre datos sinteticamente sucios)")
    parser.add_argument("--catalog", dest="catalog_path", default="data/raw/catalog_raw.csv")
    parser.add_argument("--output", dest="output_path", default="data/interim/inventory_v1.csv")
    parser.add_argument("--log", dest="log_path", default="data/interim/transformations_log.json")
    args = parser.parse_args()
    run_preprocessing(
        movements_path=args.movements_path,
        catalog_path=args.catalog_path,
        output_path=args.output_path,
        log_path=args.log_path,
    )

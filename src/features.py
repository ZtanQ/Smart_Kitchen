import polars as pl
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import json

def build_feature_matrix():
    print("Iniciando pipeline de features...")

    input_path = "data/processed/inventory_v1.csv"
    if not os.path.exists(input_path):
        print(f"Error: {input_path} no encontrado.")
        return

    df = pl.read_csv(input_path)

    # 1. Variables Numéricas (Imputación por media de categoría)
    numeric_cols = ['calories_100g', 'proteins_100g', 'carbs_100g']
    df = df.with_columns([
        pl.col(c).fill_null(pl.col(c).mean().over("category_name")).fill_null(0)
        for c in numeric_cols
    ])

    # 2. Variables de Texto (TF-IDF)
    tfidf = TfidfVectorizer(max_features=50, stop_words='english')
    text_features = tfidf.fit_transform(df['product_name'].to_list()).toarray()
    text_cols = [f"txt_{w}" for w in tfidf.get_feature_names_out()]
    df_text = pl.DataFrame(text_features, schema=text_cols)

    # 3. Variables Categóricas (One-Hot Encoding)
    df_cat = df.select(pl.col("category_name").cast(pl.Utf8)).to_dummies("category_name")

    # 4. Variables Temporales
    df_time = df.select([
        pl.col("timestamp").str.to_datetime().dt.hour().alias("hour_of_day"),
        pl.col("timestamp").str.to_datetime().dt.weekday().alias("day_of_week")
    ])

    # 5. Consolidación
    df_num = df.select(numeric_cols)
    full_matrix = pl.concat([df_num, df_cat, df_text, df_time], how="horizontal")

    # 6. Escalado Final
    print("Aplicando StandardScaler...")
    scaler = StandardScaler()
    X_raw = full_matrix.to_pandas().to_numpy()
    scaled_data = scaler.fit_transform(X_raw)

    # 7. Persistencia
    os.makedirs("data/features", exist_ok=True)
    np.save("data/features/feature_matrix.npy", scaled_data)

    with open("data/features/feature_names.json", "w") as f:
        json.dump(full_matrix.columns, f)

    print(f"Features generadas exitosamente: {scaled_data.shape}")

if __name__ == "__main__":
    build_feature_matrix()

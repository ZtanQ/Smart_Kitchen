"""Componente avanzado (Entrega 6): PCA + t-SNE sobre la matriz de features.

Genera:
- reports/figures/pca_scree_plot.png
- reports/figures/pca_scatter_2d.png
- reports/figures/tsne_scatter_2d.png
- outputs/pca_components_tableau.csv   (todas las filas, PC1-PC3 + metadata)
- outputs/tsne_sample_tableau.csv      (muestra aleatoria con coordenadas t-SNE)
- outputs/pca_variance_table.csv       (varianza explicada por componente)
"""

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import os
import json

RANDOM_STATE = 42
TSNE_SAMPLE_SIZE = 5000  # t-SNE es O(n^2); muestreamos para tiempos razonables
TSNE_PERPLEXITY = 30


def run_dimensionality_reduction():
    print("Iniciando Analisis de Reduccion de Dimensionalidad (PCA + t-SNE)...")

    matrix_path = "data/features/feature_matrix.npy"
    metadata_path = "data/processed/inventory_v1.csv"

    if not os.path.exists(matrix_path):
        print(f"Error: No se encontro {matrix_path}")
        return

    X = np.load(matrix_path)
    df_meta = pl.read_csv(metadata_path).to_pandas()

    # ===== PCA completo: energia retenida =====
    pca_full = PCA(random_state=RANDOM_STATE)
    pca_full.fit(X)
    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    n_90 = int(np.argmax(cumulative_variance >= 0.90) + 1)

    print("\n--- TABLA DE VARIANZA EXPLICADA (Top 5 Componentes) ---")
    print(f"Dimension original: {X.shape[1]} caracteristicas")
    print(f"Componentes para retener 90% de informacion: {n_90}\n")
    print("| Componente | Varianza Explicada | Varianza Acumulada |")
    print("| :--- | :--- | :--- |")
    for i in range(5):
        print(f"| PC{i+1} | {pca_full.explained_variance_ratio_[i]*100:.2f}% | {cumulative_variance[i]*100:.2f}% |")

    os.makedirs("reports/figures", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    # Grafico A: Scree Plot
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, marker='o', linestyle='--', color='b', markersize=4)
    plt.axhline(y=0.90, color='r', linestyle='-', label='Umbral 90% Informacion')
    plt.axvline(x=n_90, color='r', linestyle='--')
    plt.title('Scree Plot: Varianza Acumulada vs Componentes (PCA)')
    plt.xlabel('Numero de Componentes Principales')
    plt.ylabel('Varianza Acumulada (Energia Retenida)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("reports/figures/pca_scree_plot.png", dpi=300, bbox_inches='tight')
    plt.close()

    # Grafico B: Scatter PCA 2D coloreado por tipo de evento (IN/OUT)
    pca_3 = PCA(n_components=3, random_state=RANDOM_STATE)
    X_3 = pca_3.fit_transform(X)

    plt.figure(figsize=(12, 8))
    sns.scatterplot(x=X_3[:, 0], y=X_3[:, 1], hue=df_meta['action_type'],
                    palette="viridis", alpha=0.6, edgecolor=None, s=15)
    plt.title('Proyeccion PCA 2D: Estructura Latente de Movimientos')
    plt.xlabel(f'Componente Principal 1 ({pca_3.explained_variance_ratio_[0]*100:.1f}%)')
    plt.ylabel(f'Componente Principal 2 ({pca_3.explained_variance_ratio_[1]*100:.1f}%)')
    plt.legend(title='Tipo de Evento')
    plt.savefig("reports/figures/pca_scatter_2d.png", dpi=300, bbox_inches='tight')
    plt.close()

    # ===== t-SNE: estructura local no lineal =====
    rng = np.random.default_rng(RANDOM_STATE)
    n = X.shape[0]
    sample_idx = rng.choice(n, size=min(TSNE_SAMPLE_SIZE, n), replace=False)
    sample_idx.sort()

    # Pre-reduccion con PCA (denoising y velocidad, practica recomendada)
    n_pre = min(30, X.shape[1])
    X_pre = PCA(n_components=n_pre, random_state=RANDOM_STATE).fit_transform(X)[sample_idx]

    print(f"\nEjecutando t-SNE sobre muestra de {len(sample_idx)} registros (perplexity={TSNE_PERPLEXITY})...")
    tsne = TSNE(n_components=2, perplexity=TSNE_PERPLEXITY, random_state=RANDOM_STATE, init="pca", learning_rate="auto")
    X_tsne = tsne.fit_transform(X_pre)

    df_sample = df_meta.iloc[sample_idx].copy()
    df_sample["tsne_1"] = X_tsne[:, 0]
    df_sample["tsne_2"] = X_tsne[:, 1]

    plt.figure(figsize=(12, 8))
    sns.scatterplot(x="tsne_1", y="tsne_2", hue="category_name", data=df_sample,
                    palette="tab10", alpha=0.6, edgecolor=None, s=15)
    plt.title(f't-SNE 2D (muestra n={len(sample_idx)}): agrupamiento por categoria')
    plt.xlabel('t-SNE 1')
    plt.ylabel('t-SNE 2')
    plt.legend(title='Categoria', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
    plt.savefig("reports/figures/tsne_scatter_2d.png", dpi=300, bbox_inches='tight')
    plt.close()

    # ===== Exportables para Tableau =====
    meta_cols = ['event_id', 'household_id', 'product_name', 'action_type',
                 'category_name', 'location', 'nutriscore', 'timestamp',
                 'dias_para_vencer', 'calories_100g']

    df_pca_export = df_meta[meta_cols].copy()
    df_pca_export["PC1"] = X_3[:, 0]
    df_pca_export["PC2"] = X_3[:, 1]
    df_pca_export["PC3"] = X_3[:, 2]
    df_pca_export.to_csv("outputs/pca_components_tableau.csv", index=False)

    df_sample[meta_cols + ["tsne_1", "tsne_2"]].to_csv("outputs/tsne_sample_tableau.csv", index=False)

    var_table = pl.DataFrame({
        "componente": [f"PC{i+1}" for i in range(len(pca_full.explained_variance_ratio_))],
        "varianza_explicada": pca_full.explained_variance_ratio_,
        "varianza_acumulada": cumulative_variance,
    })
    var_table.write_csv("outputs/pca_variance_table.csv")

    summary = {
        "dim_original": int(X.shape[1]),
        "n_registros": int(n),
        "componentes_para_90pct": n_90,
        "pca_var_pc1": float(pca_full.explained_variance_ratio_[0]),
        "pca_var_pc2": float(pca_full.explained_variance_ratio_[1]),
        "pca_var_pc3": float(pca_full.explained_variance_ratio_[2]),
        "tsne_sample_size": int(len(sample_idx)),
        "tsne_perplexity": TSNE_PERPLEXITY,
        "tsne_pre_pca_dims": n_pre,
        "random_state": RANDOM_STATE,
    }
    with open("outputs/reduction_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n[OK] Reporte de Reduccion Finalizado.")
    print("Figuras en 'reports/figures/' y exportables Tableau en 'outputs/'.")
    return summary


if __name__ == "__main__":
    run_dimensionality_reduction()

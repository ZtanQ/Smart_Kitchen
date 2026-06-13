# Componente Avanzado — PCA + t-SNE (Entrega 6, Semana 12)

## 1. Pregunta que responde
¿Existe una estructura latente en los 25,819 movimientos de inventario que permita agrupar el comportamiento de compra/consumo de los hogares más allá de las categorías declaradas?

## 2. Datos y variables
- **Fuente:** `data/processed/inventory_v1.csv` (dataset limpio, Entrega 2).
- **Matriz de features (61 dims):** `calories_100g`, `proteins_100g`, `carbs_100g` (imputación por media de categoría) + one-hot de `category_name` (6) + TF-IDF de `product_name` (50 términos) + `hour_of_day`, `day_of_week`. Escalado: `StandardScaler`.

## 3. Técnicas y parámetros
| Técnica | Parámetros | Alcance |
|---|---|---|
| PCA | todos los componentes; umbral 90% varianza | 25,819 registros completos |
| t-SNE | `perplexity=30`, `init='pca'`, `learning_rate='auto'`, pre-PCA a 30 dims, `random_state=42` | muestra aleatoria reproducible n=5,000 |

## 4. Resultados clave
- **29 de 61 componentes** retienen el 90% de la varianza → la dimensionalidad efectiva es ~la mitad de la original.
- PC1=8.0%, PC2=6.8%, PC3=5.6%: varianza distribuida (esperable con TF-IDF disperso); el scree plot se lee en acumulado.
- t-SNE muestra **clusters compactos por categoría de producto**, con subestructura por patrón horario. PCA preserva geometría global; t-SNE revela grupos locales.

## 5. Integración al dashboard beta (Tableau)
1. Conectar `outputs/pca_components_tableau.csv` → hoja "Mapa latente (PCA)": scatter PC1 vs PC2, color por `action_type` o `category_name`, filtro por `household_id`.
2. Conectar `outputs/tsne_sample_tableau.csv` → hoja "Clusters t-SNE": scatter tsne_1 vs tsne_2, color por `category_name`, tooltip con `product_name` y `nutriscore`.
3. Conectar `outputs/pca_variance_table.csv` → hoja "Energía retenida": Pareto de varianza acumulada con línea de referencia en 90%.
4. Agrupar las 3 hojas en el bloque "Módulo avanzado" del dashboard beta.

## 6. Limitaciones
- t-SNE sobre muestra (5,000/25,819); distancias globales entre clusters no interpretables.
- Dataset proviene de simulación calibrada (patrones Instacart + nutrición USDA): los clusters reflejan la estructura simulada.
- PCA es lineal; relaciones no lineales solo aparecen en t-SNE.
- Reproducibilidad garantizada con `random_state=42` en todo el pipeline.

## 7. Reproducibilidad
```bash
python src/features.py    # genera data/features/feature_matrix.npy
python src/reduction.py   # genera figuras + exportables Tableau
# notebooks/04_componente_avanzado.ipynb documenta y visualiza el análisis
```

# Componente Avanzado — PCA + t-SNE (Entrega 6)

## 1. Pregunta que responde
¿Existe una estructura latente en los 25,819 movimientos de inventario que permita agrupar el comportamiento de compra/consumo de los hogares más allá de las categorías declaradas? Y, mas importante para el negocio: ¿la forma en que el dashboard principal organiza el analisis (por **ubicacion fisica**) refleja una estructura real de los datos, o es una eleccion arbitraria?

## 2. Por que se eligieron estas tecnicas
Con 61 variables por evento (nutricion, categoria, texto del nombre de producto via TF-IDF, hora y dia) no hay forma de inspeccionar visualmente si los productos forman grupos naturales — se necesita reducir dimensionalidad. Se combinaron dos tecnicas complementarias en vez de una sola:
- **PCA** porque es rapida, determinista y preserva la geometria global: permite medir formalmente cuanta informacion (varianza) se retiene al reducir de 61 a 2-3 dimensiones, con un numero exacto (ver §4).
- **t-SNE** porque PCA es lineal y puede pasar por alto agrupamientos locales no lineales; t-SNE los revela a costa de distorsionar las distancias globales entre grupos (por eso se usan juntas, no una en lugar de la otra: PCA valida "cuanta estructura hay", t-SNE valida "que forma tiene esa estructura").

## 3. Como funcionan (resumen conceptual)
- **PCA (Analisis de Componentes Principales):** busca las combinaciones lineales de las 61 variables originales que capturan la mayor varianza posible. La primera combinacion (PC1) es la direccion de maxima varianza; la segunda (PC2) es la siguiente direccion, ortogonal a la primera; y asi sucesivamente. Cada componente adicional explica menos varianza que el anterior.
- **t-SNE (t-distributed Stochastic Neighbor Embedding):** en vez de buscar direcciones de varianza, ubica cada punto en un plano 2D de forma que puntos que eran vecinos cercanos en las 61 dimensiones originales queden cerca entre si en el mapa final. Es no lineal y estocastico (por eso se fija `random_state=42`).

## 4. Datos, variables y como se aplicaron
- **Fuente:** `data/processed/inventory_v1.csv` (dataset limpio, Entrega 2).
- **Matriz de features (61 dims), `src/features.py`:** `calories_100g`, `proteins_100g`, `carbs_100g` (imputación por media de categoría) + one-hot de `category_name` (6) + TF-IDF de `product_name` (50 términos) + `hour_of_day`, `day_of_week`. Escalado: `StandardScaler`.
- **Ejecucion, `src/reduction.py`:**

| Técnica | Parámetros | Alcance |
|---|---|---|
| PCA | todos los componentes; umbral 90% varianza | 25,819 registros completos |
| t-SNE | `perplexity=30`, `init='pca'`, `learning_rate='auto'`, pre-PCA a 30 dims, `random_state=42` | muestra aleatoria reproducible n=5,000 |

## 5. Resultados clave
- **29 de 61 componentes** retienen el 90% de la varianza → la dimensionalidad efectiva es ~la mitad de la original.
- PC1=8.0%, PC2=6.8%, PC3=5.6%: varianza distribuida (esperable con TF-IDF disperso); el scree plot se lee en acumulado.
- Tanto PCA (mapa PC1 vs PC2) como t-SNE muestran **clusters casi perfectamente separados por categoría de producto** (verificado numéricamente: la media de PC1 por categoría varía de -0.96 a +11.6, con desviaciones estándar internas mucho menores — ver `outputs/pca_components_tableau.csv`).

## 6. Impacto en el analisis de negocio (no es solo un requisito tecnico)
Este es el hallazgo que conecta el componente avanzado con la pregunta central del dashboard. En este dataset, **`location` es una función determinista de `category_name`**: cada una de las 6 categorías vive en una única ubicación física (Refrigerador = Frutas y Verduras + Lácteos y Refrigerados + Congelados; Estante = Bebidas; Despensa = Panadería y Granos + Despensa General — verificado con `pd.crosstab(category_name, location)`, sin superposición). Como PCA/t-SNE muestran que **categoría de producto es la variable que más separa a los eventos** en el espacio de 61 características (más que el hogar, más que la hora del día), y ubicación es solo un alias de categoría, se concluye que:

1. **La ubicación física no es una elección de segmentación arbitraria** — es, estructuralmente, la variable dominante del dataset. Esto respalda organizar todo el dashboard principal alrededor de ella.
2. **Explica, desde los datos y no solo desde el conteo, por qué el Refrigerador concentra el 97% de la pérdida**: ahí vive el 92% de los eventos porque ahí vive la categoría más grande y perecible (Frutas y Verduras), y esa categoría es también la más dispersa/heterogénea en el mapa PCA (mayor varianza interna que el resto).
3. Sirve de **advertencia metodológica**: como ubicación ≡ categoría en este dataset, cualquier hallazgo "por ubicación" es en realidad un hallazgo "por categoría de producto" — no se puede separar el efecto de "dónde se guarda" del efecto de "qué tipo de alimento es", porque en los datos simulados nunca varían por separado. Un dataset real de hogares (donde alguien podría guardar fruta en la despensa) permitiría des-confundir ambos efectos.

## 7. Interpretación y límites
- La separación observada es principalmente por **categoría declarada** (una variable estructural/de catálogo), no por comportamiento de desperdicio: PCA/t-SNE no usan `classification` (si el evento fue consumo o merma), así que el mapa no muestra "clusters de riesgo de desperdicio" — muestra que la taxonomía de producto domina la varianza del espacio de features.
- t-SNE corre sobre una muestra (5,000/25,819); las distancias *globales* entre clusters en el mapa t-SNE no son interpretables (solo la vecindad local lo es).
- El dataset proviene de una simulación calibrada (patrones Instacart + nutrición USDA/OpenFoodFacts): los clusters reflejan la estructura simulada, que en este caso es intencionalmente realista (los alimentos perecibles sí van al refrigerador en la vida real) pero no deja de ser sintética.
- PCA es lineal; relaciones no lineales solo aparecen en t-SNE.
- Reproducibilidad garantizada con `random_state=42` en todo el pipeline.

## 8. Integración a los dashboards
- **Dashboard HTML (Plotly):** el mapa PCA (PC1 vs PC2, muestra de 3,000 eventos coloreados por categoría) es una visualización real dentro de `tableau/Sem12_Dashboard_SmartKitchen.html` (sección "Componente avanzado"), con el hallazgo de negocio del §6 explicado en el mismo bloque — ya no es un anexo desconectado de la narrativa.
- **Tableau:** pestaña `Anexo Metodologico` del workbook (`tableau/Sem12_Dashboard_SmartKitchen.twb`), 3 hojas: "Mapa latente (PCA)" (scatter PC1×PC2 coloreado por ubicación), "Clusters t-SNE" (scatter tsne_1×tsne_2), "Energía retenida (PCA)" (Pareto de varianza acumulada con referencia en 90%). Fuentes: `outputs/pca_components_tableau.csv`, `outputs/tsne_sample_tableau.csv`, `outputs/pca_variance_table.csv`.

## 9. Reproducibilidad
```bash
python src/features.py    # genera data/features/feature_matrix.npy
python src/reduction.py   # genera figuras + exportables (outputs/*_tableau.csv)
python src/build_dashboard_html.py   # integra el mapa PCA al dashboard HTML
python tableau/build_dashboard_twb.py  # integra las 3 hojas PCA/t-SNE al workbook Tableau
# notebooks/04_componente_avanzado.ipynb documenta y visualiza el análisis paso a paso
```

# Guía de Ejecución y Reproducibilidad (Runbook) - SKI Project

Este documento detalla los pasos necesarios para reproducir el pipeline completo del
proyecto, desde la ingesta de datos crudos hasta la generación de los dashboards
finales en Plotly/HTML y Tableau (Entrega 6). Todos los comandos `python` se ejecutan
desde la **raíz del repo** (`proyecto-final/`), salvo donde se indique lo contrario.

## 1. Configuración del Entorno

### 1.1. Dependencias del Sistema
El pipeline requiere Python 3.9+ y las dependencias listadas en `requirements.txt`.

```bash
# Crear y activar un entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar las dependencias de Python
pip install -r requirements.txt
```

### 1.2. Configuración de Credenciales (Obligatorio)

El pipeline utiliza dos APIs que requieren autenticación:

1.  **Kaggle API:** Para descargar el dataset de Instacart. Asegúrate de tener tu archivo `kaggle.json` en `~/.kaggle/kaggle.json`. Consulta la [guía de Kaggle](https://www.kaggle.com/docs/api) para obtener tus credenciales.

2.  **USDA FoodData Central API:** Para enriquecer los datos con información nutricional.
    *   Crea un archivo llamado `.env` en la raíz del proyecto.
    *   Añade tu clave de API de la USDA (puedes obtener una [aquí](https://fdc.nal.usda.gov/api-key.html)) dentro del archivo de la siguiente manera:

    ```.env
    USDA_API_KEY="TU_CLAVE_API_AQUI"
    ```

## 2. Ejecución Completa del Pipeline de Datos

El pipeline se ejecuta en una secuencia de scripts y notebooks. Cada uno genera
artefactos que son consumidos por el siguiente. Ejecútalos en el orden indicado.

### Paso 1: Extracción de Patrones de Comportamiento
Este script descarga un dataset público de Instacart para extraer patrones realistas de compra (distribución por horas, productos más comunes).

```bash
python src/extract_patterns.py
```
*   **Entrada:** Dataset `yasserh/instacart-online-grocery-basket-analysis-dataset` de Kaggle.
*   **Salida:** `data/raw/instacart_patterns.json`

### Paso 2: Simulación Masiva de Movimientos
Usando los patrones extraídos, este script simula el comportamiento de múltiples hogares durante 90 días para generar un volumen de datos transaccionales significativo.

```bash
python src/simulation.py
```
*   **Entrada:** `data/raw/instacart_patterns.json`
*   **Salida:** `data/raw/movements_raw.csv` (25,819 eventos, 10 hogares, 90 días)

### Paso 3: Enriquecimiento del Catálogo con Datos Nutricionales
Este script toma los productos de la simulación y consulta la API de USDA para obtener datos nutricionales reales, construyendo el catálogo de productos.

```bash
python src/ingestion.py
```
*   **Entradas:** `data/raw/movements_raw.csv`, API de USDA.
*   **Salida:** `data/raw/catalog_raw.csv`

### Paso 4: Preprocesamiento y Limpieza (reglas P1–P6)
Unifica los movimientos simulados con el catálogo en un único dataset limpio, aplicando
6 reglas de calidad verificables (outliers calóricos, homologación de categoría/ubicación,
integridad referencial, tipos de dato explícitos, nulos estructurales de NutriScore,
deduplicación). Usa Polars para alto rendimiento.

```bash
python src/preprocessing.py
```
*   **Entradas:** `data/raw/movements_raw.csv`, `data/raw/catalog_raw.csv`.
*   **Salidas:** `data/interim/inventory_v1.csv` (25,819 × 17), `data/interim/transformations_log.json`.

**Copia a `data/processed/` (obligatoria):** los pasos 5 y 6 leen el dataset limpio desde
`data/processed/inventory_v1.csv` (ruta fija en `src/features.py` y `src/reduction.py`),
mientras que este script escribe en `data/interim/`. Sincroniza ambas copias antes de
continuar:

```bash
python -c "import shutil; shutil.copy('data/interim/inventory_v1.csv', 'data/processed/inventory_v1.csv')"
```

*Verificación de calidad opcional pero recomendada:* `notebooks/02_limpieza.ipynb`
reimplementa esta misma lógica de forma independiente en Pandas; debe producir
exactamente el mismo conteo de filas, nulos y distribución de categorías (ver
`docs/QA_validation.md` §9). También puedes ejercitar el pipeline contra datos
sintéticamente sucios con `python src/anomaly_injection.py --input data/raw/movements_raw.csv --output data/interim/movements_with_anomalies.csv --seed 42 --null_ratio 0.15` y luego `python src/preprocessing.py --input data/interim/movements_with_anomalies.csv` para confirmar que las reglas P1–P6 detectan y corrigen las anomalías inyectadas.

### Paso 5: Matriz de Características (61 dimensiones)
Construye la matriz de features (nutrición, one-hot de categoría, TF-IDF del nombre de
producto, hora/día) escalada con `StandardScaler`, insumo del componente avanzado.

```bash
python src/features.py
```
*   **Entrada:** `data/processed/inventory_v1.csv`.
*   **Salidas:** `data/features/feature_matrix.npy`, `data/features/feature_names.json`.

### Paso 6: Reducción de Dimensionalidad (PCA + t-SNE)
Componente avanzado (Entrega 6): PCA completo (varianza retenida) y t-SNE sobre una
muestra reproducible de 5,000 eventos (`random_state=42`).

```bash
python src/reduction.py
```
*   **Entradas:** `data/features/feature_matrix.npy`, `data/processed/inventory_v1.csv`.
*   **Salidas:**
    *   `reports/figures/pca_scree_plot.png`, `pca_scatter_2d.png`, `tsne_scatter_2d.png`
    *   `outputs/pca_components_tableau.csv`, `outputs/tsne_sample_tableau.csv`, `outputs/pca_variance_table.csv`

*Documentación narrada del mismo análisis, paso a paso:* `notebooks/04_componente_avanzado.ipynb` (no genera artefactos nuevos, solo documenta/visualiza).

### Paso 7: Modelado Predictivo (clasificación de desperdicio)
Entrena y compara Regresión Logística vs. Random Forest para clasificar eventos de
salida como `Consumption` vs. `Waste`/`Forced_Waste`, excluyendo `dias_para_vencer`
del entrenamiento (fuga de datos confirmada empíricamente). Es un notebook, no un script standalone.

```bash
jupyter nbconvert --to notebook --execute notebooks/03_modelo_metricas.ipynb --output 03_modelo_metricas.ipynb
```
*(equivalente a abrir el notebook y correr "Run All"; el kernel debe ejecutarse con cwd = `notebooks/` para que sus rutas relativas `../data/...` y `../outputs/...` resuelvan correctamente — es el comportamiento por defecto de `nbconvert`).*

*   **Entrada:** `data/interim/inventory_v1.csv`.
*   **Salidas:** `outputs/metricas_modelos.csv`, `outputs/eda_distribucion_target.png`, `outputs/lr_confusion_roc.png`, `outputs/rf_confusion_roc.png`, `outputs/rf_feature_importance.png`, `outputs/comparacion_roc.png`.

### Paso 8: Tablas Agregadas para Tableau (star schema)
Genera las tablas de hechos y agregados que alimentan ambos dashboards (KPIs por
hogar, series temporales, cruces ubicación×NutriScore, insights prescriptivos).

```bash
jupyter nbconvert --to notebook --execute notebooks/05_metricas_segmentos_tableau.ipynb --output 05_metricas_segmentos_tableau.ipynb
```

*   **Entrada:** `data/interim/inventory_v1.csv`.
*   **Salida:** `tableau/datos_finales/*.csv` + `kpi_global.json` + `qa_integridad.json` (fact table, agregados por categoría/ubicación/tiempo, segmentos de hogar, parámetros).

### Paso 9: Construcción de los Dashboards
Con los outputs de los pasos 6 y 8 listos, genera los dos entregables finales.

```bash
# Dashboard Plotly/HTML (autocontenido)
python src/build_dashboard_html.py

# Dashboard Tableau (.twb)
python tableau/build_dashboard_twb.py
```
*   **Entradas:** `tableau/datos_finales/*.csv`, `outputs/pca_components_tableau.csv`, `outputs/tsne_sample_tableau.csv`, `outputs/pca_variance_table.csv`.
*   **Salidas:** `tableau/Sem12_Dashboard_SmartKitchen.html`, `tableau/Sem12_Dashboard_SmartKitchen.twb`.

Para abrir el `.twb` en Tableau Desktop, hazlo desde la carpeta `tableau/` (usa rutas
relativas a `datos_finales/` y `../outputs/`) — detalles y el empaquetado final a
`.twbx` en `tableau/README.md`. Puedes validar la estructura del workbook sin abrir
Tableau con `python tableau/validate_twb.py`.

## 3. Resumen del Pipeline Completo

```
extract_patterns.py → simulation.py → ingestion.py → preprocessing.py
        ↓ (copiar a data/processed/)
   ┌────┴────┐
features.py   notebooks/03_modelo_metricas.ipynb (modelado)
   ↓
reduction.py
   ↓
notebooks/05_metricas_segmentos_tableau.ipynb (tablas Tableau)
   ↓
build_dashboard_html.py  +  tableau/build_dashboard_twb.py
```

# Diccionario de datos — inventory_v1.csv (Entrega 2, pipeline revisado)

> Refleja la estructura real del dataset analítico tras el pipeline de limpieza v2.
> Ejecución: 2026-05-02 | Esquema: multi-hogar v2 (10 hogares, 90 días)

---

## Arquitectura y Modelado de Datos

Para la estructuración del dataset analítico final (`inventory_v1.csv`), el equipo evaluó tres paradigmas tradicionales de arquitectura de almacenamiento: **Modelo en Estrella (Star Schema)**, **Modelo en Copo de Nieve (Snowflake Schema)** y **Tabla Plana (Flat Table / Completamente Desnormalizado)**.

Se seleccionó el enfoque de **Tabla Plana (Flat Table)** mediante un proceso de desnormalización masiva empleando un `left join` nativo en Polars que acopla los hechos de inventario con las dimensiones de catálogo. Esta decisión arquitectónica se fundamenta en las siguientes limitaciones y ventajas técnicas:
* **Eliminación del Join Overhead en Tableau:** Al consolidar los datos en una sola entidad física, se evita que la herramienta de visualización tenga que resolver relaciones lógicas complejas en tiempo de ejecución, maximizando la velocidad de respuesta y renderizado del motor en memoria *Hyper* de Tableau.
* **Consistencia de Granularidad:** Al colapsar los hechos transaccionales y las dimensiones nutricionales de la USDA en una sola matriz ancha, se previenen errores de agregación asimétrica (duplicidad de registros) al construir campos calculados jerárquicos o realizar agrupaciones de promedios continuos por hogar.
* **Compatibilidad de Machine Learning:** Disponer de una estructura *Flat* unificada a nivel transaccional facilita la extracción directa de vectores numéricos estructurados para el pipeline de *feature engineering* e ingeniería de características requerida por los modelos predictivos de desperdicio.

---

## Tabla: `catalog_raw.csv` (Dimensión Producto)

**Registros:** 50 productos únicos.

| Columna | Tipo | Observaciones |
|---|---|---|
| `product_id` | Int64 | Identificador único del producto (PK). Instacart ID. |
| `product_name` | string | Nombre descriptivo del alimento. |
| `category` | Int64 | Instacart department_id (4=Produce, 16=Dairy, 7=Beverages, 3=Bakery, 1=Pantry, 20=Frozen). Requiere mapeo a category_name. |
| `nutriscore` | char | Calificación A-E. 7 productos con 'Falta Dato' convertidos a null en pipeline. |
| `calories_100g` | Float64 | Contenido energético (kcal/100g). Umbral de outlier: 900 kcal. |
| `proteins_100g` | Float64 | Gramos de proteína por cada 100g. |
| `carbs_100g` | Float64 | Gramos de carbohidratos por cada 100g. |

---

## Tabla: `movements_raw.csv` (Hechos de Inventario)

**Registros:** 25,819 eventos. 10 hogares x 90 días (Feb-May 2026).

| Columna | Tipo | Observaciones |
|---|---|---|
| `event_id` | string | UUID único del movimiento (PK). |
| `household_id` | Int64 | ID del hogar (0-9). Dimensión social del análisis multi-hogar. |
| `stock_id` | string | ID de la unidad física en inventario (permite rastrear lotes). |
| `product_id` | Int64 | Clave foránea al catálogo (FK). |
| `product_name` | string | Nombre del producto (desnormalizado para trazabilidad). |
| `event_type` | Categorical | Tipo de acción: IN (entrada/compra) / OUT (salida). |
| `quantity` | Int64 | Cantidad de unidades afectadas en el evento. |
| `timestamp` | Datetime | Fecha y hora exacta del evento (resolución de minutos). |
| `expiry_date` | Date | Fecha de vencimiento del producto. Presente en todos los eventos. |
| `classification` | Categorical | Motivo detallado: Purchase / Consumption / Waste / Forced_Waste. |

---

## Tabla: `inventory_v1.csv` (Dataset Analítico Final)

**Registros:** 25,819 filas x 17 columnas.  
Resultado del join movements <- catalog (left join en product_id) con columnas derivadas.

| Columna | Tipo | Origen | Observaciones |
|---|---|---|---|
| `event_id` | string | movements | PK del evento. |
| `household_id` | Int64 | movements | Hogar simulado (0-9). |
| `stock_id` | string | movements | Lote físico del producto. |
| `product_id` | Int64 | movements/catalog | FK de unión. |
| `product_name` | string | movements | Nombre del producto. |
| `action_type` | string | **Derivada** | Alias normalizado de event_type (IN/OUT). |
| `quantity` | Int64 | movements | Unidades del evento. |
| `timestamp` | Datetime | movements | Fecha y hora del evento. |
| `expiry_date` | Date | movements | Fecha de vencimiento. |
| `classification` | Categorical | movements | Purchase / Consumption / Waste / Forced_Waste. |
| `location` | string | **Derivada P2** | Ubicación física derivada del department_id: Refrigerador / Estante / Despensa. |
| `category_name` | string | **Derivada P2** | Nombre legible de categoría (6 valores): Frutas y Verduras / Lácteos y Refrigerados / Bebidas / Panadería y Granos / Despensa General / Congelados. |
| `dias_para_vencer` | Int64 | **Derivada** | expiry_date - timestamp en días. Positivo = fresco; negativo = vencido al momento del evento. |
| `nutriscore` | char | catalog | A/B/C/D/E o null (7 productos sin dato). |
| `calories_100g` | Float64 | catalog | Kcal por 100g. |
| `proteins_100g` | Float64 | catalog | Gramos de proteína por 100g. |
| `carbs_100g` | Float64 | catalog | Gramos de carbohidratos por 100g. |

### Distribución clave

| Campo | Distribución |
|---|---|
| action_type | IN: 11,581 (44.9%) / OUT: 14,238 (55.1%) |
| classification | Purchase: 11,581 / Consumption: 9,185 / Forced_Waste: 3,531 / Waste: 1,522 |
| location | Refrigerador: 23,758 / Despensa: 1,053 / Estante: 1,008 |
| category_name | Frutas y Verduras: 20,481 / Lácteos: 2,753 / Panadería: 564 / Bebidas: 1,008 / Congelados: 524 / Despensa: 489 |
| nutriscore nulos | 3,576 eventos (7 productos sin calificación) |
| eventos vencidos | 5,053 (dias_para_vencer < 0) |

### Conectividad con Tableau

Conectar como Text File. Tipos detectados automáticamente gracias al cast explícito del pipeline:  
product_id/household_id/quantity como Number (whole), timestamp como Date & Time,  
expiry_date como Date, action_type/classification/location/category_name/nutriscore como String,  
calories_100g/proteins_100g/carbs_100g como Number (decimal), dias_para_vencer como Number (whole).

---

## Trazabilidad de fuente

| Capa | Origen |
|---|---|
| Catálogo nutricional | OpenFoodFacts (API REST pública, ODbL) |
| Patrones de compra | Dataset público de Instacart (top 50 productos, distribución horaria) |
| Movimientos simulados | src/simulation.py — simulación multi-hogar estocástica (FoodKeeper shelf-life) |
| Limpieza y derivadas | src/preprocessing.py + notebooks/02_limpieza.ipynb |
| Registro de transformaciones | data/interim/transformations_log.json |
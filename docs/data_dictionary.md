# Diccionario de datos — inventory_v1.csv (Entrega 2, pipeline revisado)

> Refleja la estructura real del dataset analitico tras el pipeline de limpieza v2.
> Ejecucion: 2026-05-02 | Esquema: multi-hogar v2 (10 hogares, 90 dias)

---

## Tabla: `catalog_raw.csv` (Dimension Producto)

**Registros:** 50 productos unicos.

| Columna | Tipo | Observaciones |
|---|---|---|
| `product_id` | Int64 | Identificador unico del producto (PK). Instacart ID. |
| `product_name` | string | Nombre descriptivo del alimento. |
| `category` | Int64 | Instacart department_id (4=Produce, 16=Dairy, 7=Beverages, 3=Bakery, 1=Pantry, 20=Frozen). Requiere mapeo a category_name. |
| `nutriscore` | char | Calificacion A-E. 7 productos con 'Falta Dato' convertidos a null en pipeline. |
| `calories_100g` | Float64 | Contenido energetico (kcal/100g). Umbral de outlier: 900 kcal. |
| `proteins_100g` | Float64 | Gramos de proteina por cada 100g. |
| `carbs_100g` | Float64 | Gramos de carbohidratos por cada 100g. |

---

## Tabla: `movements_raw.csv` (Hechos de Inventario)

**Registros:** 25,819 eventos. 10 hogares x 90 dias (Feb-May 2026).

| Columna | Tipo | Observaciones |
|---|---|---|
| `event_id` | string | UUID unico del movimiento (PK). |
| `household_id` | Int64 | ID del hogar (0-9). Dimension social del analisis multi-hogar. |
| `stock_id` | string | ID de la unidad fisica en inventario (permite rastrear lotes). |
| `product_id` | Int64 | Clave foranea al catalogo (FK). |
| `product_name` | string | Nombre del producto (desnormalizado para trazabilidad). |
| `event_type` | Categorical | Tipo de accion: IN (entrada/compra) / OUT (salida). |
| `quantity` | Int64 | Cantidad de unidades afectadas en el evento. |
| `timestamp` | Datetime | Fecha y hora exacta del evento (resolucion de minutos). |
| `expiry_date` | Date | Fecha de vencimiento del producto. Presente en todos los eventos. |
| `classification` | Categorical | Motivo detallado: Purchase / Consumption / Waste / Forced_Waste. |

---

## Tabla: `inventory_v1.csv` (Dataset Analitico Final)

**Registros:** 25,819 filas x 17 columnas.
Resultado del join movements <- catalog (left join en product_id) con columnas derivadas.

| Columna | Tipo | Origen | Observaciones |
|---|---|---|---|
| `event_id` | string | movements | PK del evento. |
| `household_id` | Int64 | movements | Hogar simulado (0-9). |
| `stock_id` | string | movements | Lote fisico del producto. |
| `product_id` | Int64 | movements/catalog | FK de union. |
| `product_name` | string | movements | Nombre del producto. |
| `action_type` | string | **Derivada** | Alias normalizado de event_type (IN/OUT). |
| `quantity` | Int64 | movements | Unidades del evento. |
| `timestamp` | Datetime | movements | Fecha y hora del evento. |
| `expiry_date` | Date | movements | Fecha de vencimiento. |
| `classification` | Categorical | movements | Purchase / Consumption / Waste / Forced_Waste. |
| `location` | string | **Derivada P2** | Ubicacion fisica derivada del department_id: Refrigerador / Estante / Despensa. |
| `category_name` | string | **Derivada P2** | Nombre legible de categoria (6 valores): Frutas y Verduras / Lacteos y Refrigerados / Bebidas / Panaderia y Granos / Despensa General / Congelados. |
| `dias_para_vencer` | Int64 | **Derivada** | expiry_date - timestamp en dias. Positivo = fresco; negativo = vencido al momento del evento. |
| `nutriscore` | char | catalog | A/B/C/D/E o null (7 productos sin dato). |
| `calories_100g` | Float64 | catalog | Kcal por 100g. |
| `proteins_100g` | Float64 | catalog | Gramos de proteina por 100g. |
| `carbs_100g` | Float64 | catalog | Gramos de carbohidratos por 100g. |

### Distribucion clave

| Campo | Distribucion |
|---|---|
| action_type | IN: 11,581 (44.9%) / OUT: 14,238 (55.1%) |
| classification | Purchase: 11,581 / Consumption: 9,185 / Forced_Waste: 3,531 / Waste: 1,522 |
| location | Refrigerador: 23,758 / Despensa: 1,053 / Estante: 1,008 |
| category_name | Frutas y Verduras: 20,481 / Lacteos: 2,753 / Panaderia: 564 / Bebidas: 1,008 / Congelados: 524 / Despensa: 489 |
| nutriscore nulos | 3,576 eventos (7 productos sin calificacion) |
| eventos vencidos | 5,053 (dias_para_vencer < 0) |

### Conectividad con Tableau

Conectar como Text File. Tipos detectados automaticamente gracias al cast explicito del pipeline:
product_id/household_id/quantity como Number (whole), timestamp como Date & Time,
expiry_date como Date, action_type/classification/location/category_name/nutriscore como String,
calories_100g/proteins_100g/carbs_100g como Number (decimal), dias_para_vencer como Number (whole).

---

## Trazabilidad de fuente

| Capa | Origen |
|---|---|
| Catalogo nutricional | OpenFoodFacts (API REST publica, ODbL) |
| Patrones de compra | Dataset publico de Instacart (top 50 productos, distribucion horaria) |
| Movimientos simulados | src/simulation.py — simulacion multi-hogar estocastica (FoodKeeper shelf-life) |
| Limpieza y derivadas | src/preprocessing.py + notebooks/02_limpieza.ipynb |
| Registro de transformaciones | data/interim/transformations_log.json |

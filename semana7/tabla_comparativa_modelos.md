# Tabla Comparativa de Modelos Analíticos
## Smart Kitchen Intelligence (SKI) — Entrega 3 | Semana 7

**Problema:** Clasificación binaria — predicción de desperdicio alimentario en eventos de salida  
**Target:** `is_waste` (1 = Waste / Forced_Waste, 0 = Consumption)  
**Dataset:** `inventory_v1.csv` — subconjunto de eventos OUT (14,238 registros)  
**Fecha de ejecución:** 2026-05-15 | seed=42, split 80/20 estratificado, CV 5-fold

> **Nota metodológica:** `dias_para_vencer` fue excluida de los features tras verificar leakage.
> El simulador asignó Forced_Waste y Waste con `dias_para_vencer < 0` por construcción,
> haciendo que cualquier modelo alcanzara F1=1.0 y AUC=1.0 trivialmente.
> Las métricas a continuación corresponden al modelo sin esa variable — resultado honesto y reproducible.

---

## Comparación de modelos

| Criterio | Regresión Logística (baseline) | Random Forest (principal) |
|---|---|---|
| **Tipo** | Modelo lineal generalizado (GLM) | Ensemble de árboles de decisión (Bagging) |
| **Complejidad** | Baja — un plano de decisión lineal | Alta — 200 árboles con `max_depth=12` |
| **Interpretabilidad** | Alta — coeficientes directamente interpretables | Media — importancia de features disponible (Gini) |
| **Ventajas** | Rápido, coeficientes interpretables, bajo riesgo de sobreajuste, buen baseline estadístico | Captura interacciones no lineales, robusto ante nulos residuales, importancia de features nativa |
| **Desventajas** | Asume linealidad — insuficiente para capturar interacciones entre `category_name` × `location` × `quantity` | Mayor costo computacional; caja negra a nivel de predicción individual |
| **Requiere escalado** | Sí — `StandardScaler` obligatorio | No — árboles son invariantes a escala |
| **Accuracy** | 0.5779 | 0.5506 |
| **Precision** | 0.4309 | 0.4159 |
| **Recall** | 0.5895 | **0.6578** ✓ |
| **F1-Score** *(métrica primaria)* | 0.4979 | **0.5096** ✓ |
| **ROC-AUC** | **0.6231** | 0.6181 |
| **F1 CV 5-fold** | 0.4904 ± 0.0165 | **0.5027 ± 0.0071** ✓ |
| **Decisión** | **Descartado como modelo final.** Útil como referencia de piso. | **Seleccionado como modelo final.** |
| **Motivo de selección / descarte** | LR asume linealidad entre features y log-odds. La relación entre `category_name`, `quantity` y desperdicio es inherentemente no lineal. Menor Recall y mayor varianza en CV confirman su debilidad. | RF supera en F1 (+2.3%), Recall (+11.6%) y estabilidad CV (std 0.007 vs 0.016). El mayor Recall es el criterio definitivo: en el contexto de pérdidas alimentarias, los falsos negativos (pérdidas no detectadas) son más costosos que los falsos positivos. |

---

## Features más predictivas — Random Forest

| Rango | Feature | Importancia (Gini) | Interpretación |
|---|---|---|---|
| 1 | `quantity` | 0.246 | La cantidad de unidades del evento es el predictor más relevante. Grandes cantidades en un OUT son más propensas a incluir desperdicio. |
| 2 | `category_name_Frutas y Verduras` | 0.243 | Frutas y verduras representan ~79% del dataset — su presencia domina el modelo. |
| 3 | `location_Refrigerador` | 0.078 | La ubicación en refrigerador concentra la mayoría de los eventos (92%). |
| 4 | `carbs_100g` | 0.075 | Los carbohidratos discriminan entre tipos de productos (lácteos vs frutas). |
| 5 | `category_name_Bebidas` | 0.074 | Las bebidas tienen perfil nutricional y patrón de consumo diferenciado. |

---

## Justificación de métricas

| Métrica | Por qué es relevante |
|---|---|
| **F1-Score** *(primaria)* | Balancea Precision y Recall sin privilegiar la clase mayoritaria (64.5% Consumo). Adecuada ante desbalance de clases. |
| **ROC-AUC** | Capacidad discriminante independiente del umbral. Permite comparar modelos sin fijar un punto de corte. |
| **Recall** | Detectar pérdidas reales es prioritario en el dominio. Un falso negativo (pérdida no detectada) tiene mayor costo operativo que un falso positivo (alerta falsa). |
| **Precision** | Complementa Recall para evitar un modelo que clasifique todo como desperdicio. |
| **Accuracy** | Reportada por completitud — **no es la métrica de selección** porque un clasificador trivial (siempre predice Consumo) obtendría ~64.5% de accuracy sin detectar ninguna pérdida. |

---

## Interpretación del rendimiento moderado

Los modelos obtienen F1 ≈ 0.50 y AUC ≈ 0.62, lo que es **esperado y metodológicamente correcto** por dos razones:

1. **La variable más predictiva fue excluida por leakage**: `dias_para_vencer` trivializaba el problema. Sin ella, los modelos aprenden del perfil nutricional, categoría y cantidad — que tienen relación más débil con el desperdicio en datos sintéticos.
2. **Los datos son simulados**: el simulador asignó desperdicio con reglas simples (fecha de vencimiento). En datos reales, variables como frecuencia de compra del hogar, temperatura de almacenamiento o historial previo añadirían señal real.

**El rendimiento moderado no es un defecto** — es la respuesta honesta del modelo a features que explican parcialmente el fenómeno. Declararlo explícitamente es una práctica de ciencia de datos rigurosa.

---

## Notas de reproducibilidad

- `random_state=42`, `stratify=y` en el split, `cross_val_score(cv=5)`
- `class_weight='balanced'` en ambos modelos para compensar el desbalance de clases
- `OrdinalEncoder` con `unknown_value=-1` (fuera del rango 0–4 para evitar colisión con categorías conocidas)
- Pipeline completo reproducible: `notebooks/03_modelo_metricas.ipynb`
- Métricas exportadas: `outputs/metricas_modelos.csv`

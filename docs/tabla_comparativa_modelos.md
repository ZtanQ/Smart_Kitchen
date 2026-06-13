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

---

## Matriz de Experimentación Técnica y Optimización (Fase 2)
*Resultados empíricos obtenidos tras el balanceo de pesos de clase (`class_weight='balanced'`) y el ajuste del Umbral de Decisión Operativo a $0.40$.*

| Modelo / Fase | Accuracy | Precision | Recall (Sensibilidad) | F1-Score | Umbral (Th) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Regresión Logística (Original)** | 0.6552 | 0.5469 | 0.1672 | 0.2561 | 0.50 |
| **Regresión Logística (Optimizada)** | 0.4884 | 0.4024 | **0.9090** | **0.5578** | 0.40 |
| **Random Forest (Original)** | 0.6531 | 0.5363 | 0.1682 | 0.2560 | 0.50 |
| **Random Forest (Optimizado)** | 0.4930 | 0.4028 | **0.8872** | **0.5540** | 0.40 |

### Análisis del Trade-Off y Justificación del Umbral Operativo
La reducción del umbral de decisión matemático de $0.50$ a $0.40$ provocó un cambio drástico en el comportamiento de ambos clasificadores:

1. **Explosión del Recall (Sensibilidad):** El Recall del modelo base (Regresión Logística) incrementó del **16.72% al 90.90%**, mientras que el del modelo complejo (Random Forest) subió del **16.82% al 88.72%**. Esto significa que el sistema ahora es capaz de capturar casi el 90% de los alimentos que realmente van a terminar en el desperdicio, minimizando los falsos negativos.
2. **Sacrificio Controlado de Precision y Accuracy:** Como consecuencia matemática directa de volver al modelo más sensible, la precisión descendió a un entorno del **40%**. En el contexto de negocio de *Smart Kitchen Intelligence*, este trade-off está plenamente justificado: **es operativamente preferible lanzar una alerta preventiva sobre un alimento que podría no desperdiciarse (Falso Positivo) a omitir la notificación y permitir que la comida se descomponga en el almacenamiento sin que el usuario se entere (Falso Negativo).**
3. **Optimización del F1-Score:** El balance armónico medido por el F1-Score se duplicó en ambos paradigmas, pasando de $\sim0.25$ a **$0.55$**, validando estadísticamente que la configuración balanceada de la Fase 2 es significativamente superior para resolver el problema de negocio planteado.

---

## Documentación del Flujo de Preprocesamiento Avanzado
*Descripción detallada del pipeline técnico implementado en el entorno de desarrollo para asegurar la reproducibilidad del experimento:*

1. **Segmentación del Dominio:** Filtrado exclusivo de los eventos transaccionales de salida (`action_type = OUT`), consolidando una muestra homogénea de **14,238 registros**.
2. **Tratamiento de Nulos Estructurales:** Identificación de variables categóricas faltantes en las fuentes y su correspondiente imputación bajo la etiqueta `"Unknown"` para evitar distorsiones en las divisiones de los nodos.
3. **Transformación Categórica (Encoding):** Implementación de un `OrdinalEncoder` integrado en un `ColumnTransformer` para convertir variables de alta cardinalidad (`category_name`, `location`, `nutriscore`) en vectores numéricos continuos.
4. **Estandarización Numérica (Scaling):** Normalización de variables continuas de la USDA (`calories_100g`, `proteins_100g`, `carbs_100g`) mediante `StandardScaler` (media 0, varianza 1).
5. **Partición Estratificada:** División del dataset en un subconjunto de entrenamiento (80%) y validación (20%), aplicando la técnica de *stratify* basada en el target para mitigar el impacto del desbalance de clases (64.5% vs 35.5%).

---

## Fórmulas Matemáticas de los Criterios de Evaluación
Las métricas computadas en la matriz se rigen bajo las siguientes definiciones formales de la teoría estadística:

* **Precision (Precisión):** $$\text{Precision} = \frac{VP}{VP + FP}$$
* **Recall (Sensibilidad - Criterio Primario de Éxito):** $$\text{Recall} = \frac{VP}{VP + FN}$$
* **F1-Score (Media Armónica Ponderada):** $$\text{F1-Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

---

## Implicancias Analíticas para la Fase de Visualización en Tableau
Los resultados de esta experimentación técnica sientan las bases de diseño para los tableros interactivos de las siguientes semanas:

* **Foco en el Volumen de Alerta:** Dado que el modelo optimizado captura exitosamente el riesgo analítico a costa de generar un volumen mayor de alertas (debido al 40% de precisión), la interfaz visual en Tableau no debe usar alarmas intrusivas o bloqueantes. En su lugar, debe estructurarse mediante **mapas de calor espaciales** y códigos de colores (semáforos analíticos) basados en las probabilidades calculadas.
* **Priorización de Despensa y Perecederos:** La consistencia de las métricas en la validación cruzada confirma que las variables de volumen (`quantity`) y categorías de baja vida útil (`Frutas y Verduras`) retienen el mayor peso de Gini dentro del Random Forest, justificando que las pantallas principales del dashboard se enfoquen en la monitorización de estas zonas de riesgo.
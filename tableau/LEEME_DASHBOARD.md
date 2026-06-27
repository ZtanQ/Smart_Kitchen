# Dashboard Smart Kitchen Intelligence — guía rápida

Pregunta central: **¿Qué impacto tiene la ubicación física en la pérdida económica y de salud del hogar?**

## Archivos clave

- `Sem12_Dashboard_SmartKitchen.twb` — workbook nuevo, alineado al PDF `plan_accion_dashboard_redisenado.pdf`.
- `Sem12_Dashboard_SmartKitchen.twb.bak` — backup del workbook anterior (solo PCA/t-SNE).
- `build_dashboard_twb.py` — generador reproducible del `.twb`. Re-ejecutar si cambian los CSVs.
- `datos_finales/` — fuente única de verdad para los 4 KPIs, gráficos y panel de insights.

## Estructura del workbook

7 datasources, 11 worksheets, 2 dashboards.

### Datasources (CSV)
| Fuente | Para qué sirve |
|---|---|
| `kpi_por_hogar.csv` | Alimenta los 4 BANs y la tabla por hogar |
| `agg_temporal_ubicacion.csv` | Gráfico longitudinal (Costo perdido x semana_iso, una línea por ubicación) |
| `agg_ubicacion_nutriscore.csv` | Gráfico transversal (Ubicación × Nutriscore, consumo vs desperdicio) |
| `insights_prescriptivos.csv` | Panel lateral derecho con acciones automáticas por hogar |
| `tsne_sample_tableau.csv`, `pca_components_tableau.csv`, `pca_variance_table.csv` | Solo para el dashboard anexo "Componente Avanzado" |

### Worksheets
- **BAN1 — Mermas en Despensa (S/)** → `SUM(kpi1_costo_perdido_soles)`
- **BAN2 — Tasa Desperdicio Físico (%)** → `AVG(kpi2_tasa_desperdicio)`
- **BAN3 — Nutriscore Crítico D-E (%)** → `AVG(kpi3_pct_nutriscore_DE)`
- **BAN4 — Estancamiento Medio (días)** → `AVG(kpi4_dias_prom_vencer)`
- **Longitudinal - Costo por Ubicación** → línea por `location`, eje X `semana_iso`, eje Y `SUM(costo_perdido)`
- **Transversal - Ubicación x Nutriscore** → barras por `location` × `tipo_salida`, color `nutriscore_grupo`
- **KPIs por Hogar** → tabla de los 10 hogares con sus 4 KPIs
- **Insights Prescriptivos** → texto dinámico de los 3 ejes prescriptivos
- **Clusters t-SNE / Mapa latente (PCA) / Energía retenida (PCA)** → solo en dashboard anexo

### Dashboards
1. **Smart Kitchen Intelligence** (principal, 1500×980): franja de 4 BANs arriba, gráfico longitudinal + insights al medio, gráfico transversal + tabla por hogar abajo.
2. **Componente Avanzado (PCA y t-SNE)** (anexo, 1500×900): los 3 sheets del modelo, fuera del flujo principal.

## Cómo abrirlo

1. Abrir `Sem12_Dashboard_SmartKitchen.twb` en **Tableau Desktop 2026.2** o superior.
2. Al primer load: si algún CSV pide reubicarse, apuntar a `tableau/datos_finales/` (rutas absolutas Windows incrustadas).
3. Ir a la pestaña **Smart Kitchen Intelligence**.

## Qué ajustar manualmente en Tableau

El generador deja la estructura y los encodings base. En Desktop conviene pulir:
- Aplicar un **filtro global de `household_id`** (clic derecho en el campo → Apply to Worksheets → "Use This Data Source").
- Formato numérico de los BANs: BAN1 como `S/ #,##0`; BAN2 y BAN3 como `0.0%`; BAN4 como `0.0 "días"`.
- Paleta semáforo en `nutriscore_grupo` (Saludable verde, Crítico ámbar, Riesgo D-E rojo).
- Etiquetas en líneas del gráfico longitudinal (al final de cada serie).
- Tooltip enriquecido en la matriz transversal (incluir `unidades` y `costo`).

## Si los datos cambian

```bash
cd tableau
python build_dashboard_twb.py
```

Esto:
1. Regenera `insights_prescriptivos.csv` desde `kpi_por_hogar.csv`.
2. Sobrescribe `Sem12_Dashboard_SmartKitchen.twb` (deja backup `.twb.bak`).

## Qué se botó / qué se mantuvo

- **Sacado del dashboard principal**: PCA, t-SNE, "energía retenida", "mapa latente", "clusters". Eran artefactos internos del notebook de modelado — no respondían la pregunta de negocio. Se conservan en el dashboard anexo "Componente Avanzado" como soporte metodológico requerido por la rúbrica.
- **Incorporado**: los 4 KPIs definidos en el PDF, gráficos longitudinal y transversal, panel de insights prescriptivos, tabla por hogar.

# Tableau — Smart Kitchen Intelligence (SKI)

## Archivo canonico

**`Sem12_Dashboard_SmartKitchen.twb`** es el unico workbook vigente. Se genera con:

```bash
python tableau/build_dashboard_twb.py
```

Contiene:

- **11 hojas**: 4 BANs (KPIs), Longitudinal, Transversal, KPIs por Hogar, Insights
  Prescriptivos, Clusters t-SNE, Mapa latente (PCA), Energia retenida (PCA).
- **2 dashboards**: `Smart Kitchen Intelligence` (analisis principal, 3 bandas +
  KPIs) y `Anexo Metodologico` (PCA / t-SNE).
- **7 fuentes de datos**, todas con rutas **relativas** al `.twb` (portable entre
  maquinas): `datos_finales/*.csv` para las 4 fuentes de negocio y `../outputs/*.csv`
  para las 3 fuentes del componente avanzado (PCA/t-SNE).

Antes de abrir el `.twb` en Tableau Desktop, asegurate de que:
- `tableau/datos_finales/` contiene los 4 CSV de negocio (se generan con
  `notebooks/05_metricas_segmentos_tableau.ipynb`).
- `outputs/` (un nivel arriba de `tableau/`) contiene `pca_components_tableau.csv`,
  `tsne_sample_tableau.csv` y `pca_variance_table.csv` (se generan con `src/reduction.py`).

## Empaquetado final (.twbx) — paso manual pendiente

Este entorno no tiene Tableau Desktop instalado, así que **no se pudo generar ni
verificar visualmente un `.twbx` empaquetado** (requiere abrir el `.twb`, confirmar
que las 11 hojas y 2 dashboards renderizan correctamente, y usar
`Archivo > Exportar libro de trabajo empaquetado`). Antes de la entrega final:

1. Abrir `Sem12_Dashboard_SmartKitchen.twb` en Tableau Desktop.
2. Verificar que las 11 hojas cargan sin error de conexion (si Tableau se queja de
   una fuente de datos, revisa que las rutas relativas arriba se resuelvan bien
   desde tu maquina).
3. Revisar visualmente el dashboard principal y el anexo metodologico.
4. `Archivo > Exportar libro de trabajo empaquetado (.twbx)` para producir el
   entregable final.

Validacion automatica que SI se hizo (sin necesidad de Tableau Desktop): el XML del
`.twb` es bien formado, las 11 hojas referencian datasources existentes, cada campo
usado en filas/columnas/encodings existe en las columnas declaradas de su fuente de
datos real, y cada zona de los 2 dashboards apunta a una hoja que existe. Ver
`docs/QA_validation.md` para el detalle.

## `_archive/`

Contiene versiones descartadas/rotas del workbook conservadas solo por trazabilidad
historica (iteraciones previas, un intento "minimal" de debugging que sobrescribia
por error el archivo principal, y un `.twbx` empaquetado el 2026-06-12 que quedo
desactualizado — solo contenia las 3 hojas de PCA/t-SNE, sin el dashboard principal).
**No usar nada de esta carpeta para la entrega.**

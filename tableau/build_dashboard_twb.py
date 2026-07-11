"""
Generador del workbook Tableau Smart Kitchen Intelligence (SKI) — v2.
- Hojas componentes (BANs, charts, insights) OCULTAS por defecto.
- Solo 2 pestanas visibles al publico: Smart Kitchen Intelligence + Anexo Metodologico.
- Layout de 3 bandas + titulos contextuales dentro del lienzo.

Pregunta central: Que impacto tiene la ubicacion fisica en la perdida
economica y de salud del hogar?
"""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "datos_finales"
OUT_TWB = ROOT / "Sem12_Dashboard_SmartKitchen.twb"
# Rutas RELATIVAS a la ubicacion del .twb (portable entre maquinas/usuarios).
# Tableau resuelve 'directory' de una conexion textscan relativo al archivo .twb
# cuando no es una ruta absoluta. Requiere abrir el .twb desde tableau/ con
# datos_finales/ como hermano y outputs/ un nivel arriba (estructura del repo).
WIN_DATA_DIR = "datos_finales"
WIN_OUTPUTS_DIR = "../outputs"


# ---------------------------------------------------------------------------
# 1. CSV de insights prescriptivos por hogar
# ---------------------------------------------------------------------------
def build_insights_csv() -> Path:
    kpi_path = DATA_DIR / "kpi_por_hogar.csv"
    out = DATA_DIR / "insights_prescriptivos.csv"
    rows_out = []
    with open(kpi_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            hid = r["household_id"]
            seg = r["segmento_hogar"]
            ub = r["ubicacion_critica"]
            costo = float(r["kpi1_costo_perdido_soles"])
            tasa = float(r["kpi2_tasa_desperdicio"]) * 100
            nutri = float(r["kpi3_pct_nutriscore_DE"]) * 100
            dias = float(r["kpi4_dias_prom_vencer"])
            rows_out.append({
                "household_id": hid, "segmento_hogar": seg,
                "eje": "1. Mitigacion Financiera", "orden": 1,
                "titulo": "Punto ciego de perdida",
                "mensaje": (
                    f"El {ub} concentra S/ {costo:,.0f} de mermas acumuladas (KPI1). "
                    f"Trasladar productos con <10 dias para vencer al Estante de Alta Visibilidad."
                ),
            })
            rows_out.append({
                "household_id": hid, "segmento_hogar": seg,
                "eje": "2. Optimizacion de Compras", "orden": 2,
                "titulo": "Ajuste de abastecimiento",
                "mensaje": (
                    f"Tasa desperdicio fisico = {tasa:.1f}% (KPI2). "
                    f"Reducir 15% el volumen de Lacteos y Carnes en el proximo ciclo semanal."
                ),
            })
            rows_out.append({
                "household_id": hid, "segmento_hogar": seg,
                "eje": "3. Gestion de Salud Familiar", "orden": 3,
                "titulo": "Calidad nutricional retenida",
                "mensaje": (
                    f"{nutri:.1f}% del desperdicio es Nutriscore D-E (KPI3) y estancamiento medio "
                    f"{dias:.1f} dias (KPI4). Sustituir ultraprocesados por opciones A-B."
                ),
            })
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["household_id", "segmento_hogar", "eje", "orden", "titulo", "mensaje"])
        w.writeheader()
        w.writerows(rows_out)
    return out


# ---------------------------------------------------------------------------
# 2. Plantillas XML
# ---------------------------------------------------------------------------
def stable_id(prefix: str, key: str) -> str:
    h = hashlib.sha1(key.encode()).hexdigest()[:24]
    return f"{prefix}.{h}"


def col_meta(name, dtype, ordinal, parent, obj_id):
    agg = {"integer": "Sum", "real": "Sum", "string": "Count", "datetime": "Count"}.get(dtype, "Count")
    remote_type = {"integer": "20", "real": "5", "string": "129", "datetime": "7"}.get(dtype, "129")
    scale = "<scale>1</scale>" if dtype == "string" else ""
    width = "<width>1073741823</width>" if dtype == "string" else ""
    return (
        f"        <metadata-record class='column'>\n"
        f"          <remote-name>{name}</remote-name>\n"
        f"          <remote-type>{remote_type}</remote-type>\n"
        f"          <local-name>[{name}]</local-name>\n"
        f"          <parent-name>{parent}</parent-name>\n"
        f"          <remote-alias>{name}</remote-alias>\n"
        f"          <ordinal>{ordinal}</ordinal>\n"
        f"          <local-type>{dtype}</local-type>\n"
        f"          <aggregation>{agg}</aggregation>\n"
        f"          {scale}{width}\n"
        f"          <contains-null>true</contains-null>\n"
        f"          <object-id>{obj_id}</object-id>\n"
        f"        </metadata-record>"
    )


def datasource_block(caption, filename, columns, directory=WIN_DATA_DIR):
    ds_name = stable_id("federated", caption)
    conn_name = stable_id("textscan", caption)
    rel_name = Path(filename).stem
    parent = f"[{rel_name}.csv]"
    obj_id = f"[{rel_name}.csv_{hashlib.md5(caption.encode()).hexdigest().upper()}]"
    col_xml = "\n".join(
        f"            <column datatype='{dt}' name='{n}' ordinal='{i}' />"
        for i, (n, dt) in enumerate(columns)
    )
    meta_xml = "\n".join(col_meta(n, dt, i, parent, obj_id) for i, (n, dt) in enumerate(columns))
    xml = (
        f"    <datasource caption='{caption}' inline='true' name='{ds_name}' version='18.1'>\n"
        f"      <connection class='federated'>\n"
        f"        <named-connections>\n"
        f"          <named-connection caption='{caption}' name='{conn_name}'>\n"
        f"            <connection class='textscan' directory='{directory}' filename='{filename}' password='' server='' />\n"
        f"          </named-connection>\n"
        f"        </named-connections>\n"
        f"        <relation connection='{conn_name}' name='{filename}' table='[{rel_name}#csv]' type='table'>\n"
        f"          <columns character-set='UTF-8' header='yes' locale='es_PE' separator=','>\n"
        f"{col_xml}\n"
        f"          </columns>\n"
        f"        </relation>\n"
        f"        <metadata-records>\n"
        f"{meta_xml}\n"
        f"        </metadata-records>\n"
        f"      </connection>\n"
        f"      <aliases enabled='yes' />\n"
        f"    </datasource>"
    )
    return xml, ds_name


# ---------------------------------------------------------------------------
# 3. Definicion de fuentes
# ---------------------------------------------------------------------------
DS_DEFS = {
    "kpi_por_hogar": ("kpi_por_hogar.csv", [
        ("household_id", "integer"), ("segmento_hogar", "string"),
        ("ubicacion_critica", "string"), ("kpi1_costo_perdido_soles", "real"),
        ("kpi2_tasa_desperdicio", "real"), ("kpi3_pct_nutriscore_DE", "real"),
        ("kpi4_dias_prom_vencer", "real"), ("total_eventos_out", "integer"),
        ("total_eventos_waste", "integer"), ("costo_total_perdido", "real"),
        ("costo_total_compras", "real"),
    ]),
    "agg_temporal_ubicacion": ("agg_temporal_ubicacion.csv", [
        ("household_id", "integer"), ("semana_iso", "string"), ("location", "string"),
        ("eventos_out", "integer"), ("eventos_waste", "integer"),
        ("eventos_consumo", "integer"), ("costo_perdido", "real"),
        ("costo_consumido", "real"), ("tasa_desperdicio", "real"),
    ]),
    "agg_ubicacion_nutriscore": ("agg_ubicacion_nutriscore.csv", [
        ("household_id", "integer"), ("location", "string"), ("nutriscore", "string"),
        ("nutriscore_grupo", "string"), ("tipo_salida", "string"),
        ("eventos", "integer"), ("costo", "real"), ("unidades", "integer"),
    ]),
    "insights_prescriptivos": ("insights_prescriptivos.csv", [
        ("household_id", "integer"), ("segmento_hogar", "string"), ("eje", "string"),
        ("orden", "integer"), ("titulo", "string"), ("mensaje", "string"),
    ]),
}

MODEL_DS = {
    "tsne_sample_tableau": ("tsne_sample_tableau.csv", [
        ("event_id", "string"), ("household_id", "integer"), ("product_name", "string"),
        ("action_type", "string"), ("category_name", "string"), ("location", "string"),
        ("nutriscore", "string"), ("timestamp", "datetime"),
        ("dias_para_vencer", "integer"), ("calories_100g", "real"),
        ("tsne_1", "real"), ("tsne_2", "real"),
    ]),
    "pca_components_tableau": ("pca_components_tableau.csv", [
        ("event_id", "string"), ("household_id", "integer"), ("product_name", "string"),
        ("action_type", "string"), ("category_name", "string"), ("location", "string"),
        ("nutriscore", "string"), ("timestamp", "datetime"), ("dias_para_vencer", "integer"),
        ("calories_100g", "real"), ("PC1", "real"), ("PC2", "real"), ("PC3", "real"),
    ]),
    "pca_variance_table": ("pca_variance_table.csv", [
        ("componente", "string"), ("varianza_explicada", "real"),
        ("varianza_acumulada", "real"),
    ]),
}


# ---------------------------------------------------------------------------
# 4. Worksheets
# ---------------------------------------------------------------------------
def ws_ban(name, ds, field, agg):
    return (
        f"    <worksheet name='{name}'>\n"
        f"      <table>\n"
        f"        <view>\n"
        f"          <datasources>\n"
        f"            <datasource caption='{name}' name='{ds}' />\n"
        f"          </datasources>\n"
        f"          <aggregation value='true' />\n"
        f"        </view>\n"
        f"        <style />\n"
        f"        <panes>\n"
        f"          <pane>\n"
        f"            <view><breakdown value='auto' /></view>\n"
        f"            <mark class='Text' />\n"
        f"            <encodings>\n"
        f"              <text column='[{ds}].[{agg}:{field}:qk]' />\n"
        f"            </encodings>\n"
        f"            <style>\n"
        f"              <style-rule element='mark-labels-pane'>\n"
        f"                <format attr='font-size' value='48' />\n"
        f"                <format attr='font-weight' value='bold' />\n"
        f"              </style-rule>\n"
        f"            </style>\n"
        f"          </pane>\n"
        f"        </panes>\n"
        f"        <rows />\n"
        f"        <cols />\n"
        f"      </table>\n"
        f"    </worksheet>"
    )


def ws_longitudinal(ds):
    return (
        f"    <worksheet name='Longitudinal - Costo por Ubicacion'>\n"
        f"      <table>\n"
        f"        <view>\n"
        f"          <datasources>\n"
        f"            <datasource caption='agg_temporal_ubicacion' name='{ds}' />\n"
        f"          </datasources>\n"
        f"          <aggregation value='true' />\n"
        f"        </view>\n"
        f"        <style />\n"
        f"        <panes>\n"
        f"          <pane>\n"
        f"            <view><breakdown value='auto' /></view>\n"
        f"            <mark class='Line' />\n"
        f"            <encodings>\n"
        f"              <color column='[{ds}].[location]' />\n"
        f"            </encodings>\n"
        f"          </pane>\n"
        f"        </panes>\n"
        f"        <rows>[{ds}].[sum:costo_perdido:qk]</rows>\n"
        f"        <cols>[{ds}].[none:semana_iso:nk]</cols>\n"
        f"      </table>\n"
        f"    </worksheet>"
    )


def ws_transversal(ds):
    return (
        f"    <worksheet name='Transversal - Ubicacion x Nutriscore'>\n"
        f"      <table>\n"
        f"        <view>\n"
        f"          <datasources>\n"
        f"            <datasource caption='agg_ubicacion_nutriscore' name='{ds}' />\n"
        f"          </datasources>\n"
        f"          <aggregation value='true' />\n"
        f"        </view>\n"
        f"        <style />\n"
        f"        <panes>\n"
        f"          <pane>\n"
        f"            <view><breakdown value='auto' /></view>\n"
        f"            <mark class='Bar' />\n"
        f"            <encodings>\n"
        f"              <color column='[{ds}].[nutriscore_grupo]' />\n"
        f"            </encodings>\n"
        f"          </pane>\n"
        f"        </panes>\n"
        f"        <rows>[{ds}].[location] / [{ds}].[tipo_salida]</rows>\n"
        f"        <cols>[{ds}].[sum:eventos:qk]</cols>\n"
        f"      </table>\n"
        f"    </worksheet>"
    )


def ws_tabla(ds):
    return (
        f"    <worksheet name='KPIs por Hogar'>\n"
        f"      <table>\n"
        f"        <view>\n"
        f"          <datasources>\n"
        f"            <datasource caption='kpi_por_hogar' name='{ds}' />\n"
        f"          </datasources>\n"
        f"          <aggregation value='true' />\n"
        f"        </view>\n"
        f"        <style />\n"
        f"        <panes>\n"
        f"          <pane>\n"
        f"            <view><breakdown value='auto' /></view>\n"
        f"            <mark class='Automatic' />\n"
        f"          </pane>\n"
        f"        </panes>\n"
        f"        <rows>[{ds}].[household_id] / [{ds}].[segmento_hogar]</rows>\n"
        f"        <cols>[{ds}].[Measure Names]</cols>\n"
        f"      </table>\n"
        f"    </worksheet>"
    )


def ws_insights(ds):
    return (
        f"    <worksheet name='Insights Prescriptivos'>\n"
        f"      <table>\n"
        f"        <view>\n"
        f"          <datasources>\n"
        f"            <datasource caption='insights_prescriptivos' name='{ds}' />\n"
        f"          </datasources>\n"
        f"          <aggregation value='true' />\n"
        f"        </view>\n"
        f"        <style />\n"
        f"        <panes>\n"
        f"          <pane>\n"
        f"            <view><breakdown value='auto' /></view>\n"
        f"            <mark class='Text' />\n"
        f"            <encodings>\n"
        f"              <text column='[{ds}].[mensaje]' />\n"
        f"            </encodings>\n"
        f"          </pane>\n"
        f"        </panes>\n"
        f"        <rows>[{ds}].[eje] / [{ds}].[titulo]</rows>\n"
        f"        <cols />\n"
        f"      </table>\n"
        f"    </worksheet>"
    )


def ws_scatter(name, ds, x_field, y_field, color_field):
    return (
        f"    <worksheet name='{name}'>\n"
        f"      <table>\n"
        f"        <view>\n"
        f"          <datasources>\n"
        f"            <datasource caption='{name}' name='{ds}' />\n"
        f"          </datasources>\n"
        f"          <aggregation value='true' />\n"
        f"        </view>\n"
        f"        <style />\n"
        f"        <panes>\n"
        f"          <pane>\n"
        f"            <view><breakdown value='auto' /></view>\n"
        f"            <mark class='Shape' />\n"
        f"            <encodings>\n"
        f"              <color column='[{ds}].[{color_field}]' />\n"
        f"            </encodings>\n"
        f"          </pane>\n"
        f"        </panes>\n"
        f"        <rows>[{ds}].[{y_field}]</rows>\n"
        f"        <cols>[{ds}].[{x_field}]</cols>\n"
        f"      </table>\n"
        f"    </worksheet>"
    )


def ws_bar_simple(name, ds, x_field, y_agg, y_field):
    return (
        f"    <worksheet name='{name}'>\n"
        f"      <table>\n"
        f"        <view>\n"
        f"          <datasources>\n"
        f"            <datasource caption='{name}' name='{ds}' />\n"
        f"          </datasources>\n"
        f"          <aggregation value='true' />\n"
        f"        </view>\n"
        f"        <style />\n"
        f"        <panes>\n"
        f"          <pane>\n"
        f"            <view><breakdown value='auto' /></view>\n"
        f"            <mark class='Bar' />\n"
        f"          </pane>\n"
        f"        </panes>\n"
        f"        <rows>[{ds}].[{y_agg}:{y_field}:qk]</rows>\n"
        f"        <cols>[{ds}].[none:{x_field}:nk]</cols>\n"
        f"      </table>\n"
        f"    </worksheet>"
    )


# ---------------------------------------------------------------------------
# 5. Dashboards
# ---------------------------------------------------------------------------
def build_main_dashboard():
    parts = []
    parts.append("    <dashboard enable-sort-zone-taborder='true' name='Smart Kitchen Intelligence'>")
    parts.append("      <style />")
    parts.append("      <size maxheight='1000' maxwidth='1500' minheight='1000' minwidth='1500' />")
    parts.append("      <zones>")
    parts.append("        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>")
    parts.append("          <zone-style>")
    parts.append("            <format attr='background-color' value='#f7f7fa' />")
    parts.append("            <format attr='margin' value='4' />")
    parts.append("          </zone-style>")

    # Banda 0 — Titulo
    parts += [
        "          <zone h='6000' id='10' type-v2='text' w='100000' x='0' y='0'>",
        "            <zone-style>",
        "              <format attr='background-color' value='#1d2b4f' />",
        "              <format attr='margin' value='8' />",
        "            </zone-style>",
        "            <formatted-text>",
        "              <run bold='true' fontsize='22' fontcolor='#ffffff'>SMART KITCHEN INTELLIGENCE (SKI)</run>",
        "            </formatted-text>",
        "          </zone>",
        "          <zone h='4500' id='11' type-v2='text' w='100000' x='0' y='6000'>",
        "            <zone-style>",
        "              <format attr='background-color' value='#2a3b6c' />",
        "              <format attr='margin' value='8' />",
        "            </zone-style>",
        "            <formatted-text>",
        "              <run italic='true' fontsize='13' fontcolor='#dfe4f2'>Pregunta: Que impacto tiene la ubicacion fisica (Refrigerador / Despensa / Estante) en la perdida economica y de salud del hogar?  --  10 hogares, 90 dias, 25,819 eventos.</run>",
        "            </formatted-text>",
        "          </zone>",
    ]

    # Banda 1 - encabezado + BANs
    parts += [
        "          <zone h='2500' id='20' type-v2='text' w='100000' x='0' y='10500'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "            <formatted-text><run bold='true' fontsize='12' fontcolor='#1d2b4f'>BANDA 1 - TERMOMETRO DEL HOGAR (4 KPIs criticos)</run></formatted-text>",
        "          </zone>",
        "          <zone h='12000' id='30' name='BAN1 - Mermas en Despensa (S/)' w='25000' x='0' y='13000'>",
        "            <zone-style><format attr='background-color' value='#fde2e2' /><format attr='margin' value='4' /></zone-style>",
        "          </zone>",
        "          <zone h='12000' id='31' name='BAN2 - Tasa Desperdicio Fisico (%)' w='25000' x='25000' y='13000'>",
        "            <zone-style><format attr='background-color' value='#fce7c8' /><format attr='margin' value='4' /></zone-style>",
        "          </zone>",
        "          <zone h='12000' id='32' name='BAN3 - Nutriscore Critico D-E (%)' w='25000' x='50000' y='13000'>",
        "            <zone-style><format attr='background-color' value='#fff5cc' /><format attr='margin' value='4' /></zone-style>",
        "          </zone>",
        "          <zone h='12000' id='33' name='BAN4 - Estancamiento Medio (dias)' w='25000' x='75000' y='13000'>",
        "            <zone-style><format attr='background-color' value='#d6e9d6' /><format attr='margin' value='4' /></zone-style>",
        "          </zone>",
    ]

    # Banda 2 - longitudinal + insights
    parts += [
        "          <zone h='2500' id='40' type-v2='text' w='70000' x='0' y='25000'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "            <formatted-text><run bold='true' fontsize='12' fontcolor='#1d2b4f'>BANDA 2 - ANALISIS LONGITUDINAL: evolucion del costo perdido semana a semana por ubicacion fisica</run></formatted-text>",
        "          </zone>",
        "          <zone h='2500' id='41' type-v2='text' w='30000' x='70000' y='25000'>",
        "            <zone-style><format attr='background-color' value='#1d2b4f' /><format attr='margin' value='4' /></zone-style>",
        "            <formatted-text><run bold='true' fontsize='12' fontcolor='#ffffff'>ACCIONES PRESCRIPTIVAS</run></formatted-text>",
        "          </zone>",
        "          <zone h='30000' id='50' name='Longitudinal - Costo por Ubicacion' w='70000' x='0' y='27500'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "          </zone>",
        "          <zone h='30000' id='51' name='Insights Prescriptivos' w='30000' x='70000' y='27500'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "          </zone>",
    ]

    # Banda 3 - transversal + tabla
    parts += [
        "          <zone h='2500' id='60' type-v2='text' w='70000' x='0' y='57500'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "            <formatted-text><run bold='true' fontsize='12' fontcolor='#1d2b4f'>BANDA 3 - ANALISIS TRANSVERSAL: cruce Ubicacion fisica x Calidad Nutricional (Consumo vs Desperdicio)</run></formatted-text>",
        "          </zone>",
        "          <zone h='2500' id='61' type-v2='text' w='30000' x='70000' y='57500'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "            <formatted-text><run bold='true' fontsize='12' fontcolor='#1d2b4f'>DESGLOSE POR HOGAR (10)</run></formatted-text>",
        "          </zone>",
        "          <zone h='32000' id='70' name='Transversal - Ubicacion x Nutriscore' w='70000' x='0' y='60000'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "          </zone>",
        "          <zone h='32000' id='71' name='KPIs por Hogar' w='30000' x='70000' y='60000'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "          </zone>",
    ]

    # Footer
    parts += [
        "          <zone h='8000' id='80' type-v2='text' w='100000' x='0' y='92000'>",
        "            <zone-style><format attr='background-color' value='#e8eaf2' /><format attr='margin' value='6' /></zone-style>",
        "            <formatted-text><run fontsize='10' fontcolor='#5b6680'>Fuente: pipeline reproducible Smart Kitchen (Python + Tableau). Cobertura: 2026-W06 a 2026-W17. Filtros: usar Household Id (lateral) para aislar un hogar especifico. -- UPC | Data Visualization.</run></formatted-text>",
        "          </zone>",
    ]

    parts.append("        </zone>")
    parts.append("      </zones>")
    parts.append("      <devicelayouts />")
    parts.append("    </dashboard>")
    return "\n".join(parts)


def build_anex_dashboard():
    parts = []
    parts.append("    <dashboard enable-sort-zone-taborder='true' name='Anexo Metodologico'>")
    parts.append("      <style />")
    parts.append("      <size maxheight='900' maxwidth='1500' minheight='900' minwidth='1500' />")
    parts.append("      <zones>")
    parts.append("        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>")
    parts.append("          <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>")
    parts.append("          <zone h='7000' id='10' type-v2='text' w='100000' x='0' y='0'>")
    parts.append("            <zone-style><format attr='background-color' value='#4a5878' /><format attr='margin' value='8' /></zone-style>")
    parts.append("            <formatted-text><run bold='true' fontsize='16' fontcolor='#ffffff'>ANEXO METODOLOGICO -- Reduccion dimensional (PCA y t-SNE)</run></formatted-text>")
    parts.append("          </zone>")
    parts.append("          <zone h='4500' id='11' type-v2='text' w='100000' x='0' y='7000'>")
    parts.append("            <zone-style><format attr='background-color' value='#e8eaf2' /><format attr='margin' value='6' /></zone-style>")
    parts.append("            <formatted-text><run italic='true' fontsize='11' fontcolor='#1d2b4f'>Soporte tecnico exigido por la catedra. NO se usa para responder la pregunta de negocio del dashboard principal.</run></formatted-text>")
    parts.append("          </zone>")
    parts.append("          <zone h='42000' id='20' name='Mapa latente (PCA)' w='50000' x='0' y='11500' />")
    parts.append("          <zone h='42000' id='21' name='Clusters t-SNE' w='50000' x='50000' y='11500' />")
    parts.append("          <zone h='46500' id='30' name='Energia retenida (PCA)' w='100000' x='0' y='53500' />")
    parts.append("        </zone>")
    parts.append("      </zones>")
    parts.append("      <devicelayouts />")
    parts.append("    </dashboard>")
    return "\n".join(parts)


def build_context_dashboard():
    """Tercera pestana: contexto de gasto (benchmark de industria) + glosario
    NutriScore. Espeja el contenido agregado al dashboard HTML (Plotly) para
    que ambos entregables cuenten la misma historia. Es una pestana nueva y
    autocontenida (no reutiliza zonas de los otros dashboards), para no
    arriesgar el layout ya validado de 'Smart Kitchen Intelligence'."""
    parts = []
    parts.append("    <dashboard enable-sort-zone-taborder='true' name='Contexto y Glosario'>")
    parts.append("      <style />")
    parts.append("      <size maxheight='1000' maxwidth='1500' minheight='1000' minwidth='1500' />")
    parts.append("      <zones>")
    parts.append("        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>")
    parts.append("          <zone-style><format attr='background-color' value='#f7f7fa' /><format attr='margin' value='4' /></zone-style>")

    parts += [
        "          <zone h='6000' id='10' type-v2='text' w='100000' x='0' y='0'>",
        "            <zone-style><format attr='background-color' value='#1d2b4f' /><format attr='margin' value='8' /></zone-style>",
        "            <formatted-text><run bold='true' fontsize='22' fontcolor='#ffffff'>CONTEXTO DE GASTO Y GLOSARIO NUTRISCORE</run></formatted-text>",
        "          </zone>",
        "          <zone h='4000' id='11' type-v2='text' w='100000' x='0' y='6000'>",
        "            <zone-style><format attr='background-color' value='#2a3b6c' /><format attr='margin' value='8' /></zone-style>",
        "            <formatted-text><run italic='true' fontsize='12' fontcolor='#dfe4f2'>Referencias externas para interpretar la magnitud de la perdida simulada, y guia de lectura de las categorias NutriScore usadas en el resto del dashboard.</run></formatted-text>",
        "          </zone>",
    ]

    parts += [
        "          <zone h='3000' id='20' type-v2='text' w='100000' x='0' y='10000'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "            <formatted-text><run bold='true' fontsize='13' fontcolor='#1d2b4f'>COMO SE COMPARA ESTA PERDIDA CON LA INDUSTRIA</run></formatted-text>",
        "          </zone>",
        "          <zone h='20000' id='30' type-v2='text' w='33000' x='0' y='13000'>",
        "            <zone-style><format attr='background-color' value='#fde2e2' /><format attr='margin' value='10' /></zone-style>",
        "            <formatted-text>"
        "<run bold='true' fontsize='11' fontcolor='#5b6680'>% DEL GASTO EN COMPRAS QUE TERMINA PERDIDO</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontsize='26' fontcolor='#1d2b4f'>17.5%</run><run fontsize='11' fontcolor='#5b6680'>  SKI (este estudio)</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run fontsize='12' fontcolor='#2a2f3a'>vs. 17% de desperdicio de alimentos disponibles a nivel de consumidor, promedio mundial</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run italic='true' fontsize='10' fontcolor='#5b6680'>Fuente: PNUMA/ONU - Food Waste Index Report 2024</run>"
        "</formatted-text>",
        "          </zone>",
        "          <zone h='20000' id='31' type-v2='text' w='33000' x='33000' y='13000'>",
        "            <zone-style><format attr='background-color' value='#fce7c8' /><format attr='margin' value='10' /></zone-style>",
        "            <formatted-text>"
        "<run bold='true' fontsize='11' fontcolor='#5b6680'>ALIMENTOS DESPERDICIADOS POR PERSONA AL ANO EN EL HOGAR</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontsize='26' fontcolor='#1d2b4f'>67 kg</run><run fontsize='11' fontcolor='#5b6680'>  Peru</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run fontsize='12' fontcolor='#2a2f3a'>vs. 79 kg promedio mundial en el hogar</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run italic='true' fontsize='10' fontcolor='#5b6680'>Fuente: FAO Peru - PNUMA/ONU Food Waste Index 2024</run>"
        "</formatted-text>",
        "          </zone>",
        "          <zone h='20000' id='32' type-v2='text' w='34000' x='66000' y='13000'>",
        "            <zone-style><format attr='background-color' value='#e8eaf2' /><format attr='margin' value='10' /></zone-style>",
        "            <formatted-text>"
        "<run bold='true' fontsize='11' fontcolor='#5b6680'>PERDIDA Y DESPERDICIO DE ALIMENTOS EN PERU (TODA LA CADENA)</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontsize='26' fontcolor='#1d2b4f'>12.8 M</run><run fontsize='11' fontcolor='#5b6680'>  toneladas / ano</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run fontsize='12' fontcolor='#2a2f3a'>16% de esa perdida nacional ocurre en el hogar</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run italic='true' fontsize='10' fontcolor='#5b6680'>Fuente: FAO Peru</run>"
        "</formatted-text>",
        "          </zone>",
        "          <zone h='6000' id='33' type-v2='text' w='100000' x='0' y='33000'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='6' /></zone-style>",
        "            <formatted-text><run fontsize='11' fontcolor='#5b6680'>Las cifras de industria son referencias externas (no se calculan de este dataset). El 17.5% de gasto perdido en este estudio simulado es casi identico al 17% mundial, una senal de que las tasas simuladas -calibradas con patrones reales de compra (Instacart) y vida util (USDA FoodKeeper)- son razonables como aproximacion. El dataset no mide hogares peruanos reales.</run></formatted-text>",
        "          </zone>",
    ]

    parts += [
        "          <zone h='3000' id='40' type-v2='text' w='100000' x='0' y='40000'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='4' /></zone-style>",
        "            <formatted-text><run bold='true' fontsize='13' fontcolor='#1d2b4f'>QUE ES EL NUTRISCORE Y COMO SE INTERPRETA</run></formatted-text>",
        "          </zone>",
        "          <zone h='16000' id='50' type-v2='text' w='60000' x='0' y='43000'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='8' /></zone-style>",
        "            <formatted-text>"
        "<run bold='true' fontsize='11' fontcolor='#1d2b4f'>Que es: </run><run fontsize='11' fontcolor='#2a2f3a'>sistema de etiquetado nutricional (OpenFoodFacts) que clasifica alimentos de A (mas saludable) a E (menos saludable), con codigo de color de verde a rojo.</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontsize='11' fontcolor='#1d2b4f'>Como se calcula: </run><run fontsize='11' fontcolor='#2a2f3a'>puntos negativos (energia, azucares, grasas saturadas, sodio) menos puntos positivos (fibra, proteina, fruta/verdura) por 100g/100ml. Puntaje mas bajo = mejor letra.</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontsize='11' fontcolor='#1d2b4f'>En este proyecto: </run><run fontsize='11' fontcolor='#2a2f3a'>el catalogo de 50 productos no incluye grado E (el mas bajo presente es D); 7 productos sin dato se imputaron con la moda del catalogo.</run>"
        "</formatted-text>",
        "          </zone>",
        "          <zone h='16000' id='51' type-v2='text' w='40000' x='60000' y='43000'>",
        "            <zone-style><format attr='background-color' value='#ffffff' /><format attr='margin' value='8' /></zone-style>",
        "            <formatted-text>"
        "<run bold='true' fontcolor='#1e8f4e' fontsize='13'>A</run><run fontsize='11' fontcolor='#2a2f3a'>  Excelente calidad nutricional</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontcolor='#5cb55c' fontsize='13'>B</run><run fontsize='11' fontcolor='#2a2f3a'>  Buena calidad nutricional</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontcolor='#e8a83a' fontsize='13'>C</run><run fontsize='11' fontcolor='#2a2f3a'>  Calidad nutricional media</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontcolor='#e0703a' fontsize='13'>D</run><run fontsize='11' fontcolor='#2a2f3a'>  Calidad nutricional baja</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontcolor='#d64545' fontsize='13'>E</run><run fontsize='11' fontcolor='#2a2f3a'>  Calidad nutricional muy baja (sin productos de este grado en el catalogo)</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run fontsize='1'>&#10;</run>"
        "<run bold='true' fontcolor='#5cb55c' fontsize='11'>Saludable (A-B)</run><run fontsize='11' fontcolor='#2a2f3a'> = verde en el dashboard  ·  </run>"
        "<run bold='true' fontcolor='#e8a83a' fontsize='11'>Critico (C-D)</run><run fontsize='11' fontcolor='#2a2f3a'> = ambar</run>"
        "</formatted-text>",
        "          </zone>",
    ]

    parts += [
        "          <zone h='8000' id='90' type-v2='text' w='100000' x='0' y='92000'>",
        "            <zone-style><format attr='background-color' value='#e8eaf2' /><format attr='margin' value='6' /></zone-style>",
        "            <formatted-text><run fontsize='10' fontcolor='#5b6680'>Ver docs/data_dictionary.md y docs/QA_validation.md para el detalle metodologico completo. -- UPC | Data Visualization.</run></formatted-text>",
        "          </zone>",
    ]

    parts.append("        </zone>")
    parts.append("      </zones>")
    parts.append("      <devicelayouts />")
    parts.append("    </dashboard>")
    return "\n".join(parts)


def build_twb():
    build_insights_csv()
    ds_blocks = []
    ds_names = {}
    for key, (fname, cols) in DS_DEFS.items():
        xml, name = datasource_block(key, fname, cols, WIN_DATA_DIR)
        ds_blocks.append(xml)
        ds_names[key] = name
    for key, (fname, cols) in MODEL_DS.items():
        xml, name = datasource_block(key, fname, cols, WIN_OUTPUTS_DIR)
        ds_blocks.append(xml)
        ds_names[key] = name

    DS_KPI = ds_names["kpi_por_hogar"]
    DS_TMP = ds_names["agg_temporal_ubicacion"]
    DS_TRV = ds_names["agg_ubicacion_nutriscore"]
    DS_INS = ds_names["insights_prescriptivos"]
    DS_TSNE = ds_names["tsne_sample_tableau"]
    DS_PCA = ds_names["pca_components_tableau"]
    DS_VAR = ds_names["pca_variance_table"]

    ws_blocks = [
        ws_ban("BAN1 - Mermas en Despensa (S/)", DS_KPI, "kpi1_costo_perdido_soles", "sum"),
        ws_ban("BAN2 - Tasa Desperdicio Fisico (%)", DS_KPI, "kpi2_tasa_desperdicio", "avg"),
        ws_ban("BAN3 - Nutriscore Critico D-E (%)", DS_KPI, "kpi3_pct_nutriscore_DE", "avg"),
        ws_ban("BAN4 - Estancamiento Medio (dias)", DS_KPI, "kpi4_dias_prom_vencer", "avg"),
        ws_longitudinal(DS_TMP),
        ws_transversal(DS_TRV),
        ws_tabla(DS_KPI),
        ws_insights(DS_INS),
        ws_scatter("Clusters t-SNE", DS_TSNE, "sum:tsne_1:qk", "sum:tsne_2:qk", "location"),
        ws_scatter("Mapa latente (PCA)", DS_PCA, "none:PC1:qk", "none:PC2:qk", "location"),
        ws_bar_simple("Energia retenida (PCA)", DS_VAR, "componente", "sum", "varianza_acumulada"),
    ]

    main_db = build_main_dashboard()
    anex_db = build_anex_dashboard()
    ctx_db = build_context_dashboard()

    hidden_names = [
        "BAN1 - Mermas en Despensa (S/)",
        "BAN2 - Tasa Desperdicio Fisico (%)",
        "BAN3 - Nutriscore Critico D-E (%)",
        "BAN4 - Estancamiento Medio (dias)",
        "Longitudinal - Costo por Ubicacion",
        "Transversal - Ubicacion x Nutriscore",
        "KPIs por Hogar",
        "Insights Prescriptivos",
        "Clusters t-SNE",
        "Mapa latente (PCA)",
        "Energia retenida (PCA)",
    ]
    hidden_xml = "\n".join(
        f"    <window class='worksheet' hidden='true' name='{n}' />" for n in hidden_names
    )

    nl = "\n"
    twb = (
        "<?xml version='1.0' encoding='utf-8' ?>\n"
        f"<!-- Generado por build_dashboard_twb.py el {datetime.now().isoformat(timespec='seconds')} -->\n"
        "<workbook original-version='18.1' source-build='2026.2.0 (20262.26.0603.1643)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>\n"
        "  <document-format-change-manifest>\n"
        "    <AccessibleZoneTabOrder />\n"
        "    <AnimationOnByDefault />\n"
        "    <AutoCreateAndUpdateDSDPhoneLayouts />\n"
        "    <MarkAnimation />\n"
        "    <ObjectModelEncapsulateLegacy />\n"
        "    <ObjectModelExtractV2 />\n"
        "    <ObjectModelTableType />\n"
        "    <SchemaViewerObjectModel />\n"
        "    <SetMembershipControl />\n"
        "    <SheetIdentifierTracking />\n"
        "    <VConnDownstreamExtractsWithWarnings />\n"
        "    <WindowsPersistSimpleIdentifiers />\n"
        "    <ZoneBackgroundTransparency />\n"
        "  </document-format-change-manifest>\n"
        "  <preferences>\n"
        "    <preference name='ui.encoding.shelf.height' value='24' />\n"
        "    <preference name='ui.shelf.height' value='26' />\n"
        "  </preferences>\n"
        "  <datasources>\n"
        f"{nl.join(ds_blocks)}\n"
        "  </datasources>\n"
        "  <worksheets>\n"
        f"{nl.join(ws_blocks)}\n"
        "  </worksheets>\n"
        "  <dashboards>\n"
        f"{main_db}\n"
        f"{anex_db}\n"
        f"{ctx_db}\n"
        "  </dashboards>\n"
        "  <windows source-height='30'>\n"
        "    <window class='dashboard' maximized='true' name='Smart Kitchen Intelligence' />\n"
        "    <window class='dashboard' name='Anexo Metodologico' />\n"
        "    <window class='dashboard' name='Contexto y Glosario' />\n"
        f"{hidden_xml}\n"
        "  </windows>\n"
        "</workbook>\n"
    )
    return twb


if __name__ == "__main__":
    xml = build_twb()
    if OUT_TWB.exists():
        bkp = OUT_TWB.with_suffix(".twb.bak")
        OUT_TWB.replace(bkp)
        print(f"Backup creado: {bkp.name}")
    OUT_TWB.write_text(xml, encoding="utf-8")
    print(f"Workbook generado: {OUT_TWB}")
    print(f"Tamano: {OUT_TWB.stat().st_size:,} bytes")

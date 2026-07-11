"""
Genera un .twb minimal: SOLO 7 conexiones de datos limpias.
Sin worksheets ni dashboards (los construye el usuario en Tableau Desktop).
Garantiza apertura sin errores de schema XSD.
"""
import csv, hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "datos_finales"
OUT_TWB = ROOT / "Sem12_Dashboard_SmartKitchen.twb"
WIN_DATA = "C:/Users/gabri/Documents/Upc/Data Visualization/proyecto-final/tableau/datos_finales"
WIN_OUT  = "C:/Users/gabri/Documents/Upc/Data Visualization/proyecto-final/outputs"

# Regenerar insights CSV
def build_insights():
    out = DATA_DIR / "insights_prescriptivos.csv"
    rows = []
    with open(DATA_DIR/"kpi_por_hogar.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            hid, seg, ub = r["household_id"], r["segmento_hogar"], r["ubicacion_critica"]
            costo = float(r["kpi1_costo_perdido_soles"])
            tasa  = float(r["kpi2_tasa_desperdicio"])*100
            nutri = float(r["kpi3_pct_nutriscore_DE"])*100
            dias  = float(r["kpi4_dias_prom_vencer"])
            rows += [
                {"household_id":hid,"segmento_hogar":seg,"eje":"1. Mitigacion Financiera","orden":1,"titulo":"Punto ciego",
                 "mensaje":f"El {ub} concentra S/ {costo:,.0f} de mermas (KPI1). Trasladar productos con <10 dias para vencer al Estante de Alta Visibilidad."},
                {"household_id":hid,"segmento_hogar":seg,"eje":"2. Optimizacion de Compras","orden":2,"titulo":"Ajuste abastecimiento",
                 "mensaje":f"Tasa desperdicio = {tasa:.1f}% (KPI2). Reducir 15% el volumen de Lacteos y Carnes en el proximo ciclo."},
                {"household_id":hid,"segmento_hogar":seg,"eje":"3. Gestion de Salud","orden":3,"titulo":"Calidad nutricional",
                 "mensaje":f"{nutri:.1f}% del desperdicio es Nutriscore D-E (KPI3), estancamiento {dias:.1f} dias (KPI4). Sustituir ultraprocesados por opciones A-B."},
            ]
    with open(out,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["household_id","segmento_hogar","eje","orden","titulo","mensaje"])
        w.writeheader(); w.writerows(rows)

def sid(prefix,key):
    return f"{prefix}.{hashlib.sha1(key.encode()).hexdigest()[:24]}"

def ds_block(caption, filename, columns, directory):
    name = sid("federated",caption)
    conn = sid("textscan",caption)
    rel = Path(filename).stem
    cols_xml = "\n".join(f"            <column datatype='{dt}' name='{n}' ordinal='{i}' />"
                          for i,(n,dt) in enumerate(columns))
    return f"""    <datasource caption='{caption}' inline='true' name='{name}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='{caption}' name='{conn}'>
            <connection class='textscan' directory='{directory}' filename='{filename}' password='' server='' />
          </named-connection>
        </named-connections>
        <relation connection='{conn}' name='{filename}' table='[{rel}#csv]' type='table'>
          <columns character-set='UTF-8' header='yes' locale='es_PE' separator=','>
{cols_xml}
          </columns>
        </relation>
      </connection>
      <aliases enabled='yes' />
    </datasource>"""

DS = [
    ("kpi_por_hogar","kpi_por_hogar.csv",WIN_DATA,[
        ("household_id","integer"),("segmento_hogar","string"),("ubicacion_critica","string"),
        ("kpi1_costo_perdido_soles","real"),("kpi2_tasa_desperdicio","real"),
        ("kpi3_pct_nutriscore_DE","real"),("kpi4_dias_prom_vencer","real"),
        ("total_eventos_out","integer"),("total_eventos_waste","integer"),
        ("costo_total_perdido","real"),("costo_total_compras","real"),
    ]),
    ("agg_temporal_ubicacion","agg_temporal_ubicacion.csv",WIN_DATA,[
        ("household_id","integer"),("semana_iso","string"),("location","string"),
        ("eventos_out","integer"),("eventos_waste","integer"),("eventos_consumo","integer"),
        ("costo_perdido","real"),("costo_consumido","real"),("tasa_desperdicio","real"),
    ]),
    ("agg_ubicacion_nutriscore","agg_ubicacion_nutriscore.csv",WIN_DATA,[
        ("household_id","integer"),("location","string"),("nutriscore","string"),
        ("nutriscore_grupo","string"),("tipo_salida","string"),
        ("eventos","integer"),("costo","real"),("unidades","integer"),
    ]),
    ("insights_prescriptivos","insights_prescriptivos.csv",WIN_DATA,[
        ("household_id","integer"),("segmento_hogar","string"),("eje","string"),
        ("orden","integer"),("titulo","string"),("mensaje","string"),
    ]),
    ("fact_con_precio","fact_con_precio.csv",WIN_DATA,[
        ("event_id","string"),("household_id","integer"),("product_id","integer"),
        ("product_name","string"),("action_type","string"),("classification","string"),
        ("quantity","integer"),("fecha","date"),("semana_iso","string"),("mes","string"),
        ("dia_semana","string"),("hora","integer"),("turno","string"),("expiry_date","date"),
        ("dias_para_vencer","integer"),("location","string"),("category_name","string"),
        ("nutriscore","string"),("calories_100g","real"),("bucket_calorico","string"),
        ("is_out","integer"),("is_in","integer"),("is_waste","integer"),
        ("is_forced_waste","integer"),("is_consumo","integer"),("is_vencido","integer"),
        ("flag_riesgo_vencer","integer"),("precio_unitario","real"),
        ("costo_evento","real"),("costo_perdido","real"),
    ]),
    ("tsne_sample_tableau","tsne_sample_tableau.csv",WIN_OUT,[
        ("event_id","string"),("household_id","integer"),("product_name","string"),
        ("action_type","string"),("category_name","string"),("location","string"),
        ("nutriscore","string"),("timestamp","datetime"),("dias_para_vencer","integer"),
        ("calories_100g","real"),("tsne_1","real"),("tsne_2","real"),
    ]),
    ("pca_components_tableau","pca_components_tableau.csv",WIN_OUT,[
        ("event_id","string"),("household_id","integer"),("product_name","string"),
        ("action_type","string"),("category_name","string"),("location","string"),
        ("nutriscore","string"),("PC1","real"),("PC2","real"),("PC3","real"),
        ("PC4","real"),("PC5","real"),
    ]),
    ("pca_variance_table","pca_variance_table.csv",WIN_OUT,[
        ("componente","string"),("varianza_explicada","real"),("varianza_acumulada","real"),
    ]),
]

build_insights()
ds_xml = "\n".join(ds_block(c, fn, cols, d) for c, fn, d, cols in DS)

twb = f"""<?xml version='1.0' encoding='utf-8' ?>
<!-- Minimal SKI workbook generado {datetime.now().isoformat(timespec='seconds')} -->
<workbook original-version='18.1' source-build='2026.2.0 (20262.26.0603.1643)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
{ds_xml}
  </datasources>
</workbook>
"""

if OUT_TWB.exists():
    bkp = OUT_TWB.with_suffix(".twb.bak2")
    OUT_TWB.replace(bkp)
    print(f"Backup previo: {bkp.name}")
OUT_TWB.write_text(twb, encoding="utf-8")
print(f"Workbook minimal generado: {OUT_TWB} ({OUT_TWB.stat().st_size:,} bytes)")

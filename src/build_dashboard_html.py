"""
Dashboard Smart Kitchen Intelligence (SKI) — narrativo, responde la pregunta de negocio.

Pregunta: ¿Que impacto tiene la ubicacion fisica (Refrigerador / Despensa / Estante)
en la perdida economica y de salud del hogar?

Respuesta del dashboard: El Refrigerador concentra el 97% de las perdidas economicas
y desperdicia 64x mas alimentos saludables (A-B) que la Despensa.

Estructura:
  1. HERO: respuesta directa con la cifra mas impactante
  2. KPIs comparativos por ubicacion
  3. Contexto de gasto: benchmark de industria (PNUMA/ONU, FAO Peru)
  4. Ranking de ubicaciones (donde se pierde el dinero)
  5. Impacto en salud (donde se pierden frutas/verduras saludables)
  6. Evolucion temporal con narrativa
  7. Cruce ubicacion x NutriScore + glosario NutriScore
  8. Acciones recomendadas
  9. Componente avanzado (PCA): por que ubicacion ~= categoria de producto
  10. Sobre los datos: dataset, household_id, universo, limpieza
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tableau" / "datos_finales"
OUTPUTS = ROOT / "outputs"
OUT = ROOT / "tableau" / "Sem12_Dashboard_SmartKitchen.html"
PCA_SAMPLE_SIZE = 3000  # downsample para mantener el HTML autocontenido liviano
PCA_RANDOM_STATE = 42   # mismo seed que src/reduction.py, para reproducibilidad

# Paleta categorica para el mapa PCA (validada con el validador de paletas:
# banda de luminosidad, piso de croma, separacion CVD y contraste vs. blanco).
CATEGORY_COLORS = {
    "Frutas y Verduras": "#2e9e5b",
    "Lacteos y Refrigerados": "#4f7fe0",
    "Bebidas": "#c47f17",
    "Panaderia y Granos": "#a85ccf",
    "Congelados": "#0091a8",
    "Despensa General": "#c76b3f",
}

C = {
    "primary": "#1d2b4f",
    "secondary": "#2a3b6c",
    "danger": "#d64545",
    "warning": "#e8a83a",
    "caution": "#f1c40f",
    "success": "#5cb55c",
    "muted": "#5b6680",
    "bg": "#f4f5f9",
    "Refrigerador": "#d64545",
    "Despensa": "#3a5fcc",
    "Estante": "#e8a83a",
    "Saludable (A-B)": "#5cb55c",
    "Crítico (C-D)": "#e8a83a",
    "Riesgo (D-E)": "#d64545",
    "Desperdicio": "#d64545",
    "Consumo": "#5cb55c",
}

# Cifras de referencia de industria (fuentes externas, NO calculadas de este dataset).
# Se usan solo para dar contexto de magnitud a la perdida simulada del caso de estudio.
BENCHMARK = {
    "pct_desperdicio_consumidor_mundial": 17.0,  # % de alimentos disponibles para consumidores desperdiciado a nivel mundial
    "kg_per_capita_mundial": 79,                 # kg desperdiciados por persona/año en el hogar, promedio mundial (datos 2022)
    "kg_per_capita_peru": 67,                    # kg desperdiciados por persona/año en el hogar, Perú
    "pct_perdida_hogar_peru": 16,                # % de la pérdida y desperdicio total de alimentos en Perú que ocurre en el hogar
    "toneladas_anio_peru": 12.8,                 # millones de toneladas de alimentos perdidos/desperdiciados al año en Perú (toda la cadena)
    "fuente_mundial": "PNUMA/ONU — Food Waste Index Report 2024",
    "fuente_peru": "FAO Perú",
}


def load():
    kpi_hogar = pd.read_csv(DATA / "kpi_por_hogar.csv")
    temp = pd.read_csv(DATA / "agg_temporal_ubicacion.csv")
    trans = pd.read_csv(DATA / "agg_ubicacion_nutriscore.csv")
    insights = pd.read_csv(DATA / "insights_prescriptivos.csv")
    with open(DATA / "kpi_global.json", encoding="utf-8") as f:
        glob = json.load(f)
    return kpi_hogar, temp, trans, insights, glob


def load_pca_sample():
    """Muestra reproducible del componente avanzado (PCA) para graficar en el
    dashboard sin embeber las 25,819 filas completas (4+ MB) en el HTML."""
    path = OUTPUTS / "pca_components_tableau.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    n = min(PCA_SAMPLE_SIZE, len(df))
    return df.sample(n=n, random_state=PCA_RANDOM_STATE)


def compute_narrative(temp, trans):
    """Calcula las cifras clave que respaldan la narrativa."""
    loc = temp.groupby("location", as_index=False).agg(
        costo=("costo_perdido", "sum"),
        eventos_out=("eventos_out", "sum"),
        eventos_waste=("eventos_waste", "sum"),
    )
    loc["tasa"] = loc["eventos_waste"] / loc["eventos_out"] * 100
    loc["pct_costo"] = loc["costo"] / loc["costo"].sum() * 100
    loc = loc.sort_values("costo", ascending=False).reset_index(drop=True)

    saludable = trans[
        (trans["tipo_salida"] == "Desperdicio") &
        (trans["nutriscore_grupo"].str.contains("A-B|Saludable", regex=True, na=False))
    ].groupby("location", as_index=False).agg(eventos=("eventos", "sum"), costo=("costo", "sum"))
    saludable = saludable.sort_values("costo", ascending=False).reset_index(drop=True)

    top_loc = loc.iloc[0]
    return {
        "loc_ranking": loc,
        "saludable": saludable,
        "top_loc": top_loc["location"],
        "top_pct": top_loc["pct_costo"],
        "top_costo": top_loc["costo"],
        "total_costo": loc["costo"].sum(),
        "ratio_saludable": (
            saludable.iloc[0]["eventos"] / max(saludable.iloc[1]["eventos"], 1)
            if len(saludable) > 1 else 0
        ),
        "saludable_top_costo": saludable.iloc[0]["costo"] if len(saludable) else 0,
        "saludable_top_loc": saludable.iloc[0]["location"] if len(saludable) else "",
    }


def hero_block(n):
    return f"""
    <div class="hero">
      <div class="hero-eyebrow">RESPUESTA DIRECTA A LA PREGUNTA</div>
      <div class="hero-title">El <span class="hero-emph">{n['top_loc']}</span> concentra el <span class="hero-emph">{n['top_pct']:.0f}%</span> de las perdidas economicas del hogar</div>
      <div class="hero-sub">S/ {n['top_costo']:,.0f} de S/ {n['total_costo']:,.0f} totales (90 dias, 10 hogares). Ademas, desperdicia <b>{n['ratio_saludable']:.0f} veces mas</b> alimentos saludables A-B que la siguiente ubicacion, por S/ {n['saludable_top_costo']:,.0f}.</div>
    </div>"""


def kpi_row(kpi_hogar, n, total_compras, pct_perdido):
    """4 KPIs comparativos: cada uno se ancla a una referencia (otra ubicacion,
    el gasto total o un benchmark de industria) para que el numero sea
    interpretable por si solo, no solo un valor aislado."""
    ref_tasa = n["loc_ranking"].iloc[0]["tasa"]
    estante_tasa = n["loc_ranking"].loc[n["loc_ranking"]["location"] == "Estante", "tasa"].iloc[0]
    seg = n["saludable"].iloc[1] if len(n["saludable"]) > 1 else None
    cost_ratio = (n["saludable_top_costo"] / seg["costo"]) if seg is not None and seg["costo"] else None

    cards = [
        dict(label="Perdida economica total (90 dias)", value=f"S/ {n['total_costo']:,.0f}",
             sub=f"{pct_perdido:.1f}% del gasto total en compras (S/ {total_compras:,.0f}) &mdash; "
                 f"casi igual al {BENCHMARK['pct_desperdicio_consumidor_mundial']:.0f}% que estima la ONU a nivel mundial",
             color=C["danger"]),
        dict(label=f"Tasa de desperdicio &mdash; {n['top_loc']}", value=f"{ref_tasa:.1f}%",
             sub=f"{ref_tasa / estante_tasa:.1f}x mas alta que en Estante ({estante_tasa:.1f}%), la ubicacion mas eficiente",
             color=C["warning"]),
        dict(label="Retraso promedio al vencimiento", value=f"{kpi_hogar['kpi4_dias_prom_vencer'].mean():.1f} d",
             sub=f"En promedio, el alimento sale del inventario {abs(kpi_hogar['kpi4_dias_prom_vencer'].mean()):.1f} dias despues de vencido (negativo = ya vencido)",
             color=C["caution"]),
        dict(label="Alimentos saludables (NutriScore A-B) perdidos", value=f"S/ {n['saludable_top_costo']:,.0f}",
             sub=(f"{cost_ratio:.0f}x mas costo perdido que en {seg['location']}" if cost_ratio else "")
                 + " &mdash; es fruta y verdura fresca, no comida chatarra",
             color=C["success"]),
    ]
    return "<div class='kpi-row'>" + "".join(
        f"""<div class="kpi-card" style="border-top: 6px solid {c['color']};">
              <div class="kpi-label">{c['label']}</div>
              <div class="kpi-value" style="color: {c['color']};">{c['value']}</div>
              <div class="kpi-sub">{c['sub']}</div>
            </div>""" for c in cards
    ) + "</div>"


def benchmark_block(n, total_compras, pct_perdido):
    """Contexto de gasto: compara la perdida del caso de estudio con cifras
    publicadas de desperdicio de alimentos (industria/pais), para que el
    lector pueda juzgar si la magnitud es alta, baja o tipica."""
    return f"""
    <div class="section">
      <div class="section-eyebrow">CONTEXTO DE GASTO</div>
      <div class="section-title">Como se compara esta perdida con la industria</div>
      <div class="section-sub">S/ {n['total_costo']:,.0f} perdidos suena a mucho o poco sin una referencia. Estas cifras publicadas de desperdicio de alimentos a nivel de consumidor dan esa referencia.</div>
      <div class="benchmark-grid">
        <div class="benchmark-card" style="border-top: 6px solid {C['danger']};">
          <div class="bm-label">% del gasto en compras que termina perdido</div>
          <div class="bm-case">{pct_perdido:.1f}%<span class="bm-case-tag">SKI &mdash; este estudio</span></div>
          <div class="bm-vs">vs. <b>{BENCHMARK['pct_desperdicio_consumidor_mundial']:.0f}%</b> de desperdicio de alimentos disponibles a nivel de consumidor, promedio mundial</div>
          <div class="bm-source">Fuente: {BENCHMARK['fuente_mundial']}</div>
        </div>
        <div class="benchmark-card" style="border-top: 6px solid {C['warning']};">
          <div class="bm-label">Alimentos desperdiciados por persona al año en el hogar</div>
          <div class="bm-case">{BENCHMARK['kg_per_capita_peru']} kg<span class="bm-case-tag">Perú</span></div>
          <div class="bm-vs">vs. <b>{BENCHMARK['kg_per_capita_mundial']} kg</b> promedio mundial en el hogar</div>
          <div class="bm-source">Fuente: {BENCHMARK['fuente_peru']} · {BENCHMARK['fuente_mundial']}</div>
        </div>
        <div class="benchmark-card" style="border-top: 6px solid {C['muted']};">
          <div class="bm-label">Pérdida y desperdicio de alimentos en Perú (toda la cadena)</div>
          <div class="bm-case">{BENCHMARK['toneladas_anio_peru']:.1f} M<span class="bm-case-tag">toneladas / año</span></div>
          <div class="bm-vs"><b>{BENCHMARK['pct_perdida_hogar_peru']}%</b> de esa pérdida nacional ocurre en el hogar</div>
          <div class="bm-source">Fuente: {BENCHMARK['fuente_peru']}</div>
        </div>
      </div>
      <div class="benchmark-note">Las cifras de industria son referencias externas (no se calculan de este dataset); se muestran solo para dar contexto de magnitud. El {pct_perdido:.1f}% de gasto perdido en este estudio simulado (S/ {n['total_costo']:,.0f} de S/ {total_compras:,.0f} en compras, 10 hogares, 90 dias) es casi identico al {BENCHMARK['pct_desperdicio_consumidor_mundial']:.0f}% mundial &mdash; una senal de que las tasas de desperdicio simuladas, calibradas con patrones reales de compra (Instacart) y vida util (USDA FoodKeeper), son razonables como aproximacion. El dataset no mide hogares peruanos reales; ver la seccion "Sobre los datos" para el detalle metodologico.</div>
    </div>"""


def nutriscore_block():
    """Explica que es el NutriScore, como se calcula y como leer sus colores
    en el resto del dashboard (glosario visual, sin dependencia de datos)."""
    letras = [
        ("A", "#1e8f4e", "Excelente calidad nutricional"),
        ("B", "#5cb55c", "Buena calidad nutricional"),
        ("C", "#e8a83a", "Calidad nutricional media"),
        ("D", "#e0703a", "Calidad nutricional baja"),
        ("E", "#d64545", "Calidad nutricional muy baja"),
    ]
    chips = "".join(
        f"""<div class="ns-chip">
              <div class="ns-letter" style="background:{color};">{letra}</div>
              <div class="ns-desc">{desc}</div>
            </div>""" for letra, color, desc in letras
    )
    return f"""
    <div class="section">
      <div class="section-eyebrow">GLOSARIO</div>
      <div class="section-title">Que es el NutriScore y como se interpreta</div>
      <div class="ns-layout">
        <div class="ns-text">
          <p><b>Que es:</b> el NutriScore (Nutri-Score) es un sistema de etiquetado nutricional frontal que clasifica alimentos envasados en una escala de <b>A (mas saludable)</b> a <b>E (menos saludable)</b>, con un codigo de color de verde a rojo. Es el dato que reporta OpenFoodFacts, la fuente del catalogo de productos de este proyecto.</p>
          <p><b>Como se calcula:</b> por cada 100 g/100 ml de producto, el algoritmo suma puntos "negativos" (0-10) segun energia, azucares, grasas saturadas y sodio, y puntos "positivos" (0-5) segun fibra, proteina y proporcion de frutas, verduras, legumbres y frutos secos. El puntaje final es negativos menos positivos: mientras mas bajo el puntaje, mejor la letra asignada.</p>
          <p><b>En este proyecto:</b> el catalogo de 50 productos no incluye ningun producto con grado E (el mas bajo presente es D); 7 productos llegaron sin calificacion ("Falta Dato") y se imputaron con la moda del catalogo antes del analisis (ver "Sobre los datos"). Para simplificar la lectura, los graficos agrupan las 5 letras en 3 categorias de color:</p>
        </div>
        <div class="ns-legend">
          {chips}
          <div class="ns-groups">
            <div class="ns-group"><span class="ns-dot" style="background:{C['Saludable (A-B)']};"></span><b>Saludable (A-B)</b> &mdash; verde en los graficos de este dashboard</div>
            <div class="ns-group"><span class="ns-dot" style="background:{C['Crítico (C-D)']};"></span><b>Critico (C-D)</b> &mdash; ambar en los graficos de este dashboard</div>
            <div class="ns-group"><span class="ns-dot" style="background:{C['Riesgo (D-E)']};"></span><b>Riesgo (D-E)</b> &mdash; rojo; sin productos de este grado en el catalogo actual</div>
          </div>
        </div>
      </div>
    </div>"""


def dataset_block():
    """Explica de forma accesible que es el dataset, que representa
    'household_id', cual es el universo de estudio y que filtros/limpieza
    se aplicaron antes del analisis."""
    return f"""
    <div class="section">
      <div class="section-eyebrow">METODOLOGIA</div>
      <div class="section-title">Sobre los datos: que representan, de donde salen y que se filtro</div>
      <div class="ds-layout">
        <div class="ds-text">
          <p><b>De que trata el dataset:</b> este dashboard combina dos fuentes. Un catalogo real de 50 productos de consumo domestico con sus valores nutricionales (calorias, proteinas, carbohidratos, NutriScore), obtenido de OpenFoodFacts; y un registro simulado de movimientos de despensa (compras, consumos y desperdicios) para 10 hogares durante 90 dias, generado con un simulador estocastico calibrado con patrones reales de compra (Instacart Online Grocery) y reglas de vida util de alimentos (USDA FoodKeeper). El resultado es una tabla de 25,819 eventos que registra, para cada producto que entra o sale del inventario de una cocina, cuando ocurrio, en que ubicacion fisica estaba (Refrigerador / Despensa / Estante) y si termino consumido o desperdiciado.</p>
          <p><b>Que representa "Household" (household_id):</b> es un identificador sintetico del 0 al 9 que distingue a cada uno de los 10 hogares simulados. No corresponde a una familia real ni a datos personales: es una variable de segmentacion que permite comparar patrones de compra y desperdicio entre "hogares" simulados de forma independiente, igual que se compararian tiendas o sucursales. Por ser un ID sintetico sin informacion generalizable, se excluyo explicitamente como variable predictiva en los modelos de machine learning del proyecto; aqui se usa solo con fines descriptivos y de segmentacion.</p>
          <p><b>Universo / poblacion de estudio:</b> 10 hogares simulados, 90 dias consecutivos (2026-02-01 a 2026-05-01), 25,819 eventos de inventario sobre 50 productos en 6 categorias (Frutas y Verduras, Lacteos, Panaderia, Bebidas, Congelados, Despensa General) y 3 ubicaciones fisicas. No es una muestra probabilistica de hogares peruanos reales: es una simulacion calibrada con datos reales de comportamiento de compra, pensada para representar patrones plausibles de un hogar urbano de 2 a 4 personas. Los resultados deben leerse como ilustrativos del fenomeno, no como una medicion censal.</p>
          <p><b>Filtros y limpieza aplicados antes del analisis:</b></p>
          <ul>
            <li>7 de los 50 productos llegaron sin NutriScore ("Falta Dato"); se marcaron como nulos y se imputaron con la moda del catalogo (3,576 de los 25,819 eventos quedaron afectados).</li>
            <li>Umbral fisico de 900 kcal/100g para detectar y corregir outliers caloricos imposibles.</li>
            <li>Integridad referencial validada al 100% entre movimientos y catalogo (0 eventos huerfanos, 0 duplicados).</li>
            <li><code>dias_para_vencer</code> se excluyo de los modelos predictivos por fuga de datos (data leakage): el simulador la usaba para decidir que eventos serian desperdicio. Se conserva solo para reporting descriptivo (por ejemplo, el KPI "Retraso promedio al vencimiento").</li>
            <li>Las tasas de desperdicio se calculan solo sobre eventos de salida (OUT); las entradas (IN) son siempre compras y no aportan a esa metrica.</li>
          </ul>
        </div>
        <div class="ds-fact-card">
          <div class="ds-fact-title">Ficha tecnica</div>
          <div class="ds-fact-row"><span>Eventos totales</span><b>25,819</b></div>
          <div class="ds-fact-row"><span>Hogares simulados</span><b>10 (IDs 0-9)</b></div>
          <div class="ds-fact-row"><span>Periodo cubierto</span><b>90 dias (feb-may 2026)</b></div>
          <div class="ds-fact-row"><span>Productos en catalogo</span><b>50</b></div>
          <div class="ds-fact-row"><span>Categorias</span><b>6</b></div>
          <div class="ds-fact-row"><span>Ubicaciones fisicas</span><b>3</b></div>
          <div class="ds-fact-row"><span>Fuente catalogo</span><b>OpenFoodFacts (real)</b></div>
          <div class="ds-fact-row"><span>Fuente movimientos</span><b>Simulacion calibrada</b></div>
        </div>
      </div>
    </div>"""


def fig_ranking_ubicacion(n):
    df = n["loc_ranking"]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["location"], x=df["costo"],
        orientation="h",
        marker_color=[C.get(l, C["muted"]) for l in df["location"]],
        text=[f"S/ {v:,.0f}  ({p:.1f}%)" for v, p in zip(df["costo"], df["pct_costo"])],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>S/ %{x:,.0f}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=120, r=120, t=10, b=30),
        height=240,
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        showlegend=False,
        xaxis_title="Costo perdido (S/)",
        font=dict(family="Segoe UI, Arial", size=12),
        yaxis=dict(categoryorder="total ascending"),
    )
    fig.update_xaxes(gridcolor="#e8eaf2", tickprefix="S/ ", tickformat=",.0f")
    return fig


def fig_salud(n):
    df = n["saludable"].sort_values("costo")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["location"], x=df["costo"],
        orientation="h",
        marker_color=C["success"],
        text=[f"S/ {v:,.0f}  ({e:,} eventos)" for v, e in zip(df["costo"], df["eventos"])],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Saludable A-B perdido: S/ %{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=120, r=160, t=10, b=30),
        height=240,
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        showlegend=False,
        xaxis_title="Costo de alimentos saludables (A-B) desperdiciados",
        font=dict(family="Segoe UI, Arial", size=12),
    )
    fig.update_xaxes(gridcolor="#e8eaf2", tickprefix="S/ ", tickformat=",.0f")
    return fig


def fig_longitudinal(temp):
    df = temp.groupby(["semana_iso", "location"], as_index=False).agg(costo=("costo_perdido", "sum")).sort_values("semana_iso")
    fig = go.Figure()
    for loc in ["Refrigerador", "Despensa", "Estante"]:
        sub = df[df["location"] == loc]
        if sub.empty: continue
        fig.add_trace(go.Scatter(
            x=sub["semana_iso"], y=sub["costo"],
            mode="lines+markers", name=loc,
            line=dict(color=C.get(loc, C["primary"]), width=3),
            marker=dict(size=8),
            hovertemplate=f"<b>{loc}</b><br>%{{x}}<br>S/ %{{y:,.0f}}<extra></extra>",
        ))
    fig.update_layout(
        margin=dict(l=60, r=150, t=20, b=60), height=350,
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02,
                     title="Ubicacion", font=dict(size=11)),
        xaxis_title="Semana ISO 2026", yaxis_title="Costo perdido (S/)",
        font=dict(family="Segoe UI, Arial", size=11),
    )
    fig.update_xaxes(gridcolor="#e8eaf2", tickangle=-45)
    fig.update_yaxes(gridcolor="#e8eaf2", tickprefix="S/ ", tickformat=",.0f")
    return fig


def fig_transversal(trans):
    df = trans.groupby(["location", "tipo_salida", "nutriscore_grupo"], as_index=False).agg(eventos=("eventos", "sum"))
    df["categoria"] = df["location"] + " — " + df["tipo_salida"]
    orden = [f"{l} — {ts}" for l in ["Refrigerador", "Despensa", "Estante"] for ts in ["Consumo", "Desperdicio"]]
    fig = go.Figure()
    for grupo in sorted(df["nutriscore_grupo"].unique()):
        sub = df[df["nutriscore_grupo"] == grupo]
        fig.add_trace(go.Bar(
            y=sub["categoria"], x=sub["eventos"], name=grupo, orientation="h",
            marker_color=C.get(grupo, C["muted"]),
            hovertemplate=f"<b>{grupo}</b><br>%{{y}}<br>%{{x:,}} eventos<extra></extra>",
        ))
    fig.update_layout(
        margin=dict(l=180, r=150, t=20, b=40), height=360,
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        barmode="stack",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02,
                     title="Calidad nutricional", font=dict(size=11)),
        xaxis_title="Numero de eventos",
        font=dict(family="Segoe UI, Arial", size=11),
        yaxis=dict(categoryorder="array", categoryarray=orden[::-1]),
    )
    fig.update_xaxes(gridcolor="#e8eaf2")
    return fig


def fig_pca(df_sample):
    """Mapa PCA (PC1 vs PC2) de una muestra de 3,000 eventos, coloreado por
    categoria de producto. Componente avanzado exigido por la catedra, con
    un hallazgo de negocio real (ver pca_block)."""
    fig = go.Figure()
    for cat in sorted(df_sample["category_name"].unique()):
        sub = df_sample[df_sample["category_name"] == cat]
        fig.add_trace(go.Scattergl(
            x=sub["PC1"], y=sub["PC2"], mode="markers", name=cat,
            marker=dict(size=5, color=CATEGORY_COLORS.get(cat, C["muted"]), opacity=0.55),
            hovertemplate=f"<b>{cat}</b><br>PC1=%{{x:.2f}}, PC2=%{{y:.2f}}<extra></extra>",
        ))
    fig.update_layout(
        margin=dict(l=60, r=170, t=20, b=50), height=420,
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02,
                     title="Categoria de producto", font=dict(size=11)),
        xaxis_title="Componente principal 1 (PC1)", yaxis_title="Componente principal 2 (PC2)",
        font=dict(family="Segoe UI, Arial", size=11),
    )
    fig.update_xaxes(gridcolor="#e8eaf2", zerolinecolor="#e8eaf2")
    fig.update_yaxes(gridcolor="#e8eaf2", zerolinecolor="#e8eaf2")
    return fig


def pca_block():
    """Explica por que se eligio PCA/t-SNE, como funcionan, como se aplicaron,
    y el hallazgo de negocio real que produjeron (no es solo un requisito
    tecnico decorativo: valida la premisa de todo el dashboard)."""
    return f"""
    <div class="section">
      <div class="section-eyebrow">COMPONENTE AVANZADO</div>
      <div class="section-title">Mapa PCA: por que "ubicacion fisica" es, en la practica, "categoria de producto"</div>
      <div class="ns-layout">
        <div class="ns-text">
          <p><b>Por que se eligio PCA + t-SNE:</b> con 61 variables por evento (nutricion, categoria, texto del nombre de producto via TF-IDF, hora y dia), no hay forma de ver a simple vista si los productos forman grupos naturales. PCA se eligio porque es rapido, determinista y preserva la geometria global (sirve para medir cuanta informacion se pierde al reducir dimensiones); t-SNE se agrego porque revela agrupamientos locales no lineales que PCA, al ser lineal, puede pasar por alto.</p>
          <p><b>Como funcionan:</b> PCA busca las combinaciones lineales de variables que capturan la mayor varianza posible (los "componentes principales"); t-SNE ubica cada punto en 2D de forma que puntos parecidos en las 61 dimensiones originales queden cerca entre si.</p>
          <p><b>Como se aplico:</b> <code>src/features.py</code> arma la matriz de 61 columnas (nutricion + one-hot de categoria + TF-IDF de nombre + hora/dia, escalada con StandardScaler); <code>src/reduction.py</code> corre PCA completo (29 de 61 componentes retienen 90% de la varianza) y t-SNE sobre una muestra de 5,000 eventos (perplexity=30, semilla fija 42 para reproducibilidad). El grafico muestra PC1 vs PC2 sobre una muestra de 3,000 eventos coloreados por categoria de producto.</p>
          <p><b>Impacto en el analisis de negocio:</b> los puntos forman grupos casi perfectamente separados por <b>categoria de producto</b>, no al azar. Y en este dataset, <code>location</code> es una funcion determinista de <code>category_name</code> (Refrigerador = Frutas/Verduras + Lacteos + Congelados; Estante = Bebidas; Despensa = Panaderia + Despensa General) &mdash; cada categoria vive en una sola ubicacion. Esto significa que la estructura que organiza <b>todo este dashboard</b> (ubicacion fisica) no es una eleccion arbitraria: es la variable que mas separa a los productos en el espacio de 61 caracteristicas. Tambien explica, desde los datos, por que el Refrigerador concentra el 97% de la perdida &mdash; ahi vive el 92% de los eventos (Frutas y Verduras, la categoria mas perecible).</p>
          <p><b>Interpretacion y limite:</b> esta separacion es principalmente por categoria declarada (estructural), no por comportamiento de desperdicio en si — PCA/t-SNE no usan `classification` (si el evento fue consumo o merma), asi que el mapa no muestra "clusters de riesgo de desperdicio", muestra que la taxonomia de producto domina la varianza. Es una validacion metodologica del enfoque del dashboard, no una fuente de KPIs nuevos.</p>
        </div>
        <div id="pca"></div>
      </div>
    </div>"""


def acciones_block(insights):
    """Selecciona la accion mas representativa por eje (hogar mas critico)."""
    bloques = []
    color_map = {"1.": C["danger"], "2.": C["warning"], "3.": C["success"]}
    iconos = {"1.": "💰", "2.": "🛒", "3.": "❤️"}
    for eje in sorted(insights["eje"].unique()):
        sub = insights[insights["eje"] == eje]
        titulo = sub.iloc[0]["titulo"]
        mensajes = sub.iloc[:3]["mensaje"].tolist()
        items = "".join(f"<li>{m}</li>" for m in mensajes)
        color = color_map.get(eje[:2], C["muted"])
        icono = iconos.get(eje[:2], "•")
        bloques.append(f"""
        <div class="action" style="border-left: 4px solid {color};">
          <div class="action-header"><span class="action-icon">{icono}</span><div>
            <div class="action-eje">{eje}</div>
            <div class="action-titulo">{titulo}</div>
          </div></div>
          <ul class="action-list">{items}</ul>
        </div>""")
    return "<div class='actions-grid'>" + "".join(bloques) + "</div>"


HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Smart Kitchen Intelligence — Impacto de la ubicacion fisica</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: "Segoe UI", Arial, sans-serif; background: {bg}; color: {primary}; }}
  .header {{ background: {primary}; color: #fff; padding: 18px 36px; }}
  .header h1 {{ margin: 0; font-size: 22px; letter-spacing: 0.5px; }}
  .header .question {{ font-style: italic; opacity: 0.85; margin-top: 6px; font-size: 13px; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 16px 24px 32px; }}

  .hero {{ background: linear-gradient(135deg, #fff 0%, #fef2f2 100%); padding: 28px 32px; border-radius: 10px;
           box-shadow: 0 3px 10px rgba(29,43,79,0.08); border-left: 8px solid {danger}; margin-bottom: 20px; }}
  .hero-eyebrow {{ font-size: 11px; letter-spacing: 2px; color: {danger}; font-weight: 700; }}
  .hero-title {{ font-size: 30px; font-weight: 700; line-height: 1.25; margin: 12px 0 14px 0; color: {primary}; }}
  .hero-emph {{ color: {danger}; }}
  .hero-sub {{ font-size: 15px; color: #2a2f3a; line-height: 1.5; }}

  .section {{ background: #fff; border-radius: 10px; padding: 22px 26px; margin-bottom: 18px;
              box-shadow: 0 2px 6px rgba(29,43,79,0.06); }}
  .section-eyebrow {{ font-size: 10px; letter-spacing: 2px; color: {muted}; font-weight: 700; }}
  .section-title {{ font-size: 20px; font-weight: 700; line-height: 1.3; margin: 6px 0 4px 0; color: {primary}; }}
  .section-sub {{ font-size: 13px; color: {muted}; margin-bottom: 16px; line-height: 1.5; }}

  .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }}
  .kpi-card {{ background: #fff; padding: 16px 18px; border-radius: 8px;
               box-shadow: 0 2px 6px rgba(29,43,79,0.06); }}
  .kpi-label {{ font-size: 11px; color: {muted}; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
  .kpi-value {{ font-size: 30px; font-weight: 700; margin: 6px 0 2px 0; }}
  .kpi-sub {{ font-size: 11px; color: {muted}; }}

  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}

  .actions-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .action {{ background: #f7f8fc; padding: 14px 16px; border-radius: 6px; }}
  .action-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
  .action-icon {{ font-size: 24px; }}
  .action-eje {{ font-size: 10px; color: {muted}; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
  .action-titulo {{ font-weight: 700; color: {primary}; font-size: 14px; }}
  .action-list {{ margin: 6px 0 0 0; padding-left: 16px; font-size: 12px; color: #2a2f3a; line-height: 1.45; }}
  .action-list li {{ margin-bottom: 6px; }}

  .anex {{ background: #f0f3fa; padding: 18px 22px; border-radius: 8px; margin-top: 24px; }}
  .anex-title {{ color: {muted}; font-size: 13px; margin: 0 0 6px 0; font-weight: 600; }}
  .anex-note {{ font-style: italic; color: {muted}; font-size: 11px; margin-bottom: 10px; }}

  .footer {{ text-align: center; padding: 20px 0 0 0; color: {muted}; font-size: 11px;
             border-top: 1px solid #e8eaf2; margin-top: 20px; }}

  .benchmark-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 14px; }}
  .benchmark-card {{ background: #f7f8fc; padding: 14px 16px; border-radius: 8px; }}
  .bm-label {{ font-size: 11px; color: {muted}; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 8px; min-height: 28px; }}
  .bm-case {{ font-size: 26px; font-weight: 700; color: {primary}; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }}
  .bm-case-tag {{ font-size: 10px; font-weight: 600; color: {muted}; text-transform: uppercase; letter-spacing: 0.5px; }}
  .bm-vs {{ font-size: 12.5px; color: #2a2f3a; margin-top: 8px; line-height: 1.4; }}
  .bm-source {{ font-size: 10.5px; color: {muted}; font-style: italic; margin-top: 6px; }}
  .benchmark-note {{ font-size: 11.5px; color: {muted}; line-height: 1.55; }}

  .insight {{ font-size: 13px; color: #2a2f3a; margin-bottom: 16px; line-height: 1.5;
              background: #f7f8fc; border-left: 3px solid {secondary}; padding: 8px 12px; border-radius: 4px; }}

  .ns-layout, .ds-layout {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 22px; align-items: start; }}
  .ns-text p, .ds-text p {{ font-size: 13px; line-height: 1.55; color: #2a2f3a; margin: 0 0 10px 0; }}
  .ds-text ul {{ margin: 0 0 4px 0; padding-left: 18px; font-size: 12.5px; color: #2a2f3a; line-height: 1.5; }}
  .ds-text li {{ margin-bottom: 6px; }}

  .ns-legend {{ background: #f7f8fc; border-radius: 8px; padding: 14px 16px; }}
  .ns-chip {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
  .ns-letter {{ width: 28px; height: 28px; border-radius: 6px; color: #fff; font-weight: 700;
                display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }}
  .ns-desc {{ font-size: 12px; color: #2a2f3a; }}
  .ns-groups {{ margin-top: 10px; border-top: 1px solid #e8eaf2; padding-top: 10px; }}
  .ns-group {{ font-size: 11.5px; color: #2a2f3a; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }}
  .ns-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}

  .ds-fact-card {{ background: #f7f8fc; border-radius: 8px; padding: 14px 16px; }}
  .ds-fact-title {{ font-size: 11px; color: {muted}; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; margin-bottom: 10px; }}
  .ds-fact-row {{ display: flex; justify-content: space-between; gap: 10px; font-size: 12px; padding: 5px 0;
                  border-bottom: 1px dashed #e2e5f0; color: #2a2f3a; }}
  .ds-fact-row:last-child {{ border-bottom: none; }}
  .ds-fact-row span {{ color: {muted}; }}

  @media (max-width: 900px) {{
    .kpi-row, .benchmark-grid, .grid-2, .actions-grid, .ns-layout, .ds-layout {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
  <div class="header">
    <h1>SMART KITCHEN INTELLIGENCE (SKI)</h1>
    <div class="question">PREGUNTA DE INVESTIGACION: &iquest;Que impacto tiene la ubicacion fisica (Refrigerador / Despensa / Estante) en la perdida economica y de salud del hogar? &mdash; 10 hogares, 90 dias, 25,819 eventos.</div>
  </div>
  <div class="container">

    {hero}

    {kpi_row}

    {benchmark}

    <div class="grid-2">
      <div class="section">
        <div class="section-eyebrow">DONDE SE PIERDE EL DINERO</div>
        <div class="section-title">Costo total perdido por ubicacion fisica (S/)</div>
        <div class="insight"><b>Insight clave:</b> el {top_loc} concentra el {top_pct:.0f}% de la perdida acumulada (S/ {top_costo:,.0f} de S/ {total_costo:,.0f}) &mdash; dos ordenes de magnitud por encima de la ubicacion mas eficiente.</div>
        <div id="ranking"></div>
      </div>
      <div class="section">
        <div class="section-eyebrow">DONDE SE PIERDE LA SALUD</div>
        <div class="section-title">Costo de alimentos saludables (NutriScore A-B) desperdiciados, por ubicacion</div>
        <div class="insight"><b>Insight clave:</b> S/ {sal_costo:,.0f} en frutas y verduras saludables se pierden en el {sal_loc} &mdash; la perdida no es comida chatarra, es la parte mas nutritiva de la compra.</div>
        <div id="salud"></div>
      </div>
    </div>

    <div class="section">
      <div class="section-eyebrow">CUANDO SE PIERDE</div>
      <div class="section-title">Evolucion semanal del costo perdido, por ubicacion (S/, semanas ISO)</div>
      <div class="insight"><b>Insight clave:</b> el {top_loc} muestra picos sistematicos ligados a las compras grandes de la semana; Despensa y Estante se mantienen practicamente planos.</div>
      <div id="longitudinal"></div>
    </div>

    <div class="section">
      <div class="section-eyebrow">QUE CALIDAD SE PIERDE</div>
      <div class="section-title">Eventos de consumo y desperdicio por ubicacion, segun categoria NutriScore</div>
      <div class="insight"><b>Insight clave:</b> el desperdicio del {top_loc} es mayoritariamente saludable (NutriScore A-B); el de Despensa concentra los productos de menor calidad nutricional (C-D). Leyenda de colores y explicacion del NutriScore abajo.</div>
      <div id="transversal"></div>
    </div>

    {nutriscore}

    <div class="section">
      <div class="section-eyebrow">QUE HACER</div>
      <div class="section-title">3 acciones prescriptivas por hogar</div>
      <div class="section-sub">Recomendaciones automaticas generadas por el pipeline. Cada eje muestra los 3 hogares mas criticos.</div>
      {actions}
    </div>

    {pca}

    {dataset}

    <div class="footer">
      Fuente: pipeline reproducible Smart Kitchen (Python + Plotly). Cobertura 2026-W06 a 2026-W17. &mdash; Universidad Peruana de Ciencias Aplicadas | Data Visualization
    </div>
  </div>
<script>
  {plot_js}
</script>
</body>
</html>"""


def main():
    kpi_hogar, temp, trans, insights, glob = load()
    n = compute_narrative(temp, trans)
    total_compras = kpi_hogar["costo_total_compras"].sum()
    pct_perdido = n["total_costo"] / total_compras * 100

    fig_rank = fig_ranking_ubicacion(n)
    fig_sal = fig_salud(n)
    fig_long = fig_longitudinal(temp)
    fig_trans = fig_transversal(trans)

    plot_calls = [
        f"Plotly.newPlot('ranking', {fig_rank.to_json()}.data, {fig_rank.to_json()}.layout, {{responsive:true, displayModeBar:false}});",
        f"Plotly.newPlot('salud', {fig_sal.to_json()}.data, {fig_sal.to_json()}.layout, {{responsive:true, displayModeBar:false}});",
        f"Plotly.newPlot('longitudinal', {fig_long.to_json()}.data, {fig_long.to_json()}.layout, {{responsive:true, displayModeBar:false}});",
        f"Plotly.newPlot('transversal', {fig_trans.to_json()}.data, {fig_trans.to_json()}.layout, {{responsive:true, displayModeBar:false}});",
    ]

    pca_sample = load_pca_sample()
    if pca_sample is not None:
        fig_pc = fig_pca(pca_sample)
        plot_calls.append(
            f"Plotly.newPlot('pca', {fig_pc.to_json()}.data, {fig_pc.to_json()}.layout, {{responsive:true, displayModeBar:false}});"
        )

    plot_js = "\n  ".join(plot_calls)

    html = HTML.format(
        bg=C["bg"], primary=C["primary"], danger=C["danger"], muted=C["muted"], secondary=C["secondary"],
        hero=hero_block(n),
        kpi_row=kpi_row(kpi_hogar, n, total_compras, pct_perdido),
        benchmark=benchmark_block(n, total_compras, pct_perdido),
        nutriscore=nutriscore_block(),
        dataset=dataset_block(),
        pca=pca_block(),
        top_loc=n["top_loc"], top_pct=n["top_pct"],
        sal_costo=n["saludable_top_costo"], sal_loc=n["saludable_top_loc"],
        top_costo=n["top_costo"], total_costo=n["total_costo"],
        actions=acciones_block(insights),
        plot_js=plot_js,
    )

    OUT.write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {OUT}")
    print(f"Tamano: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

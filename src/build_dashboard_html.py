"""
Dashboard Smart Kitchen Intelligence (SKI) — narrativo, responde la pregunta de negocio.

Pregunta: ¿Que impacto tiene la ubicacion fisica (Refrigerador / Despensa / Estante)
en la perdida economica y de salud del hogar?

Respuesta del dashboard: El Refrigerador concentra el 97% de las perdidas economicas
y desperdicia 64x mas alimentos saludables (A-B) que la Despensa.

Estructura:
  1. HERO: respuesta directa con la cifra mas impactante
  2. KPIs comparativos por ubicacion
  3. Ranking de ubicaciones (donde se pierde el dinero)
  4. Impacto en salud (donde se pierden frutas/verduras saludables)
  5. Evolucion temporal con narrativa
  6. Acciones recomendadas
  7. Anexo metodologico (PCA) - solo si se requiere
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tableau" / "datos_finales"
OUT = ROOT / "tableau" / "Sem12_Dashboard_SmartKitchen.html"

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


def load():
    kpi_hogar = pd.read_csv(DATA / "kpi_por_hogar.csv")
    temp = pd.read_csv(DATA / "agg_temporal_ubicacion.csv")
    trans = pd.read_csv(DATA / "agg_ubicacion_nutriscore.csv")
    insights = pd.read_csv(DATA / "insights_prescriptivos.csv")
    with open(DATA / "kpi_global.json", encoding="utf-8") as f:
        glob = json.load(f)
    return kpi_hogar, temp, trans, insights, glob


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


def kpi_row(kpi_hogar, n):
    cards = [
        dict(label="Perdida total acumulada", value=f"S/ {n['total_costo']:,.0f}",
             sub=f"Concentrada en {n['top_loc']} ({n['top_pct']:.0f}%)", color=C["danger"]),
        dict(label="Tasa de desperdicio", value=f"{n['loc_ranking'].iloc[0]['tasa']:.1f}%",
             sub=f"En {n['top_loc']} (vs {n['loc_ranking'].iloc[2]['tasa']:.1f}% en Estante)", color=C["warning"]),
        dict(label="Estancamiento medio", value=f"{kpi_hogar['kpi4_dias_prom_vencer'].mean():.1f} d",
             sub="Negativo = se vence antes de salir", color=C["caution"]),
        dict(label="Saludables (A-B) perdidos", value=f"S/ {n['saludable_top_costo']:,.0f}",
             sub=f"Frutas/verduras en {n['saludable_top_loc']}", color=C["success"]),
    ]
    return "<div class='kpi-row'>" + "".join(
        f"""<div class="kpi-card" style="border-top: 6px solid {c['color']};">
              <div class="kpi-label">{c['label']}</div>
              <div class="kpi-value" style="color: {c['color']};">{c['value']}</div>
              <div class="kpi-sub">{c['sub']}</div>
            </div>""" for c in cards
    ) + "</div>"


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
        margin=dict(l=60, r=20, t=20, b=60), height=350,
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
        margin=dict(l=180, r=20, t=20, b=40), height=360,
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="Calidad nutricional"),
        xaxis_title="Numero de eventos",
        font=dict(family="Segoe UI, Arial", size=11),
        yaxis=dict(categoryorder="array", categoryarray=orden[::-1]),
    )
    fig.update_xaxes(gridcolor="#e8eaf2")
    return fig


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

    <div class="grid-2">
      <div class="section">
        <div class="section-eyebrow">DONDE SE PIERDE EL DINERO</div>
        <div class="section-title">El {top_loc} concentra {top_pct:.0f}% de las perdidas</div>
        <div class="section-sub">Costo acumulado por ubicacion fisica. La diferencia es de 2 ordenes de magnitud entre el peor y el mejor.</div>
        <div id="ranking"></div>
      </div>
      <div class="section">
        <div class="section-eyebrow">DONDE SE PIERDE LA SALUD</div>
        <div class="section-title">S/ {sal_costo:,.0f} en frutas y verduras saludables se botan en el {sal_loc}</div>
        <div class="section-sub">Doble impacto: financiero y nutricional. Los alimentos A-B (mas saludables) son los que mas se desperdician.</div>
        <div id="salud"></div>
      </div>
    </div>

    <div class="section">
      <div class="section-eyebrow">CUANDO SE PIERDE</div>
      <div class="section-title">El {top_loc} muestra picos sistematicos: las perdidas se concentran en compras grandes</div>
      <div class="section-sub">Evolucion semanal del costo perdido. Las otras 2 ubicaciones son practicamente planas.</div>
      <div id="longitudinal"></div>
    </div>

    <div class="section">
      <div class="section-eyebrow">QUE CALIDAD SE PIERDE</div>
      <div class="section-title">El desperdicio del {top_loc} es predominantemente saludable; el de Despensa concentra ultraprocesados</div>
      <div class="section-sub">Cruce ubicacion x consumo/desperdicio, segmentado por calidad nutricional (Nutriscore A-B verde, C-D ambar, D-E rojo).</div>
      <div id="transversal"></div>
    </div>

    <div class="section">
      <div class="section-eyebrow">QUE HACER</div>
      <div class="section-title">3 acciones prescriptivas por hogar</div>
      <div class="section-sub">Recomendaciones automaticas generadas por el pipeline. Cada eje muestra los 3 hogares mas criticos.</div>
      {actions}
    </div>

    <div class="anex">
      <div class="anex-title">ANEXO METODOLOGICO -- Componente avanzado (PCA / t-SNE)</div>
      <div class="anex-note">Soporte tecnico exigido por la catedra. NO se usa para responder la pregunta de negocio. Disponible en notebook 04_componente_avanzado.ipynb.</div>
    </div>

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

    fig_rank = fig_ranking_ubicacion(n)
    fig_sal = fig_salud(n)
    fig_long = fig_longitudinal(temp)
    fig_trans = fig_transversal(trans)

    plot_js = "\n  ".join([
        f"Plotly.newPlot('ranking', {fig_rank.to_json()}.data, {fig_rank.to_json()}.layout, {{responsive:true, displayModeBar:false}});",
        f"Plotly.newPlot('salud', {fig_sal.to_json()}.data, {fig_sal.to_json()}.layout, {{responsive:true, displayModeBar:false}});",
        f"Plotly.newPlot('longitudinal', {fig_long.to_json()}.data, {fig_long.to_json()}.layout, {{responsive:true, displayModeBar:false}});",
        f"Plotly.newPlot('transversal', {fig_trans.to_json()}.data, {fig_trans.to_json()}.layout, {{responsive:true, displayModeBar:false}});",
    ])

    html = HTML.format(
        bg=C["bg"], primary=C["primary"], danger=C["danger"], muted=C["muted"],
        hero=hero_block(n),
        kpi_row=kpi_row(kpi_hogar, n),
        top_loc=n["top_loc"], top_pct=n["top_pct"],
        sal_costo=n["saludable_top_costo"], sal_loc=n["saludable_top_loc"],
        actions=acciones_block(insights),
        plot_js=plot_js,
    )

    OUT.write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {OUT}")
    print(f"Tamano: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

import json
import copy

import dash
from dash import dcc, html, Input, Output, State, ALL, callback_context
import plotly.graph_objects as go

from data import (
    ALL_PTS, PT_COLORS, PHASE_COLORS, PHASES,
    IMPACT_OPTIONS, IMPACT_UNITS, DEFAULTS,
)
from calculations import get_default_params, compute_impacts, compute_lifetime_points

app = dash.Dash(__name__, title="What are the impacts of road transport vehicles?")
server = app.server

# ── Translations ──────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "en": {
        "vehicleMode":    "Vehicle mode",
        "decarbPace":     "Decarbonisation pace",
        "impactCategory": "Impact category",
        "vehicleParams":  "Vehicle parameters",
        "chartBarTitle":  "Impact contributions per kilometre",
        "chartLineTitle": "Impact evolution over vehicle lifetime",
        "appTitle":       "What are the impacts of road transport vehicles?",
        "totalMileage":   "Total mileage",
        "annualMileage":  "Annual mileage",
        "consumption":    "Consumption",
        "electricPct":    "% electric",
        "kmDriven":       "km driven",
        "Car": "Car", "LCV": "LCV", "Truck": "Truck", "Bus": "Bus",
        "Base": "Slow", "NPi": "Middle", "NDC": "Fast",
        "Vehicle prod.":  "Vehicle prod.",
        "Battery prod.":  "Battery prod.",
        "Well-to-tank":   "Well-to-tank",
        "Tank-to-wheel":  "Tank-to-wheel",
        "Maintenance":    "Maintenance",
        "EoL impacts":    "EoL impacts",
        "EoL savings":    "EoL savings",
    },
    "cs": {
        "vehicleMode":    "Typ vozidla",
        "decarbPace":     "Tempo dekarbonizace",
        "impactCategory": "Kategorie dopadu",
        "vehicleParams":  "Parametry vozidla",
        "chartBarTitle":  "Příspěvky k dopadu na kilometr",
        "chartLineTitle": "Vývoj dopadu po dobu životnosti vozidla",
        "appTitle":       "Jaké jsou dopady silničních vozidel?",
        "totalMileage":   "Celkový nájezd",
        "annualMileage":  "Roční nájezd",
        "consumption":    "Spotřeba",
        "electricPct":    "% elektrický pohon",
        "kmDriven":       "najetých km",
        "Car": "Auto", "LCV": "LUV", "Truck": "Náklaďák", "Bus": "Autobus",
        "Base": "Pomalé", "NPi": "Střední", "NDC": "Rychlé",
        "Vehicle prod.":  "Výroba vozidla",
        "Battery prod.":  "Výroba baterie",
        "Well-to-tank":   "Těžba a doprava paliva",
        "Tank-to-wheel":  "Provoz vozidla",
        "Maintenance":    "Údržba",
        "EoL impacts":    "Konec životnosti",
        "EoL savings":    "Úspory z recyklace",
    },
}

def tr(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))

# ── Popup content ─────────────────────────────────────────────────────────────

POPUP_DATA = {
    "en": {
        "vehicleParams": {
            "title": "Vehicle Parameters",
            "paragraphs": [
                "Car: A medium-size car weighing approximately 1.0 to 1.4 tonnes and designed for five passengers.",
                "LCV: A light commercial vehicle, classified as N1-III, weighing between 1.5 and 1.9 tonnes and functioning as a compact delivery van for commercial purposes.",
                "Truck: A rigid truck weighing approximately 6.4 to 6.9 tonnes with a 7.5 to 12 tonnes payload, designed for freight transport and commercial operations over longer distances.",
                "Bus: An urban midi bus, weighing 12.5 to 13.9 tonnes, carrying dozens of passengers for public transit in urban areas.",
            ],
        },
        "vehicleMode": {
            "title": "Vehicle Mode",
            "paragraphs": [
                "Car: A medium-size car weighing approximately 1.0 to 1.4 tonnes and designed for five passengers.",
                "LCV: A light commercial vehicle, classified as N1-III, weighing between 1.5 and 1.9 tonnes and functioning as a compact delivery van for commercial purposes.",
                "Truck: A rigid truck weighing approximately 6.4 to 6.9 tonnes with a 7.5 to 12 tonnes payload, designed for freight transport and commercial operations over longer distances.",
                "Bus: An urban midi bus, weighing 12.5 to 13.9 tonnes, carrying dozens of passengers for public transit in urban areas.",
            ],
        },
        "decarbPace": {
            "title": "Decarbonisation Pace",
            "paragraphs": [
                "Slow: A business as usual scenario that assumes the pace of decarbonisation will continue at the same rate as in the past.",
                "Middle: 'National Policies Implemented' scenario that assumes no additional climate policies or mitigation measures beyond those currently in place.",
                "Fast: 'Nationally Determined Contributions' scenario that assumes individual countries will set emissions reduction targets in line with the Paris agreement to limit global warming to well below 2°C.",
            ],
        },
        "impactCategories": {
            "title": "Impact Categories",
            "paragraphs": [
                "The 16 life cycle impact categories of the European Commission's Environmental Footprint 3.1 framework are reported in their respective units.",
                "The EF 3.1 indicator represents a normalised, weighted, and aggregated single-score result across all 16 impact categories.",
            ],
        },
        "impactPerKm": {
            "title": "Impact Contributions Per Kilometre",
            "paragraphs": [
                "This chart shows life cycle phase contributions for each powertrain option, expressed per kilometre in the respective unit of the selected impact category.",
                "Negative values represent environmental savings from recycling and material recovery at the vehicle end-of-life.",
            ],
        },
        "impactLifetime": {
            "title": "Impact Evolution Over Vehicle Lifetime",
            "paragraphs": [
                "This chart shows how total environmental impacts accumulate over the vehicle's operational life.",
                "The slightly curved lines reflect gradual changes in the electricity grid's carbon intensity over time.",
                "The sharp drop near the end represents the environmental benefit from recycling and material recovery at end-of-life.",
            ],
        },
    },
    "cs": {
        "vehicleParams": {
            "title": "Parametry vozidla",
            "paragraphs": [
                "Auto: Osobní automobil střední velikosti o hmotnosti přibližně 1,0 až 1,4 tuny, určený pro pět cestujících.",
                "Dodávka: Lehké užitkové vozidlo kategorie N1-III o hmotnosti 1,5 až 1,9 tuny, sloužící jako kompaktní dodávkové vozidlo pro komerční účely.",
                "Náklaďák: Pevný nákladní automobil o hmotnosti přibližně 6,4 až 6,9 tuny s užitečným zatížením 7,5 až 12 tun, určený pro nákladní dopravu a komerční provoz na delší vzdálenosti.",
                "Autobus: Městský midi autobus o hmotnosti 12,5 až 13,9 tuny, přepravující desítky cestujících v rámci městské hromadné dopravy.",
            ],
        },
        "vehicleMode": {
            "title": "Typ vozidla",
            "paragraphs": [
                "Auto: Osobní automobil střední velikosti o hmotnosti přibližně 1,0 až 1,4 tuny, určený pro pět cestujících.",
                "Dodávka: Lehké užitkové vozidlo kategorie N1-III o hmotnosti 1,5 až 1,9 tuny, sloužící jako kompaktní dodávkové vozidlo pro komerční účely.",
                "Náklaďák: Pevný nákladní automobil o hmotnosti přibližně 6,4 až 6,9 tuny s užitečným zatížením 7,5 až 12 tun, určený pro nákladní dopravu a komerční provoz na delší vzdálenosti.",
                "Autobus: Městský midi autobus o hmotnosti 12,5 až 13,9 tuny, přepravující desítky cestujících v rámci městské hromadné dopravy.",
            ],
        },
        "decarbPace": {
            "title": "Tempo dekarbonizace",
            "paragraphs": [
                "Pomalé: Scénář „business as usual“, který předpokládá, že tempo dekarbonizace bude pokračovat stejnou rychlostí jako v minulosti.",
                "Střední: Scénář „National Policies Implemented“, který nepředpokládá žádné dodatečné klimatické politiky ani mitigační opatření nad rámec těch, která jsou již v současnosti zavedena.",
                "Rychlé: Scénář „Nationally Determined Contributions“, který předpokládá, že jednotlivé státy stanovi cíle snižování emisí v souladu s Pařížskou dohodou, tedy s cílem omezit globální oteplování výrazně pod 2 °C.",
            ],
        },
        "impactCategories": {
            "title": "Kategorie dopadu",
            "paragraphs": [
                "Šestnáct kategorií dopadu podle rámce Environmental Footprint 3.1 Evropské komise vykazovaných v příslušných jednotkách.",
                "Ukazatel EF 3.1 představuje normalizovaný, vážený a agregovaný výsledek shrnující všech 16 kategorií dopadu.",
            ],
        },
        "impactPerKm": {
            "title": "Příspěvky k dopadům na kilometr",
            "paragraphs": [
                "Tento graf zobrazuje příspěvky jednotlivých fází životního cyklu pro každou variantu pohonu, vyjádřené na kilometr v příslušné jednotce zvolené kategorie dopadu.",
                "Záporné hodnoty představují environmentální úspory plynoucí z recyklace a materiálového využití na konci životního cyklu vozidla.",
            ],
        },
        "impactLifetime": {
            "title": "Vývoj dopadů během životnosti vozidla",
            "paragraphs": [
                "Tento graf zobrazuje, jak se celkové environmentální dopady kumulují během provozní životnosti vozidla.",
                "Mírně zakřivené linie odrážejí postupné změny elektrické sítě v čase.",
                "Prudký pokles v závěrečné části představuje environmentální přínos recyklace a materiálového využití na konci životního cyklu.",
            ],
        },
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_val(v):
    if abs(v) < 0.001:
        return f"{v:.2e}"
    if abs(v) < 1:
        return f"{v:.3f}"
    return f"{v:.2f}"

def fmt_km(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M km"
    return f"{round(v/1000):.0f}k km"

def fmt_annual(v):
    return f"{round(v/1000):.0f},{round(v%1000):03d} km" if v >= 1000 else f"{round(v)} km"

LABEL_STYLE = {
    "fontSize": "9px", "color": "#aaa",
    "letterSpacing": "0.06em", "textTransform": "uppercase",
    "fontFamily": "'IBM Plex Mono', monospace",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────

def make_slider_row(pt, key, label, min_val, max_val, current_val, unit, step=None, lang="en"):
    if step is None:
        if key in ("totalKm", "annualKm"):
            step = max(1, round((max_val - min_val) / 100))
        elif max_val <= 100:
            step = 1
        else:
            step = max(0.1, round((max_val - min_val) / 100, 2))
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize": "10.5px", "color": "#5a5750"}),
            html.Div([
                dcc.Input(
                    id={"type": "slider-val", "pt": pt, "key": key},
                    type="number",
                    value=round(current_val, 4),
                    debounce=True,
                    style={
                        "fontSize": "10px", "fontFamily": "'IBM Plex Mono', monospace",
                        "color": "#1a1917", "width": "68px", "textAlign": "right",
                        "border": "none", "borderBottom": "1px dashed #bbb",
                        "background": "transparent", "outline": "none", "padding": "0 2px",
                        "MozAppearance": "textfield",
                    },
                ),
                html.Span(unit, style={
                    "fontSize": "10px", "fontFamily": "'IBM Plex Mono', monospace",
                    "color": "#5a5750", "marginLeft": "3px", "whiteSpace": "nowrap",
                }),
            ], style={"display": "flex", "alignItems": "baseline"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "baseline", "marginBottom": "0px"}),
        dcc.Slider(
            id={"type": "param-slider", "pt": pt, "key": key},
            min=min_val, max=max_val, step=step, value=current_val,
            marks=None, tooltip={"always_visible": False}, className="vlca-slider",
            updatemode="mouseup",
        ),
    ], style={"marginBottom": "0px"})


def build_sidebar(vtype, params, hidden_pts, lang="en"):
    hidden_set = set(hidden_pts or [])
    active_pts = [pt for pt in ALL_PTS if DEFAULTS.get(vtype, {}).get(pt)]
    sections = []
    for pt in active_pts:
        p = params.get(pt)
        if not p:
            continue
        defn = DEFAULTS[vtype][pt]
        color = PT_COLORS[pt]
        is_phev = bool(defn.get("isPhev"))
        is_hidden = pt in hidden_set

        is_fcev = (pt == "FCEV")
        if is_phev:
            cons_min, cons_max, cons_step = 0, 100, 1
            cons_unit = "%"
        elif is_fcev:
            fcev_ranges = {
                "Car":   (0.40,  2.00, 0.01),
                "LCV":   (0.60,  4.00, 0.01),
                "Truck": (1.20,  8.00, 0.05),
                "Bus":   (3.00, 15.00, 0.05),
            }
            cons_min, cons_max, cons_step = fcev_ranges.get(vtype, (0.40, 2.00, 0.01))
            cons_unit = defn["unit1"]
        else:
            cons_min, cons_max, cons_step = defn["cons1"] * 0.5, defn["cons1"] * 2.0, None
            cons_unit = defn["unit1"]
        km_min = round(defn["totalKm"] * 0.4)
        km_max = round(defn["totalKm"] * 2.0)
        ann_min = round(defn["annualKm"] * 0.4)
        ann_max = round(defn["annualKm"] * 2.0)

        name_style = {
            "display": "flex", "alignItems": "center", "gap": "6px",
            "fontSize": "11.5px", "fontWeight": "600", "cursor": "pointer",
            "borderRadius": "3px", "padding": "2px 4px", "marginLeft": "-4px",
            "marginBottom": "4px", "transition": "background 0.1s",
            "opacity": "0.35" if is_hidden else "1",
            "textDecoration": "line-through" if is_hidden else "none",
        }

        # Translate "% electric" label for PHEV
        disp_unit = tr(lang, "electricPct") if is_phev else cons_unit
        sliders = [] if is_hidden else [
            make_slider_row(pt, "cons1", tr(lang, "consumption"),
                            cons_min, cons_max, p["cons1"], disp_unit,
                            step=cons_step, lang=lang),
            make_slider_row(pt, "totalKm", tr(lang, "totalMileage"),
                            km_min, km_max, p["totalKm"], "km", lang=lang),
            make_slider_row(pt, "annualKm", tr(lang, "annualMileage"),
                            ann_min, ann_max, p["annualKm"], "km/yr", lang=lang),
        ]

        sections.append(html.Div([
            html.Div(
                [html.Div(style={"width": "8px", "height": "8px", "borderRadius": "50%",
                                 "background": color, "flexShrink": "0"}),
                 html.Span(pt, style={"color": color})],
                id={"type": "sidebar-pt-toggle", "pt": pt},
                n_clicks=0,
                style=name_style,
            ),
            *sliders,
        ], style={"padding": "3px 12px 4px", "borderTop": "1px solid #e2e0db"}))
    return sections


# ── Summary strip ─────────────────────────────────────────────────────────────

def build_summary(vtype, results, impact, hidden_pts):
    hidden_set = set(hidden_pts or [])
    unit = IMPACT_UNITS[impact]
    active_pts = [pt for pt in ALL_PTS if DEFAULTS.get(vtype, {}).get(pt)]
    children = []

    # Visible PT cards
    for pt in active_pts:
        r = results.get(pt)
        if not r or pt in hidden_set:
            continue
        color = PT_COLORS[pt]
        children.append(html.Div([
            html.Div(pt,   style={"fontSize": "10px", "fontWeight": "600",
                                  "letterSpacing": "0.04em", "color": color, "marginBottom": "1px"}),
            html.Div(fmt_val(r["total"]),
                     style={"fontSize": "20px", "fontWeight": "600",
                            "fontFamily": "'IBM Plex Mono', monospace",
                            "lineHeight": "1", "color": "#1a1917", "marginBottom": "1px"}),
            html.Div(unit, style={"fontSize": "9px", "color": "#9a948c",
                                  "fontFamily": "'IBM Plex Mono', monospace"}),
        ], id={"type": "summary-pt-toggle", "pt": pt}, n_clicks=0,
           style={"display": "flex", "flexDirection": "column", "alignItems": "flex-start",
                  "padding": "4px 10px 4px 8px", "borderLeft": f"3px solid {color}",
                  "minWidth": "88px", "flexShrink": "0", "cursor": "pointer",
                  "borderRadius": "0 3px 3px 0"}))

    # Separator + hidden PT chips
    hidden_here = [pt for pt in active_pts if pt in hidden_set]
    if hidden_here:
        children.append(html.Div(style={"width": "1px", "height": "32px",
                                        "background": "#e2e0db", "flexShrink": "0",
                                        "alignSelf": "center", "margin": "0 4px"}))
        for pt in hidden_here:
            color = PT_COLORS[pt]
            children.append(html.Div(pt,
                id={"type": "summary-pt-toggle", "pt": pt}, n_clicks=0,
                style={"fontSize": "10px", "fontWeight": "600", "color": color,
                       "border": f"1px dashed {color}", "borderRadius": "3px",
                       "padding": "3px 8px", "cursor": "pointer", "flexShrink": "0",
                       "opacity": "0.6"}))
    return children


# ── Bar chart ─────────────────────────────────────────────────────────────────

def build_bar_chart(results, hidden_pts, hidden_phases, impact="climateChange"):
    hidden_set = set(hidden_pts or [])
    hidden_ph  = set(hidden_phases or [])
    active_pts = [pt for pt in ALL_PTS if results.get(pt) and pt not in hidden_set]
    if not active_pts:
        return go.Figure()

    fig = go.Figure()
    pos_phases = [p for p in PHASES if p != "EoL savings"]
    neg_phases  = ["EoL savings"]

    for phase in pos_phases:
        visible = phase not in hidden_ph
        vals = [results[pt]["phases"].get(phase, 0) for pt in active_pts]
        fig.add_trace(go.Bar(
            name=phase, x=active_pts, y=vals,
            marker_color=PHASE_COLORS[phase],
            visible=True if visible else "legendonly",
            showlegend=False,
        ))

    for phase in neg_phases:
        visible = phase not in hidden_ph
        vals = [results[pt]["phases"].get(phase, 0) for pt in active_pts]
        fig.add_trace(go.Bar(
            name=phase, x=active_pts, y=vals,
            marker_color=PHASE_COLORS[phase], marker_opacity=0.85,
            visible=True if visible else "legendonly",
            showlegend=False,
        ))

    # Colored bold x-axis labels via annotations (tickfont only supports one color)
    annotations = [
        dict(
            x=pt, y=0,
            xref="x", yref="paper",
            text=f"<b>{pt}</b>",
            showarrow=False,
            yanchor="top", yshift=-6,
            font=dict(size=10.5, color=PT_COLORS[pt], family="IBM Plex Sans"),
        )
        for pt in active_pts
    ]

    y_unit = IMPACT_UNITS.get(impact, "")

    fig.update_layout(
        barmode="relative",
        paper_bgcolor="#f7f6f3", plot_bgcolor="#f7f6f3",
        margin=dict(l=62, r=8, t=4, b=40),
        showlegend=False,
        annotations=annotations,
        xaxis=dict(
            showticklabels=False,
            showline=False, gridcolor="rgba(0,0,0,0)",
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text=y_unit,
                       font=dict(size=9, color="#9a948c", family="IBM Plex Mono")),
            gridcolor="#e8e5e0", zerolinecolor="#bbb", zerolinewidth=1.5,
            tickfont=dict(size=9, family="IBM Plex Mono", color="#9a948c"),
            showline=False,
        ),
        font=dict(family="IBM Plex Sans"),
    )
    return fig


def build_bar_legend(hidden_phases, lang="en"):
    hidden_ph = set(hidden_phases or [])
    items = []
    for phase in PHASES:
        is_hidden = phase in hidden_ph
        items.append(html.Div([
            html.Div(style={
                "width": "9px", "height": "9px", "borderRadius": "2px",
                "background": PHASE_COLORS[phase], "flexShrink": "0",
                "opacity": "0.3" if is_hidden else "1",
            }),
            html.Span(tr(lang, phase), style={
                "fontSize": "10px", "color": "#5a5750" if not is_hidden else "#bbb",
                "textDecoration": "line-through" if is_hidden else "none",
            }),
        ], id={"type": "bar-legend-phase-toggle", "phase": phase}, n_clicks=0,
           style={"display": "flex", "alignItems": "center", "gap": "5px",
                  "cursor": "pointer", "userSelect": "none"}))
    return html.Div(items, style={
        "display": "flex", "gap": "10px", "flexWrap": "wrap",
        "marginBottom": "8px", "flexShrink": "0",
    })


# ── Line chart ────────────────────────────────────────────────────────────────

def build_line_chart(vtype, trajectory, impact, params, results, hidden_pts, lang="en"):
    hidden_set = set(hidden_pts or [])
    fig = go.Figure()

    for pt in ALL_PTS:
        if not results.get(pt) or pt in hidden_set:
            continue
        pts = compute_lifetime_points(vtype, trajectory, impact, params, pt)
        if not pts:
            continue
        xs = [p["km"] for p in pts]
        ys = [p["val"] for p in pts]
        color = PT_COLORS[pt]

        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", name=pt,
            line=dict(color=color, width=2), showlegend=False,
        ))
        if xs:
            fig.add_annotation(
                x=xs[-1], y=ys[-1], text=pt, showarrow=False,
                xanchor="left", xshift=4,
                font=dict(size=10, color=color, family="IBM Plex Sans"),
            )

    per_km_unit = IMPACT_UNITS.get(impact, "")
    base_unit   = per_km_unit.replace("/km", "").strip()

    fig.update_layout(
        paper_bgcolor="#f7f6f3", plot_bgcolor="#f7f6f3",
        margin=dict(l=62, r=60, t=4, b=36),
        showlegend=False,
        xaxis=dict(
            title=dict(text=tr(lang, "kmDriven"),
                       font=dict(size=9, color="#9a948c", family="IBM Plex Mono")),
            gridcolor="#e8e5e0",
            tickfont=dict(size=9, family="IBM Plex Mono", color="#9a948c"),
            showline=False,
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text=base_unit,
                       font=dict(size=9, color="#9a948c", family="IBM Plex Mono")),
            gridcolor="#e8e5e0", zerolinecolor="#bbb", zerolinewidth=1.5,
            tickfont=dict(size=9, family="IBM Plex Mono", color="#9a948c"),
            showline=False,
        ),
        font=dict(family="IBM Plex Sans"),
    )
    return fig


def build_line_legend(vtype, results, hidden_pts):
    hidden_set = set(hidden_pts or [])
    active_pts = [pt for pt in ALL_PTS if DEFAULTS.get(vtype, {}).get(pt)]
    items = []
    for pt in active_pts:
        is_hidden = pt in hidden_set
        color = PT_COLORS[pt]
        items.append(html.Div([
            html.Div(style={
                "width": "16px", "height": "2.5px", "borderRadius": "1px",
                "background": color, "flexShrink": "0",
                "opacity": "0.3" if is_hidden else "1",
            }),
            html.Span(pt, style={
                "fontSize": "10px", "color": "#5a5750" if not is_hidden else "#bbb",
                "textDecoration": "line-through" if is_hidden else "none",
            }),
        ], id={"type": "line-legend-pt-toggle", "pt": pt}, n_clicks=0,
           style={"display": "flex", "alignItems": "center", "gap": "5px",
                  "cursor": "pointer", "userSelect": "none"}))
    return html.Div(items, style={
        "display": "flex", "gap": "10px", "flexWrap": "wrap",
        "marginBottom": "8px", "flexShrink": "0",
    })


# ── Layout ────────────────────────────────────────────────────────────────────

def _vtype_tab_style(vt, active):
    s = {"padding": "4px 12px", "borderRadius": "3px", "fontSize": "12px",
         "fontWeight": "500", "cursor": "pointer", "letterSpacing": "0.01em",
         "border": "1px solid transparent", "transition": "all 0.12s"}
    s.update({"background": "#f7f6f3", "color": "#1a1917"} if vt == active
              else {"background": "transparent", "color": "#aaa"})
    return s

def _traj_tab_style(tr, active):
    s = {"padding": "4px 11px", "borderRadius": "3px", "fontSize": "11.5px",
         "cursor": "pointer", "whiteSpace": "nowrap", "transition": "all 0.12s"}
    s.update({"background": "#3d8c6f", "color": "#fff", "border": "1px solid #3d8c6f"}
             if tr == active else
             {"background": "transparent", "color": "#aaa", "border": "1px solid #444"})
    return s


POPUP_TRIGGER_STYLE = {
    "display": "inline-flex", "alignItems": "center", "justifyContent": "center",
    "width": "14px", "height": "14px", "borderRadius": "50%",
    "background": "#888", "color": "#fff", "fontSize": "9px", "fontWeight": "700",
    "cursor": "help", "flexShrink": "0", "marginLeft": "4px",
    "transition": "background 0.15s", "userSelect": "none",
}

def popup_trigger(key):
    """Small ? circle that opens a popup."""
    return html.Span("?", className="popup-trigger",
                     **{"data-popup": key}, style=POPUP_TRIGGER_STYLE)


app.layout = html.Div([

    # ── Stores ────────────────────────────────────────────────────────────────
    dcc.Store(id="params-store",        data=json.dumps(get_default_params("Car"))),
    dcc.Store(id="vtype-store",         data="Car"),
    dcc.Store(id="trajectory-store",    data="Base"),
    dcc.Store(id="hidden-pts-store",    data=[]),
    dcc.Store(id="hidden-phases-store", data=[]),
    dcc.Store(id="lang-store",          data="en"),

    # ── Popup overlay ─────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Button("×", id="popup-close",
                        style={"position": "absolute", "top": "10px", "right": "10px",
                               "border": "none", "background": "none", "fontSize": "20px",
                               "cursor": "pointer", "color": "#999", "lineHeight": "1",
                               "padding": "0 4px"}),
            html.Div(id="popup-title",
                     style={"fontSize": "16px", "fontWeight": "600",
                            "marginBottom": "14px", "paddingRight": "28px",
                            "color": "#1a1917"}),
            html.Div(id="popup-body"),
        ], style={"background": "#fff", "border": "1px solid #ccc",
                  "borderRadius": "8px", "padding": "22px",
                  "maxWidth": "500px", "width": "90%",
                  "maxHeight": "80vh", "overflowY": "auto",
                  "boxShadow": "0 8px 24px rgba(0,0,0,0.18)",
                  "position": "relative"}),
    ], id="popup-overlay",
       style={"display": "none", "position": "fixed", "top": "0", "left": "0",
              "right": "0", "bottom": "0", "background": "rgba(0,0,0,0.4)",
              "alignItems": "center", "justifyContent": "center", "zIndex": "9999"}),

    # ── TOP BAR ──────────────────────────────────────────────────────────────
    html.Div([
        html.Span("What are the impacts of road transport vehicles?",
                  id="app-title",
                  style={"fontSize": "13px", "fontWeight": "500",
                         "letterSpacing": "0.02em", "whiteSpace": "nowrap",
                         "color": "#f7f6f3", "flexShrink": "1",
                         "overflow": "hidden", "textOverflow": "ellipsis"}),
        html.Div(style={"width": "1px", "height": "20px",
                        "background": "#444", "flexShrink": "0"}),

        # Vehicle mode group
        html.Div([
            html.Span("Vehicle mode", id="label-vehicle-mode", style=LABEL_STYLE),
            html.Div([
                html.Div([
                    html.Div(vt, id={"type": "vtype-tab", "vtype": vt}, n_clicks=0,
                             style=_vtype_tab_style(vt, "Car"))
                    for vt in ["Car", "LCV", "Truck", "Bus"]
                ], style={"display": "flex", "gap": "3px"}),
                popup_trigger("vehicleMode"),
            ], style={"display": "flex", "alignItems": "center", "gap": "4px"}),
        ], style={"display": "flex", "flexDirection": "column", "gap": "3px"}),

        html.Div(style={"width": "1px", "height": "20px",
                        "background": "#444", "flexShrink": "0"}),

        # Decarbonisation pace group
        html.Div([
            html.Span("Decarbonisation pace", id="label-decarb-pace", style=LABEL_STYLE),
            html.Div([
                html.Div([
                    html.Div(label, id={"type": "traj-tab", "traj": traj}, n_clicks=0,
                             style=_traj_tab_style(traj, "Base"))
                    for traj, label in [("Base", "Slow"),
                                        ("NPi",  "Middle"),
                                        ("NDC",  "Fast")]
                ], style={"display": "flex", "gap": "3px"}),
                popup_trigger("decarbPace"),
            ], style={"display": "flex", "alignItems": "center", "gap": "4px"}),
        ], style={"display": "flex", "flexDirection": "column", "gap": "3px"}),

        # Impact category + EN/CZ (margin-left: auto pushes to right)
        html.Div([
            html.Span("Impact category", id="label-impact-category", style=LABEL_STYLE),
            html.Div([
                dcc.Dropdown(
                    id="impact-select",
                    options=IMPACT_OPTIONS,
                    value="climateChange",
                    clearable=False, searchable=False,
                    style={"minWidth": "300px", "fontSize": "12px",
                           "fontFamily": "'IBM Plex Sans', sans-serif",
                           "color": "#000000"},
                ),
                popup_trigger("impactCategories"),
                # EN / CZ toggle
                html.Div([
                    html.Button("EN", id="lang-btn-en", n_clicks=0,
                                style={"padding": "0 9px", "height": "26px",
                                       "fontSize": "11px", "fontWeight": "600",
                                       "letterSpacing": "0.04em", "cursor": "pointer",
                                       "border": "none", "borderRight": "1px solid #444",
                                       "background": "#f7f6f3", "color": "#1a1917",
                                       "fontFamily": "'IBM Plex Sans', sans-serif",
                                       "transition": "all 0.12s"}),
                    html.Button("CZ", id="lang-btn-cs", n_clicks=0,
                                style={"padding": "0 9px", "height": "26px",
                                       "fontSize": "11px", "fontWeight": "600",
                                       "letterSpacing": "0.04em", "cursor": "pointer",
                                       "border": "none",
                                       "background": "#2a2927", "color": "#aaa",
                                       "fontFamily": "'IBM Plex Sans', sans-serif",
                                       "transition": "all 0.12s"}),
                ], style={"display": "flex", "border": "1px solid #444",
                          "borderRadius": "3px", "overflow": "hidden",
                          "flexShrink": "0"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "6px"}),
        ], style={"display": "flex", "flexDirection": "column",
                  "gap": "3px", "marginLeft": "auto"}),

    ], style={
        "background": "#242424", "color": "#f7f6f3",
        "padding": "0 20px", "display": "flex", "alignItems": "center",
        "gap": "16px", "height": "56px", "flexShrink": "0",
        "borderBottom": "1px solid #333",
        "fontFamily": "'IBM Plex Sans', sans-serif",
        "overflow": "visible",
    }),

    # ── MAIN ─────────────────────────────────────────────────────────────────
    html.Div([

        # SIDEBAR
        html.Div([
            html.Div([
                html.Span("Vehicle parameters", id="label-vehicle-params",
                          style={"fontSize": "10px", "fontWeight": "600",
                                 "letterSpacing": "0.08em", "textTransform": "uppercase",
                                 "color": "#9a948c"}),
                popup_trigger("vehicleParams"),
            ], style={"display": "flex", "alignItems": "center",
                      "padding": "8px 12px 6px",
                      "borderBottom": "1px solid #e2e0db", "flexShrink": "0"}),
            html.Div(id="sidebar-content",
                     style={"overflowY": "auto", "flex": "1",
                            "padding": "8px 0 16px"}),
        ], style={"width": "224px", "flexShrink": "0",
                  "borderRight": "1px solid #e2e0db", "background": "#ffffff",
                  "display": "flex", "flexDirection": "column", "overflow": "hidden"}),

        # RIGHT PANEL
        html.Div([
            # Summary strip
            html.Div(id="summary-strip",
                     style={"background": "#ffffff", "borderBottom": "1px solid #e2e0db",
                            "padding": "8px 16px", "display": "flex", "gap": "8px",
                            "alignItems": "center", "flexShrink": "0",
                            "overflowX": "auto", "minHeight": "56px"}),

            # Charts
            html.Div([
                # Bar chart
                html.Div([
                    html.Div([
                        html.Span("Impact contributions per kilometre",
                                  id="label-bar-title",
                                  style={"fontSize": "12.5px", "fontWeight": "600",
                                         "color": "#1a1917"}),
                        popup_trigger("impactPerKm"),
                    ], style={"display": "flex", "alignItems": "center", "gap": "6px",
                              "marginBottom": "6px", "flexShrink": "0"}),
                    html.Div(id="bar-legend"),
                    dcc.Graph(id="bar-chart", config={"displayModeBar": False},
                              style={"flex": "1", "minHeight": "0", "background": "#f7f6f3"},
                              responsive=True),
                ], style={"display": "flex", "flexDirection": "column",
                           "padding": "14px 16px 12px", "overflow": "hidden",
                           "minHeight": "0", "flex": "1"}),

                # Line chart
                html.Div([
                    html.Div([
                        html.Span("Impact evolution over vehicle lifetime",
                                  id="label-line-title",
                                  style={"fontSize": "12.5px", "fontWeight": "600",
                                         "color": "#1a1917"}),
                        popup_trigger("impactLifetime"),
                    ], style={"display": "flex", "alignItems": "center", "gap": "6px",
                              "marginBottom": "6px", "flexShrink": "0"}),
                    html.Div(id="line-legend"),
                    dcc.Graph(id="line-chart", config={"displayModeBar": False},
                              style={"flex": "1", "minHeight": "0", "background": "#f7f6f3"},
                              responsive=True),
                ], style={"display": "flex", "flexDirection": "column",
                           "padding": "14px 16px 12px", "overflow": "hidden",
                           "minHeight": "0", "flex": "1",
                           "borderLeft": "1px solid #e2e0db"}),
            ], style={"display": "flex", "flex": "1",
                      "minHeight": "0", "overflow": "hidden"}),

        ], style={"flex": "1", "display": "flex", "flexDirection": "column",
                  "overflow": "hidden", "minWidth": "0"}),

    ], style={"display": "flex", "flex": "1",
              "overflow": "hidden", "minHeight": "0"}),

], style={
    "minHeight": "100vh", "height": "100vh",
    "display": "flex", "flexDirection": "column", "overflow": "hidden",
    "fontFamily": "'IBM Plex Sans', sans-serif",
    "fontSize": "13px", "color": "#1a1917", "background": "#f7f6f3",
})


# ── Callbacks ─────────────────────────────────────────────────────────────────

# 1. Vehicle type tab → reset vtype, params, and hidden sets
@app.callback(
    Output("vtype-store",      "data"),
    Output("params-store",     "data"),
    Output("hidden-pts-store", "data"),
    Input({"type": "vtype-tab", "vtype": ALL}, "n_clicks"),
    State("vtype-store", "data"),
    prevent_initial_call=True,
)
def update_vtype(_, current_vtype):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    new_vtype = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["vtype"]
    return new_vtype, json.dumps(get_default_params(new_vtype)), []


# 2. Trajectory tab
@app.callback(
    Output("trajectory-store", "data"),
    Input({"type": "traj-tab", "traj": ALL}, "n_clicks"),
    State("trajectory-store", "data"),
    prevent_initial_call=True,
)
def update_trajectory(_, current_traj):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    return json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["traj"]


# 3. Slider move → update params
@app.callback(
    Output("params-store", "data", allow_duplicate=True),
    Input({"type": "param-slider", "pt": ALL, "key": ALL}, "value"),
    State("params-store", "data"),
    prevent_initial_call=True,
)
def update_params(_, params_json):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    params = json.loads(params_json)
    changed = False
    for trigger in ctx.triggered:
        try:
            id_dict = json.loads(trigger["prop_id"].split(".")[0])
            pt, key = id_dict["pt"], id_dict["key"]
            new_val = trigger["value"]
            if new_val is None:
                continue
            if pt in params and key in params[pt]:
                if round(float(params[pt][key]), 6) != round(float(new_val), 6):
                    params[pt][key] = float(new_val)
                    changed = True
        except Exception:
            pass
    if not changed:
        raise dash.exceptions.PreventUpdate
    return json.dumps(params)


# 3b. Editable input → update params
@app.callback(
    Output("params-store", "data", allow_duplicate=True),
    Input({"type": "slider-val", "pt": ALL, "key": ALL}, "value"),
    State("params-store", "data"),
    prevent_initial_call=True,
)
def update_params_from_input(_, params_json):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    params = json.loads(params_json)
    changed = False
    for trigger in ctx.triggered:
        try:
            id_dict = json.loads(trigger["prop_id"].split(".")[0])
            if id_dict.get("type") != "slider-val":
                continue
            pt, key = id_dict["pt"], id_dict["key"]
            new_val = trigger["value"]
            if new_val is None:
                continue
            new_val = float(new_val)
            if pt in params and key in params[pt]:
                if round(float(params[pt][key]), 6) != round(new_val, 6):
                    params[pt][key] = new_val
                    changed = True
        except Exception:
            pass
    if not changed:
        raise dash.exceptions.PreventUpdate
    return json.dumps(params)


# 4. PT toggle (sidebar name, summary card, or line legend click)
@app.callback(
    Output("hidden-pts-store", "data", allow_duplicate=True),
    Input({"type": "sidebar-pt-toggle",  "pt": ALL}, "n_clicks"),
    Input({"type": "summary-pt-toggle",  "pt": ALL}, "n_clicks"),
    Input({"type": "line-legend-pt-toggle", "pt": ALL}, "n_clicks"),
    State("hidden-pts-store", "data"),
    prevent_initial_call=True,
)
def toggle_pt(*args):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    # Ignore spurious fires caused by component re-renders resetting n_clicks to 0
    trigger = ctx.triggered[0]
    if not trigger["value"]:
        raise dash.exceptions.PreventUpdate
    hidden = set(args[-1] or [])
    try:
        prop_id_obj = json.loads(trigger["prop_id"].split(".")[0])
        # Only act on recognised PT-toggle types; ignore anything else
        if prop_id_obj.get("type") not in (
            "sidebar-pt-toggle", "summary-pt-toggle", "line-legend-pt-toggle"
        ):
            raise dash.exceptions.PreventUpdate
        pt = prop_id_obj["pt"]
        if pt in hidden:
            hidden.discard(pt)
        else:
            hidden.add(pt)
    except dash.exceptions.PreventUpdate:
        raise
    except Exception:
        raise dash.exceptions.PreventUpdate
    return list(hidden)


# 5. Phase toggle (bar legend click)
@app.callback(
    Output("hidden-phases-store", "data"),
    Input({"type": "bar-legend-phase-toggle", "phase": ALL}, "n_clicks"),
    State("hidden-phases-store", "data"),
    prevent_initial_call=True,
)
def toggle_phase(_, hidden_phases):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    trigger = ctx.triggered[0]
    if not trigger["value"]:
        raise dash.exceptions.PreventUpdate
    hidden = set(hidden_phases or [])
    try:
        prop_id_obj = json.loads(trigger["prop_id"].split(".")[0])
        if prop_id_obj.get("type") != "bar-legend-phase-toggle":
            raise dash.exceptions.PreventUpdate
        phase = prop_id_obj["phase"]
        if phase in hidden:
            hidden.discard(phase)
        else:
            hidden.add(phase)
    except dash.exceptions.PreventUpdate:
        raise
    except Exception:
        raise dash.exceptions.PreventUpdate
    return list(hidden)


# 6a. Language toggle
@app.callback(
    Output("lang-store",  "data"),
    Output("lang-btn-en", "style"),
    Output("lang-btn-cs", "style"),
    Output("label-vehicle-mode",    "children"),
    Output("label-decarb-pace",     "children"),
    Output("label-impact-category", "children"),
    Output("label-vehicle-params",  "children"),
    Output("label-bar-title",       "children"),
    Output("label-line-title",      "children"),
    Output("app-title",             "children"),
    Output({"type": "traj-tab",  "traj":  "Base"},  "children"),
    Output({"type": "traj-tab",  "traj":  "NPi"},   "children"),
    Output({"type": "traj-tab",  "traj":  "NDC"},   "children"),
    Output({"type": "vtype-tab", "vtype": "Car"},   "children"),
    Output({"type": "vtype-tab", "vtype": "LCV"},   "children"),
    Output({"type": "vtype-tab", "vtype": "Truck"}, "children"),
    Output({"type": "vtype-tab", "vtype": "Bus"},   "children"),
    Input("lang-btn-en", "n_clicks"),
    Input("lang-btn-cs", "n_clicks"),
    State("lang-store",  "data"),
    prevent_initial_call=True,
)
def toggle_lang(n_en, n_cs, current_lang):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    lang = "cs" if triggered_id == "lang-btn-cs" else "en"
    active_style   = {"padding": "0 9px", "height": "26px", "fontSize": "11px",
                      "fontWeight": "600", "letterSpacing": "0.04em", "cursor": "pointer",
                      "border": "none", "borderRight": "1px solid #444",
                      "background": "#f7f6f3", "color": "#1a1917",
                      "fontFamily": "'IBM Plex Sans', sans-serif", "transition": "all 0.12s"}
    inactive_style = {"padding": "0 9px", "height": "26px", "fontSize": "11px",
                      "fontWeight": "600", "letterSpacing": "0.04em", "cursor": "pointer",
                      "border": "none",
                      "background": "#2a2927", "color": "#aaa",
                      "fontFamily": "'IBM Plex Sans', sans-serif", "transition": "all 0.12s"}
    en_style = active_style   if lang == "en" else inactive_style
    cs_style = active_style   if lang == "cs" else inactive_style
    # Fix border-right for CZ button (last button)
    cs_style = {**cs_style, "borderRight": "none"}
    return (
        lang,
        en_style, cs_style,
        tr(lang, "vehicleMode"),
        tr(lang, "decarbPace"),
        tr(lang, "impactCategory"),
        tr(lang, "vehicleParams"),
        tr(lang, "chartBarTitle"),
        tr(lang, "chartLineTitle"),
        tr(lang, "appTitle"),
        tr(lang, "Base"),  tr(lang, "NPi"),   tr(lang, "NDC"),
        tr(lang, "Car"),   tr(lang, "LCV"),   tr(lang, "Truck"), tr(lang, "Bus"),
    )


# 6b. Popup show/hide (clientside — pure JS in index_string)

# 6. Main render
@app.callback(
    Output("sidebar-content", "children"),
    Output("summary-strip",   "children"),
    Output("bar-legend",      "children"),
    Output("bar-chart",       "figure"),
    Output("line-legend",     "children"),
    Output("line-chart",      "figure"),
    Output({"type": "vtype-tab", "vtype": "Car"},   "style"),
    Output({"type": "vtype-tab", "vtype": "LCV"},   "style"),
    Output({"type": "vtype-tab", "vtype": "Truck"}, "style"),
    Output({"type": "vtype-tab", "vtype": "Bus"},   "style"),
    Output({"type": "traj-tab", "traj": "Base"}, "style"),
    Output({"type": "traj-tab", "traj": "NPi"},  "style"),
    Output({"type": "traj-tab", "traj": "NDC"},  "style"),
    Input("vtype-store",         "data"),
    Input("trajectory-store",    "data"),
    Input("impact-select",       "value"),
    Input("params-store",        "data"),
    Input("hidden-pts-store",    "data"),
    Input("hidden-phases-store", "data"),
    Input("lang-store",          "data"),
)
def render_dashboard(vtype, trajectory, impact, params_json,
                     hidden_pts, hidden_phases, lang):
    lang = lang or "en"
    params = json.loads(params_json)

    # Cache compute_impacts — same inputs → same results, no recompute
    cache_key = (vtype, trajectory, impact, params_json)
    if not hasattr(render_dashboard, "_cache") or render_dashboard._cache_key != cache_key:
        render_dashboard._cache     = compute_impacts(vtype, trajectory, impact, params)
        render_dashboard._cache_key = cache_key
    results = render_dashboard._cache
    sidebar   = build_sidebar(vtype, params, hidden_pts, lang)
    summary   = build_summary(vtype, results, impact, hidden_pts)
    bar_leg   = build_bar_legend(hidden_phases, lang)
    bar_fig   = build_bar_chart(results, hidden_pts, hidden_phases, impact)
    line_leg  = build_line_legend(vtype, results, hidden_pts)
    line_fig  = build_line_chart(vtype, trajectory, impact, params, results, hidden_pts, lang)

    vtype_styles = [_vtype_tab_style(vt, vtype) for vt in ["Car","LCV","Truck","Bus"]]
    traj_styles  = [_traj_tab_style(traj_key, trajectory) for traj_key in ["Base","NPi","NDC"]]

    return (sidebar, summary, bar_leg, bar_fig, line_leg, line_fig,
            *vtype_styles, *traj_styles)


# 7. Sync input values and slider positions from params-store
@app.callback(
    Output({"type": "slider-val",   "pt": ALL, "key": ALL}, "value"),
    Output({"type": "param-slider", "pt": ALL, "key": ALL}, "value"),
    Input("params-store", "data"),
    Input("vtype-store",  "data"),
)
def update_slider_labels(params_json, vtype):
    ctx = callback_context
    params = json.loads(params_json)
    input_vals  = []
    slider_vals = []
    for output in ctx.outputs_list[0]:   # slider-val inputs
        id_dict = output["id"]
        pt, key = id_dict["pt"], id_dict["key"]
        p    = params.get(pt, {})
        defn = DEFAULTS.get(vtype, {}).get(pt) or {}
        val = p.get(key, defn.get(key, 0))
        input_vals.append(round(float(val), 4))
    for output in ctx.outputs_list[1]:   # param-slider
        id_dict = output["id"]
        pt, key = id_dict["pt"], id_dict["key"]
        p    = params.get(pt, {})
        defn = DEFAULTS.get(vtype, {}).get(pt) or {}
        val = p.get(key, defn.get(key, 0))
        slider_vals.append(round(float(val), 4))
    return input_vals, slider_vals


# ── Custom CSS ────────────────────────────────────────────────────────────────

_popup_data_js = json.dumps(POPUP_DATA)

app.index_string = """<!DOCTYPE html>
<html>
<head>
  {%metas%}
  <title>{%title%}</title>
  {%favicon%}
  {%css%}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; overflow: hidden; }
    #react-entry-point, ._dash-loading { height: 100%; }

    .vlca-slider .rc-slider-rail   { height: 3px; background: #e2e0db; border-radius: 2px; }
    .vlca-slider .rc-slider-track  { height: 3px; background: #1a1917; border-radius: 2px; }
    .vlca-slider .rc-slider-handle { width: 11px; height: 11px; margin-top: -4px;
                                     background: #1a1917; border: none; opacity: 1; box-shadow: none; }
    .vlca-slider .rc-slider-handle:hover,
    .vlca-slider .rc-slider-handle:active { background: #3d8c6f; box-shadow: none; }
    .vlca-slider { padding: 2px 0; }

    #sidebar-content::-webkit-scrollbar       { width: 4px; }
    #sidebar-content::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }
    #summary-strip::-webkit-scrollbar         { height: 3px; }
    #summary-strip::-webkit-scrollbar-thumb   { background: #ddd; }

    /* Popup trigger */
    .popup-trigger {
      display: inline-flex; align-items: center; justify-content: center;
      width: 14px; height: 14px; border-radius: 50%;
      background: #999; color: #fff; font-size: 9px; font-weight: 700;
      cursor: help; flex-shrink: 0; margin-left: 4px; transition: background 0.15s;
      user-select: none; line-height: 1;
    }
    .popup-trigger:hover { background: #555; }
  </style>
</head>
<body>
  {%app_entry%}
  <footer>{%config%}{%scripts%}{%renderer%}</footer>
  <script>
  /* ── Popup system ── */
  const VLCA_POPUP_DATA = """ + _popup_data_js + """;

  // Updated by the Dash lang-store clientside callback below
  window._vlcaLang = 'en';
  function vlcaCurrentLang() { return window._vlcaLang || 'en'; }

  function vlcaShowPopup(key) {
    const lang = vlcaCurrentLang();
    const data = (VLCA_POPUP_DATA[lang] || VLCA_POPUP_DATA['en'])[key];
    if (!data) return;
    document.getElementById('popup-title').textContent = data.title;
    const body = document.getElementById('popup-body');
    body.innerHTML = '';
    (data.paragraphs || []).forEach((p, i) => {
      const el = document.createElement('p');
      el.textContent = p;
      el.style.cssText = 'font-size:13px;line-height:1.65;color:#5a5750;' + (i > 0 ? 'margin-top:10px;' : '');
      body.appendChild(el);
    });
    const overlay = document.getElementById('popup-overlay');
    overlay.style.display = 'flex';
  }

  function vlcaClosePopup() {
    document.getElementById('popup-overlay').style.display = 'none';
  }

  // Use capture phase so stopPropagation from other handlers doesn't interfere
  document.addEventListener('click', function(e) {
    const trigger = e.target.closest('.popup-trigger');
    if (trigger) {
      e.stopPropagation();
      vlcaShowPopup(trigger.getAttribute('data-popup'));
      return;
    }
    if (e.target.id === 'popup-close') { vlcaClosePopup(); return; }
    if (e.target.id === 'popup-overlay') { vlcaClosePopup(); return; }
  }, true);

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') vlcaClosePopup();
  });

  /* ── Impact dropdown portal fix ──
     react-select v1 positions .Select-menu-outer as absolute inside the
     flex container. When that container has overflow constraints the menu
     gets clipped. We reposition it to position:fixed after every open. */
  function vlcaFixDropdown() {
    var wrap = document.getElementById('impact-select');
    if (!wrap) return;
    var control = wrap.querySelector('.Select-control');
    var menu    = wrap.querySelector('.Select-menu-outer');
    if (!control || !menu) return;
    var r = control.getBoundingClientRect();
    menu.style.position = 'fixed';
    menu.style.top      = r.bottom + 'px';
    menu.style.left     = r.left   + 'px';
    menu.style.width    = r.width  + 'px';
    menu.style.zIndex   = '9999';
  }
  document.addEventListener('mousedown', function(e) {
    var wrap = document.getElementById('impact-select');
    if (wrap && wrap.contains(e.target)) {
      requestAnimationFrame(vlcaFixDropdown);
    }
  }, false);
  </script>
</body>
</html>"""


# Keep window._vlcaLang in sync so popup JS always uses correct language
app.clientside_callback(
    "function(lang) { window._vlcaLang = lang || 'en'; return lang; }",
    Output("lang-store", "data", allow_duplicate=True),
    Input("lang-store",  "data"),
    prevent_initial_call=True,
)


if __name__ == "__main__":
    app.run(debug=True, port=8050)

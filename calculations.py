"""
LCA calculations engine backed by the real Excel data tables.

Data flow mirrors the Excel Interactive model:
  - Static production   → vehicle/battery production (per vehicle, time-fixed)
  - Static abrasion     → TtW abrasion term (per km, time-fixed)
  - Static exhaust      → TtW exhaust term (per kg fuel, time-fixed)
  - Dynamic 'Fuel'      → WTT emission factor (per fuel-unit, year-interpolated)
  - Dynamic 'Maintenance'→ maintenance per km (year-interpolated, per vehicle type)
  - Dynamic 'End-of-life impacts/savings' → EoL total (year-interpolated, applied once)
"""

import copy
import os

import numpy as np
import pandas as pd

from data import ALL_PTS, DEFAULTS

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")

# ── Year grid ─────────────────────────────────────────────────────────────────
YEAR_COLS = ["2020", "2025", "2030", "2035", "2040", "2045",
             "2050", "2060", "2070", "2080", "2090", "2100"]
YEARS_INT = [int(y) for y in YEAR_COLS]
START_YEAR = 2025

# ── Impact category → (CSV label, is_normalised) ─────────────────────────────
# is_normalised=True  → use EF_3.1_total col in static, Normalization='Yes' in dynamic
# is_normalised=False → use non_norm_{label} col in static, Normalization='No' in dynamic
IMPACT_MAP = {
    "climateChange":               ("Climate change",                              False),
    "acidification":               ("Acidification",                               False),
    "ecotoxicityFreshwater":       ("Ecotoxicity: freshwater",                     False),
    "energyNonRenewable":          ("Energy resources: non-renewable",             False),
    "eutrophicationFreshwater":    ("Eutrophication: freshwater",                  False),
    "eutrophicationMarine":        ("Eutrophication: marine",                      False),
    "eutrophicationTerrestrial":   ("Eutrophication: terrestrial",                 False),
    "humanToxCarcinogenic":        ("Human toxicity: carcinogenic",                False),
    "humanToxNonCarcinogenic":     ("Human toxicity: non-carcinogenic",            False),
    "ionisingRadiation":           ("Ionising radiation: human health",            False),
    "landUse":                     ("Land use",                                    False),
    "materialResources":           ("Material resources: metals/minerals",         False),
    "ozoneDepletion":              ("Ozone depletion",                             False),
    "particulateMatter":           ("Particulate matter formation",                False),
    "photochemicalOzone":          ("Photochemical oxidant formation: human health",False),
    "waterUse":                    ("Water use",                                   False),
    "ef31total":                   ("EF 3.1 total",                                True),
}

# ── Fuel density conversions (litres → kg) ────────────────────────────────────
DENSITY = {
    "Petrol": 1 / 1.336898,        # kg/l
    "Diesel": 1 / 1.204819277,     # kg/l
}

# ── Fuel name lookup per powertrain (and per vehicle for FCEV) ────────────────
# PHEV is handled separately
PT_FUEL = {
    "ICEV-P":   "Petrol",
    "ICEV-D":   "Diesel",
    "ICEV-CNG": "CNG",
    "BEV":      "Electricity",
    "HEV":      "Diesel",
}
FCEV_FUEL = {
    "Car":   "Hydrogen 1",
    "LCV":   "Hydrogen 1",
    "Truck": "Hydrogen 2",
    "Bus":   "Hydrogen 2",
}

# PHEV base consumptions (from Excel Block A formulas)
PHEV_BASE = {
    "Car": {"liquid_per_100km": 4.319,  "liquid_fuel": "Petrol",  "elec_per_100km": 20.1175},
    "LCV": {"liquid_per_100km": 5.221,  "liquid_fuel": "Diesel",  "elec_per_100km": 24.16625},
}


# ══════════════════════════════════════════════════════════════════════════════
# Load & index data tables
# ══════════════════════════════════════════════════════════════════════════════

def _load_tables():
    dyn    = pd.read_csv(os.path.join(_DATA, "dynamic_results.csv"))
    s_prod = pd.read_csv(os.path.join(_DATA, "static_production.csv"))
    s_ae   = pd.read_csv(os.path.join(_DATA, "static_abrasion_exhaust.csv"))
    # Keep both normalisation variants; callers specify which they need
    return dyn, s_prod, s_ae


_DYN, _SPROD, _SAE = _load_tables()


# ── Pre-built O(1) lookup indices ─────────────────────────────────────────────

class _Row:
    """Thin dict wrapper that mimics the pandas Series interface used by callers.

    Callers access values with ``row["column name"]`` and check membership with
    ``col in row.index``.  All original column names (including spaces / slashes)
    are preserved because we build from ``to_dict(orient='records')``.
    """
    __slots__ = ("_d",)

    def __init__(self, d: dict):
        self._d = d

    def __getitem__(self, key):
        return self._d[key]

    def __contains__(self, key):
        return key in self._d

    @property
    def index(self):
        return list(self._d.keys())


def _build_dyn_index(dyn: pd.DataFrame) -> dict:
    idx: dict = {}
    for d in dyn.to_dict(orient="records"):
        key = (
            d["Phase"],
            d["Vehicle"],
            d["Powertrain"],
            d["RCP"],
            d["Impact category"],
            d["Normalization and weighting"],
        )
        idx[key] = _Row(d)
    return idx


def _build_static_index(df: pd.DataFrame) -> dict:
    idx: dict = {}
    for d in df.to_dict(orient="records"):
        key = (d["Vehicle"], d["Powertrain"], d["Phase"])
        idx[key] = _Row(d)
    return idx


_DYN_IDX   = _build_dyn_index(_DYN)
_SPROD_IDX = _build_static_index(_SPROD)
_SAE_IDX   = _build_static_index(_SAE)


def _dyn_row(phase, vehicle, powertrain, rcp, impact_label, normalised: bool = False):
    """O(1) dict lookup — replaces the previous full-DataFrame scan."""
    norm_val = "Yes" if normalised else "No"
    return _DYN_IDX.get((phase, vehicle, powertrain, rcp, impact_label, norm_val))


def _static_row(df, vehicle, powertrain, phase):
    """O(1) dict lookup for static tables."""
    if df is _SPROD:
        return _SPROD_IDX.get((vehicle, powertrain, phase))
    if df is _SAE:
        return _SAE_IDX.get((vehicle, powertrain, phase))
    # Fallback (should never be reached with current callers)
    mask = (
        (df["Vehicle"]    == vehicle)    &
        (df["Powertrain"] == powertrain) &
        (df["Phase"]      == phase)
    )
    rows = df[mask]
    return rows.iloc[0] if len(rows) >= 1 else None


def _interp(row, year: float) -> float:
    """Linearly interpolate dynamic table row at a fractional year."""
    if row is None:
        return 0.0
    year = float(year)
    if year <= YEARS_INT[0]:
        return float(row[YEAR_COLS[0]])
    if year >= YEARS_INT[-1]:
        return float(row[YEAR_COLS[-1]])
    for i in range(len(YEARS_INT) - 1):
        y0, y1 = YEARS_INT[i], YEARS_INT[i + 1]
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0)
            return float(row[YEAR_COLS[i]]) * (1 - t) + float(row[YEAR_COLS[i + 1]]) * t
    return 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Fuel normalisation helpers
# ══════════════════════════════════════════════════════════════════════════════

def _fuel_info(vtype: str, pt: str, params: dict):
    """
    Return (fuel_name, cons_fuel_units_per_100km, fuel2_name, cons2_fuel_units_per_100km)
    where fuel_units are kg for solids/gases, kWh for electricity.
    cons is in the fuel's native unit per 100 km.
    """
    p = params[pt]
    cons1 = p["cons1"]

    if pt == "PHEV":
        base = PHEV_BASE.get(vtype)
        if not base:
            return None, 0, None, 0
        elec_share  = cons1 / 100.0
        # Excel KC formula already outputs kg/100km (density-normalised constant)
        liq_cons_kg = base["liquid_per_100km"] * (1 - elec_share)   # kg/100km
        elec_cons   = base["elec_per_100km"]   * elec_share          # kWh/100km
        liq_fuel    = base["liquid_fuel"]
        return liq_fuel, liq_cons_kg, "Electricity", elec_cons

    if pt == "FCEV":
        fuel = FCEV_FUEL[vtype]
        return fuel, cons1, None, 0   # cons already in kg/100km

    fuel = PT_FUEL.get(pt)
    if fuel is None:
        return None, 0, None, 0

    # Convert liquid fuels from l → kg
    if fuel in DENSITY:
        cons_kg = cons1 * DENSITY[fuel]
    else:
        cons_kg = cons1   # CNG already in kg, electricity in kWh

    return fuel, cons_kg, None, 0


# ══════════════════════════════════════════════════════════════════════════════
# Per-step operational impacts
# ══════════════════════════════════════════════════════════════════════════════

def _wtt_per_km(fuel1, cons1_per100, fuel2, cons2_per100, rcp, impact_label, year, normalised):
    """WTT impact per km at a given year."""
    row1 = _dyn_row("Fuel", "All", fuel1, rcp, impact_label, normalised) if fuel1 else None
    row2 = _dyn_row("Fuel", "All", fuel2, rcp, impact_label, normalised) if fuel2 else None
    f1 = _interp(row1, year) * cons1_per100 / 100 if row1 is not None else 0.0
    f2 = _interp(row2, year) * cons2_per100 / 100 if row2 is not None else 0.0
    return f1 + f2


def _ttw_per_km(vtype, pt, cons1_kg_per100, impact_label, normalised):
    """TtW impact per km (time-fixed): abrasion + exhaust."""
    if normalised:
        # EF 3.1 total: use EF_3.1_total column (already summed normalised value)
        col = "EF_3.1_total"
    else:
        col = f"non_norm_{impact_label}"

    row_ab = _static_row(_SAE, vtype, pt, "Abrasion")
    abrasion = float(row_ab[col]) if row_ab is not None and col in row_ab.index else 0.0

    row_ex = _static_row(_SAE, vtype, pt, "Exhaust")
    if row_ex is not None and col in row_ex.index:
        exhaust = float(row_ex[col]) * cons1_kg_per100 / 100
    else:
        exhaust = 0.0

    return abrasion + exhaust


def _maint_per_km(vtype, rcp, impact_label, year, normalised):
    """Dynamic maintenance per km at a given year (per vehicle type, all powertrains)."""
    row = _dyn_row("Maintenance", vtype, "All", rcp, impact_label, normalised)
    return _interp(row, year)


# ══════════════════════════════════════════════════════════════════════════════
# Production & EoL (static or dynamic at end-of-life year)
# ══════════════════════════════════════════════════════════════════════════════

def _prod_values(vtype, pt, impact_label, normalised):
    """Vehicle production and battery production (absolute per vehicle)."""
    if normalised:
        col = "EF_3.1_total"
    else:
        col = f"non_norm_{impact_label}"
    vp_row = _static_row(_SPROD, vtype, pt, "Vehicle production")
    bp_row = _static_row(_SPROD, vtype, pt, "Battery production")
    vp = float(vp_row[col]) if vp_row is not None and col in vp_row.index else 0.0
    bp = float(bp_row[col]) if bp_row is not None and col in bp_row.index else 0.0
    return vp, bp


def _eol_values(vtype, pt, rcp, impact_label, eol_year, normalised):
    """EoL impact and savings (absolute per vehicle) at end-of-life year."""
    row_imp = _dyn_row("End-of-life impacts", vtype, pt, rcp, impact_label, normalised)
    row_sav = _dyn_row("End-of-life savings",  vtype, pt, rcp, impact_label, normalised)
    eol_imp = _interp(row_imp, eol_year)
    eol_sav = _interp(row_sav, eol_year)
    return eol_imp, eol_sav


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════

def get_default_params(vtype: str) -> dict:
    params = {}
    for pt in ALL_PTS:
        defn = DEFAULTS.get(vtype, {}).get(pt)
        if defn:
            params[pt] = copy.deepcopy(defn)
    return params


def compute_impacts(vtype: str, trajectory: str, impact: str, params: dict) -> dict:
    """
    Compute per-km phase breakdown for each active powertrain.
    WTT and Maintenance are time-averaged over the vehicle lifetime.
    EoL is applied at end-of-life year.
    """
    impact_label, normalised = IMPACT_MAP[impact]
    results = {}

    for pt in ALL_PTS:
        p = params.get(pt)
        if p is None:
            results[pt] = None
            continue

        total_km  = p["totalKm"]
        annual_km = p["annualKm"]
        eol_year  = START_YEAR + total_km / annual_km

        fuel1, cons1_kg, fuel2, cons2_kg = _fuel_info(vtype, pt, params)
        if fuel1 is None and pt not in ("BEV", "FCEV"):
            results[pt] = None
            continue

        # Production (per km)
        vp, bp = _prod_values(vtype, pt, impact_label, normalised)
        v_prod_km = vp / total_km
        b_prod_km = bp / total_km

        # TtW (time-fixed, per km)
        ttw_km = _ttw_per_km(vtype, pt, cons1_kg, impact_label, normalised)

        # WTT + Maintenance: time-average by stepping over lifetime
        step = max(10_000, round(total_km / 40))
        km_steps = list(range(0, int(total_km), step))
        if not km_steps or km_steps[-1] < total_km:
            km_steps.append(int(total_km))

        wtt_total   = 0.0
        maint_total = 0.0
        for km in km_steps:
            yr = START_YEAR + km / annual_km
            wtt_total   += _wtt_per_km(fuel1, cons1_kg, fuel2, cons2_kg,
                                       trajectory, impact_label, yr, normalised) * step
            maint_total += _maint_per_km(vtype, trajectory, impact_label, yr, normalised) * step

        wtt_km   = wtt_total   / total_km
        maint_km = maint_total / total_km

        # EoL (per km)
        eol_imp, eol_sav = _eol_values(vtype, pt, trajectory, impact_label, eol_year, normalised)
        eol_imp_km = eol_imp / total_km
        eol_sav_km = eol_sav / total_km

        total = v_prod_km + b_prod_km + wtt_km + ttw_km + maint_km + eol_imp_km + eol_sav_km

        results[pt] = {
            "total": total,
            "phases": {
                "Vehicle prod.": v_prod_km,
                "Battery prod.": b_prod_km,
                "Well-to-tank":  wtt_km,
                "Tank-to-wheel": ttw_km,
                "Maintenance":   maint_km,
                "EoL impacts":   eol_imp_km,
                "EoL savings":   eol_sav_km,
            },
            "totalKm":  total_km,
            "annualKm": annual_km,
        }

    return results


def compute_lifetime_points(
    vtype: str, trajectory: str, impact: str, params: dict, pt: str
) -> list[dict]:
    """
    Step-by-step cumulative impact curve (mirrors Excel Block E recurrence).
    Returns list of {km, val} dicts.
    """
    p = params.get(pt)
    if p is None:
        return []

    impact_label, normalised = IMPACT_MAP[impact]
    total_km  = p["totalKm"]
    annual_km = p["annualKm"]
    eol_year  = START_YEAR + total_km / annual_km

    fuel1, cons1_kg, fuel2, cons2_kg = _fuel_info(vtype, pt, params)
    if fuel1 is None and pt not in ("BEV", "FCEV"):
        return []

    # Sunk production cost at km=0
    vp, bp = _prod_values(vtype, pt, impact_label, normalised)
    prod_cost = vp + bp

    # TtW per km (time-fixed)
    ttw_km = _ttw_per_km(vtype, pt, cons1_kg, impact_label, normalised)

    # EoL total (applied at end of life)
    eol_imp, eol_sav = _eol_values(vtype, pt, trajectory, impact_label, eol_year, normalised)
    eol_total = eol_imp + eol_sav

    step = max(10_000, round(total_km / 40))
    points = []
    cumulative = prod_cost
    km = 0

    while km <= total_km:
        yr = START_YEAR + km / annual_km
        wtt   = _wtt_per_km(fuel1, cons1_kg, fuel2, cons2_kg,
                             trajectory, impact_label, yr, normalised)
        maint = _maint_per_km(vtype, trajectory, impact_label, yr, normalised)
        op_per_km = wtt + ttw_km + maint

        if km == 0:
            points.append({"km": 0, "val": prod_cost})
        else:
            cumulative += op_per_km * step
            is_eol = km >= total_km
            val = cumulative + (eol_total if is_eol else 0)
            points.append({"km": km, "val": val})

        km += step

    # Ensure last point is exactly at totalKm
    if points[-1]["km"] < total_km:
        yr = eol_year
        wtt   = _wtt_per_km(fuel1, cons1_kg, fuel2, cons2_kg,
                             trajectory, impact_label, yr, normalised)
        maint = _maint_per_km(vtype, trajectory, impact_label, yr, normalised)
        remaining = total_km - (points[-1]["km"] if len(points) > 1 else 0)
        cumulative += (wtt + ttw_km + maint) * remaining
        points.append({"km": total_km, "val": cumulative + eol_total})

    return points

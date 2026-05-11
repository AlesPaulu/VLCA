# ── Powertrain / vehicle metadata ────────────────────────────────────────────

ALL_PTS = ["ICEV-P", "ICEV-D", "ICEV-CNG", "BEV", "PHEV", "HEV", "FCEV"]

PT_COLORS = {
    "ICEV-P":   "#e07a5f",
    "ICEV-D":   "#e8a838",
    "ICEV-CNG": "#7fba7a",
    "BEV":      "#3d8c6f",
    "PHEV":     "#4a90b8",
    "HEV":      "#9b7fd4",
    "FCEV":     "#c0606a",
}

PHASE_COLORS = {
    "Vehicle prod.": "#b8c4e8",
    "Battery prod.": "#f0c27f",
    "Well-to-tank":  "#9fc4c7",
    "Tank-to-wheel": "#4a7c87",
    "Maintenance":   "#a8c9a0",
    "EoL impacts":   "#d4a0a0",
    "EoL savings":   "#e07a5f",
}

PHASES = [
    "Vehicle prod.", "Battery prod.", "Well-to-tank",
    "Tank-to-wheel", "Maintenance", "EoL impacts", "EoL savings",
]

# ── Impact category definitions ───────────────────────────────────────────────

IMPACT_OPTIONS = [
    {"label": "Climate change (kg CO₂ eq.)",                          "value": "climateChange"},
    {"label": "Acidification (mol H⁺ eq.)",                           "value": "acidification"},
    {"label": "Ecotoxicity: freshwater (CTUe)",                       "value": "ecotoxicityFreshwater"},
    {"label": "Energy resources: non-renewable (MJ)",                  "value": "energyNonRenewable"},
    {"label": "Eutrophication: freshwater (kg P eq.)",                 "value": "eutrophicationFreshwater"},
    {"label": "Eutrophication: marine (kg N eq.)",                     "value": "eutrophicationMarine"},
    {"label": "Eutrophication: terrestrial (mol N eq.)",               "value": "eutrophicationTerrestrial"},
    {"label": "Human toxicity: carcinogenic (CTUh)",                   "value": "humanToxCarcinogenic"},
    {"label": "Human toxicity: non-carcinogenic (CTUh)",               "value": "humanToxNonCarcinogenic"},
    {"label": "Ionising radiation: human health (kBq U235 eq.)",       "value": "ionisingRadiation"},
    {"label": "Land use (dimensionless)",                              "value": "landUse"},
    {"label": "Material resources: metals/minerals (kg Sb eq.)",       "value": "materialResources"},
    {"label": "Ozone depletion (kg CFC-11 eq.)",                       "value": "ozoneDepletion"},
    {"label": "Particulate matter formation (disease incidence)",       "value": "particulateMatter"},
    {"label": "Photochemical oxidant formation: HH (kg NMVOC eq.)",    "value": "photochemicalOzone"},
    {"label": "Water use (m³ world eq. deprived)",                     "value": "waterUse"},
    {"label": "EF 3.1 total (normalised score, Pt)",                   "value": "ef31total"},
]

IMPACT_UNITS = {
    "climateChange":            "kg CO₂ eq./km",
    "acidification":            "mol H⁺ eq./km",
    "ecotoxicityFreshwater":    "CTUe/km",
    "energyNonRenewable":       "MJ/km",
    "eutrophicationFreshwater": "kg P eq./km",
    "eutrophicationMarine":     "kg N eq./km",
    "eutrophicationTerrestrial":"mol N eq./km",
    "humanToxCarcinogenic":     "CTUh/km",
    "humanToxNonCarcinogenic":  "CTUh/km",
    "ionisingRadiation":        "kBq U235/km",
    "landUse":                  "dim./km",
    "materialResources":        "kg Sb eq./km",
    "ozoneDepletion":           "kg CFC-11/km",
    "particulateMatter":        "disease inc./km",
    "photochemicalOzone":       "kg NMVOC/km",
    "waterUse":                 "m³/km",
    "ef31total":                "Pt/km",
}

# ── Default vehicle parameters (from Excel Interactive model) ─────────────────
# cons1: consumption in native unit (l/100km, kWh/100km, kg/100km, or % for PHEV)
# fuel: identifier used for WTT lookup — maps to Dynamic results Powertrain column
# isPhev: True → cons1 is % electric share; liquid fraction computed internally

DEFAULTS = {
    "Car": {
        "ICEV-P":   {"cons1": 9.061,  "unit1": "l/100 km",      "totalKm": 225000, "annualKm": 22081, "fuel": "petrol"},
        "ICEV-D":   {"cons1": 6.396,  "unit1": "l/100 km",      "totalKm": 307000, "annualKm": 22081, "fuel": "diesel"},
        "BEV":      {"cons1": 18.5,   "unit1": "kWh/100 km",    "totalKm": 225000, "annualKm": 22081, "fuel": "elec"},
        "PHEV":     {"cons1": 53.0,   "unit1": "% electric",    "totalKm": 225000, "annualKm": 22081, "fuel": "elec",  "isPhev": True},
        "FCEV":     {"cons1": 0.897,  "unit1": "kg H₂/100 km",  "totalKm": 225000, "annualKm": 22081, "fuel": "h2"},
        "HEV":      None,        # Car HEV not in Excel model
        "ICEV-CNG": None,
    },
    "LCV": {
        "ICEV-D":   {"cons1": 9.384,  "unit1": "l/100 km",      "totalKm": 398200, "annualKm": 32548, "fuel": "diesel"},
        "ICEV-CNG": {"cons1": 7.744,  "unit1": "kg/100 km",     "totalKm": 396300, "annualKm": 32548, "fuel": "cng"},
        "BEV":      {"cons1": 30.903, "unit1": "kWh/100 km",    "totalKm": 398200, "annualKm": 32548, "fuel": "elec"},
        "PHEV":     {"cons1": 53.0,   "unit1": "% electric",    "totalKm": 398200, "annualKm": 32548, "fuel": "elec",  "isPhev": True},
        "FCEV":     {"cons1": 1.498,  "unit1": "kg H₂/100 km",  "totalKm": 398200, "annualKm": 32548, "fuel": "h2"},
        "HEV":      None,
        "ICEV-P":   None,
    },
    "Truck": {
        "ICEV-D":   {"cons1": 18.372, "unit1": "l/100 km",      "totalKm": 647000, "annualKm": 42999, "fuel": "diesel"},
        "BEV":      {"cons1": 62.796, "unit1": "kWh/100 km",    "totalKm": 550000, "annualKm": 42999, "fuel": "elec"},
        "HEV":      {"cons1": 13.780, "unit1": "l/100 km",      "totalKm": 550000, "annualKm": 42999, "fuel": "diesel"},
        "FCEV":     {"cons1": 3.045,  "unit1": "kg H₂/100 km",  "totalKm": 550000, "annualKm": 42999, "fuel": "h2"},
        "ICEV-CNG": None,
        "PHEV":     None,
        "ICEV-P":   None,
    },
    "Bus": {
        "ICEV-D":   {"cons1": 38.860, "unit1": "l/100 km",      "totalKm": 784600, "annualKm": 63700, "fuel": "diesel"},
        "ICEV-CNG": {"cons1": 36.363, "unit1": "kg/100 km",     "totalKm": 629700, "annualKm": 63700, "fuel": "cng"},
        "BEV":      {"cons1": 132.825,"unit1": "kWh/100 km",    "totalKm": 784600, "annualKm": 63700, "fuel": "elec"},
        "HEV":      {"cons1": 26.666, "unit1": "l/100 km",      "totalKm": 784600, "annualKm": 63700, "fuel": "diesel"},
        "FCEV":     {"cons1": 6.440,  "unit1": "kg H₂/100 km",  "totalKm": 784600, "annualKm": 63700, "fuel": "h2"},
        "PHEV":     None,
        "ICEV-P":   None,
    },
}

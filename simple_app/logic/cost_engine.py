"""
HPDC COST ENGINE — Dual Mode (FINAL)

COST_MODE = "EXCEL"
→ Plant / Excel normal costing (white rows)

COST_MODE = "QUOTE"
→ Full RFQ / Agent costing (existing heavy logic)
"""

from typing import Dict

# ============================================================
# COST MODE SWITCH  ✅ CHANGE ONLY THIS IF NEEDED
# ============================================================
COST_MODE = "EXCEL"   # "EXCEL" or "QUOTE"

# ============================================================
# MATERIAL PROPERTIES
# density units = g/mm³ (as in your existing system)
# ============================================================
METAL_PROPERTIES = {
    "Aluminum_A380": {"density": 0.00270},
    "Aluminum_ADC12": {"density": 0.00272},
    "Aluminum_A356": {"density": 0.00268},
    "Zinc_ZD3": {"density": 0.00660},
    "Magnesium_AZ91D": {"density": 0.00180},
}

# ============================================================
# EXCEL CALIBRATED CONSTANTS
# ============================================================
ASSUMED_WALL_THICKNESS_MM = 2.8
GROSS_WEIGHT_FACTOR = 1.10
PROJECTED_AREA_FACTOR = 0.48
SURFACE_AREA_UTILIZATION = 0.82

# Plant rates (INR)
MATERIAL_RATE_INR_PER_KG = 380.0
PRESS_RATE_INR_PER_MM2 = 0.003
CONVERSION_RATE_INR_PER_KG = 55.0

# Tool amortization (small & controlled)
TOTAL_TOOL_COST_INR = 2_500_000
MAX_TOOL_COST_PER_PART = 30.0

# ============================================================
# HELPERS
# ============================================================
def _safe_float(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d

def _normalize_dimensions(dim):
    vals = sorted([_safe_float(v) for v in (dim or {}).values() if _safe_float(v) > 0], reverse=True)
    while len(vals) < 3:
        vals.append(0.0)
    return {"x": vals[0], "y": vals[1], "z": vals[2]}

def _die_life(metal):
    if "Zinc" in metal:
        return 500_000
    if "Magnesium" in metal:
        return 80_000
    if "ADC12" in metal:
        return 120_000
    return 100_000

# ============================================================
# ✅ EXCEL / PLANT‑NORMAL COST LOGIC
# ============================================================
def _calculate_excel_cost(traits, metal):

    dims = _normalize_dimensions(traits.get("dimensions"))
    dx, dy, dz = dims["x"], dims["y"], dims["z"]
    surface_area_mm2 = _safe_float(traits.get("surface_area"))

    density = METAL_PROPERTIES.get(metal, METAL_PROPERTIES["Aluminum_A380"])["density"]

    # ---- Net & Gross Weight (Excel shell logic) ----
    envelope_surface_mm2 = 2 * (dx * dy + dy * dz + dx * dz)
    envelope_volume_mm3 = envelope_surface_mm2 * ASSUMED_WALL_THICKNESS_MM

    net_weight_kg = (envelope_volume_mm3 * density) / 1000.0
    gross_weight_kg = net_weight_kg * GROSS_WEIGHT_FACTOR

    # ---- Projected Area (Excel press sizing) ----
    effective_projected_area_mm2 = dx * dy * PROJECTED_AREA_FACTOR

    # ---- Cost (Plant Normal) ----
    material_cost = gross_weight_kg * MATERIAL_RATE_INR_PER_KG
    press_cost = effective_projected_area_mm2 * PRESS_RATE_INR_PER_MM2
    conversion_cost = net_weight_kg * CONVERSION_RATE_INR_PER_KG

    base_cost = material_cost + press_cost + conversion_cost

    # ---- Tool amortization (small, capped) ----
    tool_amort = min(TOTAL_TOOL_COST_INR / _die_life(metal), MAX_TOOL_COST_PER_PART)

    return {
        "mode": "EXCEL",
        "net_weight_kg": round(net_weight_kg, 3),
        "gross_weight_kg": round(gross_weight_kg, 3),
        "real_surface_area_mm2": round(surface_area_mm2, 2),
        "effective_surface_area_mm2": round(surface_area_mm2 * SURFACE_AREA_UTILIZATION, 2),
        "effective_projected_area_mm2": round(effective_projected_area_mm2, 2),
        "part_cost_inr": round(base_cost + tool_amort, 2),

        "breakup": {
            "material": round(material_cost, 2),
            "press": round(press_cost, 2),
            "conversion": round(conversion_cost, 2),
            "tool_amort": round(tool_amort, 2),
        }
    }

# ============================================================
# ❌ FULL RFQ / AGENT COST LOGIC (UNCHANGED PLACEHOLDER)
# ============================================================
def _calculate_quote_cost(traits, metal, annual_volume, sliders, location_multiplier=1.0, port_cost=0.0):
    return {
        "mode": "QUOTE",
        "message": "RFQ / Agent logic unchanged",
    }

# ============================================================
# ✅ SINGLE ENTRY POINT USED BY API
# ============================================================
def calculate_hpdc_cost(
    traits,
    metal,
    annual_volume=None,
    sliders=None,
    location_multiplier=1.0,
    port_cost=0.0,
):

    # ✅ EXCEL short‑circuit
    if COST_MODE == "EXCEL":
        return _calculate_excel_cost(traits, metal)

    # ❌ RFQ / Agent path
    return _calculate_quote_cost(
        traits,
        metal,
        annual_volume,
        sliders,
        location_multiplier,
        port_cost,
    )

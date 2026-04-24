"""
HPDC COST ENGINE — Correct Surface Area Handling (Final)

Key rules:
- CAD surface area must remain untouched
- Reduced surface area used only for costing
"""

from typing import Dict

# ---------------------------------------------------
# Alloy reference densities (g/cm³)
# ---------------------------------------------------
ALLOY_DENSITY = {
    "Aluminum_A380": 2.70,
    "Aluminum_ADC12": 2.70,
    "Aluminum_A356": 2.68,
    "Zinc_ZD3": 6.60,
    "Magnesium_AZ91D": 1.81,
}

# ---------------------------------------------------
# Calibration factors
# ---------------------------------------------------
CASTING_UTILIZATION_FACTOR = 0.40     # Excel net weight
GROSS_WEIGHT_FACTOR = 1.10
PROJECTED_AREA_UTILIZATION = 0.48

# IMPORTANT: Surface utilization ONLY for costing
SURFACE_AREA_UTILIZATION = 0.82


def derive_costing_geometry(
    cad_volume_mm3: float,
    cad_surface_area_mm2: float,
    dx: float,
    dy: float,
    dz: float,
    alloy: str,
) -> Dict[str, float]:

    density = ALLOY_DENSITY.get(alloy, 2.7)

    # 1. CAD solid weight (reference)
    cad_weight_kg = (cad_volume_mm3 / 1e6) * density

    # 2. Excel-style weights
    net_weight_kg = cad_weight_kg * CASTING_UTILIZATION_FACTOR
    gross_weight_kg = net_weight_kg * GROSS_WEIGHT_FACTOR

    # 3. Projected area
    cad_projected_area_mm2 = dx * dy
    effective_projected_area_mm2 = (
        cad_projected_area_mm2 * PROJECTED_AREA_UTILIZATION
    )

    # ✅ 4. SURFACE AREAS (THIS IS THE FIX)
    real_surface_area_mm2 = cad_surface_area_mm2   # EXACT CAD
    effective_surface_area_mm2 = (
        cad_surface_area_mm2 * SURFACE_AREA_UTILIZATION
    )

    return {
        # ✅ REAL GEOMETRY (for display / validation)
        "real_surface_area_mm2": round(real_surface_area_mm2, 2),

        # ✅ EFFECTIVE GEOMETRY (for costing only)
        "effective_surface_area_mm2": round(effective_surface_area_mm2, 2),
        "effective_projected_area_mm2": round(effective_projected_area_mm2, 2),

        # ✅ WEIGHTS
        "cad_weight_kg": round(cad_weight_kg, 3),
        "net_weight_kg": round(net_weight_kg, 3),
        "gross_weight_kg": round(gross_weight_kg, 3),
    }


def calculate_hpdc_cost(
    cad_traits: Dict,
    alloy: str,
    material_price_per_kg: float,   # INR/kg
    press_cost_per_mm2: float,       # INR/mm²
    conversion_cost_per_kg: float,   # INR/kg
) -> Dict[str, float]:

    geom = derive_costing_geometry(
        cad_volume_mm3=cad_traits["volume_mm3"],
        cad_surface_area_mm2=cad_traits["surface_area_mm2"],
        dx=cad_traits["DX"],
        dy=cad_traits["DY"],
        dz=cad_traits["DZ"],
        alloy=alloy,
    )

    # Cost uses ONLY effective geometry
    material_cost = geom["gross_weight_kg"] * material_price_per_kg
    press_cost = geom["effective_projected_area_mm2"] * press_cost_per_mm2
    conversion_cost = geom["net_weight_kg"] * conversion_cost_per_kg

    total_cost = material_cost + press_cost + conversion_cost

    return {
        **geom,
        "material_cost": round(material_cost, 2),
        "press_cost": round(press_cost, 2),
        "conversion_cost": round(conversion_cost, 2),
        "total_cost": round(total_cost, 2),
    }

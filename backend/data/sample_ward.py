"""
Sample Urban Ward Data - Kurla-Sion Pilot Ward (Mumbai Basin)
Realistic testbed representing an urban flood-prone basin:
- Center: 19.0680° N, 72.8800° E
- Features: Arterial roads (LBS Marg, CST Road), Railway Subway (depressed elevation),
  Mithi River Canal Outfall, Central Storm Outfall, dense commercial/residential, open recreation ground.
"""

import numpy as np

# Ward Geospatial Boundary (approx 1.8km x 1.8km)
BOUNDS = {
    "min_lat": 19.0580,
    "max_lat": 19.0780,
    "min_lon": 72.8700,
    "max_lon": 72.8900,
    "center": [19.0680, 72.8800]
}

GRID_ROWS = 36
GRID_COLS = 36
CELL_SIZE_METERS = 50.0  # 50m resolution grid cell

def generate_dem():
    """
    Generates a 36x36 DEM (elevation in meters above sea level).
    Natural slope from East (ridge ~18m) and North (hillock ~22m)
    down towards West and South-West (Mithi River level ~3.0m).
    Features an engineered depression for Railway Underpass / Subway (elevation 2.1m)
    and Gandhi Market depression (elevation 2.8m).
    """
    dem = np.zeros((GRID_ROWS, GRID_COLS), dtype=float)
    
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            # Base regional gradient: high in NE, sloping to SW
            norm_r = r / (GRID_ROWS - 1)  # 0 (North) to 1 (South)
            norm_c = c / (GRID_COLS - 1)  # 0 (West) to 1 (East)
            
            base_elev = 3.5 + 14.0 * norm_c + 6.0 * (1.0 - norm_r)
            # Add microtopography
            micro = 1.2 * np.sin(norm_r * 4.0 * np.pi) * np.cos(norm_c * 3.0 * np.pi)
            dem[r, c] = round(base_elev + micro, 2)
            
    # Depressions (natural low-lying choke points prone to severe flooding)
    # 1. Railway Subway / Culvert Underpass (around r=20..23, c=10..13)
    dem[19:24, 9:14] -= 3.8
    # 2. Market Lowland (around r=14..17, c=15..18)
    dem[13:17, 14:18] -= 2.6
    # 3. Mithi River Outfall Bank (Western edge r=24..35, c=0..4)
    dem[24:36, 0:5] = np.clip(dem[24:36, 0:5], 2.2, 3.8)

    # Ensure min elevation is 1.8m
    dem = np.clip(dem, 1.8, 25.0)
    return dem

def generate_land_use_cn():
    """
    Runoff Curve Number (SCS-CN):
    - Roads / Paved Surfaces: 98
    - Dense Commercial / Slum Rooftops: 92
    - Residential / Mixed: 84
    - Parks / Mangroves / Permeable: 62
    """
    cn_grid = np.full((GRID_ROWS, GRID_COLS), 86.0, dtype=float)
    
    # West edge (Mithi mangrove buffer)
    cn_grid[:, 0:4] = 62.0
    # Central Park / Recreation ground (r=7..11, c=18..23)
    cn_grid[7:12, 18:24] = 58.0
    # Dense commercial market area
    cn_grid[13:22, 12:20] = 94.0
    # Arterial road corridors (high CN 98)
    cn_grid[18, :] = 98.0
    cn_grid[:, 12] = 98.0
    cn_grid[:, 24] = 98.0
    
    return cn_grid

# Road network segments with metadata, connectivity, and approximate geo-paths
ROADS = [
    {
        "id": "R1",
        "name": "LBS Marg (North-South Arterial)",
        "type": "arterial",
        "lanes": 4,
        "width_m": 22.0,
        "base_speed_kmh": 40.0,
        "path": [
            [19.0775, 72.8765],
            [19.0725, 72.8768],
            [19.0675, 72.8770],
            [19.0620, 72.8773],
            [19.0585, 72.8775]
        ],
        "dem_cells": [[r, 12] for r in range(2, 34, 2)]
    },
    {
        "id": "R2",
        "name": "Sion-Bandra Link Road (West-East Expressway)",
        "type": "arterial",
        "lanes": 6,
        "width_m": 30.0,
        "base_speed_kmh": 50.0,
        "path": [
            [19.0670, 72.8710],
            [19.0672, 72.8760],
            [19.0675, 72.8820],
            [19.0678, 72.8890]
        ],
        "dem_cells": [[18, c] for c in range(2, 34, 2)]
    },
    {
        "id": "R3",
        "name": "Railway Culvert Underpass (Subway Road)",
        "type": "subway",
        "lanes": 2,
        "width_m": 12.0,
        "base_speed_kmh": 25.0,
        "path": [
            [19.0660, 72.8755],
            [19.0645, 72.8760],
            [19.0630, 72.8768],
            [19.0625, 72.8785]
        ],
        "dem_cells": [[20, 10], [21, 11], [22, 12], [22, 14]]
    },
    {
        "id": "R4",
        "name": "Market Bazaar Lane (Commercial Hub)",
        "type": "local",
        "lanes": 2,
        "width_m": 10.0,
        "base_speed_kmh": 20.0,
        "path": [
            [19.0710, 72.8770],
            [19.0705, 72.8805],
            [19.0700, 72.8845]
        ],
        "dem_cells": [[14, 13], [14, 16], [15, 20], [15, 24]]
    },
    {
        "id": "R5",
        "name": "Station Approach Road",
        "type": "collector",
        "lanes": 2,
        "width_m": 14.0,
        "base_speed_kmh": 30.0,
        "path": [
            [19.0620, 72.8773],
            [19.0615, 72.8810],
            [19.0610, 72.8850]
        ],
        "dem_cells": [[25, 12], [25, 17], [25, 22], [25, 27]]
    },
    {
        "id": "R6",
        "name": "Park View Boulevard",
        "type": "collector",
        "lanes": 2,
        "width_m": 16.0,
        "base_speed_kmh": 35.0,
        "path": [
            [19.0740, 72.8770],
            [19.0742, 72.8825],
            [19.0745, 72.8885]
        ],
        "dem_cells": [[8, 12], [8, 18], [8, 24], [8, 30]]
    },
    {
        "id": "R7",
        "name": "East Ridge Avenue",
        "type": "collector",
        "lanes": 3,
        "width_m": 18.0,
        "base_speed_kmh": 40.0,
        "path": [
            [19.0760, 72.8840],
            [19.0700, 72.8845],
            [19.0650, 72.8850],
            [19.0590, 72.8855]
        ],
        "dem_cells": [[r, 25] for r in range(4, 34, 4)]
    },
    {
        "id": "R8",
        "name": "Riverfront Canal Road (West Flood-Margin)",
        "type": "collector",
        "lanes": 2,
        "width_m": 12.0,
        "base_speed_kmh": 30.0,
        "path": [
            [19.0750, 72.8720],
            [19.0700, 72.8725],
            [19.0650, 72.8728],
            [19.0600, 72.8730]
        ],
        "dem_cells": [[r, 4] for r in range(4, 32, 4)]
    },
    {
        "id": "R9",
        "name": "Hospital Emergency Corridor",
        "type": "arterial",
        "lanes": 3,
        "width_m": 20.0,
        "base_speed_kmh": 45.0,
        "path": [
            [19.0765, 72.8725],
            [19.0768, 72.8770],
            [19.0772, 72.8840]
        ],
        "dem_cells": [[4, 4], [4, 12], [4, 25]]
    }
]

# Drainage Network: Nodes (Manholes, Catch-pits, Outfalls)
# Notes on Indian ULB Reality:
# - Invert elevation: depth beneath ground where pipe invert lies
# - Max depth: chamber height
# - Auto-inferred status: True for nodes deduced from DEM/Roads without ground-survey GIS
MANHOLES = [
    {"id": "MH-01", "name": "North LBS Inlet", "lat": 19.0765, "lon": 72.8765, "grid_r": 4, "grid_c": 12, "depth_m": 1.8, "is_outfall": False, "inferred": False},
    {"id": "MH-02", "name": "Park Boulevard Junction", "lat": 19.0740, "lon": 72.8768, "grid_r": 8, "grid_c": 12, "depth_m": 2.0, "is_outfall": False, "inferred": False},
    {"id": "MH-03", "name": "Market North Chamber", "lat": 19.0710, "lon": 72.8770, "grid_r": 13, "grid_c": 12, "depth_m": 2.2, "is_outfall": False, "inferred": False},
    {"id": "MH-04", "name": "Gandhi Market Low-Point", "lat": 19.0705, "lon": 72.8795, "grid_r": 14, "grid_c": 16, "depth_m": 2.5, "is_outfall": False, "inferred": False},
    {"id": "MH-05", "name": "East Bazaar Catch-Pit", "lat": 19.0700, "lon": 72.8835, "grid_r": 15, "grid_c": 23, "depth_m": 1.8, "is_outfall": False, "inferred": True},
    {"id": "MH-06", "name": "Central Expressway Interchange", "lat": 19.0675, "lon": 72.8770, "grid_r": 18, "grid_c": 12, "depth_m": 2.4, "is_outfall": False, "inferred": False},
    {"id": "MH-07", "name": "Subway Entry Manhole", "lat": 19.0655, "lon": 72.8758, "grid_r": 20, "grid_c": 10, "depth_m": 2.8, "is_outfall": False, "inferred": False},
    {"id": "MH-08", "name": "Railway Culvert Sump", "lat": 19.0635, "lon": 72.8762, "grid_r": 22, "grid_c": 11, "depth_m": 3.2, "is_outfall": False, "inferred": False},
    {"id": "MH-09", "name": "Subway Exit Catch-Pit", "lat": 19.0625, "lon": 72.8778, "grid_r": 23, "grid_c": 13, "depth_m": 2.5, "is_outfall": False, "inferred": False},
    {"id": "MH-10", "name": "Station Circle Chamber", "lat": 19.0620, "lon": 72.8775, "grid_r": 25, "grid_c": 12, "depth_m": 2.0, "is_outfall": False, "inferred": False},
    {"id": "MH-11", "name": "Station Approach East", "lat": 19.0615, "lon": 72.8815, "grid_r": 25, "grid_c": 19, "depth_m": 1.8, "is_outfall": False, "inferred": True},
    {"id": "MH-12", "name": "South LBS Terminal", "lat": 19.0585, "lon": 72.8775, "grid_r": 31, "grid_c": 12, "depth_m": 2.0, "is_outfall": False, "inferred": False},
    {"id": "MH-13", "name": "East Ridge Junction 1", "lat": 19.0745, "lon": 72.8845, "grid_r": 8, "grid_c": 25, "depth_m": 1.6, "is_outfall": False, "inferred": True},
    {"id": "MH-14", "name": "East Ridge Junction 2", "lat": 19.0650, "lon": 72.8850, "grid_r": 21, "grid_c": 25, "depth_m": 1.8, "is_outfall": False, "inferred": True},
    {"id": "MH-15", "name": "River Canal West Manhole 1", "lat": 19.0720, "lon": 72.8725, "grid_r": 11, "grid_c": 5, "depth_m": 2.0, "is_outfall": False, "inferred": True},
    {"id": "MH-16", "name": "River Canal West Manhole 2", "lat": 19.0670, "lon": 72.8720, "grid_r": 18, "grid_c": 4, "depth_m": 2.2, "is_outfall": False, "inferred": True},
    # Outfalls:
    {"id": "OUTFALL-01", "name": "Mithi River Tidal Outfall (West)", "lat": 19.0630, "lon": 72.8715, "grid_r": 24, "grid_c": 2, "depth_m": 3.5, "is_outfall": True, "inferred": False},
    {"id": "OUTFALL-02", "name": "South Tidal Canal Discharge", "lat": 19.0580, "lon": 72.8730, "grid_r": 33, "grid_c": 4, "depth_m": 3.0, "is_outfall": True, "inferred": False}
]

# Drainage Conduits / Storm Pipes
# Key SIH bottleneck: Pipes P4, P7, P8 have undersized diameters (450-600mm)
# leading to rapid surcharge during >40 mm/hr downpours!
CONDUITS = [
    {"id": "P1", "from": "MH-01", "to": "MH-02", "diam_mm": 900, "length_m": 280, "manning_n": 0.015, "inferred": False},
    {"id": "P2", "from": "MH-02", "to": "MH-03", "diam_mm": 1000, "length_m": 340, "manning_n": 0.015, "inferred": False},
    {"id": "P3", "from": "MH-13", "to": "MH-05", "diam_mm": 600, "length_m": 380, "manning_n": 0.018, "inferred": True},
    {"id": "P4", "from": "MH-05", "to": "MH-04", "diam_mm": 600, "length_m": 320, "manning_n": 0.018, "inferred": False}, # Bottleneck
    {"id": "P5", "from": "MH-04", "to": "MH-03", "diam_mm": 800, "length_m": 260, "manning_n": 0.016, "inferred": False},
    {"id": "P6", "from": "MH-03", "to": "MH-06", "diam_mm": 1200, "length_m": 390, "manning_n": 0.014, "inferred": False},
    {"id": "P7", "from": "MH-06", "to": "MH-07", "diam_mm": 600, "length_m": 240, "manning_n": 0.018, "inferred": False}, # Bottleneck to subway
    {"id": "P8", "from": "MH-07", "to": "MH-08", "diam_mm": 500, "length_m": 220, "manning_n": 0.020, "inferred": False}, # Severe Culvert Bottleneck
    {"id": "P9", "from": "MH-08", "to": "MH-09", "diam_mm": 750, "length_m": 190, "manning_n": 0.016, "inferred": False},
    {"id": "P10", "from": "MH-09", "to": "MH-10", "diam_mm": 900, "length_m": 180, "manning_n": 0.015, "inferred": False},
    {"id": "P11", "from": "MH-11", "to": "MH-10", "diam_mm": 600, "length_m": 360, "manning_n": 0.018, "inferred": True},
    {"id": "P12", "from": "MH-10", "to": "MH-12", "diam_mm": 1000, "length_m": 420, "manning_n": 0.015, "inferred": False},
    {"id": "P13", "from": "MH-02", "to": "MH-15", "diam_mm": 800, "length_m": 450, "manning_n": 0.016, "inferred": True},
    {"id": "P14", "from": "MH-15", "to": "MH-16", "diam_mm": 1000, "length_m": 520, "manning_n": 0.015, "inferred": True},
    {"id": "P15", "from": "MH-16", "to": "OUTFALL-01", "diam_mm": 1600, "length_m": 480, "manning_n": 0.013, "inferred": False},
    {"id": "P16", "from": "MH-08", "to": "OUTFALL-01", "diam_mm": 900, "length_m": 410, "manning_n": 0.016, "inferred": False}, # Culvert discharge line
    {"id": "P17", "from": "MH-12", "to": "OUTFALL-02", "diam_mm": 1400, "length_m": 460, "manning_n": 0.014, "inferred": False},
    {"id": "P18", "from": "MH-14", "to": "MH-11", "diam_mm": 600, "length_m": 490, "manning_n": 0.018, "inferred": True}
]

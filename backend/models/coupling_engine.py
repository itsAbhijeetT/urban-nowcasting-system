"""
Module D: Two-Way Coupled Simulation Engine (Surface ↔ Drainage Feedback Loop)
- Executes rolling 15-min coupled nowcasts:
  Rainfall (Module A) -> Surface Runoff (Module B) -> Inlet Capture ->
  1D Drainage Routing (Module C) -> Surcharge Eruption -> Re-injection onto Streets (Module B)
- Calculates street-by-street water depths (cm), risk hazard categories, and telemetry.
"""

import numpy as np
from typing import Dict, List, Any
from backend.data.sample_ward import ROADS, MANHOLES, BOUNDS
from backend.models.radar_nowcast import RadarNowcastEngine, TIMESTEPS
from backend.models.surface_routing import SurfaceRoutingEngine
from backend.models.drainage_network import DrainageNetworkEngine

def classify_street_risk(depth_cm: float) -> str:
    if depth_cm < 10.0:
        return "SAFE"
    elif depth_cm < 25.0:
        return "MODERATE_WATERLOGGING"
    elif depth_cm < 45.0:
        return "SEVERE_HAZARD"
    else:
        return "CRITICAL_INUNDATION"

class CouplingEngine:
    def __init__(self, scenario_id: str = "cloudburst", drainage_engine: DrainageNetworkEngine = None):
        self.scenario_id = scenario_id
        self.radar_engine = RadarNowcastEngine(scenario_id=scenario_id)
        self.surface_engine = SurfaceRoutingEngine()
        self.drainage_engine = drainage_engine if drainage_engine else DrainageNetworkEngine()
        self.roads = ROADS

    def run_coupled_nowcast(self) -> Dict[str, Any]:
        """
        Executes the two-way coupled simulation across all timesteps (0 to 180 min).
        Returns comprehensive dictionary organized by timestep for the UI.
        """
        nowcast_radar_series = self.radar_engine.generate_nowcast_series()
        results_by_timestep = {}
        
        # Reset surface engine state
        self.surface_engine.water_depth.fill(0.0)
        self.surface_engine.accumulated_rain_mm.fill(0.0)

        inlet_nodes = [m for m in self.drainage_engine.nodes.values() if not m["is_outfall"]]

        for t in TIMESTEPS:
            radar_step = nowcast_radar_series[t]
            rain_rate_grid = radar_step["full_rain_rate_grid"] # mm/hr
            
            # Step 1: Surface Runoff Generation from Rainfall (SCS-CN)
            dt_step = 15.0 if t > 0 else 5.0
            self.surface_engine.apply_rainfall_and_runoff(rain_rate_grid, dt_minutes=dt_step)
            
            # Step 2: Surface Overland 2D Routing (Cellular Automata)
            self.surface_engine.step_cellular_automata(num_substeps=6)
            
            # Step 3: Inlet Water Capture (Surface -> Drainage Network)
            captured_flows = self.surface_engine.extract_inflow_to_inlets(inlet_nodes)
            inlet_flow_dict = {inlet_nodes[i]["id"]: captured_flows[i] for i in range(len(inlet_nodes))}
            
            # Step 4: 1D Drainage Hydraulic Routing & Surcharge Detection
            drainage_state, surcharge_events = self.drainage_engine.solve_hydraulics_and_surcharge(inlet_flow_dict)
            
            # Step 5: Surcharge Re-injection (Drainage -> Surface Feedback Loop)
            # THIS IS THE KEY SIH WINNING DIFFERENTIATOR:
            # Over-capacity backflow erupts from manholes and pools onto surrounding streets!
            if surcharge_events:
                self.surface_engine.inject_surcharge_water(surcharge_events, dt_seconds=dt_step * 60.0)
                # Additional CA steps to diffuse surcharged backflow across streets
                self.surface_engine.step_cellular_automata(num_substeps=4)
                
            # Step 6: Map Street Segments to Surface Inundation Depths
            road_predictions = []
            flooded_count = 0
            severe_count = 0
            max_overall_depth = 0.0

            for road in self.roads:
                # Query water depth at road DEM cells
                cell_depths = [
                    float(self.surface_engine.water_depth[r, c] * 100.0) # meters -> cm
                    for r, c in road["dem_cells"]
                    if 0 <= r < self.surface_engine.rows and 0 <= c < self.surface_engine.cols
                ]
                
                avg_depth_cm = round(float(np.mean(cell_depths)), 1) if cell_depths else 0.0
                max_depth_cm = round(float(np.max(cell_depths)), 1) if cell_depths else 0.0
                
                risk = classify_street_risk(max_depth_cm)
                if max_depth_cm >= 10.0:
                    flooded_count += 1
                if max_depth_cm >= 25.0:
                    severe_count += 1
                if max_depth_cm > max_overall_depth:
                    max_overall_depth = max_depth_cm
                    
                # Time to flood estimation
                ttf = 0 if max_depth_cm >= 10.0 else max(0, 45 - t)
                
                road_predictions.append({
                    "id": road["id"],
                    "name": road["name"],
                    "type": road["type"],
                    "path": road["path"],
                    "avg_depth_cm": avg_depth_cm,
                    "max_depth_cm": max_depth_cm,
                    "risk_level": risk,
                    "time_to_flood_min": ttf,
                    "is_passable_car": max_depth_cm < 15.0,
                    "is_passable_ambulance": max_depth_cm < 35.0
                })

            # Step 7: Surface Contours
            surface_polygons = self.surface_engine.get_inundation_contours()
            
            # Step 8: Package Timestep Results
            results_by_timestep[str(t)] = {
                "timestep_min": t,
                "lead_time_label": f"T+{t} min",
                "confidence_score": radar_step["confidence_score"],
                "peak_rain_rate_mmh": radar_step["peak_rainfall_rate_mmh"],
                "mean_rain_rate_mmh": radar_step["mean_rainfall_rate_mmh"],
                "radar_points": radar_step["radar_heatmap_points"],
                "roads": road_predictions,
                "drainage": drainage_state,
                "surcharge_events": surcharge_events,
                "inundation_polygons": surface_polygons,
                "summary": {
                    "total_roads_flooded": flooded_count,
                    "severely_flooded_roads": severe_count,
                    "surcharging_manholes": len(surcharge_events),
                    "total_surcharge_lps": round(drainage_state["total_surcharge_volume_rate_m3s"] * 1000.0, 1),
                    "max_inundation_depth_cm": round(max_overall_depth, 1),
                    "estimated_population_impacted": int(flooded_count * 2400 + severe_count * 4500)
                }
            }

        return {
            "scenario": self.scenario_id,
            "timesteps": TIMESTEPS,
            "results": results_by_timestep
        }

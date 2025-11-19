"""Functions for processing PyPSA network data for map visualization"""

import logging
from typing import Any, Dict

import pandas as pd
from pypsa.plot.maps.interactive import MapDataExtractor

from pypsa_app.backend.services.network import NetworkService

logger = logging.getLogger(__name__)


def extract_geographic_layer(file_path: str, layer_type: str) -> Dict[str, Any]:
    """Extract geographic layer data (buses or lines) from a network file"""

    n = NetworkService(file_path).n

    # Extract positions and build DataFrame
    extractor = MapDataExtractor(n)
    if layer_type == "buses":
        positions = extractor.get_bus_positions()
        df = n.buses.loc[positions.index].copy()
        df[["lng", "lat"]] = positions[["x", "y"]]
    else:
        positions = extractor.get_branch_positions("Line")
        df = n.components["Line"].static.loc[positions.index].copy()
        df[["lng0", "lat0", "lng1", "lat1"]] = positions[
            ["bus0_x", "bus0_y", "bus1_x", "bus1_y"]
        ]

    # Build fields (id, name, + all columns)
    fields = [{"name": "id", "type": "string"}, {"name": "name", "type": "string"}]
    for col in df.columns:
        field_type = "real" if pd.api.types.is_numeric_dtype(df[col]) else "string"
        fields.append({"name": col, "type": field_type})

    # Build rows
    data_df = df.fillna("")
    rows = [
        [str(idx), str(idx)] + row
        for idx, row in zip(data_df.index, data_df.values.tolist())
    ]

    logger.debug(
        "Extracted geographic layer",
        extra={
            "file_path": file_path,
            "layer_type": layer_type,
            "row_count": len(rows),
            "field_count": len(fields),
        },
    )

    return {"fields": fields, "rows": rows}


def generate_topology_svg(n) -> str:
    """Generate simple SVG topology visualization"""
    import numpy as np

    extractor = MapDataExtractor(n)
    bus_pos = extractor.get_bus_positions()

    if len(bus_pos) == 0:
        logger.warning(
            "No buses with valid coordinates found",
            extra={
                "total_buses": len(n.buses),
            },
        )
        return None

    line_pos = extractor.get_branch_positions("Line") if len(n.lines) else None

    width, height, padding = 400, 300, 20

    # Calculate bounds from all coordinates
    coords = [bus_pos[["x", "y"]].values]
    if line_pos is not None and len(line_pos):
        coords.extend(
            [
                line_pos[["bus0_x", "bus0_y"]].values,
                line_pos[["bus1_x", "bus1_y"]].values,
            ]
        )
    all_coords = np.vstack(coords)

    min_x, min_y = all_coords.min(axis=0)
    max_x, max_y = all_coords.max(axis=0)
    x_range, y_range = max_x - min_x or 1, max_y - min_y or 1

    def norm(x, y):
        return (
            padding + (x - min_x) / x_range * (width - 2 * padding),
            height - (padding + (y - min_y) / y_range * (height - 2 * padding)),
        )

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        "<style>",
        ".line{stroke:#000;stroke-width:2.5;stroke-opacity:0.75;stroke-linecap:round;stroke-linejoin:round}",
        ".bus{fill:#000}",
        "</style>",
    ]

    if line_pos is not None and len(line_pos):
        for _, p in line_pos.iterrows():
            x0, y0 = norm(p["bus0_x"], p["bus0_y"])
            x1, y1 = norm(p["bus1_x"], p["bus1_y"])
            svg.append(
                f'<line class="line" x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}"/>'
            )

    for _, p in bus_pos.iterrows():
        x, y = norm(p["x"], p["y"])
        svg.append(f'<circle class="bus" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')

    svg.append("</svg>")
    return "".join(svg)

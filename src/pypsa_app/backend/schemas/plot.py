from typing import Any

from pydantic import BaseModel, Field, field_validator

from pypsa_app.backend.utils.allowlists import ALLOWED_CHART_TYPES, ALLOWED_STATISTICS


class PlotRequest(BaseModel):
    """Request schema for plot generation

    For single network: Maps to Network.statistics.<statistic>.<plot_type>(<parameters>)
    For multiple networks: Maps to NetworkCollection.statistics.<statistic>.<plot_type>(<parameters>)
    """

    network_ids: list[str] = Field(
        ..., description="List of network UUIDs (single or multiple)"
    )
    statistic: str = Field(
        ...,
        description="Statistics method (e.g., 'energy_balance', 'installed_capacity')",
    )
    plot_type: str = Field(..., description="Plot method (e.g., 'bar', 'area', 'line')")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Parameters to pass to the plot function"
    )

    @field_validator("network_ids")
    @classmethod
    def validate_network_ids(cls, v):
        if not v:
            raise ValueError("At least one network ID is required")
        return v

    @field_validator("statistic")
    @classmethod
    def validate_statistic(cls, v):
        if v not in ALLOWED_STATISTICS:
            raise ValueError(
                f"Invalid statistic '{v}'. Allowed: {sorted(ALLOWED_STATISTICS)}"
            )
        return v

    @field_validator("plot_type")
    @classmethod
    def validate_plot_type(cls, v):
        if v not in ALLOWED_CHART_TYPES:
            raise ValueError(
                f"Invalid plot_type '{v}'. Allowed: {sorted(ALLOWED_CHART_TYPES)}"
            )
        return v

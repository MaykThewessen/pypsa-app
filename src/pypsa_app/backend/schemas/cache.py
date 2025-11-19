"""Cache response schemas"""

from pydantic import BaseModel


class RedisStatsResponse(BaseModel):
    available: bool
    total_keys: int
    keys_by_type: dict[str, int]
    memory_used: str | None = None


class NetworkCacheStatsResponse(BaseModel):
    total_networks: int
    networks: dict[str, dict]


class ClearCacheResponse(BaseModel):
    message: str
    deleted_keys: int

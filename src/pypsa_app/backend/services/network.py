import gc
import hashlib
import logging
import math
import threading
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Optional

import pypsa
from sqlalchemy.exc import IntegrityError

from pypsa_app.backend.database import SessionLocal
from pypsa_app.backend.models import Network
from pypsa_app.backend.settings import settings
from pypsa_app.backend.utils.path_validation import validate_path
from pypsa_app.backend.utils.serializers import sanitize_metadata

logger = logging.getLogger(__name__)


class NetworkCache:
    """Thread-safe LRU cache for loaded PyPSA networks with TTL"""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = self.misses = 0
        self._lock = threading.Lock()

    def get(self, file_path: Path) -> Optional[pypsa.Network]:
        """Get network from cache if not expired (thread-safe)"""
        key = str(file_path)

        with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None

            network, timestamp = self.cache[key]
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]
                self.misses += 1
                return None

            self.cache.move_to_end(key)
            self.hits += 1
            return network

    def put(self, file_path: Path, network: pypsa.Network):
        """Add network to cache with LRU eviction (thread-safe)"""
        key = str(file_path)

        with self._lock:
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                logger.debug(
                    "Evicted oldest network from cache (LRU)",
                    extra={
                        "evicted_network": oldest,
                        "cache_size": len(self.cache),
                        "max_size": self.max_size,
                    },
                )

            self.cache[key] = (network, time.time())
            self.cache.move_to_end(key)
            logger.debug(
                "Cached network",
                extra={
                    "file_path": str(file_path),
                    "cache_size": len(self.cache),
                },
            )

    def clear(self):
        """Clear all cached networks (thread-safe)"""
        with self._lock:
            cached_count = len(self.cache)
            self.cache.clear()
            self.hits = self.misses = 0
            logger.info(
                "Network cache cleared",
                extra={
                    "cleared_count": cached_count,
                    "cache_type": "in_memory",
                },
            )

    def stats(self) -> dict:
        """Get cache statistics (thread-safe)"""
        with self._lock:
            total = self.hits + self.misses
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_percent": round((self.hits / total * 100) if total else 0, 2),
                "cached_networks": [
                    {"file_path": k, "cached_at": time.ctime(t)}
                    for k, (_, t) in self.cache.items()
                ],
            }


_network_cache = NetworkCache(ttl_seconds=settings.network_cache_ttl)


class NetworkService:
    """Service for PyPSA network operations (handles single networks)"""

    def __init__(self, network: pypsa.Network | Path | str, use_cache: bool = True):
        """Initialize service with a network object or file path"""
        if isinstance(network, (Path, str)):
            self.file_path = validate_path(Path(network), must_exist=True)

            # Try to get from cache first
            if use_cache and (cached_network := _network_cache.get(self.file_path)):
                self.n = cached_network
            else:
                self.n = pypsa.Network(self.file_path)
                logger.debug(
                    "Successfully loaded network from file",
                    extra={
                        "file_path": str(self.file_path),
                        "use_cache": use_cache,
                    },
                )

                if use_cache:
                    _network_cache.put(self.file_path, self.n)
        elif isinstance(network, pypsa.Network):
            self.n = network
            self.file_path = None
        else:
            raise ValueError("Invalid network type")

    def extract_database_info(self) -> dict:
        """Extract network metadata for database storage (mirrors Network model field order)"""
        info = {}

        info["name"] = self.n.name

        info["dimensions_count"] = {
            "timesteps": len(self.n.snapshots),
            "periods": len(self.n.investment_periods),
            "scenarios": len(self.n.scenarios),
        }

        info["components_count"] = {
            c.name: int(len(c))
            for c in self.n.components
            if not c.name.endswith("Type")
        }

        info["meta"] = (
            sanitize_metadata(dict(self.n.meta))
            if hasattr(self.n, "meta") and self.n.meta
            else {}
        )

        facets = {}
        if carriers := self._extract_carriers(self.n):
            facets["carriers"] = carriers
        if countries := self._extract_countries(self.n):
            facets["countries"] = countries
        info["facets"] = facets or None

        return info

    @staticmethod
    def _extract_carriers(network: pypsa.Network) -> dict[str, dict]:
        """Extract bus carrier information from the network"""
        carriers = {}
        for carrier_name in network.buses.carrier.unique():
            carrier_info = {}
            if carrier_name in network.carriers.index:
                carrier_info = {
                    k: v
                    for k, v in network.carriers.loc[carrier_name].to_dict().items()
                    if not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))
                }
            carriers[carrier_name] = carrier_info

        return carriers

    @staticmethod
    def _extract_countries(network: pypsa.Network) -> list[str]:
        """Extract unique countries from the network buses"""
        if not len(network.buses) or "country" not in network.buses.columns:
            return []

        countries = network.buses["country"].dropna().unique()
        return sorted(countries)

    def calculate_file_hash(self) -> str:
        """Calculate SHA256 hash of the network file"""
        if self.file_path is None:
            raise ValueError("Cannot calculate hash for network without file_path")

        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_file_size(self) -> int:
        """Get file size in bytes"""
        if self.file_path is None:
            raise ValueError("Cannot get file size for network without file_path")
        return self.file_path.stat().st_size


class NetworkCollectionService:
    """Service for PyPSA network collection operations (handles multiple networks)"""

    def __init__(self, file_paths: list[Path] | list[str], use_cache: bool = True):
        """Initialize service by loading networks and creating a collection"""
        file_paths = [Path(p) for p in file_paths]
        names = self._generate_unique_names_from_paths(file_paths)

        networks = {}
        for file_path, name in zip(file_paths, names):
            file_path = validate_path(file_path, must_exist=True)

            # Try cache first
            if use_cache and (cached := _network_cache.get(file_path)):
                networks[name] = cached
            else:
                # Load network directly
                network = pypsa.Network(file_path)
                if use_cache:
                    _network_cache.put(file_path, network)
                networks[name] = network

        self.n = pypsa.NetworkCollection(
            list(networks.values()), index=list(networks.keys())
        )

    def get_summary(self) -> dict:
        """Get summary information about the collection"""
        info = {}
        info["collection_size"] = len(self.n.networks)
        info["network_indices"] = list(self.n.index)

        return info

    @staticmethod
    def _generate_unique_names_from_paths(file_paths: list[Path]) -> list[str]:
        """Generate unique names for networks based on file paths"""
        names = []
        for path in file_paths:
            # Use filename without extension as name
            name = path.stem
            # Handle duplicates by appending parent directory
            if name in names:
                name = f"{path.parent.name}_{name}"
            names.append(name)
        return names


def load_service(
    file_paths: list[str] | list[Path], use_cache: bool = True
) -> NetworkService | NetworkCollectionService:
    """Load one or more networks, returning appropriate service.

    Args:
        file_paths: Single file path or list of file paths
        use_cache: Whether to use the network cache

    Returns:
        NetworkService if single file, NetworkCollectionService if multiple files
    """
    if len(file_paths) == 1:
        return NetworkService(file_paths[0], use_cache=use_cache)
    else:
        return NetworkCollectionService(file_paths, use_cache=use_cache)


def _process_network_file(
    file_path: Path, existing: Network | None, db
) -> tuple[bool, bool, str | None]:
    """Process a single network file (create or update).

    Returns:
        Tuple of (was_added, was_updated, error_message)
    """
    try:
        from pypsa_app.backend.services.map import generate_topology_svg

        service = NetworkService(file_path, use_cache=False)
        file_hash = service.calculate_file_hash()
        file_size = service.get_file_size()

        if existing:
            # Update existing network
            needs_update = existing.file_hash != file_hash
            needs_svg = existing.topology_svg is None

            if not (needs_update or needs_svg):
                del service
                return False, False, None

            if needs_update:
                info = service.extract_database_info()
                existing.file_hash = file_hash
                existing.file_size = file_size
                existing.name = info["name"]
                existing.components_count = info["components_count"]
                existing.dimensions_count = info["dimensions_count"]
                existing.meta = info["meta"]
                existing.facets = info["facets"]

                update_time = datetime.utcnow().isoformat()
                if existing.update_history is None:
                    existing.update_history = []
                existing.update_history.append(update_time)

            if needs_svg:
                existing.topology_svg = generate_topology_svg(service.n)

            del service
            gc.collect()
            db.commit()

            return False, needs_update, None

        else:
            # Add new network
            info = service.extract_database_info()
            topology_svg = generate_topology_svg(service.n)
            creation_time = datetime.utcnow().isoformat()

            network = Network(
                filename=file_path.name,
                file_path=str(file_path),
                file_hash=file_hash,
                file_size=file_size,
                name=info["name"],
                components_count=info["components_count"],
                dimensions_count=info["dimensions_count"],
                meta=info["meta"],
                facets=info["facets"],
                topology_svg=topology_svg,
                update_history=[creation_time],
            )
            db.add(network)

            try:
                db.commit()
                del service
                gc.collect()
                return True, False, None
            except IntegrityError:
                db.rollback()
                del service
                return False, False, None

    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to process network",
            extra={
                "filename": file_path.name,
                "file_path": str(file_path),
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return False, False, str(e)


def scan_networks(networks_path: Path | str) -> dict:
    """Scan directory for network files and update database

    Args:
        networks_path: Path to directory containing network files (Path or str)

    Returns:
        Dict with scan results (added, updated, errors)
    """
    networks_path = Path(networks_path)
    if not networks_path.exists():
        return {
            "status": "error",
            "error": f"Networks directory does not exist: {networks_path}",
        }

    files = list(networks_path.rglob("*.nc"))
    total_files = len(files)
    added = updated = 0
    errors = []

    db = SessionLocal()
    try:
        for file_path in files:
            existing = (
                db.query(Network)
                .filter(Network.file_path == str(file_path))
                .with_for_update()
                .first()
            )

            was_added, was_updated, error = _process_network_file(
                file_path, existing, db
            )

            if was_added:
                added += 1
            if was_updated:
                updated += 1
            if error:
                errors.append({"filename": file_path.name, "error": error})

    finally:
        db.close()

    return {
        "status": "success",
        "files_found": total_files,
        "added": added,
        "updated": updated,
        "errors": errors,
    }

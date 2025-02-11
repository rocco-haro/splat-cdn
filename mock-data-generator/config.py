# config.py
from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, Optional

@dataclass
class GridDimensions:
    width: int  # cells in x dimension
    height: int # cells in y dimension
    depth: int  # cells in z dimension
    cell_size: float  # size of each cell in units
    loading_radius: float = 50.0  # default loading radius

@dataclass
class SplatConfig:
    min_size: int  # minimum size in bytes
    max_size: int  # maximum size in bytes
    
@dataclass
class CacheConfig:
    l1_size: int  # L1 cache size in bytes
    l2_size: int  # L2 cache size in bytes

@dataclass
class NetworkConfig:
    l1_latency_ms: int  # L1 cache latency
    l2_latency_ms: int  # L2 cache latency
    origin_latency_ms: int  # Origin (S3) latency
    packet_loss_percent: float  # Simulated packet loss rate

@dataclass
class SuccessMetrics:
    min_cache_hit_rate: float  # Minimum acceptable cache hit rate
    max_latency_ms: float  # Maximum acceptable latency
    min_preload_success_rate: float  # Minimum successful preloads

@dataclass
class ExperimentConfig:
    grid: GridDimensions
    splat: SplatConfig
    cache: CacheConfig
    network: NetworkConfig
    metrics: SuccessMetrics

class ConfigLoader:
    def __init__(self, experiments_dir: Path):
        self.experiments_dir = experiments_dir
        
    def load_experiment(self, experiment_id: str) -> ExperimentConfig:
        """Load configuration for a specific experiment"""
        config_path = self.experiments_dir / experiment_id / "config.json"
        
        if not config_path.exists():
            raise ValueError(f"No configuration found for experiment {experiment_id}")
            
        with open(config_path) as f:
            data = json.load(f)
            
        return ExperimentConfig(
            grid=GridDimensions(
                width=data["grid"]["width"],
                height=data["grid"]["height"],
                depth=data["grid"]["depth"],
                cell_size=data["grid"]["cell_size"],
                loading_radius=data["grid"].get("loading_radius", 50.0)
            ),
            splat=SplatConfig(
                min_size=data["splat"]["min_size"],
                max_size=data["splat"]["max_size"]
            ),
            cache=CacheConfig(
                l1_size=data["cache"]["l1_size"],
                l2_size=data["cache"]["l2_size"]
            ),
            network=NetworkConfig(
                l1_latency_ms=data["network"]["l1_latency_ms"],
                l2_latency_ms=data["network"]["l2_latency_ms"],
                origin_latency_ms=data["network"]["origin_latency_ms"],
                packet_loss_percent=data["network"]["packet_loss_percent"]
            ),
            metrics=SuccessMetrics(
                min_cache_hit_rate=data["metrics"]["min_cache_hit_rate"],
                max_latency_ms=data["metrics"]["max_latency_ms"],
                min_preload_success_rate=data["metrics"]["min_preload_success_rate"]
            )
        )
    
    def create_default_config(self, experiment_id: str) -> None:
        """Create a default configuration file for an experiment"""
        config = {
            "grid": {
                "width": 10,
                "height": 10,
                "depth": 10,
                "cell_size": 5.0,
                "loading_radius": 2.0
            },
            "splat": {
                "min_size": 100 * 1024,    # 100KB
                "max_size": 10 * 1024 * 1024  # 10MB
            },
            "cache": {
                "l1_size": 1 * 1024 * 1024 * 1024,  # 1GB
                "l2_size": 10 * 1024 * 1024 * 1024  # 10GB
            },
            "network": {
                "l1_latency_ms": 10,
                "l2_latency_ms": 50,
                "origin_latency_ms": 500,
                "packet_loss_percent": 1.0
            },
            "metrics": {
                "min_cache_hit_rate": 0.99,
                "max_latency_ms": 500.0,
                "min_preload_success_rate": 0.95
            }
        }
        
        output_dir = self.experiments_dir / experiment_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)
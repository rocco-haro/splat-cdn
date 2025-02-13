import pytest
from pathlib import Path
import json
import shutil
from generator import ExperimentGenerator
from config import (
    GridDimensions, 
    SplatConfig, 
    CacheConfig, 
    NetworkConfig, 
    SuccessMetrics,
    ScenarioConfig,
    TeleportScenarioConfig,
    SpiralScenarioConfig,
)

class MockConfigLoader:
    def load_experiment(self, experiment_id: str):
        # Return a test configuration
        class Config:
            pass
        
        config = Config()
        config.grid = GridDimensions(
            width=4,    # Small grid for testing
            height=4,
            depth=4,
            cell_size=1.0,
            loading_radius=2.0
        )
        
        config.splat = SplatConfig(
            min_size=100,    # Small sizes for testing
            max_size=1000
        )
        
        config.cache = CacheConfig(
            l1_size=1024 * 1024,      # 1MB
            l2_size=10 * 1024 * 1024  # 10MB
        )
        
        config.network = NetworkConfig(
            l1_latency_ms=10,
            l2_latency_ms=50,
            origin_latency_ms=500,
            packet_loss_percent=1.0
        )
        
        config.metrics = SuccessMetrics(
            min_cache_hit_rate=0.99,
            max_latency_ms=500.0,
            min_preload_success_rate=0.95
        )

        config.scenarios = ScenarioConfig(
            teleport=TeleportScenarioConfig(
                dwell_duration=15.0,
                teleport_duration=1.0,
                post_teleport_duration=5.0
            ),
            spiral=SpiralScenarioConfig(
                duration=30.0
            )
        )
        
        return config

@pytest.fixture
def output_dir(tmp_path):
    test_dir = tmp_path / "test_experiment"
    yield test_dir
    # Cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)

@pytest.fixture
def generator():
    return ExperimentGenerator(MockConfigLoader())

def test_successful_generation(generator, output_dir):
    # Generate experiment data
    generator.generate_experiment("test", output_dir)
    
    # Check required files exist
    assert (output_dir / "grid_map.json").exists()
    assert (output_dir / "test_paths.json").exists()
    
    # Validate grid_map.json content
    with open(output_dir / "grid_map.json") as f:
        grid_map = json.load(f)
        
    assert "bounds" in grid_map
    assert "metadata" in grid_map
    assert "splats" in grid_map
    assert grid_map["metadata"]["cellSize"] == 1.0
    assert grid_map["metadata"]["loadingRadius"] == 2.0
    
    # Check splat files exist and match metadata
    for splat_id, splat_info in grid_map["splats"].items():
        splat_path = output_dir / splat_info["path"]
        assert splat_path.exists()
        assert splat_path.stat().st_size == splat_info["size"]
        
    # Validate test_paths.json content
    with open(output_dir / "test_paths.json") as f:
        paths = json.load(f)
    
    # Check top-level structure
    assert "cdn" in paths
    assert "scenarios" in paths
    assert "config" in paths
    
    # Check CDN config
    assert "domain" in paths["cdn"]
    assert "type" in paths["cdn"]
    
    # Check scenarios
    assert "teleport" in paths["scenarios"]
    assert "spiral" in paths["scenarios"]
    
    # Check scenario configs
    assert "scenarios" in paths["config"]
    assert "teleport" in paths["config"]["scenarios"]
    assert "spiral" in paths["config"]["scenarios"]
    
    # Check teleport config values
    teleport_config = paths["config"]["scenarios"]["teleport"]
    assert teleport_config["dwell_duration"] == 15.0
    assert teleport_config["teleport_duration"] == 1.0
    assert teleport_config["post_teleport_duration"] == 5.0
    
    # Check points structure
    for scenario in ["teleport", "spiral"]:
        assert "points" in paths["scenarios"][scenario]
        for point in paths["scenarios"][scenario]["points"]:
            assert "position" in point
            assert "timestamp" in point
            assert "expected_splats" in point

def test_validation_missing_file(generator, output_dir):
    # Generate experiment data
    generator.generate_experiment("test", output_dir)
    
    # Remove a required file
    (output_dir / "test_paths.json").unlink()
    
    # Validation should fail
    with pytest.raises(ValueError, match="Missing required file"):
        generator._validate_experiment(output_dir, generator.config_loader.load_experiment("test"))

def test_validation_invalid_splat_size(generator, output_dir):
    # Generate experiment data
    generator.generate_experiment("test", output_dir)
    
    # Load grid map
    with open(output_dir / "grid_map.json") as f:
        grid_map = json.load(f)
    
    # Modify a splat size in metadata but not the file
    first_splat = next(iter(grid_map["splats"].values()))
    original_size = first_splat["size"]
    first_splat["size"] = original_size + 100
    
    # Save modified grid map
    with open(output_dir / "grid_map.json", "w") as f:
        json.dump(grid_map, f)
    
    # Validation should fail
    with pytest.raises(ValueError, match="Size mismatch"):
        generator._validate_experiment(output_dir, generator.config_loader.load_experiment("test"))

def test_validation_missing_scenario(generator, output_dir):
    # Generate experiment data
    generator.generate_experiment("test", output_dir)
    
    # Load test paths
    with open(output_dir / "test_paths.json") as f:
        paths = json.load(f)
    
    # Remove a required scenario
    del paths["scenarios"]["teleport"]
    
    # Save modified paths
    with open(output_dir / "test_paths.json", "w") as f:
        json.dump(paths, f)
    
    # Validation should fail
    with pytest.raises(ValueError, match="Missing required test scenario"):
        generator._validate_experiment(output_dir, generator.config_loader.load_experiment("test"))
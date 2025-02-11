# test_splat_generator.py
import pytest
from pathlib import Path
import json
from config import GridDimensions, SplatConfig
from splat_generator import SplatGenerator

@pytest.fixture
def config():
    grid = GridDimensions(
        width=2,    # Small grid for testing
        height=2,
        depth=2,
        cell_size=10.0
    )
    splat = SplatConfig(
        min_size=100,    # Small sizes for testing
        max_size=1000
    )
    # Create a simple object with our config attributes
    class Config:
        pass
    config = Config()
    config.grid = grid
    config.splat = splat
    return config

@pytest.fixture
def generator(config):
    return SplatGenerator(config)

@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "test_output"

def test_splat_size_bounds(generator, output_dir):
    metadata = generator.generate_splats(output_dir)
    
    # Check each generated splat
    for splat_info in metadata.values():
        assert splat_info['size'] >= generator.config.splat.min_size
        assert splat_info['size'] <= generator.config.splat.max_size

def test_directory_structure(generator, output_dir):
    metadata = generator.generate_splats(output_dir)
    
    # Check splats directory exists
    assert (output_dir / "splats").exists()
    
    # Check each splat file exists
    for splat_info in metadata.values():
        assert (output_dir / splat_info['path']).exists()
        
    # Check stats file exists
    assert (output_dir / "splat_stats.json").exists()

def test_adjacency_calculation(generator):
    # Position (1,1,1) in a 2x2x2 grid has 3 adjacent positions
    adjacent = generator._get_adjacent_splats(1, 1, 1)
    assert len(adjacent) == 3
    assert "0_1_1" in adjacent  # -x
    assert "1_0_1" in adjacent  # -y
    assert "1_1_0" in adjacent  # -z
    
    # Test (0,0,0) which should have 3 adjacent in positive directions
    corner = generator._get_adjacent_splats(0, 0, 0)
    assert len(corner) == 3
    assert "1_0_0" in corner  # +x
    assert "0_1_0" in corner  # +y
    assert "0_0_1" in corner  # +z

def test_stats_calculation(generator, output_dir):
    generator.generate_splats(output_dir)
    
    with open(output_dir / "splat_stats.json") as f:
        stats = json.load(f)
    
    # Check stats fields exist
    assert "total_splats" in stats
    assert "total_size_bytes" in stats
    assert "min_size" in stats
    assert "max_size" in stats
    assert "mean_size" in stats
    assert "size_percentiles" in stats
    
    # Verify total splats for 2x2x2 grid
    assert stats["total_splats"] == 8
    
    # Verify bounds
    assert stats["min_size"] >= generator.config.splat.min_size
    assert stats["max_size"] <= generator.config.splat.max_size

def test_splat_content_size(generator, output_dir):
    metadata = generator.generate_splats(output_dir)
    
    # Check each splat file size matches metadata
    for splat_info in metadata.values():
        file_size = (output_dir / splat_info['path']).stat().st_size
        assert file_size == splat_info['size']
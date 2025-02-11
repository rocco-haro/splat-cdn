# test_path_generator.py
import pytest
import math
from config import GridDimensions
from path_generator import PathGenerator, Position

@pytest.fixture
def config():
    class Config:
        pass
    
    config = Config()
    config.grid = GridDimensions(
        width=10,       # 10x10x10 grid for testing
        height=10,
        depth=10,
        cell_size=1.0,   # 1 unit cells for easy math
        loading_radius=2
    )
    config.grid.loading_radius = 2.0  # 2 unit loading radius
    
    return config

@pytest.fixture
def generator(config):
    return PathGenerator(config)

def test_get_splats_in_radius(generator):
    # Test center of grid
    center_pos = Position(x=5.0, y=5.0, z=5.0)
    splats = generator._get_splats_in_radius(center_pos)
    
    # For a radius of 2.0 units in a 1.0 unit cell grid,
    # we should get roughly a sphere of cells with radius 2
    # Count should be approximately 4/3 * pi * r^3
    expected_count = int(4/3 * math.pi * 8)  # r=2 units
    assert abs(len(splats) - expected_count) <= 5  # Allow some variation due to grid alignment
    
    # Test grid edge
    edge_pos = Position(x=0.0, y=0.0, z=0.0)
    edge_splats = generator._get_splats_in_radius(edge_pos)
    
    # At corner, should get significantly fewer splats than at center
    assert len(edge_splats) < len(splats)
    # The exact count should be valid for a sphere portion bounded by grid
    assert 8 <= len(edge_splats) <= 14  # Allowing some variation due to grid alignment

def test_teleport_path(generator):
    path = generator.generate_teleport_path()
    
    # Should have exactly 3 points: start, move, teleport
    assert len(path.points) == 3
    
    # Check timestamps
    assert path.points[0].timestamp == 0.0
    assert path.points[1].timestamp == 30.0
    assert path.points[2].timestamp == 31.0
    
    # First point should be in "NY" region (25% of grid)
    start = path.points[0].position
    assert start.x == pytest.approx(generator.config.grid.width * 0.25)
    assert start.z == pytest.approx(generator.config.grid.depth * 0.25)
    
    # Last point should be in "LA" region (75% of grid)
    end = path.points[2].position
    assert end.x == pytest.approx(generator.config.grid.width * 0.75)
    assert end.z == pytest.approx(generator.config.grid.depth * 0.75)
    
    # Each point should have expected splats
    for point in path.points:
        assert len(point.expected_splats) > 0

def test_spiral_path(generator):
    path = generator.generate_spiral_path()
    
    # Should have multiple points
    assert len(path.points) > 5
    
    # First point should be at center of grid
    start = path.points[0].position
    assert start.x == pytest.approx(generator.config.grid.width / 2)
    assert start.z == pytest.approx(generator.config.grid.depth / 2)
    
    # Time should increase monotonically
    for i in range(1, len(path.points)):
        assert path.points[i].timestamp > path.points[i-1].timestamp
        
    # Points should spiral outward
    center_dist = []
    center_x = generator.config.grid.width / 2
    center_z = generator.config.grid.depth / 2
    
    for point in path.points:
        dx = point.position.x - center_x
        dz = point.position.z - center_z
        dist = math.sqrt(dx*dx + dz*dz)
        center_dist.append(dist)
    
    # Distances should generally increase
    # (allowing for some grid alignment variation)
    increasing_count = sum(1 for i in range(1, len(center_dist))
                         if center_dist[i] >= center_dist[i-1])
    assert increasing_count > len(center_dist) * 0.8  # At least 80% should increase

    # Each point should have expected splats
    for point in path.points:
        assert len(point.expected_splats) > 0
        
def test_paths_stay_in_bounds(generator):
    # Test both path types
    paths = [
        generator.generate_teleport_path(),
        generator.generate_spiral_path()
    ]
    
    for path in paths:
        for point in path.points:
            # Check x bounds
            assert 0 <= point.position.x < generator.config.grid.width
            # Check y bounds
            assert 0 <= point.position.y < generator.config.grid.height
            # Check z bounds
            assert 0 <= point.position.z < generator.config.grid.depth
# mock-data-generator/path_generator.py
import math
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

@dataclass
class Position:
    x: float
    y: float
    z: float

@dataclass
class PathPoint:
    position: Position
    timestamp: float  # seconds from start
    expected_splats: List[str]  # list of splat IDs that should be loaded

@dataclass
class TestPath:
    points: List[PathPoint]

class PathGenerator:
    def __init__(self, config):
        self.config = config

    def _get_splats_in_radius(self, position: Position) -> List[str]:
        """Get all splat IDs within loading radius of position"""
        splats = []
        center_x = int(position.x / self.config.grid.cell_size)
        center_y = int(position.y / self.config.grid.cell_size)
        center_z = int(position.z / self.config.grid.cell_size)
        radius_cells = math.ceil(self.config.grid.loading_radius / self.config.grid.cell_size)

        for x in range(center_x - radius_cells, center_x + radius_cells + 1):
            for y in range(center_y - radius_cells, center_y + radius_cells + 1):
                for z in range(center_z - radius_cells, center_z + radius_cells + 1):
                    # Check if cell is within grid bounds
                    if (0 <= x < self.config.grid.width and
                        0 <= y < self.config.grid.height and
                        0 <= z < self.config.grid.depth):
                        # Check if cell is within spherical loading radius
                        dx = (x - center_x) * self.config.grid.cell_size
                        dy = (y - center_y) * self.config.grid.cell_size
                        dz = (z - center_z) * self.config.grid.cell_size
                        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                        
                        if distance <= self.config.grid.loading_radius:
                            splats.append(f"{x}_{y}_{z}")

        return splats

    def generate_teleport_path(self) -> TestPath:
        """Generate a teleport test scenario path"""
        # Start in NY region (25% into grid)
        start_x = self.config.grid.width * 0.25
        start_z = self.config.grid.depth * 0.25
        start_pos = Position(x=start_x, y=0, z=start_z)

        # End in LA region (75% into grid)
        end_x = self.config.grid.width * 0.75
        end_z = self.config.grid.depth * 0.75
        end_pos = Position(x=end_x, y=0, z=end_z)

        points = []
        
        # Initial position
        points.append(PathPoint(
            position=start_pos,
            timestamp=0.0,
            expected_splats=self._get_splats_in_radius(start_pos)
        ))

        # Move in straight line for 30 seconds
        move_distance = self.config.grid.cell_size * 2  # Move 2 cells
        move_pos = Position(
            x=start_pos.x + move_distance,
            y=0,
            z=start_pos.z
        )
        points.append(PathPoint(
            position=move_pos,
            timestamp=30.0,
            expected_splats=self._get_splats_in_radius(move_pos)
        ))

        # Teleport to LA
        points.append(PathPoint(
            position=end_pos,
            timestamp=31.0,  # 1 second after last position
            expected_splats=self._get_splats_in_radius(end_pos)
        ))

        return TestPath(points=points)

    def generate_spiral_path(self) -> TestPath:
        """Generate a spiral test scenario path"""
        # Start at center of grid
        center_x = self.config.grid.width / 2
        center_z = self.config.grid.depth / 2
        center = Position(x=center_x, y=0, z=center_z)

        points = []
        time = 0.0
        spiral_radius = 0.0
        angle = 0.0

        # Initial position
        points.append(PathPoint(
            position=center,
            timestamp=time,
            expected_splats=self._get_splats_in_radius(center)
        ))

        # Generate spiral points until we reach double the loading radius
        time += 1.0  # Move to first spiral point
        
        while spiral_radius < self.config.grid.loading_radius * 2:
            # Calculate next point on spiral
            x = center_x + spiral_radius * math.cos(angle)
            z = center_z + spiral_radius * math.sin(angle)

            # Only add point if it's within grid bounds and different from last position
            if (0 <= x < self.config.grid.width and 
                0 <= z < self.config.grid.depth):
                pos = Position(x=x, y=0, z=z)
                
                # Only add if this is a new position (avoid duplicates)
                if not points or (abs(points[-1].position.x - x) > 0.01 or 
                                abs(points[-1].position.z - z) > 0.01):
                    points.append(PathPoint(
                        position=pos,
                        timestamp=time,
                        expected_splats=self._get_splats_in_radius(pos)
                    ))
                    time += 1.0  # 1 second between points
                
            angle += 0.5  # Rate of rotation
            spiral_radius += self.config.grid.cell_size * 0.5  # Rate of expansion

        return TestPath(points=points)
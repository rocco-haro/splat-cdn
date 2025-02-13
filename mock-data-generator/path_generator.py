import math
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import numpy as np

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
        self.points_per_second = 10  # Higher sampling rate for smoother movement

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
                    if (0 <= x < self.config.grid.width and
                        0 <= y < self.config.grid.height and
                        0 <= z < self.config.grid.depth):
                        dx = (x - center_x) * self.config.grid.cell_size
                        dy = (y - center_y) * self.config.grid.cell_size
                        dz = (z - center_z) * self.config.grid.cell_size
                        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                        
                        if distance <= self.config.grid.loading_radius:
                            splats.append(f"{x}_{y}_{z}")

        return splats

    def _interpolate_positions(self, start: Position, end: Position, num_points: int) -> List[Position]:
        """Generate intermediate positions between start and end points"""
        if not isinstance(num_points, int):
            num_points = int(num_points)  # Convert float to int if needed
            
        if num_points < 1:
            raise ValueError("num_points must be at least 1")
                
        positions = []
        for i in range(num_points):
            t = i / (num_points - 1) if num_points > 1 else 0
            pos = Position(
                x=start.x + t * (end.x - start.x),
                y=start.y + t * (end.y - start.y),
                z=start.z + t * (end.z - start.z)
            )
            positions.append(pos)
        return positions

    def generate_teleport_path(self) -> TestPath:
        """Generate an enhanced teleport test scenario path"""
        dwell_duration = self.config.scenarios.teleport.dwell_duration
        post_teleport_duration = self.config.scenarios.teleport.post_teleport_duration
        teleport_duration = self.config.scenarios.teleport.teleport_duration
        
        # Start in NY region (25% into grid)
        start_x = self.config.grid.width * 0.25
        start_z = self.config.grid.depth * 0.25
        start_pos = Position(x=start_x, y=0, z=start_z)

        # End in LA region (75% into grid)
        end_x = self.config.grid.width * 0.75
        end_z = self.config.grid.depth * 0.75
        teleport_pos = Position(x=end_x, y=0, z=end_z)

        points = []
        
        # Initial dwell period
        num_dwell_points = int(dwell_duration * self.points_per_second)
        dwell_points = self._interpolate_positions(
            start_pos,
            Position(x=start_x + self.config.grid.cell_size, y=0, z=start_z),
            num_dwell_points
        )
        
        for i, pos in enumerate(dwell_points):
            points.append(PathPoint(
                position=pos,
                timestamp=i / self.points_per_second,
                expected_splats=self._get_splats_in_radius(pos)
            ))

        # Teleport sequence
        num_teleport_points = int(teleport_duration * self.points_per_second)
        teleport_points = self._interpolate_positions(
            points[-1].position,
            teleport_pos,
            num_teleport_points
        )
        
        current_time = dwell_duration
        for i, pos in enumerate(teleport_points):
            points.append(PathPoint(
                position=pos,
                timestamp=current_time + (i / self.points_per_second),
                expected_splats=self._get_splats_in_radius(pos)
            ))
            
        # Post-teleport movement
        if post_teleport_duration > 0:
            current_time = dwell_duration + teleport_duration
            num_post_points = int(post_teleport_duration * self.points_per_second)
            post_end = Position(
                x=end_x + self.config.grid.cell_size * 2,
                y=0,
                z=end_z + self.config.grid.cell_size
            )
            post_points = self._interpolate_positions(
                teleport_pos,
                post_end,
                num_post_points
            )
            
            for i, pos in enumerate(post_points):
                points.append(PathPoint(
                    position=pos,
                    timestamp=current_time + (i / self.points_per_second),
                    expected_splats=self._get_splats_in_radius(pos)
                ))

        return TestPath(points=points)

    def generate_spiral_path(self) -> TestPath:
        """Generate an enhanced spiral test scenario path"""
        duration = self.config.scenarios.spiral.duration
        center_x = self.config.grid.width / 2
        center_z = self.config.grid.depth / 2
        points = []
        
        # Parameters for a smoother, longer spiral
        max_radius = self.config.grid.loading_radius * 2
        total_points = int(duration * self.points_per_second)
        
        # Generate spiral using parametric equations
        t = np.linspace(0, 8*np.pi, total_points)
        spiral_radius = (t / (8*np.pi)) * max_radius
        
        x_coords = center_x + spiral_radius * np.cos(t)
        z_coords = center_z + spiral_radius * np.sin(t)
        
        for i in range(total_points):
            if (0 <= x_coords[i] < self.config.grid.width and 
                0 <= z_coords[i] < self.config.grid.depth):
                pos = Position(
                    x=float(x_coords[i]),
                    y=0,
                    z=float(z_coords[i])
                )
                points.append(PathPoint(
                    position=pos,
                    timestamp=i / self.points_per_second,
                    expected_splats=self._get_splats_in_radius(pos)
                ))

        return TestPath(points=points)
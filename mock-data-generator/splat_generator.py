# mock-data-generator/splat_generator.py
import random
from pathlib import Path
from typing import Dict, List, Tuple
import json

class SplatGenerator:
    def __init__(self, config):
        self.config = config
        self.size_distribution = []  # Track generated sizes for stats
        
    def _generate_splat_data(self, size: int) -> bytes:
        """Generate random binary data of specified size"""
        return random.randbytes(size)
        
    def _get_splat_path(self, x: int, y: int, z: int) -> str:
        """Generate consistent path for splat storage"""
        return f"splats/{x}_{y}_{z}/splat.bin"

    def generate_splats(self, output_dir: Path) -> Dict:
        """Generate all splats for the grid and return metadata"""
        splat_metadata = {}
        splats_dir = output_dir / "splats"
        splats_dir.mkdir(parents=True, exist_ok=True)

        # Generate splats for each grid cell
        for x in range(self.config.grid.width):
            for y in range(self.config.grid.height):
                for z in range(self.config.grid.depth):
                    # Generate size following distribution
                    size = random.randint(self.config.splat.min_size, 
                                       self.config.splat.max_size)
                    self.size_distribution.append(size)
                    
                    # Generate splat data
                    splat_data = self._generate_splat_data(size)
                    
                    # Setup path and save
                    relative_path = self._get_splat_path(x, y, z)
                    full_path = output_dir / relative_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(full_path, "wb") as f:
                        f.write(splat_data)
                    
                    # Record metadata
                    splat_metadata[f"{x}_{y}_{z}"] = {
                        "path": relative_path,
                        "size": size,
                        "coordinates": [x, y, z],
                        "adjacent_splats": self._get_adjacent_splats(x, y, z)
                    }
        
        # Save size distribution stats
        stats = self._calculate_stats()
        with open(output_dir / "splat_stats.json", "w") as f:
            json.dump(stats, f, indent=2)
            
        return splat_metadata
    
    def _get_adjacent_splats(self, x: int, y: int, z: int) -> List[str]:
        """Get IDs of adjacent splats for preloading"""
        adjacent = []
        
        # Check all 6 faces (±x, ±y, ±z)
        directions = [
            (1,0,0), (-1,0,0),  # x-axis
            (0,1,0), (0,-1,0),  # y-axis
            (0,0,1), (0,0,-1)   # z-axis
        ]
        
        for dx, dy, dz in directions:
            new_x, new_y, new_z = x + dx, y + dy, z + dz
            
            # Check if within grid bounds
            if (0 <= new_x < self.config.grid.width and
                0 <= new_y < self.config.grid.height and
                0 <= new_z < self.config.grid.depth):
                adjacent.append(f"{new_x}_{new_y}_{new_z}")
            
        return adjacent
    
    def _calculate_stats(self) -> Dict:
        """Calculate statistics about generated splats"""
        if not self.size_distribution:
            return {}
            
        sizes = sorted(self.size_distribution)
        total = len(sizes)
        
        return {
            "total_splats": total,
            "total_size_bytes": sum(sizes),
            "min_size": sizes[0],
            "max_size": sizes[-1],
            "median_size": sizes[total // 2],
            "mean_size": sum(sizes) / total,
            "size_percentiles": {
                "p25": sizes[total // 4],
                "p50": sizes[total // 2],
                "p75": sizes[3 * total // 4],
                "p90": sizes[9 * total // 10],
                "p99": sizes[99 * total // 100]
            }
        }
import argparse
import json
from pathlib import Path
from typing import Dict, Any

from config import ConfigLoader
from splat_generator import SplatGenerator
from path_generator import PathGenerator

class ExperimentGenerator:
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader

    def generate_experiment(self, experiment_id: str, output_dir: Path) -> None:
        """Generate all data for an experiment"""
        # Load experiment config
        config = self.config_loader.load_experiment(experiment_id)
        
        # Create output directories
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate splats
        splat_generator = SplatGenerator(config)
        splat_metadata = splat_generator.generate_splats(output_dir)
        
        # Generate test paths
        path_generator = PathGenerator(config)
        paths = {
            "teleport": path_generator.generate_teleport_path(),
            "spiral": path_generator.generate_spiral_path()
        }
        
        # Convert paths to JSON-serializable format
        paths_json = {
            "cdn": {
                "domain": "d1234.cloudfront.net",
                "type": "single_tier"
            },
            "scenarios": {
                name: {
                    "points": [
                        {
                            "position": {
                                "x": p.position.x,
                                "y": p.position.y,
                                "z": p.position.z
                            },
                            "timestamp": p.timestamp,
                            "expected_splats": p.expected_splats
                        }
                        for p in path.points
                    ]
                }
                for name, path in paths.items()
            },
            "config": {
                "scenarios": {
                    "teleport": {
                        "dwell_duration": config.scenarios.teleport.dwell_duration,
                        "teleport_duration": config.scenarios.teleport.teleport_duration,
                        "post_teleport_duration": config.scenarios.teleport.post_teleport_duration
                    },
                    "spiral": {
                        "duration": config.scenarios.spiral.duration
                    }
                }
            }
        }
        
        # Write grid map
        grid_map = {
            "bounds": {
                "minX": 0,
                "maxX": config.grid.width * config.grid.cell_size,
                "minY": 0,
                "maxY": config.grid.height * config.grid.cell_size,
                "minZ": 0,
                "maxZ": config.grid.depth * config.grid.cell_size
            },
            "metadata": {
                "cellSize": config.grid.cell_size,
                "loadingRadius": config.grid.loading_radius
            },
            "splats": splat_metadata
        }
        
        with open(output_dir / "grid_map.json", "w") as f:
            json.dump(grid_map, f, indent=2)
            
        # Write test paths
        with open(output_dir / "test_paths.json", "w") as f:
            json.dump(paths_json, f, indent=2)
            
        # Validate the generated data
        self._validate_experiment(output_dir, config)
        
    def _validate_experiment(self, output_dir: Path, config: Any) -> None:
        """Validate that all required files and data are present and valid"""
        required_files = ["grid_map.json", "test_paths.json"]
        for file in required_files:
            if not (output_dir / file).exists():
                raise ValueError(f"Missing required file: {file}")
                
        with open(output_dir / "grid_map.json") as f:
            grid_map = json.load(f)
            
        # Check all splat files exist
        for splat_id, splat_info in grid_map["splats"].items():
            splat_path = output_dir / splat_info["path"]
            if not splat_path.exists():
                raise ValueError(f"Missing splat file: {splat_path}")
            
            # Verify file size matches metadata
            if splat_path.stat().st_size != splat_info["size"]:
                raise ValueError(
                    f"Size mismatch for {splat_id}: "
                    f"expected {splat_info['size']}, "
                    f"got {splat_path.stat().st_size}"
                )
                
        # Load and validate test paths
        with open(output_dir / "test_paths.json") as f:
            paths = json.load(f)
            
        # Check required scenarios exist
        required_scenarios = ["teleport", "spiral"]
        for scenario in required_scenarios:
            if scenario not in paths["scenarios"]:
                raise ValueError(f"Missing required test scenario: {scenario}")
                
        print(f"Successfully validated experiment data in {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Generate CDN test data")
    parser.add_argument("--experiment", required=True, help="Experiment ID")
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    experiments_dir = base_dir / "experiments"
    output_dir = base_dir / "generated" / args.experiment
    
    config_loader = ConfigLoader(experiments_dir)
    generator = ExperimentGenerator(config_loader)
    
    try:
        generator.generate_experiment(args.experiment, output_dir)
        print(f"Successfully generated experiment data in {output_dir}")
    except Exception as e:
        print(f"Error generating experiment: {e}")
        exit(1)

if __name__ == "__main__":
    main()
from pathlib import Path
from config import ConfigLoader

# Setup paths
base_dir = Path(__file__).parent
experiments_dir = base_dir / "experiments"

# Create config loader
config_loader = ConfigLoader(experiments_dir)

# Create default config for experiment_A
config_loader.create_default_config("experiment_A")
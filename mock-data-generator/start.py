from pathlib import Path
from config import ConfigLoader

base_dir = Path(__file__).parent
experiments_dir = base_dir / "experiments"

config_loader = ConfigLoader(experiments_dir)

config_loader.create_default_config("experiment_A")
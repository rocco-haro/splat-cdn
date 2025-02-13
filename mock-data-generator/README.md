# Splat Content Delivery Mock Data Generator

## Setup

### Prerequisites
- Python 3.9+
- pip
- (Optional) virtualenv

### Installation

1. Create and activate a virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate on Unix/macOS
source venv/bin/activate

```
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Generating Experiment Data

### Create a New Experiment

#### Start
To generate mock data for a new experiment:

 Create a new configuration in `experiments/experiment_A/config.json` and create manually or 
```bash
python start.py
```

```bash
# Run the generator with a unique experiment ID
python generator.py --experiment experiment_A
```

This will:
- Generate mock splat files 
- Create test paths
- Output data to `generated/experiment_A/`

### Customizing Experiment Configuration

You can modify the experiment configuration before generating data. Edit `experiments/experiment_A/config.json`:

### Generated Data Structure

After running the generator, you'll find:
- `grid_map.json`: Complete grid and splat metadata
- `test_paths.json`: Test scenario movement paths
- `splats/`: Directory containing generated splat files
- `splat_stats.json`: Statistics about generated splats

## Running Tests

```bash
# Run all tests
pytest

```

## Experiment Design Considerations

The generator supports two main test scenarios:
1. **Teleport Scenario**: Simulates moving between distant regions
2. **Spiral Scenario**: Tests cache performance during continuous movement

You can adjust the experiment configuration to test different:
- Grid sizes
- Splat sizes
- (WIP) Network conditions
- Caching strategies

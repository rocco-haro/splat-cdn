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

# Activate on Windows
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Generating Experiment Data

### Create a New Experiment

To generate mock data for a new experiment:

```bash
# Run the generator with a unique experiment ID
python generator.py --experiment experiment_A
```

This will:
- Create a new configuration in `experiments/experiment_A/config.json`
- Generate mock splat files 
- Create test paths
- Output data to `generated/experiment_A/`

### Customizing Experiment Configuration

You can modify the experiment configuration before generating data. Edit `experiments/experiment_A/config.json`:

```json
{
    "grid": {
        "width": 100,    // Number of cells in x dimension
        "height": 100,   // Number of cells in y dimension
        "depth": 100,    // Number of cells in z dimension
        "cell_size": 10.0 // Size of each cell in units
    },
    "splat": {
        "min_size": 102400,   // Minimum splat size (100 KB)
        "max_size": 10485760  // Maximum splat size (10 MB)
    },
    "cache": {
        "l1_size": 1073741824,   // L1 cache size (1 GB)
        "l2_size": 10737418240   // L2 cache size (10 GB)
    },
    "network": {
        "l1_latency_ms": 10,
        "l2_latency_ms": 50,
        "origin_latency_ms": 500,
        "packet_loss_percent": 1.0
    },
    "metrics": {
        "min_cache_hit_rate": 0.99,
        "max_latency_ms": 500.0,
        "min_preload_success_rate": 0.95
    }
}
```

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

# Run specific test
pytest tests/test_generator.py
```

## Troubleshooting

- Ensure you have write permissions in the project directory
- Check that all dependencies are installed correctly
- Verify Python version compatibility

## Experiment Design Considerations

The generator supports two main test scenarios:
1. **Teleport Scenario**: Simulates moving between distant regions
2. **Spiral Scenario**: Tests cache performance during continuous movement

You can adjust the experiment configuration to test different:
- Grid sizes
- Splat sizes
- Network conditions
- Caching strategies

## Next Steps

1. Review generated data in `generated/experiment_A/`
2. Use the generated data with the mock CDN service
3. Analyze cache performance and preloading effectiveness

## Contributing

- Report issues on the project GitHub repository
- Submit pull requests with improvements
- Follow the existing code style and add appropriate tests
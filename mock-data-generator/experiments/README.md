# Experiment Configurations

This directory contains configuration files for different experimental scenarios in the Splat Content Delivery System.

## Configuration Structure

Each experiment configuration is a JSON file that defines:

### Grid Parameters
- `width`: Number of cells in x dimension
- `height`: Number of cells in y dimension
- `depth`: Number of cells in z dimension
- `cell_size`: Physical size of each grid cell SMALLER CELLS PRODUCE HIGHER EXPECTED SPLATS

### Splat Parameters
- `min_size`: Minimum size of generated splat files (bytes)
- `max_size`: Maximum size of generated splat files (bytes)

### Cache Configuration
- `l1_size`: Size of L1 (edge) cache in bytes
- `l2_size`: Size of L2 (regional) cache in bytes

### Network Simulation
- `l1_latency_ms`: Latency for L1 cache (milliseconds)
- `l2_latency_ms`: Latency for L2 cache (milliseconds)
- `origin_latency_ms`: Latency for origin (S3) retrieval
- `packet_loss_percent`: Simulated network packet loss

### Success Metrics
- `min_cache_hit_rate`: Minimum acceptable cache hit rate
- `max_latency_ms`: Maximum acceptable latency
- `min_preload_success_rate`: Minimum successful preloads

## Creating a New Experiment

1. Create a new directory with your experiment ID
2. Create a `config.json` file in that directory
3. Use the default configuration as a template
4. Modify parameters as needed for your specific test scenario

## Example

```json
{
    "grid": {
        "width": 100,
        "height": 100,
        "depth": 100,
        "cell_size": 10.0
    },
    "splat": {
        "min_size": 102400,
        "max_size": 10485760
    },
    "cache": {
        "l1_size": 1073741824,
        "l2_size": 10737418240
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

## Experiment Design Considerations

- Vary grid sizes to test different spatial distributions
- Adjust splat sizes to simulate different content types
- Modify network parameters to simulate various network conditions
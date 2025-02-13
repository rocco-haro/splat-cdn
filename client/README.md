client/
├── index.html          # Chart containers and script imports
├── style.css          # Basic layout
└── js/
    ├── config.js      # Static CDN configuration (environment, endpoints)
    ├── experiment.js  # Loads experiment settings from /experiment endpoint
    ├── metrics.js     # Handles collecting and storing performance metrics
    ├── charts.js      # Creates and updates charts (position, cache hits, latency)
    ├── path.js        # Handles path traversal and splat requests
    └── app.js         # Main initialization and test coordination


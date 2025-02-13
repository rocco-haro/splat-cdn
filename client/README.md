client/
├── index.html          # Chart containers and script imports
├── style.css          # Basic layout
└── js/
    ├── config.js      # Static CDN configuration (environment, endpoints)
    ├── experiment.js  # Loads experiment settings from /experiment endpoint
    ├── metrics.js     # Handles collecting and storing performance metrics
    ├── charts.js      # Creates and updates both charts (position and latency)
    ├── path.js        # Handles path traversal and splat requests
    └── app.js         # Main initialization and test coordination

Script loading order in index.html:
1. Chart.js (from CDN)
2. config.js (static configuration)
3. experiment.js
4. metrics.js
5. charts.js
6. path.js
7. app.js
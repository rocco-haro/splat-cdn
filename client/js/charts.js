class ChartManager {
    constructor() {
        this.pathChart = null;
        this.cacheChart = null;
        this.latencyChart = null;
        this.metricsData = {
            labels: [],
            cacheHits: {
                l1: [],
                l2: []
            },
            originHits: [],
            latencies: {
                l1: [],
                l2: [],
                origin: []
            }
        };
    }

    initialize() {
        this.initializePathChart();
        this.initializeCacheChart();
        this.initializeLatencyChart();
    }

    initializePathChart() {
        const ctx = document.getElementById('pathChart').getContext('2d');
        this.pathChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Path',
                    data: [],
                    showLine: true,
                    fill: false,
                    borderColor: '#2ecc71',
                    backgroundColor: '#2ecc71',
                    borderWidth: 2,
                    pointRadius: 4
                }, {
                    label: 'Current Position',
                    data: [],
                    backgroundColor: '#e74c3c',
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                plugins: {
                    title: {
                        display: true,
                        text: 'Path Visualization',
                        font: { size: 16 }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'X Position'
                        },
                        beginAtZero: true
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Z Position'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    initializeCacheChart() {
        const ctx = document.getElementById('cacheChart').getContext('2d');
        this.cacheChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'L1 Cache Hits',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    fill: true,
                    borderWidth: 2,
                    tension: 0.4
                }, {
                    label: 'L2 Cache Hits',
                    data: [],
                    borderColor: '#2ecc71',
                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    fill: true,
                    borderWidth: 2,
                    tension: 0.4
                }, {
                    label: 'Origin Hits',
                    data: [],
                    borderColor: '#f1c40f',
                    backgroundColor: 'rgba(241, 196, 15, 0.2)',
                    fill: true,
                    borderWidth: 2,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                plugins: {
                    title: {
                        display: true,
                        text: 'Cache Performance',
                        font: { size: 16 }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Time (s)'
                        },
                        beginAtZero: true
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Hit Count'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    initializeLatencyChart() {
        const ctx = document.getElementById('latencyChart').getContext('2d');
        this.latencyChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                labels: [],
                datasets: [{
                    label: 'L1 Cache Latency',
                    data: [],
                    borderColor: '#3498db',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
                }, {
                    label: 'L2 Cache Latency',
                    data: [],
                    borderColor: '#2ecc71',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
                }, {
                    label: 'Origin Latency',
                    data: [],
                    borderColor: '#e74c3c',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                plugins: {
                    title: {
                        display: true,
                        text: 'Request Latency by Cache Level',
                        font: { size: 16 }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Time (s)'
                        },
                        beginAtZero: true
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Latency (ms)'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updateMetrics(metrics, timestamp) {
        const timeInSeconds = (timestamp - window.metricsManager.metrics.experiment_start) / 1000;
        
        // Add new data points for cache hits
        this.metricsData.labels.push(timeInSeconds);
        this.metricsData.cacheHits.l1.push(metrics.l1_hits);
        this.metricsData.cacheHits.l2.push(metrics.l2_hits);
        this.metricsData.originHits.push(metrics.origin_hits);

        // Add latency data points only if they exist
        if (metrics.l1_latency !== null) {
            this.metricsData.latencies.l1.push({
                x: timeInSeconds,
                y: metrics.l1_latency
            });
        }
        if (metrics.l2_latency !== null) {
            this.metricsData.latencies.l2.push({
                x: timeInSeconds,
                y: metrics.l2_latency
            });
        }
        if (metrics.origin_latency !== null) {
            this.metricsData.latencies.origin.push({
                x: timeInSeconds,
                y: metrics.origin_latency
            });
        }

        // Update time range
        const maxTime = Math.max(...this.metricsData.labels);
        const xMin = Math.min(...this.metricsData.labels);
        const xMax = maxTime + (maxTime - xMin) * 0.1;

        // Update cache hit chart
        this.cacheChart.data.labels = this.metricsData.labels;
        this.cacheChart.data.datasets[0].data = this.metricsData.cacheHits.l1;
        this.cacheChart.data.datasets[1].data = this.metricsData.cacheHits.l2;
        this.cacheChart.data.datasets[2].data = this.metricsData.originHits;

        // Update cache chart scales
        const maxHits = Math.max(
            Math.max(...this.metricsData.cacheHits.l1, 0),
            Math.max(...this.metricsData.cacheHits.l2, 0),
            Math.max(...this.metricsData.originHits, 0)
        );
        this.cacheChart.options.scales.y.max = maxHits + Math.ceil(maxHits * 0.1);
        this.cacheChart.options.scales.x.min = xMin;
        this.cacheChart.options.scales.x.max = xMax;

        // Update latency chart with scatter data
        this.latencyChart.data.datasets[0].data = this.metricsData.latencies.l1;
        this.latencyChart.data.datasets[1].data = this.metricsData.latencies.l2;
        this.latencyChart.data.datasets[2].data = this.metricsData.latencies.origin;

        // Calculate max latency for scale
        const allLatencies = [
            ...this.metricsData.latencies.l1.map(p => p.y),
            ...this.metricsData.latencies.l2.map(p => p.y),
            ...this.metricsData.latencies.origin.map(p => p.y)
        ].filter(v => v !== null);

        if (allLatencies.length > 0) {
            const maxLatency = Math.max(...allLatencies);
            this.latencyChart.options.scales.y.suggestedMax = maxLatency * 1.1;
        }

        this.latencyChart.options.scales.x.min = xMin;
        this.latencyChart.options.scales.x.max = xMax;

        // Update charts
        this.cacheChart.update('none');
        this.latencyChart.update('none');
    }

    updatePath(points) {
        this.pathChart.data.datasets[0].data = points.map(p => ({
            x: p.position.x,
            y: p.position.z
        }));
        this.pathChart.update('none');
    }

    updateCurrentPosition(position) {
        this.pathChart.data.datasets[1].data = [{
            x: position.x,
            y: position.z
        }];
        this.pathChart.update('none');
    }

    reset() {
        this.metricsData = {
            labels: [],
            cacheHits: {
                l1: [],
                l2: []
            },
            originHits: [],
            latencies: {
                l1: [],
                l2: [],
                origin: []
            }
        };

        // Reset all charts
        this.pathChart.data.datasets.forEach(dataset => dataset.data = []);
        this.cacheChart.data.datasets.forEach(dataset => dataset.data = []);
        this.latencyChart.data.datasets.forEach(dataset => dataset.data = []);

        this.pathChart.update('none');
        this.cacheChart.update('none');
        this.latencyChart.update('none');
    }
}

// Create global instance
window.chartManager = new ChartManager();
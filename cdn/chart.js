// charts.js
class ChartManager {
    constructor() {
        this.pathChart = null;
        this.latencyChart = null;
        this.metricsData = {
            labels: [],
            cacheHits: [],
            originHits: [],
            latencies: []
        };
    }

    initialize() {
        this.initializePathChart();
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
                    borderColor: '#4CAF50',
                    backgroundColor: '#4CAF50',
                    pointRadius: 4
                }, {
                    label: 'Current Position',
                    data: [],
                    backgroundColor: '#FF5722',
                    pointRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0  // Disable animation for real-time updates
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Path Visualization'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const point = context.raw;
                                return `(${point.x.toFixed(2)}, ${point.z.toFixed(2)})`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'X Position'
                        }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Z Position'
                        }
                    }
                }
            }
        });
    }

    initializeLatencyChart() {
        const ctx = document.getElementById('latencyChart').getContext('2d');
        this.latencyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Cache Hits',
                    data: [],
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    fill: true,
                    yAxisID: 'y-hits'
                }, {
                    label: 'Origin Hits',
                    data: [],
                    borderColor: '#FF9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    fill: true,
                    yAxisID: 'y-hits'
                }, {
                    label: 'Latency (ms)',
                    data: [],
                    borderColor: '#F44336',
                    borderDash: [5, 5],
                    fill: false,
                    yAxisID: 'y-latency'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Cache Performance & Latency'
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Time (s)'
                        }
                    },
                    'y-hits': {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Hit Count'
                        },
                        min: 0
                    },
                    'y-latency': {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Latency (ms)'
                        },
                        min: 0,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    updatePath(points) {
        // Update full path
        this.pathChart.data.datasets[0].data = points.map(p => ({
            x: p.position.x,
            y: p.position.z  // Using z as y for 2D visualization
        }));
        this.pathChart.update('none');
    }

    updateCurrentPosition(position) {
        // Update current position marker
        this.pathChart.data.datasets[1].data = [{
            x: position.x,
            y: position.z  // Using z as y for 2D visualization
        }];
        this.pathChart.update('none');
    }

    updateMetrics(metrics, timestamp) {
        const timeInSeconds = timestamp / 1000;
        
        // Add new data points
        this.metricsData.labels.push(timeInSeconds);
        this.metricsData.cacheHits.push(metrics.l1_hits + metrics.l2_hits);
        this.metricsData.originHits.push(metrics.origin_hits);
        this.metricsData.latencies.push(metrics.average_latency);

        // Update chart data
        this.latencyChart.data.labels = this.metricsData.labels;
        this.latencyChart.data.datasets[0].data = this.metricsData.cacheHits;
        this.latencyChart.data.datasets[1].data = this.metricsData.originHits;
        this.latencyChart.data.datasets[2].data = this.metricsData.latencies;

        this.latencyChart.update('none');
    }

    reset() {
        // Clear all data
        this.metricsData = {
            labels: [],
            cacheHits: [],
            originHits: [],
            latencies: []
        };

        // Reset path chart
        this.pathChart.data.datasets[0].data = [];
        this.pathChart.data.datasets[1].data = [];
        this.pathChart.update('none');

        // Reset metrics chart
        this.latencyChart.data.labels = [];
        this.latencyChart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        this.latencyChart.update('none');
    }
}

// Create global instance
window.chartManager = new ChartManager();
// metrics.js
class MetricsManager {
    constructor() {
        this.metrics = {
            l1_hits: 0,
            l1_misses: 0,
            l2_hits: 0,
            l2_misses: 0,
            origin_hits: 0,
            total_requests: 0,
            total_latency: 0,
            current_latencies: {
                l1: null,
                l2: null,
                origin: null
            },
            historical_latencies: {
                l1: [],
                l2: [],
                origin: []
            },
            errors: 0,
            experiment_start: null,
            experiment_end: null,
            scenario_type: null,
            cdn_architecture: null
        };
        
        this.isRecording = false;
        this.onMetricsUpdate = null;
    }

    startRecording(scenario, architecture = 'single_tier') {
        console.log(`Starting metrics recording for ${scenario} scenario with ${architecture} architecture`);
        this.reset();
        this.metrics.experiment_start = performance.now();
        this.metrics.scenario_type = scenario;
        this.metrics.cdn_architecture = architecture;
        this.isRecording = true;
    }

    stopRecording() {
        if (!this.isRecording) return;
        
        this.metrics.experiment_end = performance.now();
        this.isRecording = false;
        console.log('Metrics recording stopped');
        return this.getResults();
    }

    reset() {
        this.metrics = {
            l1_hits: 0,
            l1_misses: 0,
            l2_hits: 0,
            l2_misses: 0,
            origin_hits: 0,
            total_requests: 0,
            total_latency: 0,
            current_latencies: {
                l1: null,
                l2: null,
                origin: null
            },
            historical_latencies: {
                l1: [],
                l2: [],
                origin: []
            },       
            errors: 0,
            experiment_start: null,
            experiment_end: null,
            scenario_type: null,
            cdn_architecture: null
        };
    }

    recordRequest(startTime, response) {
        if (!this.isRecording) return;

        const endTime = performance.now();
        const latency = endTime - startTime;

        this.metrics.total_requests++;
        
        if (response && response.cache_status) {
            switch (response.cache_status) {
                case 'l1_hit':
                    this.metrics.l1_hits++;
                    this.metrics.current_latencies.l1 = latency;
                    this.metrics.historical_latencies.l1.push(latency);
                    break;
                case 'l2_hit':
                    this.metrics.l2_hits++;
                    this.metrics.current_latencies.l2 = latency;
                    this.metrics.historical_latencies.l2.push(latency);
                    break;
                case 'origin_hit':
                    this.metrics.origin_hits++;
                    this.metrics.current_latencies.origin = latency;
                    this.metrics.historical_latencies.origin.push(latency);
                    break;
            }
        }

        if (this.onMetricsUpdate) {
            this.onMetricsUpdate(this.getCurrentMetrics());
        }
    }

    recordError() {
        if (!this.isRecording) return;
        this.metrics.errors++;
    }

    getCurrentMetrics() {
        const totalRequests = this.metrics.total_requests || 1;
        const totalHits = this.metrics.l1_hits + this.metrics.l2_hits;
        
        return {
            l1_hits: this.metrics.l1_hits,
            l2_hits: this.metrics.l2_hits,
            origin_hits: this.metrics.origin_hits,
            cache_hit_rate: (totalHits / totalRequests) * 100,
            // Return current (instantaneous) latencies
            l1_latency: this.metrics.current_latencies.l1,
            l2_latency: this.metrics.current_latencies.l2,
            origin_latency: this.metrics.current_latencies.origin,
            error_rate: (this.metrics.errors / totalRequests) * 100,
            total_requests: this.metrics.total_requests,
            current_duration: this.metrics.experiment_start ? 
                (performance.now() - this.metrics.experiment_start) / 1000 : 0
        };
    }

    getResults() {
        const duration = (this.metrics.experiment_end - this.metrics.experiment_start) / 1000;
        const totalRequests = this.metrics.total_requests || 1;
        const totalHits = this.metrics.l1_hits + this.metrics.l2_hits;

        const l1Stats = this.calculateLatencyStats(this.metrics.historical_latencies.l1);
        const l2Stats = this.calculateLatencyStats(this.metrics.historical_latencies.l2);
        const originStats = this.calculateLatencyStats(this.metrics.historical_latencies.origin);

        return {
            experiment_type: this.metrics.cdn_architecture,
            scenario: this.metrics.scenario_type,
            metrics: {
                l1_hits: this.metrics.l1_hits,
                l2_hits: this.metrics.l2_hits,
                origin_hits: this.metrics.origin_hits,
                cache_hit_rate: (totalHits / totalRequests) * 100,
                
                latency_stats: {
                    l1: l1Stats,
                    l2: l2Stats,
                    origin: originStats
                },
                
                error_rate: (this.metrics.errors / totalRequests) * 100,
                total_requests: this.metrics.total_requests,
                duration_seconds: duration,
                requests_per_second: totalRequests / duration
            }
        };
    }

    calculateLatencyStats(latencies) {
        if (!latencies || latencies.length === 0) {
            return {
                min: 0,
                max: 0,
                avg: 0,
                p50: 0,
                p90: 0,
                p99: 0
            };
        }

        const sorted = [...latencies].sort((a, b) => a - b);
        const sum = sorted.reduce((a, b) => a + b, 0);

        return {
            min: sorted[0],
            max: sorted[sorted.length - 1],
            avg: sum / sorted.length,
            p50: sorted[Math.floor(sorted.length * 0.5)],
            p90: sorted[Math.floor(sorted.length * 0.9)],
            p99: sorted[Math.floor(sorted.length * 0.99)]
        };
    }

    calculatePercentiles(latencies) {
        if (!latencies || latencies.length === 0) {
            return { p50: 0, p90: 0, p99: 0 };
        }

        const sorted = [...latencies].sort((a, b) => a - b);
        return {
            p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
            p90: sorted[Math.floor(sorted.length * 0.9)] || 0,
            p99: sorted[Math.floor(sorted.length * 0.99)] || 0
        };
    }

    calculateAverageLatency(latencies) {
        if (!latencies || latencies.length === 0) return 0;
        return latencies.reduce((sum, val) => sum + val, 0) / latencies.length;
    }

    async submitResults(experimentId) {
        if (!experimentId) {
            throw new Error('experimentId is required');
        }

        // TODO
        // const results = this.getResults();
        // const baseUrl = CONFIG.endpoints.services[CONFIG.environment];
        
        // try {
        //     const response = await fetch(`${baseUrl}/results/${experimentId}`, {
        //         method: 'POST',
        //         headers: {
        //             'Content-Type': 'application/json'
        //         },
        //         body: JSON.stringify(results)
        //     });

        //     if (!response.ok) {
        //         throw new Error(`Failed to submit results: ${response.statusText}`);
        //     }

        //     console.log('Results submitted successfully');
        //     return await response.json();
        // } catch (error) {
        //     console.error('Error submitting results:', error);
        //     throw error;
        // }
    }
    setMetricsUpdateCallback(callback) {
        this.onMetricsUpdate = callback;
    }
}

window.metricsManager = new MetricsManager();
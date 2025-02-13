// app.js
class App {
    constructor() {
        // Get DOM elements
        this.startButton = document.getElementById('startTest');
        this.exportButton = document.getElementById('exportData');
        this.scenarioSelect = document.getElementById('testScenario');
        this.cdnArchitectureSelect = document.getElementById('cdnArchitecture');
        this.currentPosElement = document.getElementById('currentPos');
        this.cacheHitsElement = document.getElementById('cacheHits');
        this.cacheMissesElement = document.getElementById('cacheMisses');
        this.avgLatencyElement = document.getElementById('avgLatency');

        // Bind event handlers
        this.startButton.addEventListener('click', () => this.startTest());
        this.exportButton.addEventListener('click', () => this.exportResults());
        this.scenarioSelect.addEventListener('change', () => this.handleScenarioChange());
        this.cdnArchitectureSelect.addEventListener('change', () => this.handleArchitectureChange());
        window.chartManager.initialize();
        // Initialize experiment
        this.init();
    }

    async init() {
        try {
            console.log('Initializing application...');
            
            // Load experiment data
            await window.experimentManager.loadExperiment();
            console.log('Experiment data loaded');

            // Set initial scenario and architecture
            this.handleScenarioChange();
            this.handleArchitectureChange();
            
            // Setup metrics update callback
            window.metricsManager.setMetricsUpdateCallback(this.updateMetricsDisplay.bind(this));
            
            // Enable controls
            this.startButton.disabled = false;
            this.scenarioSelect.disabled = false;
            this.cdnArchitectureSelect.disabled = false;

        } catch (error) {
            console.error('Error initializing application:', error);
            this.showError('Failed to initialize application. Check console for details.');
        }
    }

    handleScenarioChange() {
        const scenarioType = this.scenarioSelect.value;
        console.log('Changing scenario to:', scenarioType);
        
        try {
            // Set the scenario in experiment manager
            const scenario = window.experimentManager.setScenario(scenarioType);
            console.log('Scenario set:', scenario);

            // Reset path manager and metrics
            window.pathManager.reset();
            window.metricsManager.reset();
            window.chartManager.reset();

            // Initialize path manager with new path
            const path = window.experimentManager.getScenarioPath();
            window.pathManager.initialize(path, this.handlePositionUpdate.bind(this));
            window.chartManager.updatePath(path);

            console.log('Path manager initialized with new path');

        } catch (error) {
            console.error('Error changing scenario:', error);
            this.showError('Failed to change scenario. Check console for details.');
        }
    }

    handleArchitectureChange() {
        const architecture = this.cdnArchitectureSelect.value;
        console.log('Changing CDN architecture to:', architecture);
        
        try {
            // Set the architecture in experiment manager
            window.experimentManager.setCDNArchitecture(architecture);
            
            // Reset path manager and metrics since we're changing CDN configuration
            window.pathManager.reset();
            window.metricsManager.reset();
            
            console.log('CDN architecture changed to:', architecture);
        } catch (error) {
            console.error('Error changing CDN architecture:', error);
            this.showError('Failed to change CDN architecture. Check console for details.');
        }
    }

    startTest() {
        console.log('Starting test...');
        
        try {
            // Disable controls during test
            this.startButton.disabled = true;
            this.scenarioSelect.disabled = true;
            this.cdnArchitectureSelect.disabled = true;
            this.startButton.textContent = 'Running...';

            // Start path traversal
            window.pathManager.start();

            // Listen for completion
            const checkCompletion = setInterval(() => {
                if (!window.pathManager.isRunning) {
                    console.log('Test complete');
                    clearInterval(checkCompletion);
                    this.handleTestComplete();
                }
            }, 100);

        } catch (error) {
            console.error('Error starting test:', error);
            this.showError('Failed to start test. Check console for details.');
            this.resetControls();
        }
    }

    async handleTestComplete() {
        console.log('Handling test completion');
        
        try {
            // Get final metrics
            const results = window.metricsManager.getResults();
            console.log('Final test results:', results);

            // Submit results
            await window.metricsManager.submitResults('experiment_A');
            console.log('Results submitted successfully');
            
        } catch (error) {
            console.error('Error handling test completion:', error);
            this.showError('Failed to submit test results. Check console for details.');
        }
        
        // Reset controls
        this.resetControls();
        
        // Enable export if we have results
        this.exportButton.disabled = false;
    }

    resetControls() {
        this.startButton.disabled = false;
        this.scenarioSelect.disabled = false;
        this.cdnArchitectureSelect.disabled = false;
        this.startButton.textContent = 'Start Test';
    }

    handlePositionUpdate(position, expectedSplats) {
        // Update position display
        this.currentPosElement.textContent = 
            `(${position.x.toFixed(2)}, ${position.y.toFixed(2)}, ${position.z.toFixed(2)})`;
        
        window.chartManager.updateCurrentPosition(position);

        // console.log('Position update:', {
        //     position,
        //     expectedSplats
        // });
    }

    updateMetricsDisplay(metrics) {
        if (!metrics) return;

        try {
            // Update cache hits/misses display
            const totalHits = (metrics.l1_hits || 0) + (metrics.l2_hits || 0);
            const totalMisses = metrics.origin_hits || 0;
            
            this.cacheHitsElement.textContent = `${totalHits} (L1: ${metrics.l1_hits || 0}, L2: ${metrics.l2_hits || 0})`;
            this.cacheMissesElement.textContent = totalMisses;

            // Handle average latency display - only show if we have valid latency data
            let avgLatency = 0;
            let validLatencyCount = 0;
            
            if (metrics.l1_latency) {
                avgLatency += metrics.l1_latency * (metrics.l1_hits || 0);
                validLatencyCount += metrics.l1_hits || 0;
            }
            if (metrics.l2_latency) {
                avgLatency += metrics.l2_latency * (metrics.l2_hits || 0);
                validLatencyCount += metrics.l2_hits || 0;
            }
            if (metrics.origin_latency) {
                avgLatency += metrics.origin_latency * (metrics.origin_hits || 0);
                validLatencyCount += metrics.origin_hits || 0;
            }

            // Only update if we have valid latency data
            if (validLatencyCount > 0) {
                avgLatency = avgLatency / validLatencyCount;
                this.avgLatencyElement.textContent = avgLatency.toFixed(2) + 'ms';
            } else {
                this.avgLatencyElement.textContent = '0.00ms';
            }

            // Update charts
            window.chartManager.updateMetrics(metrics, performance.now());

        } catch (error) {
            console.error('Error updating metrics display:', error);
        }
    }

    async exportResults() {
        console.log('Exporting results...');
        
        try {
            const results = window.metricsManager.getResults();
            
            // Create JSON file
            const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            // Create download link
            const a = document.createElement('a');
            a.href = url;
            a.download = `test-results-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Error exporting results:', error);
            this.showError('Failed to export results. Check console for details.');
        }
    }

    showError(message) {
        // For now, just alert. Could be improved with a proper UI notification
        alert(message);
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
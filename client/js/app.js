// app.js
class App {
    constructor() {
        this.startButton = document.getElementById('startTest');
        this.exportButton = document.getElementById('exportData');
        this.scenarioSelect = document.getElementById('testScenario');
        this.cdnArchitectureSelect = document.getElementById('cdnArchitecture');
        this.currentPosElement = document.getElementById('currentPos');
        this.cacheHitsElement = document.getElementById('cacheHits');
        this.cacheMissesElement = document.getElementById('cacheMisses');
        this.avgLatencyElement = document.getElementById('avgLatency');

        this.startButton.addEventListener('click', () => this.startTest());
        this.exportButton.addEventListener('click', () => this.exportResults());
        this.scenarioSelect.addEventListener('change', () => this.handleScenarioChange());
        this.cdnArchitectureSelect.addEventListener('change', () => this.handleArchitectureChange());
        window.chartManager.initialize();
        this.init();
    }

    async init() {
        try {
            console.log('Initializing application...');
            
            await window.experimentManager.loadExperiment();

            this.handleScenarioChange();
            this.handleArchitectureChange();
            
            window.metricsManager.setMetricsUpdateCallback(this.updateMetricsDisplay.bind(this));
            
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
            const scenario = window.experimentManager.setScenario(scenarioType);
            console.log('Scenario set:', scenario);

            window.pathManager.reset();
            window.metricsManager.reset();
            window.chartManager.reset();

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
            window.experimentManager.setCDNArchitecture(architecture);
            
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
            this.startButton.disabled = true;
            this.scenarioSelect.disabled = true;
            this.cdnArchitectureSelect.disabled = true;
            this.startButton.textContent = 'Running...';

            window.pathManager.start();

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
            const results = window.metricsManager.getResults();
            console.log('Final test results:', results);

            await window.metricsManager.submitResults('experiment_A');
            console.log('Results submitted successfully');
            
        } catch (error) {
            console.error('Error handling test completion:', error);
            this.showError('Failed to submit test results. Check console for details.');
        }
        
        this.resetControls();
        
        this.exportButton.disabled = false;
    }

    resetControls() {
        this.startButton.disabled = false;
        this.scenarioSelect.disabled = false;
        this.cdnArchitectureSelect.disabled = false;
        this.startButton.textContent = 'Start Test';
    }

    handlePositionUpdate(position, expectedSplats) {
        this.currentPosElement.textContent = 
            `(${position.x.toFixed(2)}, ${position.y.toFixed(2)}, ${position.z.toFixed(2)})`;
        
        window.chartManager.updateCurrentPosition(position);
    }

    updateMetricsDisplay(metrics) {
        if (!metrics) return;

        try {
            const totalHits = (metrics.l1_hits || 0) + (metrics.l2_hits || 0);
            const totalMisses = metrics.origin_hits || 0;
            
            this.cacheHitsElement.textContent = `${totalHits} (L1: ${metrics.l1_hits || 0}, L2: ${metrics.l2_hits || 0})`;
            this.cacheMissesElement.textContent = totalMisses;

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

            if (validLatencyCount > 0) {
                avgLatency = avgLatency / validLatencyCount;
                this.avgLatencyElement.textContent = avgLatency.toFixed(2) + 'ms';
            } else {
                this.avgLatencyElement.textContent = '0.00ms';
            }

            window.chartManager.updateMetrics(metrics, performance.now());

        } catch (error) {
            console.error('Error updating metrics display:', error);
        }
    }

    async exportResults() {
        console.log('Exporting results...');
        
        try {
            const results = window.metricsManager.getResults();
            
            const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
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
        alert(message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
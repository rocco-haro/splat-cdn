// experiment.js

class ExperimentManager {
    constructor() {
        this.experimentData = null;
        this.currentScenario = null;
        this.cdnArchitecture = 'single-tier';
    }

    async loadExperiment(experimentId = 'experiment_A') {
        console.log('CDN_CONFIG:', CONFIG);
        console.log('Using environment:', CONFIG.environment);
        console.log('Using services endpoint:', CONFIG.endpoints.services[CONFIG.environment]);
        
        try {
            const baseUrl = CONFIG.endpoints.services[CONFIG.environment]

            const experimentUrl = `${baseUrl}/experiment/${experimentId}`;

            const response = await fetch(experimentUrl);
            if (!response.ok) {
                throw new Error(`Failed to load experiment: ${response.statusText}`);
            }
            
            this.experimentData = await response.json();
            console.log('Loaded experiment data:', this.experimentData);
            return this.experimentData;
        } catch (error) {
            console.error('Error loading experiment:', error);
            throw error;
        }
    }

    setCDNArchitecture(architecture) {
        if (!['single-tier', 'two-tier'].includes(architecture)) {
            throw new Error(`Invalid CDN architecture: ${architecture}`);
        }
        this.cdnArchitecture = architecture;
        console.log(`CDN architecture set to: ${architecture}`);
    }

    setScenario(scenarioType) {
        if (!this.experimentData) {
            throw new Error('No experiment data loaded');
        }
        
        if (!this.experimentData.scenarios[scenarioType]) {
            throw new Error(`Invalid scenario type: ${scenarioType}`);
        }

        this.currentScenario = scenarioType;
        return this.experimentData.scenarios[scenarioType];
    }

    getScenarioPath() {
        if (!this.currentScenario || !this.experimentData) {
            throw new Error('No scenario selected or experiment data not loaded');
        }
        return this.experimentData.scenarios[this.currentScenario].points;
    }

    getCDNEndpoint() {
        if (!this.experimentData) {
            throw new Error('No experiment data loaded');
        }

        const environment = CONFIG.environment;
        return CONFIG.endpoints["cdn"][environment][this.cdnArchitecture];
    }
}

// Create global instance
window.experimentManager = new ExperimentManager();
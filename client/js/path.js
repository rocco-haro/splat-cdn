// path.js
class PathManager {
    constructor() {
        this.currentPath = null;
        this.currentPointIndex = 0;
        this.isRunning = false;
        this.lastTimestamp = null;
        this.animationFrameId = null;
        this.onPositionUpdate = null;
        this.requestedSplats = new Set();
    }

    initialize(path, onPositionUpdate) {
        console.log('Initializing PathManager with path:', path);
        this.currentPath = path;
        this.currentPointIndex = 0;
        this.onPositionUpdate = onPositionUpdate;
        this.lastTimestamp = null;
        this.isRunning = false;
    }

    start() {
        if (!this.currentPath) {
            console.error('No path loaded');
            return;
        }

        console.log('Starting path traversal');
        this.isRunning = true;
        this.lastTimestamp = null;
        
        if (window.metricsManager) {
            const architecture = window.experimentManager.getCDNEndpoint().includes('two-tier') ? 
                'two_tier' : 'single_tier';
            window.metricsManager.startRecording(
                window.experimentManager.currentScenario,
                architecture
            );
        }
        
        this.animationLoop(performance.now());
    }

    stop() {
        console.log('Stopping path traversal');
        this.isRunning = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        
        if (window.metricsManager) {
            const results = window.metricsManager.stopRecording();
            console.log('Final metrics:', results);
        }
    }

    reset() {
        console.log('Resetting path traversal');
        this.currentPointIndex = 0;
        this.lastTimestamp = null;
        this.requestedSplats.clear();
        this.stop();
    }

    animationLoop(timestamp) {
        if (!this.isRunning) return;

        if (!this.lastTimestamp) {
            this.lastTimestamp = timestamp;
        }

        const currentTime = (timestamp - this.lastTimestamp) / 1000;
        
        while (this.currentPointIndex < this.currentPath.length) {
            const point = this.currentPath[this.currentPointIndex];
            
            if (point.timestamp > currentTime) {
                break;
            }

            this.requestSplats(point.expected_splats);
            
            if (this.onPositionUpdate) {
                this.onPositionUpdate(point.position, point.expected_splats);
            }

            this.currentPointIndex++;
        }

        // Check if we've completed the path
        if (this.currentPointIndex >= this.currentPath.length) {
            console.log('Path traversal complete');
            this.stop();
            return;
        }

        // Continue the animation loop
        this.animationFrameId = requestAnimationFrame(this.animationLoop.bind(this));
    }

    async requestSplats(splatIds) {
        if (!splatIds || !splatIds.length) return;

        const newSplats = splatIds.filter(id => !this.requestedSplats.has(id));
        if (newSplats.length === 0) return;

        const cdnEndpoint = window.experimentManager.getCDNEndpoint();
        console.log(`Requesting ${newSplats.length} new splats from ${cdnEndpoint}`);
        
        const requests = newSplats.map(async (splatId) => {
            try {
                console.log(`Requesting splat: ${splatId}`);
                this.requestedSplats.add(splatId);
                
                const startTime = performance.now();

                const response = await fetch(`${cdnEndpoint}/content/${splatId}`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch splat ${splatId}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // Single metrics recording with all necessary data
                if (window.metricsManager) {
                    window.metricsManager.recordRequest(startTime, data);
                }
                
                return data;
            } catch (error) {
                this.requestedSplats.delete(splatId);
                
                if (window.metricsManager) {
                    window.metricsManager.recordError();
                }
                
                console.error(`Error fetching splat ${splatId}:`, error);
                throw error;
            }
        });

        try {
            await Promise.all(requests);
        } catch (error) {
            console.error('Error fetching splats:', error);
        }
    }
}

window.pathManager = new PathManager();
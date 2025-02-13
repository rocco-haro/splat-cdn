// path.js
class PathManager {
    constructor() {
        this.currentPath = null;
        this.currentPointIndex = 0;
        this.isRunning = false;
        this.lastTimestamp = null;
        this.animationFrameId = null;
        this.onPositionUpdate = null;  // Callback for position updates
        this.requestedSplats = new Set();
        this.protocolVersion = null; // Track the protocol version being used
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
        
        // Start metrics recording
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
        
        // Stop metrics recording
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

        // Convert to seconds to match the path timestamps
        const currentTime = (timestamp - this.lastTimestamp) / 1000;
        
        // Find the appropriate point in the path based on time
        while (this.currentPointIndex < this.currentPath.length) {
            const point = this.currentPath[this.currentPointIndex];
            
            if (point.timestamp > currentTime) {
                break;
            }

            // We've reached or passed this point's timestamp
           // console.log(`Reached point ${this.currentPointIndex} at time ${currentTime}s:`, point);
            
            // Request splats for this position
            this.requestSplats(point.expected_splats);
            
            // Update position
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
                
                // Create observer to capture protocol information
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach(entry => {
                        this.protocolVersion = entry.nextHopProtocol;
                        console.log(`Request to ${entry.name} used protocol: ${this.protocolVersion}`);
                    });
                });
                
                observer.observe({ entryTypes: ['resource'] });

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

    // New method to get current protocol version
    getProtocolVersion() {
        return this.protocolVersion;
    }

}

// Create global instance
window.pathManager = new PathManager();
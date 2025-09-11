// const insConfigs = {};

class TrajectoryMonitor {
    constructor() {
        this.updateInterval = 1000; // 1 seconde
        this.isRunning = false;
        this.map = null;

        this.insConfigs = new Map();
        this.trajectories = {};
        this.currentMarkers = {};

        this.init();
    }

    init() {

        this.map = L.map('map', {center: [48.9100065, 2.1662488], zoom: 17, zoomControl: true});
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);

        if (typeof window.INS_CONFIGS !== 'undefined') {
            const insIds = Object.keys(window.INS_CONFIGS);
            
            insIds.forEach((insId) => {
                const config = window.INS_CONFIGS[insId];
            
                // Stocker la configuration
                this.insConfigs[insId] = {
                    name: config.name,
                    color: config.color,
                    visible: true
                };
            
                // Créer la trajectoire pour cet INS
                const trajectory = L.polyline([], {
                    color: config.color,
                    weight: 3,
                    opacity: 0.8,
                    smoothFactor: 1
                }).addTo(this.map);
            
                // Créer un marqueur pour la position actuelle
                const currentMarker = L.marker([48.9100065, 2.1662488], {
                    icon: L.divIcon({
                        className: 'current-position-marker',
                        html: '<div style="background-color: ' + config.color + '; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    })
                });
            
                // Initialement masquer les marqueurs (seront affichés quand on aura des données)
                currentMarker.setOpacity(0);
            
                // Stocker les références
                this.trajectories[insId] = trajectory;
                this.currentMarkers[insId] = currentMarker;
            
                // Données de trajectoire
                trajectory.points = [];
                trajectory.insId = insId;
            });
        }

        this.startMonitoring();
    }

    startMonitoring() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.fetchData();
        this.intervalId = setInterval(() => this.fetchData(), this.updateInterval);
    }

    stopMonitoring() {
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }

    async fetchData() {
        try {
            const response = await fetch('/api/positions');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.updateDisplay(data);

        } catch (error) {
            console.error('Error on fetching positions:', error);
        }
    }

    updateDisplay(positions) {
        const insIds = Object.keys(positions);
        insIds.forEach((insId) => {
            if (insId in this.trajectories && positions[insId].length > 0) {
                this.trajectories[insId].setLatLngs(positions[insId]);
                this.currentMarkers[insId].setLatLng(positions[insId][0]);
                this.currentMarkers[insId].setOpacity(1);
                this.currentMarkers[insId].addTo(this.map);
            }
        });
    }

}

// Initialisation de la carte globale après le chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    window.trajectoryMonitor = new TrajectoryMonitor();
});

class INSMonitor {
    constructor() {
        this.updateInterval = 1000; // 1 seconde
        this.isRunning = false;
        this.init();
    }

    init() {
        this.startMonitoring();
        console.log('Surveillance INS initialisée');
    }

    startMonitoring() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.fetchData();
        this.intervalId = setInterval(() => this.fetchData(), this.updateInterval);

        this.updateSystemStatus('En cours d\'exécution', true);
    }

    stopMonitoring() {
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        this.updateSystemStatus('Arrêté', false);
    }

    async fetchData() {
        try {
            const response = await fetch('/api/data');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.updateDisplay(data);

        } catch (error) {
            console.error('Erreur lors de la récupération des données:', error);
            this.updateSystemStatus('Erreur de connexion', false);
        }
    }

    updateDisplay(allData) {
        Object.entries(allData).forEach(([insId, data]) => {
            this.updateINSCard(insId, data.data);

            // Timestamp
            this.updateElement(`timestamp-${insId}`, `Dernière mise à jour : ${data.timestamp}`);
        });

        // Mise à jour du statut système
        const onlineCount = Object.values(allData).filter(data => data.data.online).length;
        const totalCount = Object.keys(allData).length;
        this.updateSystemStatus(`${onlineCount}/${totalCount} INS en ligne`, onlineCount > 0);
    }

    updateINSCard(insId, data) {
        // Statut en ligne
        const statusIndicator = document.getElementById(`status-${insId}`);
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${data.online ? 'status-online' : 'status-offline'}`;
        }

        // Message d'erreur
        const errorElement = document.getElementById(`error-${insId}`);
        if (errorElement) {
            if (data.error_message && !data.online) {
                errorElement.textContent = `Erreur: ${data.error_message}`;
                errorElement.style.display = 'block';
            } else {
                errorElement.style.display = 'none';
            }
        }

        if (!data.online) { return; }

        // UTC Clock
        this.updateUTCStatus(insId, data.status.utc, data.ins_measurement.dateTime);

        // DataLogger
        this.updateDataLogger(insId, data.datalogger);

        // Position GNSS avec std dev
        this.updateGNSSMeasurements(insId, 1, data.gnss1_measurement);
        this.updateGNSSMeasurements(insId, 2, data.gnss2_measurement);

        // Position EKF avec std dev
        this.updateEkfMeasurements(insId, data.ins_measurement.ekf, data.status.ins.type);

        // Solution INS
        this.updateInsSolution(insId, data.status);
    }

    updateUTCStatus(insId, utc, insDateTime) {
        const validElement = document.getElementById(`utc-valid-${insId}`);
        if (validElement) {
            validElement.textContent = utc.utcStatus;
            validElement.className = `status-info-value status-info-utc-${utc.utcStatus}`;
        }
        const clockElement = document.getElementById(`utc-clock-${insId}`);
        if (clockElement) {
            clockElement.textContent = utc.clockStatus;
            clockElement.className = `status-info-value status-info-clock-${utc.clockStatus}`;
        }

        this.updateElement(`utc-date-${insId}`, insDateTime);
    }

    updateDataLogger(insId, dataLogger) {
        const statusElement = document.getElementById(`datalogger-status-${insId}`);
        if (statusElement) {
            statusElement.textContent = dataLogger.status;
            statusElement.className = `status-info-value status-info-dlstatus-${dataLogger.status}`;
        }
        const modeElement = document.getElementById(`datalogger-mode-${insId}`);
        if (modeElement) {
            modeElement.textContent = dataLogger.mode;
            modeElement.className = `status-info-value status-info-dlmode-${dataLogger.mode}`;
        }

        const spaceRatio = 100. * dataLogger.usedSpace / dataLogger.totalSpace;
        this.updateElement(`datalogger-space-${insId}`, `${dataLogger.usedSpace} / ${dataLogger.totalSpace} (${spaceRatio} %)`);
    }

    updateGNSSMeasurements(insId, gnssId, gnssMeasurements) {

        const gnssSectionElement = document.getElementById(`gnss${gnssId}-section-${insId}`);
        if (gnssSectionElement) {
            gnssSectionElement.hidden = gnssMeasurements.status === 'disabled';
        }

        const statusElement = document.getElementById(`gnss${gnssId}-status-${insId}`);
        if (statusElement) {
            statusElement.textContent = gnssMeasurements.status
            statusElement.className = `gnss-status-${gnssMeasurements.status}`
        }

        if (gnssMeasurements.status === 'enabled') {

            const pvtStatusElement = document.getElementById(`gnss${gnssId}-pvt-status-${insId}`);
            if (pvtStatusElement) {
                switch (gnssMeasurements.pvt.status) {
                    case 'error':
                    case 'exportRestrictions':
                        pvtStatusElement.className = `solution-type solution-error`;
                        break;

                    case 'noSolution':
                    case 'static':
                        pvtStatusElement.className = `solution-type solution-degraded`;
                        break;

                    case 'single':
                    case 'differential':
                    case 'rtkFloat':
                    case 'pppFloat':
                        pvtStatusElement.className = `solution-type solution-good`;
                        break;

                    case 'sbas':
                    case 'rtkFixed':
                    case 'pppFixed':
                        pvtStatusElement.className = `solution-type solution-best`;
                        break;

                    default:
                        pvtStatusElement.className = `solution-type solution-unknown`;
                        break;
                }
                pvtStatusElement.textContent = gnssMeasurements.pvt.status;
            }

            this.updateElement(`gnss${gnssId}-lat-${insId}`, this.formatCoordinate(gnssMeasurements.pvt.latitude));
            this.updateElement(`gnss${gnssId}-lon-${insId}`, this.formatCoordinate(gnssMeasurements.pvt.longitude));
            this.updateElement(`gnss${gnssId}-alt-${insId}`, this.formatNumber(gnssMeasurements.pvt.height, 1));

            this.updateElement(`gnss${gnssId}-lat-std-${insId}`, `± ${this.formatNumber(gnssMeasurements.pvt.latitudeStd, 3, 'm')}`);
            this.updateElement(`gnss${gnssId}-lon-std-${insId}`, `± ${this.formatNumber(gnssMeasurements.pvt.longitudeStd, 3, 'm')}`);
            this.updateElement(`gnss${gnssId}-alt-std-${insId}`, `± ${this.formatNumber(gnssMeasurements.pvt.heightStd, 3, 'm')}`);

            const spoofingElement = document.getElementById(`gnss${gnssId}-spoofing-${insId}`);
            if (spoofingElement) {
                spoofingElement.textContent = `🛡️ Spoofing: ${gnssMeasurements.pvt.spoofing}`;
            }

            const interferenceElement = document.getElementById(`gnss${gnssId}-interference-${insId}`);
            if (interferenceElement) {
                interferenceElement.textContent = `📡 Interference: ${gnssMeasurements.pvt.interference}`;
            }

            const osnmaElement = document.getElementById(`gnss${gnssId}-osnma-${insId}`);
            if (osnmaElement) {
                osnmaElement.textContent = `🔒 OSNMA: ${gnssMeasurements.pvt.osnma}`;
            }

            const numSvElement = document.getElementById(`gnss${gnssId}-num-sv-${insId}`);
            if (numSvElement) {
                numSvElement.textContent = `🛰 SV: ${gnssMeasurements.pvt.numSvUsed} / ${gnssMeasurements.pvt.numSvTracked}`;
            }

            this.updateGNSSSignals(insId, gnssId, gnssMeasurements.pvt.signals);
        }
    }

    updateGNSSSignals(insId, gnssId, signals) {
        if (signals && Object.keys(signals).length > 0) {
            Object.entries(signals).forEach(([constName, constUsed]) => {
                const element = document.getElementById(`gnss${gnssId}-${constName}-${insId}`);
                if (element) {
                    element.className = constUsed ? `freq-available` : `freq-unavailable`;
                }
            });
        }
    }

    updateEkfMeasurements(insId, ekf, insSolutionType) {

        const ekfSolutionElement = document.getElementById(`ekf-ins-solution-type-${insId}`);
        if (ekfSolutionElement) {
            switch (insSolutionType) {
                case 'invalid':
                    ekfSolutionElement.className = `solution-type solution-error`;
                    break;

                case 'vg':
                case 'inertial':
                case 'velConst':
                case 'odometer':
                case 'airData':
                case 'dvl':
                case 'gnssVel':
                case 'gnssUnknown':
                    ekfSolutionElement.className = `solution-type solution-degraded`;
                    break;

                case 'singlePoint':
                case 'dgps':
                case 'sbas':
                case 'rtkFloat':
                case 'pppFloat':
                    ekfSolutionElement.className = `solution-type solution-good`;
                    break;

                case 'rtkFixed':
                case 'pppFixed':
                    ekfSolutionElement.className = `solution-type solution-best`;
                    break;

                default:
                    ekfSolutionElement.className = `solution-type solution-unknown`;
                    break;
            }
            ekfSolutionElement.textContent = insSolutionType;
        }

        this.updateElement(`ekf-lat-${insId}`, this.formatCoordinate(ekf?.latitude));
        this.updateElement(`ekf-lon-${insId}`, this.formatCoordinate(ekf?.longitude));
        this.updateElement(`ekf-alt-${insId}`, this.formatNumber(ekf?.altitude, 1));

        this.updateElement(`ekf-lat-std-${insId}`, `± ${this.formatNumber(ekf?.posStd[0], 3, 'm')}`);
        this.updateElement(`ekf-lon-std-${insId}`, `± ${this.formatNumber(ekf?.posStd[1], 3, 'm')}`);
        this.updateElement(`ekf-alt-std-${insId}`, `± ${this.formatNumber(ekf?.posStd[2], 3, 'm')}`);
    }

    updateInsSolution(insId, status) {
        if (status.ins && Object.keys(status.ins).length > 0) {
            Object.entries(status.ins).forEach(([constName, constUsed]) => {
                const element = document.getElementById(`ekf-solution-${constName}-${insId}`);
                if (element) {
                    element.textContent = constUsed ? '✓' : '✗';
                    element.className = `ekf-status-icon ${constUsed ? 'ekf-status-ok' : 'ekf-status-ko'}`;
                }

                if (constName.includes('gnss1')) {
                    const itemElement = document.getElementById(`ekf-solution-item-${constName}-${insId}`);
                    if (itemElement) {
                        itemElement.style.display = status.aiding.gnss1.enabled ? 'flex' : 'none';
                    }
                }

                if (constName.includes('gnss2')) {
                    const itemElement = document.getElementById(`ekf-solution-item-${constName}-${insId}`);
                    if (itemElement) {
                        itemElement.style.display = status.aiding.gnss2.enabled ? 'flex' : 'none';
                    }
                }
            });
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value || '--';
        }
    }

    updateSystemStatus(text, isOnline) {
        const statusElement = document.getElementById('statusText');
        if (statusElement) {
            statusElement.textContent = text;
            statusElement.style.color = isOnline ? '#4CAF50' : '#f44336';
        }
    }

    formatCoordinate(value) {
        return value !== undefined ? value.toFixed(6) + '°' : '--';
    }

    formatAngle(value) {
        return value !== undefined ? value.toFixed(1) + '°' : '--';
    }

    formatNumber(value, decimals = 2, unit = '') {
        if (value === undefined || value === null) return '--';
        return value.toFixed(decimals) + (unit ? ' ' + unit : '');
    }
}

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', () => {
    window.insMonitor = new INSMonitor();
});

// Gestion des erreurs globales
window.addEventListener('error', (e) => {
    console.error('Erreur JavaScript:', e.error);
});

// Gestion de la visibilité de la page
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Page cachée - surveillance suspendue');
    } else {
        console.log('Page visible - surveillance reprise');
        if (window.insMonitor) {
            window.insMonitor.fetchData();
        }
    }
});
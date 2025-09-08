#!/usr/bin/env python3
"""
Application Flask pour la surveillance des systèmes INS SBG Systems
Surveille position, attitude et statut GNSS en temps réel
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, render_template, jsonify
import requests
import serial
from contextlib import contextmanager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class INSConfig:
    """Configuration d'un système INS"""
    id: str
    name: str
    connection_type: str  # 'ethernet' ou 'serial'
    ip_address: Optional[str] = None
    port: int = 80
    serial_port: Optional[str] = None
    serial_baudrate: int = 115200
    timeout: float = 5.0

@dataclass
class INSData:
    """Données de statut d'un système INS"""
    ins_id: str
    timestamp: str
    online: bool
    position: Dict[str, float]
    attitude: Dict[str, float]
    gnss_status: Dict[str, Any]
    error_message: Optional[str] = None

class INSClient:
    """Client pour communiquer avec un système INS"""
    
    def __init__(self, config: INSConfig):
        self.config = config
        self.base_url = self._build_base_url()
    
    def _build_base_url(self) -> str:
        """Construit l'URL de base selon le type de connexion"""
        if self.config.connection_type == 'ethernet':
            return f"http://{self.config.ip_address}:{self.config.port}"
        elif self.config.connection_type == 'serial':
            # Pour connexion série, on utilise localhost avec un proxy
            return "http://localhost:8080"  # Port proxy pour série
        else:
            raise ValueError(f"Type de connexion non supporté: {self.config.connection_type}")
    
    def fetch_status(self) -> INSData:
        """Récupère les données de statut du système INS"""
        try:
            if self.config.connection_type == 'ethernet':
                return self._fetch_ethernet_status()
            elif self.config.connection_type == 'serial':
                return self._fetch_serial_status()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut pour {self.config.id}: {e}")
            return INSData(
                ins_id=self.config.id,
                timestamp=datetime.now().isoformat(),
                online=False,
                position={},
                attitude={},
                gnss_status={},
                error_message=str(e)
            )
    
    def _fetch_ethernet_status(self) -> INSData:
        """Récupère le statut via connexion Ethernet"""
        url = f"{self.base_url}/api/v1/data"
        headers = {'Accept': 'application/json'}
        
        response = requests.get(
            url, 
            headers=headers, 
            timeout=self.config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        return self._parse_api_response(data)
    
    def _fetch_serial_status(self) -> INSData:
        """Récupère le statut via connexion série"""
        # Implémentation simplifiée pour la connexion série
        # En réalité, vous pourriez avoir besoin d'un protocole série spécifique
        with self._serial_connection() as ser:
            # Envoie une commande pour obtenir les infos
            ser.write(b'GET_INFO\n')
            response = ser.readline().decode('utf-8').strip()
            data = json.loads(response)
            return self._parse_api_response(data)
    
    @contextmanager
    def _serial_connection(self):
        """Gestionnaire de contexte pour connexion série"""
        ser = None
        try:
            ser = serial.Serial(
                self.config.serial_port,
                self.config.serial_baudrate,
                timeout=self.config.timeout
            )
            yield ser
        finally:
            if ser and ser.is_open:
                ser.close()
    
    def _parse_api_response(self, data: Dict) -> INSData:
        """Parse la réponse de l'API et extrait les informations pertinentes"""
        # Extraction de la position
        position = {}
        if 'ekf' in data:
            ekf_data = data['ekf']
            position = {
                'latitude': ekf_data.get('latitude', 0.0),
                'longitude': ekf_data.get('longitude', 0.0),
                'altitude': ekf_data.get('altitude', 0.0)
            }
        
        # Extraction de l'attitude
        attitude = {}
        if 'attitude' in data:
            att_data = data['attitude']
            attitude = {
                'roll': att_data.get('roll', 0.0),
                'pitch': att_data.get('pitch', 0.0),
                'yaw': att_data.get('yaw', 0.0)
            }
        
        # Extraction du statut GNSS
        gnss_status = {}
        if 'gnss' in data:
            gnss_data = data['gnss']
            gnss_status = {
                'fix_type': gnss_data.get('fixType', 'NO_FIX'),
                'num_satellites': gnss_data.get('numSatellites', 0),
                'hdop': gnss_data.get('hdop', 0.0),
                'signal_quality': gnss_data.get('signalQuality', 'UNKNOWN')
            }
        
        return INSData(
            ins_id=self.config.id,
            timestamp=datetime.now().isoformat(),
            online=True,
            position=position,
            attitude=attitude,
            gnss_status=gnss_status
        )

class INSMonitor:
    """Moniteur principal pour tous les systèmes INS"""
    
    def __init__(self, configs: List[INSConfig], update_interval: float = 1.0):
        self.configs = configs
        self.update_interval = update_interval
        self.clients = {config.id: INSClient(config) for config in configs}
        self.latest_data: Dict[str, INSData] = {}
        self.running = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Démarre la surveillance en arrière-plan"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Surveillance démarrée")
    
    def stop_monitoring(self):
        """Arrête la surveillance"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Surveillance arrêtée")
    
    def _monitor_loop(self):
        """Boucle principale de surveillance"""
        while self.running:
            start_time = time.time()
            
            # Mise à jour des données pour tous les INS
            for ins_id, client in self.clients.items():
                try:
                    data = client.fetch_status()
                    self.latest_data[ins_id] = data
                    logger.debug(f"Données mises à jour pour {ins_id}")
                except Exception as e:
                    logger.error(f"Erreur lors de la mise à jour de {ins_id}: {e}")
            
            # Attente pour respecter l'intervalle de mise à jour
            elapsed = time.time() - start_time
            sleep_time = max(0, self.update_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def get_all_data(self) -> Dict[str, Dict]:
        """Retourne toutes les dernières données"""
        return {ins_id: asdict(data) for ins_id, data in self.latest_data.items()}
    
    def get_ins_data(self, ins_id: str) -> Optional[Dict]:
        """Retourne les données d'un INS spécifique"""
        if ins_id in self.latest_data:
            return asdict(self.latest_data[ins_id])
        return None

# Configuration des systèmes INS
INS_CONFIGS = []
with open('config.json', 'r') as f:
    configs_json_data = json.load(f)
    for config_json_data in configs_json_data:
        INS_CONFIGS.append(INSConfig(
                    id=config_json_data["id"], 
                    name=config_json_data["name"],
                    connection_type=config_json_data["connection_type"],
                    ip_address=config_json_data["ip_address"]
                    ))


# Création de l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Initialisation du moniteur
monitor = INSMonitor(INS_CONFIGS, update_interval=1.0)

@app.route('/')
def index():
    """Page principale de l'application"""
    return render_template('index.html', ins_configs=INS_CONFIGS)

@app.route('/api/data')
def get_all_data():
    """API pour récupérer toutes les données INS"""
    return jsonify(monitor.get_all_data())

@app.route('/api/data/<ins_id>')
def get_ins_data(ins_id):
    """API pour récupérer les données d'un INS spécifique"""
    data = monitor.get_ins_data(ins_id)
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'INS non trouvé'}), 404

@app.route('/api/status')
def get_system_status():
    """API pour récupérer le statut du système"""
    return jsonify({
        'monitoring': monitor.running,
        'ins_count': len(INS_CONFIGS),
        'last_update': datetime.now().isoformat()
    })

if __name__ == '__main__':
    try:
        monitor.start_monitoring()
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        monitor.stop_monitoring()
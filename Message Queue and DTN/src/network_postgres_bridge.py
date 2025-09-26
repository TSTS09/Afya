#!/usr/bin/env python3
import psycopg2
import subprocess
import re
import platform
import time
import json

class NetworkPostgresBridge:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.channel_id = None
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        self.connection = psycopg2.connect(**self.db_config)
        
    def get_channel_id(self, pid=None):
        """Get channel_id for current process"""
        if not pid:
            pid = subprocess.os.getpid()
        
        with self.connection.cursor() as cur:
            cur.execute(
                "SELECT channel_id FROM mq.channel WHERE channel_name = %s",
                (str(pid),)
            )
            result = cur.fetchone()
            if result:
                self.channel_id = result[0]
                return self.channel_id
        return None
    
    def detect_network(self):
        """Detect current network status"""
        system = platform.system().lower()
        
        try:
            if system == "windows":
                p = subprocess.Popen(
                    "netsh wlan show interfaces",
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                out = p.stdout.read().decode('utf-8').strip()
                signal_match = re.search(r'Signal\s*:\s*(\d+)%', out)
                
            elif system == "linux":
                p = subprocess.Popen(
                    "iwconfig", 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                out = p.stdout.read().decode('utf-8').strip()
                signal_match = re.search(r'Signal level=(-?\d+) dBm', out)
                
            if signal_match:
                signal_strength = int(signal_match.group(1))
                return self.classify_network(signal_strength)
            else:
                return 'offline', 0
                
        except Exception as e:
            print(f"Network detection error: {e}")
            return 'offline', 0
    
    def classify_network(self, signal_strength):
        """Classify network type based on signal strength"""
        if signal_strength > 75:
            return '4G', 1000  # Assume good bandwidth
        elif signal_strength > 50:
            return '3G', 500
        elif signal_strength > 25:
            return '2G', 50
        else:
            return 'EDGE', 10
    
    def update_network_status(self):
        """Update network status in PostgreSQL"""
        if not self.channel_id:
            return
        
        network_type, bandwidth = self.detect_network()
        
        with self.connection.cursor() as cur:
            cur.execute(
                "SELECT mq.update_network_status(%s, %s, %s)",
                (self.channel_id, network_type, bandwidth)
            )
            self.connection.commit()
    
    def monitor_network(self, interval=30):
        """Continuously monitor network and update database"""
        while True:
            try:
                self.update_network_status()
                print(f"Network status updated for channel {self.channel_id}")
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(interval)

# Usage
if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'database': 'pg_mq_poc',
        'user': 'cfurano',
        'password': 'cfurano'
    }
    
    bridge = NetworkPostgresBridge(db_config)
    bridge.connect_db()
    bridge.get_channel_id()
    bridge.monitor_network()
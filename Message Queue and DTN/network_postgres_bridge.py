#!/usr/bin/env python3
"""
Network-PostgreSQL Bridge Service
Connects the Network Analyser to the Message Queue system
"""
import sys
import os
import time
import psycopg2
import threading
import logging
from typing import Dict, Optional

# Add Network Analyser to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Network Analyser'))

try:
    from Network_analyser import (
        read_data_from_cmd, 
        percentage_to_dbm,
        all_Networks
    )
except ImportError as e:
    print(f"Error importing Network_analyser: {e}")
    print("Make sure Network_analyser.py is in the correct location")
    sys.exit(1)

class NetworkPostgresBridge:
    def __init__(self, db_config: Dict, channel_id: int = 1):
        self.db_config = db_config
        self.channel_id = channel_id
        self.connection = None
        self.running = False
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = True
            self.logger.info("Connected to database")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
            
    def detect_network_type(self) -> str:
        """
        Detect current network type
        TODO: Extend beyond WiFi to include cellular
        """
        try:
            # Check WiFi signal
            wifi_data = read_data_from_cmd()
            if wifi_data:
                # We have WiFi - assume good connection
                strongest_signal = max(int(signal) for _, signal in wifi_data)
                if strongest_signal > 70:
                    return "4G"  # Strong WiFi treated as 4G equivalent
                elif strongest_signal > 50:
                    return "3G"
                else:
                    return "2G"
            else:
                # No WiFi detected - check for other connections
                # TODO: Add cellular network detection here
                return "offline"
                
        except Exception as e:
            self.logger.error(f"Network detection failed: {e}")
            return "offline"
            
    def estimate_bandwidth(self, network_type: str) -> int:
        """
        Estimate bandwidth based on network type
        TODO: Implement actual bandwidth testing
        """
        bandwidth_map = {
            "4G": 10000,    # 10 Mbps
            "3G": 2000,     # 2 Mbps  
            "2G": 100,      # 100 Kbps
            "EDGE": 200,    # 200 Kbps
            "offline": 0
        }
        return bandwidth_map.get(network_type, 0)
        
    def update_network_status(self, network_type: str, bandwidth: int):
        """Update network status in database"""
        if not self.connection:
            return
            
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    SELECT mq.update_network_status(%s, %s, %s)
                """, (self.channel_id, network_type, bandwidth))
                
            self.logger.info(f"Updated network status: {network_type} ({bandwidth} kbps)")
            
        except Exception as e:
            self.logger.error(f"Failed to update network status: {e}")
            
    def check_and_trigger_messages(self, network_type: str):
        """Check if network came online and trigger message processing"""
        if network_type != "offline":
            try:
                with self.connection.cursor() as cur:
                    # Trigger sweep for any waiting messages
                    cur.execute("""
                        SELECT q.queue_name 
                        FROM mq.queue q
                        JOIN mq.message_waiting mw ON mw.queue_id = q.queue_id
                        GROUP BY q.queue_name
                    """)
                    
                    queues_with_messages = cur.fetchall()
                    
                    for (queue_name,) in queues_with_messages:
                        cur.execute("CALL mq.sweep_waiting_message(%s)", (queue_name,))
                        self.logger.info(f"Triggered message sweep for queue: {queue_name}")
                        
            except Exception as e:
                self.logger.error(f"Failed to trigger message processing: {e}")
                
    def monitor_network(self, interval: int = 30):
        """Main monitoring loop"""
        self.running = True
        last_network_type = "unknown"
        
        while self.running:
            try:
                # Detect current network
                current_network = self.detect_network_type()
                bandwidth = self.estimate_bandwidth(current_network)
                
                # Update database
                self.update_network_status(current_network, bandwidth)
                
                # If network came back online, trigger message processing
                if last_network_type == "offline" and current_network != "offline":
                    self.logger.info("Network came back online - triggering message processing")
                    self.check_and_trigger_messages(current_network)
                    
                last_network_type = current_network
                
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                
            time.sleep(interval)
            
    def start_monitoring(self, interval: int = 30):
        """Start monitoring in background thread"""
        self.connect_db()
        
        monitor_thread = threading.Thread(
            target=self.monitor_network, 
            args=(interval,)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.logger.info(f"Network monitoring started (interval: {interval}s)")
        return monitor_thread
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.connection:
            self.connection.close()
        self.logger.info("Network monitoring stopped")

if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'pg_mq_poc', 
        'user': 'root',
        'password': 'Christelle09123'
    }
    
    bridge = NetworkPostgresBridge(db_config, channel_id=1)
    
    try:
        monitor_thread = bridge.start_monitoring(interval=10)  # Check every 10 seconds
        
        # Keep running until Ctrl+C
        print("Network monitoring running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping network monitoring...")
        bridge.stop_monitoring()
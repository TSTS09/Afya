#!/usr/bin/env python3
"""
Network Monitoring Utilities
============================

Network condition monitoring for intelligent protocol selection
in healthcare data transmission systems.
"""

import asyncio
import time
from typing import Dict, Any, Optional
import aiohttp
import psutil

from ..core.models import NetworkStatus, NetworkCondition
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NetworkMonitor:
    """Network condition monitoring service"""
    
    def __init__(self, test_urls: Optional[list] = None, timeout: int = 10):
        self.test_urls = test_urls or [
            'https://www.google.com',
            'https://httpbin.org/ip',
            'https://api.github.com'
        ]
        self.timeout = timeout
        self.logger = get_logger(f"{__name__}.NetworkMonitor")
    
    async def check_network_status(self) -> NetworkStatus:
        """Check current network status and return metrics"""
        try:
            # Measure latency
            latency = await self._measure_latency()
            
            # Estimate bandwidth (simplified)
            bandwidth = await self._estimate_bandwidth()
            
            # Check packet loss (simplified)
            packet_loss = await self._check_packet_loss()
            
            return NetworkStatus(
                bandwidth=bandwidth,
                latency=latency,
                packet_loss=packet_loss
            )
        
        except Exception as e:
            self.logger.error(f"Network status check failed: {str(e)}")
            # Return offline status on error
            return NetworkStatus(
                bandwidth=0.0,
                latency=999.0,
                packet_loss=100.0
            )
    
    async def _measure_latency(self) -> float:
        """Measure network latency by pinging test URLs"""
        latencies = []
        
        for url in self.test_urls[:2]:  # Test only first 2 URLs for speed
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            end_time = time.time()
                            latency_ms = (end_time - start_time) * 1000
                            latencies.append(latency_ms)
            
            except Exception as e:
                self.logger.debug(f"Latency test failed for {url}: {str(e)}")
                latencies.append(999.0)  # High latency for failed requests
        
        return sum(latencies) / len(latencies) if latencies else 999.0
    
    async def _estimate_bandwidth(self) -> float:
        """Estimate bandwidth (simplified implementation)"""
        try:
            # Use network interface stats as a proxy
            net_io = psutil.net_io_counters()
            
            if hasattr(net_io, 'bytes_sent') and hasattr(net_io, 'bytes_recv'):
                # This is a very simplified estimation
                # In reality, you'd need to measure over time
                total_bytes = net_io.bytes_sent + net_io.bytes_recv
                
                # Rough estimation based on activity
                if total_bytes > 1000000000:  # 1GB
                    return 10.0  # Assume high bandwidth
                elif total_bytes > 100000000:  # 100MB
                    return 5.0   # Medium bandwidth
                else:
                    return 1.0   # Low bandwidth
            
            return 2.0  # Default estimate
        
        except Exception as e:
            self.logger.debug(f"Bandwidth estimation failed: {str(e)}")
            return 1.0  # Conservative estimate
    
    async def _check_packet_loss(self) -> float:
        """Check packet loss (simplified implementation)"""
        try:
            successful_requests = 0
            total_requests = min(3, len(self.test_urls))
            
            for url in self.test_urls[:total_requests]:
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                successful_requests += 1
                
                except Exception:
                    pass  # Failed request
            
            if total_requests == 0:
                return 0.0
            
            loss_rate = ((total_requests - successful_requests) / total_requests) * 100
            return loss_rate
        
        except Exception as e:
            self.logger.debug(f"Packet loss check failed: {str(e)}")
            return 10.0  # Assume some packet loss on error
    
    def get_recommended_protocol(self, network_status: NetworkStatus) -> str:
        """Get recommended transmission protocol based on network conditions"""
        condition = network_status.get_condition()
        
        recommendations = {
            NetworkCondition.EXCELLENT: "HTTPS",
            NetworkCondition.GOOD: "HTTPS",
            NetworkCondition.POOR: "SMS",
            NetworkCondition.OFFLINE: "SMS"
        }
        
        return recommendations.get(condition, "SMS")
    
    async def continuous_monitoring(self, interval: int = 60, callback=None):
        """Continuous network monitoring with optional callback"""
        self.logger.info(f"Starting continuous network monitoring (interval: {interval}s)")
        
        while True:
            try:
                status = await self.check_network_status()
                condition = status.get_condition()
                
                self.logger.debug(f"Network status: {condition.value} "
                                 f"(BW: {status.bandwidth:.1f}Mbps, "
                                 f"Latency: {status.latency:.1f}ms, "
                                 f"Loss: {status.packet_loss:.1f}%)")
                
                if callback:
                    await callback(status)
                
                await asyncio.sleep(interval)
            
            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {str(e)}")
                await asyncio.sleep(interval)


class FacilityNetworkManager:
    """Manage network status for multiple healthcare facilities"""
    
    def __init__(self):
        self.facility_status: Dict[str, NetworkStatus] = {}
        self.logger = get_logger(f"{__name__}.FacilityNetworkManager")
    
    def update_facility_status(self, facility_id: str, status: NetworkStatus):
        """Update network status for a facility"""
        self.facility_status[facility_id] = status
        self.logger.debug(f"Updated network status for facility {facility_id}: {status.get_condition().value}")
    
    def get_facility_status(self, facility_id: str) -> Optional[NetworkStatus]:
        """Get network status for a facility"""
        return self.facility_status.get(facility_id)
    
    def get_facilities_by_condition(self, condition: NetworkCondition) -> list:
        """Get facilities with specific network condition"""
        facilities = []
        for facility_id, status in self.facility_status.items():
            if status.get_condition() == condition:
                facilities.append(facility_id)
        return facilities
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of all facility network statuses"""
        summary = {
            'total_facilities': len(self.facility_status),
            'by_condition': {
                'excellent': 0,
                'good': 0,
                'poor': 0,
                'offline': 0
            },
            'average_bandwidth': 0.0,
            'average_latency': 0.0
        }
        
        if not self.facility_status:
            return summary
        
        total_bandwidth = 0.0
        total_latency = 0.0
        
        for status in self.facility_status.values():
            condition = status.get_condition()
            summary['by_condition'][condition.value] += 1
            total_bandwidth += status.bandwidth
            total_latency += status.latency
        
        facility_count = len(self.facility_status)
        summary['average_bandwidth'] = total_bandwidth / facility_count
        summary['average_latency'] = total_latency / facility_count
        
        return summary
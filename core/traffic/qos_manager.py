"""
Enterprise NGFW - QoS Manager

Implements traffic shaping and bandwidth limits using a Token Bucket algorithm.
Provides limits per IP, subnets, or globally.
"""

import time
import asyncio
import logging
from typing import Dict, Optional

class TokenBucket:
    """Implement Token Bucket algorithm for rate limiting."""
    
    def __init__(self, capacity_bytes: float, fill_rate_bytes_sec: float):
        self.capacity = capacity_bytes
        self.fill_rate = fill_rate_bytes_sec
        self.tokens = capacity_bytes
        self.last_update = time.time()
        self._lock = asyncio.Lock()
        
    async def consume(self, amount: int) -> bool:
        """Attempt to consume tokens. Returns True if successful, False if blocked."""
        async with self._lock:
            now = time.time()
            # Replenish tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
            self.last_update = now
            
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False

class QoSManager:
    """Manages Quality of Service (QoS) rules and rate limits."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        self.config = config or {}
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # IP -> TokenBucket mapping for per-IP limits
        self.ip_buckets: Dict[str, TokenBucket] = {}
        
        # Load defaults from config
        qos_cfg = self.config.get('qos', {})
        self.enabled = qos_cfg.get('enabled', False)
        
        # Default: 10 Mbps (1.25 MB/s) per user, burstable to 20 Mbps
        self.default_per_ip_rate = qos_cfg.get('default_user_rate_bytes', 1250000)
        self.default_per_ip_burst = qos_cfg.get('default_user_burst_bytes', 2500000)
        
    def _get_bucket_for_ip(self, ip_address: str) -> TokenBucket:
        """Get or create a token bucket for a specific IP."""
        if ip_address not in self.ip_buckets:
            # Check if there's a specific rule for this IP (omitted for brevity)
            rate = self.default_per_ip_rate
            burst = self.default_per_ip_burst
            self.ip_buckets[ip_address] = TokenBucket(burst, rate)
            
            self.ip_buckets[ip_address] = TokenBucket(burst, rate)
            
        return self.ip_buckets[ip_address]
        
    def update_limits(self, enabled: bool, rate_bytes: int, burst_bytes: int):
        """Dynamically update global QoS limits."""
        self.enabled = enabled
        self.default_per_ip_rate = rate_bytes
        self.default_per_ip_burst = burst_bytes
        
        # Reset existing buckets with new limits
        for bucket in self.ip_buckets.values():
            bucket.fill_rate = rate_bytes
            bucket.capacity = burst_bytes
            if bucket.tokens > burst_bytes:
                bucket.tokens = burst_bytes
                
        self.logger.info(f"QoS global limits updated: enabled={enabled}, rate={rate_bytes} B/s, burst={burst_bytes} B")
        
    async def throttle(self, ip_address: str, data_size: int) -> None:
        """
        Throttle traffic for the given IP address.
        If the bucket is empty, asynchronously sleeps until tokens refill.
        """
        if not self.enabled or data_size <= 0:
            return
            
        bucket = self._get_bucket_for_ip(ip_address)
        
        while True:
            # Try to consume tokens
            if await bucket.consume(data_size):
                return
                
            # If not enough tokens, calculate wait time
            needed = data_size - bucket.tokens
            wait_time = needed / bucket.fill_rate
            
            # Avoid microscopic sleeps
            if wait_time < 0.001:
                wait_time = 0.001
                
            await asyncio.sleep(wait_time)

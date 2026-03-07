#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════
Traffic Router - Smart Packet Routing Engine
═══════════════════════════════════════════════════════════════════

Intelligent traffic router that determines how to handle each connection:
- Route to appropriate proxy mode (forward, transparent, reverse)
- Apply initial policy decisions
- Interface with eBPF for fast-path decisions

Author: Enterprise Security Team
"""

import asyncio
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProxyMode(Enum):
    """Proxy operation modes"""
    FORWARD = "forward"           # Explicit proxy
    TRANSPARENT = "transparent"   # Gateway mode
    REVERSE = "reverse"           # Web server protection
    HYBRID = "hybrid"             # Mixed mode


@dataclass
class RoutingDecision:
    """Routing decision for a connection"""
    mode: ProxyMode
    target_host: Optional[str]
    target_port: Optional[int]
    ssl_inspection: bool
    policy_id: Optional[str]
    metadata: dict
    
    def __repr__(self):
        return (f"RoutingDecision(mode={self.mode.value}, "
                f"target={self.target_host}:{self.target_port}, "
                f"ssl_inspection={self.ssl_inspection})")


class TrafficRouter:
    """
    Smart Traffic Router
    
    Routes incoming connections to appropriate proxy handlers based on:
    - Connection characteristics (ports, protocols)
    - Policy rules
    - Performance requirements
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.routing_config = config.get('routing', {})
        
        # Default mode
        self.default_mode = ProxyMode(
            self.routing_config.get('default_mode', 'transparent')
        )
        
        # Port mappings
        self.port_mode_map = self._build_port_map()
        
        # Statistics
        self.stats = {
            'total_routes': 0,
            'by_mode': {mode: 0 for mode in ProxyMode}
        }
        
        logger.info(f"Traffic Router initialized (default_mode={self.default_mode.value})")
    
    def _build_port_map(self) -> dict:
        """Build port to mode mapping"""
        port_map = {}
        
        # Default mappings
        defaults = {
            8080: ProxyMode.FORWARD,
            8443: ProxyMode.FORWARD,
            443: ProxyMode.TRANSPARENT,
            80: ProxyMode.TRANSPARENT,
        }
        
        # Apply config overrides
        custom_mappings = self.routing_config.get('port_mappings', {})
        for port, mode_str in custom_mappings.items():
            try:
                defaults[int(port)] = ProxyMode(mode_str)
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid port mapping: {port}={mode_str}: {e}")
        
        return defaults
    
    async def route(self, 
                   client_addr: Tuple[str, int],
                   local_port: int,
                   initial_data: Optional[bytes] = None) -> RoutingDecision:
        """
        Route incoming connection
        
        Args:
            client_addr: (ip, port) of client
            local_port: Local port where connection arrived
            initial_data: Initial bytes from connection (for protocol detection)
        
        Returns:
            RoutingDecision with routing instructions
        """
        self.stats['total_routes'] += 1
        
        # Step 1: Determine proxy mode based on port
        mode = self.port_mode_map.get(local_port, self.default_mode)
        
        # Step 2: Extract target from initial data if available
        target_host = None
        target_port = None
        
        if initial_data:
            target_host, target_port = await self._extract_target(
                initial_data, mode
            )
        
        # Step 3: Determine if SSL inspection is needed
        ssl_inspection = self._should_inspect_ssl(
            client_addr[0], target_host, local_port
        )
        
        # Step 4: Create decision
        decision = RoutingDecision(
            mode=mode,
            target_host=target_host,
            target_port=target_port or (443 if local_port in [443, 8443] else 80),
            ssl_inspection=ssl_inspection,
            policy_id=None,  # Will be set by policy engine
            metadata={
                'client_ip': client_addr[0],
                'client_port': client_addr[1],
                'local_port': local_port,
            }
        )
        
        # Update statistics
        self.stats['by_mode'][mode] = self.stats['by_mode'].get(mode, 0) + 1
        
        logger.debug(f"Routed: {client_addr[0]} -> {decision}")
        
        return decision
    
    async def _extract_target(self, 
                              data: bytes, 
                              mode: ProxyMode) -> Tuple[Optional[str], Optional[int]]:
        """
        Extract target host/port from initial connection data
        
        Handles:
        - HTTP CONNECT requests
        - TLS SNI
        - SOCKS protocol
        """
        # Check for HTTP CONNECT
        if data.startswith(b'CONNECT'):
            try:
                line = data.split(b'\r\n')[0].decode('latin-1')
                parts = line.split()
                if len(parts) >= 2:
                    target = parts[1].split(':')
                    host = target[0]
                    port = int(target[1]) if len(target) > 1 else 443
                    return host, port
            except Exception as e:
                logger.debug(f"Error parsing CONNECT: {e}")
        
        # Check for TLS ClientHello (SNI)
        if data[0] == 0x16 and len(data) > 5:
            from core.ssl_engine.sni_router import extract_sni
            sni = extract_sni(data)
            if sni:
                return sni, 443
        
        return None, None
    
    def _should_inspect_ssl(self, 
                           client_ip: str, 
                           target_host: Optional[str],
                           local_port: int) -> bool:
        """
        Determine if SSL inspection should be performed
        
        Factors:
        - Global SSL inspection policy
        - Per-client policies
        - Per-domain bypass rules
        - Certificate pinning detection
        """
        # Check global setting
        ssl_config = self.config.get('ssl_inspection', {})
        if not ssl_config.get('enabled', True):
            return False
        
        # Check bypass list for domains
        if target_host:
            bypass_domains = ssl_config.get('bypass_domains', [])
            for pattern in bypass_domains:
                if self._match_domain(target_host, pattern):
                    logger.debug(f"SSL inspection bypassed for {target_host}")
                    return False
        
        # Check bypass list for IPs
        bypass_ips = ssl_config.get('bypass_ips', [])
        if client_ip in bypass_ips:
            logger.debug(f"SSL inspection bypassed for {client_ip}")
            return False
        
        # Default: inspect
        return True
    
    def _match_domain(self, domain: str, pattern: str) -> bool:
        """Match domain against pattern (supports wildcards)"""
        import re
        regex_pattern = pattern.replace('.', r'\.').replace('*', '.*')
        return bool(re.match(f'^{regex_pattern}$', domain, re.IGNORECASE))
    
    def get_statistics(self) -> dict:
        """Get routing statistics"""
        return {
            'total_routes': self.stats['total_routes'],
            'by_mode': {
                mode.value: count 
                for mode, count in self.stats['by_mode'].items()
            }
        }

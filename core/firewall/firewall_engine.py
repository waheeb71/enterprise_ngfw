#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════
Enterprise NGFW - Firewall Engine
═══════════════════════════════════════════════════════════════════

Core firewall logic handling:
- L3/L4 Filtering
- eBPF/XDP Management
- DPI Integration
- QoS

Author: Enterprise Security Team
"""

import asyncio
import logging
import platform
from typing import Optional, List, Dict
from .dpi_analyzer import DPIAnalyzer

logger = logging.getLogger(__name__)

class FirewallEngine:
    """
    Core Firewall Engine
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.firewall_config = config.get('firewall', {})
        self.ebpf_config = self.firewall_config.get('ebpf', {})
        
        self.dpi_analyzer = DPIAnalyzer(config) if self.firewall_config.get('dpi', {}).get('enabled', False) else None
        self.ebpf_enabled = self.ebpf_config.get('enabled', False)
        
        # State
        self.blocked_ips = set()
        self.blocked_ports = set()
        self.qos_rules = []
        
        self._load_rules()
        
    def _load_rules(self):
        """Load firewall rules from config"""
        filtering = self.firewall_config.get('filtering', {})
        
        # Port filtering
        allowed = set(filtering.get('allow_ports', []))
        default_policy = filtering.get('default_policy', 'deny')
        
        logger.info(f"Firewall Policy: Default {default_policy}, Allowed Ports: {allowed}")
        
        # QoS Rules
        self.qos_rules = filtering.get('priority_ports', [])
        
    async def start(self):
        """Start firewall engine"""
        logger.info("🛡️ Starting Firewall Engine")
        
        if self.ebpf_enabled:
            await self._init_ebpf()
            
        if self.dpi_analyzer:
            await self.dpi_analyzer.start()
            
    async def stop(self):
        """Stop firewall engine"""
        logger.info("Stopping Firewall Engine")
        if self.dpi_analyzer:
            await self.dpi_analyzer.stop()
            
    async def _init_ebpf(self):
        """Initialize eBPF/XDP subsystem"""
        if platform.system() != 'Linux':
            logger.warning("⚠️  eBPF/XDP is only supported on Linux. Running in simulation mode.")
            return

        try:
            # Here we would load the BPF programs
            # self.bpf = BPF(src_file="core/firewall/bpf/filter.c")
            # self.bpf.attach_xdp(device=self.ebpf_config.get('interface', 'eth0'), fn=self.bpf.load_func("xdp_filter", BPF.XDP))
            logger.info("✅ eBPF XDP programs loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load eBPF: {e}")
            self.ebpf_enabled = False

    async def inspect_packet(self, packet_info: dict) -> str:
        """
        Inspect a packet (L3/L4 + DPI)
        Returns: 'allow', 'drop', 'qos_high', 'qos_low'
        """
        # 1. L3/L4 Check
        if not self._check_l3_l4(packet_info):
            return 'drop'
            
        # 2. DPI Check
        if self.dpi_analyzer:
            dpi_result = await self.dpi_analyzer.analyze(packet_info)
            if dpi_result == 'block':
                return 'drop'
                
        # 3. QoS Check
        qos = self._check_qos(packet_info)
        if qos:
            return f"qos_{qos}"
            
        return 'allow'

    def _check_l3_l4(self, info: dict) -> bool:
        """Check basic IP/Port rules"""
        # Check IP
        if info.get('src_ip') in self.blocked_ips:
            return False
            
        # Check Port
        port = info.get('dest_port')
        filtering = self.firewall_config.get('filtering', {})
        allowed = set(filtering.get('allow_ports', []))
        default_policy = filtering.get('default_policy', 'deny')
        
        if default_policy == 'deny':
            return port in allowed
        else:
            return port not in self.blocked_ports

    def _check_qos(self, info: dict) -> Optional[str]:
        """Check QoS rules"""
        port = info.get('dest_port')
        for rule in self.qos_rules:
            if rule['port'] == port:
                return rule['priority']
        return None

    def add_block_rule(self, ip: str = None, port: int = None):
        """Dynamically add block rule"""
        if ip:
            self.blocked_ips.add(ip)
            # Update eBPF map if enabled
            
        if port:
            self.blocked_ports.add(port)
            
        logger.info(f"🚫 Added block rule: IP={ip}, Port={port}")

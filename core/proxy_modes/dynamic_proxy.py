#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════
Enterprise NGFW - Dynamic Proxy Mode
═══════════════════════════════════════════════════════════════════

Intelligent proxy manager that switches modes based on:
1. Network configuration
2. Traffic analysis
3. Policy rules

Author: Enterprise Security Team
"""

import asyncio
import logging
from typing import Optional, Dict, List
from .base_proxy import BaseProxy
from .forward_proxy import ForwardProxy
from .transparent_proxy import MITMProxy as TransparentProxy
from .reverse_proxy import ReverseProxy

logger = logging.getLogger(__name__)

class DynamicProxy(BaseProxy):
    """
    Dynamic Proxy Manager
    
    Orchestrates multiple proxy modes and routes traffic intelligently.
    """
    
    def __init__(self, config: dict, ca_manager, flow_tracker, ssl_policy_engine=None):
        super().__init__(config)
        self.ca_manager = ca_manager
        self.flow_tracker = flow_tracker
        self.ssl_policy_engine = ssl_policy_engine
        
        self.active_proxies: Dict[str, BaseProxy] = {}
        self.mode_config = config.get('proxy', {}).get('dynamic', {})
        
        # Initialize sub-proxies
        self._init_proxies()
        
    def _init_proxies(self):
        """Initialize all proxy components"""
        proxy_config = self.config.get('proxy', {})
        
        # Forward Proxy
        if proxy_config.get('forward', {}).get('enabled', False):
            self.active_proxies['forward'] = ForwardProxy(
                self.config, self.ca_manager, self.flow_tracker
            )
            
        # Transparent Proxy
        if proxy_config.get('transparent', {}).get('enabled', False):
            self.active_proxies['transparent'] = TransparentProxy(
                self.config, self.ca_manager, self.ssl_policy_engine
            )
            
        # Reverse Proxy
        if proxy_config.get('reverse', {}).get('enabled', False):
            self.active_proxies['reverse'] = ReverseProxy(
                self.config, self.ca_manager, self.flow_tracker
            )
            
    async def start(self):
        """Start all enabled proxy modes"""
        logger.info("🚀 Starting Dynamic Proxy Manager")
        
        tasks = []
        for name, proxy in self.active_proxies.items():
            logger.info(f"Starting {name} proxy mode...")
            tasks.append(proxy.start())
            
        if not tasks:
            logger.warning("⚠️  No proxy modes enabled in dynamic configuration!")
            return
            
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in dynamic proxy: {e}")
            raise

    async def stop(self):
        """Stop all proxies"""
        logger.info("🛑 Stopping Dynamic Proxy Manager")
        
        for name, proxy in self.active_proxies.items():
            try:
                await proxy.stop()
            except Exception as e:
                logger.error(f"Error stopping {name} proxy: {e}")

    def get_status(self) -> dict:
        """Get status of all proxies"""
        status = {
            'mode': 'dynamic',
            'active_modes': list(self.active_proxies.keys()),
            'sub_proxies': {}
        }
        
        for name, proxy in self.active_proxies.items():
            if hasattr(proxy, 'get_statistics'):
                status['sub_proxies'][name] = proxy.get_statistics()
                
        return status
        return status

    async def handle_connection(self, reader, writer):
        """
        Handle incoming connection.
        
        For DynamicProxy, this method should typically not be called directly
        as it delegates to sub-proxies. However, if used as a standalone proxy,
        it could route to the appropriate sub-proxy.
        """
        logger.warning("DynamicProxy.handle_connection called directly - this is unexpected")
        writer.close()
        await writer.wait_closed()

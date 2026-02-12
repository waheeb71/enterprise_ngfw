#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════
Enterprise NGFW - Main Entry Point
═══════════════════════════════════════════════════════════════════

Next-Generation Firewall with advanced features:
- Multiple proxy modes (Forward, Transparent, Reverse)
- SSL/TLS inspection with policy engine
- eBPF XDP acceleration
- Deep packet inspection
- Smart blocker with reputation engine
- ML-based anomaly detection
- REST API & Dashboard

Author: Enterprise Security Team
License: Proprietary
Version: 2.0.0
"""

import asyncio
import logging
import signal
import sys
import yaml
import logging.handlers
from pathlib import Path
from typing import Optional
import argparse

# Core components
from core.router import TrafficRouter, RoutingDecision, ProxyMode
#from core.router.dispatcher import RouteDispatcher
#from core.router.policy_integration import PolicyRouter
#from core.router.utils import create_routing_context
from core.flow_tracker import FlowTracker
from core.ssl_engine.ca_pool import CAPoolManager
from core.ssl_engine.inspector import SSLInspector
from core.ssl_engine.policy_engine import SSLPolicyEngine
from core.proxy_modes import TransparentProxy, ForwardProxy, ReverseProxy

# Acceleration
from acceleration.ebpf.xdp_engine import create_xdp_engine

# ML Components
from ml.inference import (
    AnomalyDetector, TrafficFeatures,
    TrafficProfiler, TrafficPattern,
    AdaptivePolicyEngine, PolicyAction
)

# API
import uvicorn
from api.rest.main import app as api_app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class NGFWApplication:
    """
    Main NGFW Application Controller
    
    Manages lifecycle of all components.
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: Optional[dict] = None
        
        # Core components
        self.traffic_router: Optional[TrafficRouter] = None
        self.flow_tracker: Optional[FlowTracker] = None
        self.ca_manager: Optional[CAPoolManager] = None
        self.ssl_inspector: Optional[SSLInspector] = None
        self.ssl_policy_engine: Optional[SSLPolicyEngine] = None
        self.xdp_engine = None
        
        # ML Components
        self.anomaly_detector: Optional[AnomalyDetector] = None
        self.traffic_profiler: Optional[TrafficProfiler] = None
        self.policy_engine: Optional[AdaptivePolicyEngine] = None
        
        # Proxy modes
        self.transparent_proxy: Optional[TransparentProxy] = None
        self.forward_proxy: Optional[ForwardProxy] = None
        self.reverse_proxy: Optional[ReverseProxy] = None
        
        # Running state
        self.running = False
        self.shutdown_event = asyncio.Event()
    
    def load_config(self):
        """Load configuration from YAML file"""
        logger.info(f"Loading configuration from {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info("✅ Configuration loaded successfully")
            
            # Validate configuration
            self._validate_config()
            
            # Log proxy mode
            proxy_mode = self.config.get('proxy', {}).get('mode', 'transparent')
            logger.info(f"🔥 Proxy mode: {proxy_mode}")
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML configuration: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def _validate_config(self):
        """Validate configuration"""
        required_sections = ['proxy', 'tls', 'logging']
        
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required configuration section: {section}")
                sys.exit(1)
        
        logger.info("✅ Configuration validated")
    
    def setup_logging(self):
        """Setup logging based on configuration"""
        log_config = self.config.get('logging', {})
        
        # Set log level
        log_level = log_config.get('level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        # Create log directory
        log_file = Path(log_config.get('file', '/var/log/ngfw/ngfw.log'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Add file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_config.get('max_bytes', 104857600),
            backupCount=log_config.get('backup_count', 10)
        )
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        logging.getLogger().addHandler(file_handler)
        
        logger.info(f"✅ Logging configured (level={log_level}, file={log_file})")
    
    async def initialize_components(self):
        """Initialize all components"""
        logger.info("Initializing components...")
        
        try:
            # 1. Initialize CA Manager
            logger.info("Initializing CA Manager...")
            self.ca_manager = CAPoolManager(self.config)
            logger.info("✅ CA Manager initialized")
            
            # 2. Initialize SSL components
            logger.info("Initializing SSL Inspector...")
            self.ssl_inspector = SSLInspector(self.ca_manager, self.config)
            logger.info("✅ SSL Inspector initialized")
            
            logger.info("Initializing SSL Policy Engine...")
            self.ssl_policy_engine = SSLPolicyEngine(self.config)
            logger.info("✅ SSL Policy Engine initialized")
            
            # 3. Initialize Traffic Router
            logger.info("Initializing Traffic Router...")
            self.traffic_router = TrafficRouter(self.config)
            logger.info("✅ Traffic Router initialized")
            
            # 4. Initialize Flow Tracker
            logger.info("Initializing Flow Tracker...")
            self.flow_tracker = FlowTracker(self.config)
            await self.flow_tracker.start()
            logger.info("✅ Flow Tracker initialized")
            
            # 5. Initialize eBPF XDP Engine
            logger.info("Initializing eBPF XDP Engine...")
            self.xdp_engine = create_xdp_engine(self.config)
            await self.xdp_engine.start()
            logger.info("✅ eBPF XDP Engine initialized")
            
            # 6. Initialize ML Components
            ml_config = self.config.get('ml', {})
            if ml_config.get('enabled', True):
                logger.info("Initializing ML components...")
                self.anomaly_detector = AnomalyDetector(
                    contamination=ml_config.get('anomaly_contamination', 0.1)
                )
                self.traffic_profiler = TrafficProfiler(
                    time_window=ml_config.get('profiler_time_window', 300)
                )
                self.policy_engine = AdaptivePolicyEngine(
                    learning_rate=ml_config.get('policy_learning_rate', 0.1)
                )
                logger.info("✅ ML components initialized")
            
            # 7. Initialize proxy modes based on configuration
            proxy_mode = self.config.get('proxy', {}).get('mode', 'transparent')
            
            if proxy_mode == 'transparent' or proxy_mode == 'all':
                logger.info("Initializing Transparent Proxy...")
                self.transparent_proxy = TransparentProxy(
                    self.config,
                    self.ca_manager,
                    self.xdp_engine
                )
                logger.info("✅ Transparent Proxy initialized")
            
            if proxy_mode == 'forward' or proxy_mode == 'all':
                logger.info("Initializing Forward Proxy...")
                self.forward_proxy = ForwardProxy(
                    self.config, 
                    self.ca_manager, 
                    self.flow_tracker
                )
                logger.info("✅ Forward Proxy initialized")
            
            if proxy_mode == 'reverse' or proxy_mode == 'all':
                logger.info("Initializing Reverse Proxy...")
                self.reverse_proxy = ReverseProxy(
                    self.config,
                    self.ca_manager,
                    self.flow_tracker
                )
                logger.info("✅ Reverse Proxy initialized")
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            raise
    
    async def start(self):
        """Start the application"""
        logger.info("=" * 70)
        logger.info("🚀 Starting Enterprise NGFW")
        logger.info("=" * 70)
        
        self.running = True
        
        # Load configuration
        self.load_config()
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        await self.initialize_components()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Print startup banner
        self._print_banner()
        
        # Start background tasks
        tasks = []
        
        # 1. Start proxy servers
        if self.transparent_proxy:
            tasks.append(self.transparent_proxy.start())
            
        if self.forward_proxy:
            tasks.append(self.forward_proxy.start())
        
        if self.reverse_proxy:
            tasks.append(self.reverse_proxy.start())
            
        # 2. Start ML maintenance loop
        if self.config.get('ml', {}).get('enabled', True):
            tasks.append(asyncio.create_task(self._ml_maintenance_loop()))
            
        # 3. Start API server
        if self.config.get('api', {}).get('enabled', True):
            tasks.append(asyncio.create_task(self._start_api_server()))
        
        if tasks:
            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"Failed to start services: {e}", exc_info=True)
                await self.stop()
                raise
        else:
            logger.warning("No services enabled!")
            await self.run_forever()
    
    async def stop(self):
        """Stop the application"""
        if not self.running:
            return
        
        logger.info("=" * 70)
        logger.info("🛑 Stopping Enterprise NGFW")
        logger.info("=" * 70)
        
        self.running = False
        
        # Stop components in reverse order
        if self.transparent_proxy:
            try:
                await self.transparent_proxy.stop()
            except Exception as e:
                logger.error(f"Error stopping transparent proxy: {e}")

        if self.forward_proxy:
            try:
                await self.forward_proxy.stop()
            except Exception as e:
                logger.error(f"Error stopping forward proxy: {e}")
        
        if self.reverse_proxy:
            try:
                await self.reverse_proxy.stop()
            except Exception as e:
                logger.error(f"Error stopping reverse proxy: {e}")
        
        if self.flow_tracker:
            try:
                await self.flow_tracker.stop()
            except Exception as e:
                logger.error(f"Error stopping flow tracker: {e}")
        
        if self.xdp_engine:
            try:
                await self.xdp_engine.stop()
            except Exception as e:
                logger.error(f"Error stopping XDP engine: {e}")
        
        logger.info("✅ Enterprise NGFW stopped")
        
        # Set shutdown event
        self.shutdown_event.set()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("✅ Signal handlers installed")
    
    def _print_banner(self):
        """Print startup banner"""
        proxy_config = self.config.get('proxy', {})
        tls_config = self.config.get('tls', {})
        ebpf_config = self.config.get('ebpf', {})
        api_config = self.config.get('api', {})
        
        logger.info("")
        logger.info("╔═══════════════════════════════════════════════════════════════════╗")
        logger.info("║         🔥 Enterprise NGFW - Successfully Started                ║")
        logger.info("╚═══════════════════════════════════════════════════════════════════╝")
        logger.info("")
        logger.info(f"  📡 Forward Proxy:  {proxy_config.get('forward_listen_host', '0.0.0.0')}:{proxy_config.get('forward_listen_port', 8080)}")
        logger.info(f"  🔒 Reverse Proxy:  {proxy_config.get('reverse_listen_host', '0.0.0.0')}:{proxy_config.get('reverse_listen_port', 443)}")
        logger.info(f"  📜 Root CA:        {tls_config.get('ca_cert_path', '/etc/ngfw/certs/root-ca.crt')}")
        logger.info(f"  🔐 Intermediate:   {tls_config.get('use_intermediate_ca', False)}")
        logger.info(f"  ⚡ eBPF XDP:       {ebpf_config.get('enabled', False)}")
        logger.info(f"  🧠 ML Engine:      {self.config.get('ml', {}).get('enabled', True)}")
        logger.info(f"  🔌 REST API:       http://{api_config.get('host', '0.0.0.0')}:{api_config.get('port', 8000)}")
        logger.info("")
        logger.info("  ⚠️  IMPORTANT: Install the Root CA certificate on all client devices!")
        logger.info("  📖 See documentation for client installation instructions")
        logger.info("")
        logger.info("  Press Ctrl+C to stop")
        logger.info("")
    
    async def run_forever(self):
        """Run until shutdown signal received"""
        await self.shutdown_event.wait()

    async def _ml_maintenance_loop(self):
        """ML maintenance tasks"""
        logger.info("ML maintenance loop started")
        
        while self.running:
            try:
                await asyncio.sleep(60)  # Every minute
                
                if self.traffic_profiler and self.policy_engine:
                    # Get statistics
                    profiler_stats = self.traffic_profiler.get_statistics()
                    policy_metrics = self.policy_engine.get_metrics()
                    
                    logger.debug(f"ML Stats - Profiles: {profiler_stats.total_profiles}, "
                               f"Policy Accuracy: {policy_metrics.calculate_accuracy():.2%}")
                
            except Exception as e:
                logger.error(f"Error in ML maintenance: {e}")

    async def _start_api_server(self):
        """Start API server"""
        logger.info("Starting API server...")
        
        api_config = self.config.get('api', {})
        host = api_config.get('host', '0.0.0.0')
        port = api_config.get('port', 8000)
        
        try:
            # Pass NGFW instance to API
            api_app.state.ngfw = self
            
            config = uvicorn.Config(
                api_app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Enterprise NGFW - Next-Generation Firewall'
    )
    parser.add_argument(
        '-c', '--config',
        type=Path,
        default=Path('/etc/ngfw/config.yaml'),
        help='Configuration file path (default: /etc/ngfw/config.yaml)'
    )
    parser.add_argument(
        '--init-ca',
        action='store_true',
        help='Initialize CA certificates and exit'
    )
    parser.add_argument(
        '--export-ca',
        type=Path,
        metavar='DIR',
        help='Export CA certificates for client installation and exit'
    )
    
    args = parser.parse_args()
    
    # Handle special operations
    if args.init_ca or args.export_ca:
        app = NGFWApplication(args.config)
        app.load_config()
        
        ca_manager = CAPoolManager(app.config)
        
        if args.export_ca:
            ca_manager.export_ca_for_clients(args.export_ca)
            logger.info(f"✅ CA certificates exported to {args.export_ca}")
        
        return
    
    # Normal operation
    app = NGFWApplication(args.config)
    
    try:
        await app.start()
        await app.run_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await app.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting...")
        sys.exit(0)

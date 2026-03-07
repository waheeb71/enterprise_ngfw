#!/usr/bin/env python3
"""
Enterprise NGFW - Main Integrated Engine (Legacy Wrapper)

DEPRECATED: This module is a thin wrapper around the main NGFWApplication
in main.py. For new code, use NGFWApplication directly.
This wrapper exists for backward compatibility with scripts that import
from ngfw_engine.
"""

import asyncio
import logging
import warnings
from typing import Dict, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Deprecation warning
warnings.warn(
    "ngfw_engine.EnterpriseNGFW is deprecated. "
    "Use main.NGFWApplication instead.",
    DeprecationWarning,
    stacklevel=2
)


@dataclass
class NGFWConfig:
    """NGFW configuration (legacy)

    DEPRECATED: Use config/defaults/base.yaml with NGFWApplication instead.
    """
    interface: str = "eth0"

    # ML Configuration
    ml_enabled: bool = True
    anomaly_contamination: float = 0.1
    profiler_time_window: int = 300
    policy_learning_rate: float = 0.1

    # eBPF Configuration
    ebpf_enabled: bool = True
    ebpf_port_filter: bool = True

    # Smart Blocker Configuration
    reputation_enabled: bool = True
    geoip_enabled: bool = True
    category_blocking_enabled: bool = True
    threat_intel_enabled: bool = True

    # Deep Inspection Configuration
    http_inspection: bool = True
    dns_inspection: bool = True
    smtp_inspection: bool = True

    # API Configuration
    api_enabled: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    websocket_enabled: bool = True

    def to_yaml_dict(self) -> dict:
        """Convert to YAML-compatible dict for NGFWApplication"""
        return {
            'ebpf': {
                'enabled': self.ebpf_enabled,
                'interface': self.interface,
                'port_filter': {'enabled': self.ebpf_port_filter},
            },
            'ml': {
                'enabled': self.ml_enabled,
                'anomaly_detection': {
                    'enabled': self.ml_enabled,
                    'threshold': 1.0 - self.anomaly_contamination,
                },
                'traffic_profiling': {
                    'enabled': self.ml_enabled,
                    'learning_period': self.profiler_time_window,
                },
            },
            'api': {
                'enabled': self.api_enabled,
                'listen_host': self.api_host,
                'listen_port': self.api_port,
                'websocket': {'enabled': self.websocket_enabled},
            },
        }


class EnterpriseNGFW:
    """
    Enterprise NGFW Main Engine (Legacy Wrapper)

    DEPRECATED: This class delegates to NGFWApplication from main.py.
    Use NGFWApplication directly for new code.
    """

    def __init__(self, config: NGFWConfig):
        warnings.warn(
            "EnterpriseNGFW is deprecated. Use main.NGFWApplication instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.config = config
        self._app = None

        # Statistics (maintained for backward compatibility)
        self.stats = {
            'total_packets': 0,
            'allowed_packets': 0,
            'blocked_packets': 0,
            'throttled_packets': 0,
            'anomalies_detected': 0,
            'threats_blocked': 0
        }

        self.running = False
        logger.info("EnterpriseNGFW wrapper initialized (delegates to NGFWApplication)")

    async def start(self):
        """Start the NGFW engine by delegating to NGFWApplication"""
        logger.info("Starting Enterprise NGFW (via NGFWApplication)...")
        self.running = True

        try:
            from main import NGFWApplication
            config_path = Path("config/defaults/base.yaml")
            self._app = NGFWApplication(config_path)
            self._app.load_config()
            self._app.initialize_components()
            await self._app.run()
        except ImportError:
            logger.warning(
                "Could not import NGFWApplication. "
                "Running in standalone ML-only mode."
            )
            await self._run_standalone()

    async def _run_standalone(self):
        """Fallback: run ML components only (legacy behavior)"""
        from ml.inference import AnomalyDetector, TrafficProfiler, AdaptivePolicyEngine

        if self.config.ml_enabled:
            self.anomaly_detector = AnomalyDetector(
                contamination=self.config.anomaly_contamination
            )
            self.traffic_profiler = TrafficProfiler(
                time_window=self.config.profiler_time_window
            )
            self.policy_engine = AdaptivePolicyEngine(
                learning_rate=self.config.policy_learning_rate
            )
            logger.info("✓ ML components initialized (standalone mode)")

        if self.config.api_enabled:
            asyncio.create_task(self._start_api_server())

        # Keep running
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop the NGFW engine"""
        logger.info("Stopping Enterprise NGFW...")
        self.running = False
        if self._app:
            self._app.stop()
        logger.info("✓ Enterprise NGFW stopped")

    async def _start_api_server(self):
        """Start API server"""
        try:
            import uvicorn
            from api.rest.main import app

            app.state.ngfw = self

            config = uvicorn.Config(
                app,
                host=self.config.api_host,
                port=self.config.api_port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")

    def get_statistics(self) -> Dict:
        """Get current statistics"""
        if self._app and hasattr(self._app, 'get_statistics'):
            return self._app.get_statistics()
        return self.stats.copy()


# ==================== Main Entry Point ====================

async def main():
    """Main function (legacy entry point)"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.warning(
        "⚠️ Using legacy entry point ngfw_engine.py. "
        "Prefer: python main.py --config config/defaults/base.yaml"
    )

    config = NGFWConfig(
        interface="eth0",
        ml_enabled=True,
        api_enabled=True,
        api_host="0.0.0.0",
        api_port=8000
    )

    ngfw = EnterpriseNGFW(config)

    try:
        await ngfw.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await ngfw.stop()


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║          Enterprise NGFW - Integrated System              ║
    ║                                                            ║
    ║  ⚠️  This entry point is DEPRECATED.                      ║
    ║  Use: python main.py --config config/defaults/base.yaml   ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ NGFW stopped gracefully")
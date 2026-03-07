"""
DEPRECATED: This module has been replaced by core/router/ package.

Use:
    from core.router.manager import TrafficRouter
    from core.router.types import RoutingDecision, ProxyMode
"""

import warnings
warnings.warn(
    "core.router_old is deprecated. Use core.router package instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
try:
    from core.router.types import ProxyMode, RoutingDecision  # noqa: F401
    from core.router.manager import TrafficRouter  # noqa: F401
except ImportError:
    pass

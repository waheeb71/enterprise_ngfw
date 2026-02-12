"""
Policy Engine Verification Demo (Modular Router Version)
Tests the integration of PolicyManager with the refactored TrafficRouter.
"""

import sys
import os
import asyncio
import logging
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.router import TrafficRouter
from policy.schema import Action, AppRule

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s')
logger = logging.getLogger("PolicyDemo")

async def test_policy_enforcement():
    logger.info("--- Starting Policy Engine Demo ---")

    # 1. Initialize Router (which initializes PolicyManager)
    config = {
        'routing': {'default_mode': 'transparent'},
        'ssl_inspection': {'enabled': True}
    }
    router = TrafficRouter(config)
    
    # 2. Add a Rule to Block "Facebook"
    logger.info("Adding rule: BLOCK Facebook")
    fb_rule = AppRule(
        name="Block FB",
        action=Action.BLOCK,
        application="facebook",
        priority=10
    )
    # Inject rule into the app_engine
    router.policy_integrator.policy_manager.app_engine.rules.append(fb_rule)
    
    # 3. Simulate Traffic to Facebook
    logger.info("\nTest 1: Traffic to facebook.com (SNI Detection)")
    
    # Mocking the extract_target function in the core.router.manager module
    async def mock_extract(data, mode):
        if b'facebook.com' in data:
            return "facebook.com", 443
        return "example.com", 443

    with patch('core.router.manager.extract_target', side_effect=mock_extract):
        decision = await router.route(
            client_addr=('192.168.1.100', 54321),
            local_port=443,
            initial_data=b'valid_tls_for_facebook.com'
        )
        
        if decision.target_host == "0.0.0.0":
            logger.info("✅ SUCCESS: Facebook traffic blocked!")
        else:
            logger.error(f"❌ FAILURE: Facebook traffic allowed to {decision.target_host}")

        # 4. Simulate Traffic to Allowed Site
        logger.info("\nTest 2: Traffic to example.com (Allowed)")
        decision_ok = await router.route(
            client_addr=('192.168.1.100', 54322),
            local_port=443,
            initial_data=b'valid_tls_for_example.com'
        )
        
        if decision_ok.target_host != "0.0.0.0":
            logger.info(f"✅ SUCCESS: Normal traffic allowed to {decision_ok.target_host}")
        else:
            logger.error("❌ FAILURE: Normal traffic blocked!")

if __name__ == "__main__":
    asyncio.run(test_policy_enforcement())

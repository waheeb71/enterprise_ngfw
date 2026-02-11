"""
Dummy end-to-end policy checks.
Runs lightweight, in-memory tests with fake data before integration.
"""

from datetime import datetime, time

# Allow running as a standalone script or module.
try:
    from .schema import (
        Action,
        Protocol,
        FirewallRule,
        AppRule,
        WebFilterRule,
        IPSRule,
        PolicyContext,
    )
    from .manager import PolicyManager
    from .access_control.acl_engine import ACLEngine
    from .access_control.schedules import Schedule
    from .access_control.zones import ZoneManager
    from .app_control.signatures import EncryptedAppSignatures
    from .web_filter.category import CategoryEngine, ContentCategory
    from .web_filter.dns_filter import DNSFilter
    from .web_filter.safe_search import SafeSearch
    from .ips.engine import IPSEngine
    from .ips.threat_intel import ThreatLevel, ThreatType
    from .ips.reputation import ReputationLevel
    from .ips.signatures import SignatureEngine
except ImportError:  # pragma: no cover - fallback for direct execution
    from schema import (
        Action,
        Protocol,
        FirewallRule,
        AppRule,
        WebFilterRule,
        IPSRule,
        PolicyContext,
    )
    from manager import PolicyManager
    from access_control.acl_engine import ACLEngine
    from access_control.schedules import Schedule
    from access_control.zones import ZoneManager
    from app_control.signatures import EncryptedAppSignatures
    from web_filter.category import CategoryEngine, ContentCategory
    from web_filter.dns_filter import DNSFilter
    from web_filter.safe_search import SafeSearch
    from ips.engine import IPSEngine
    from ips.threat_intel import ThreatLevel, ThreatType
    from ips.reputation import ReputationLevel
    from ips.signatures import SignatureEngine


def _assert(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def test_acl_engine():
    acl = ACLEngine()
    acl.load_rules(
        [
            FirewallRule(
                name="block-ssh",
                action=Action.BLOCK,
                src_ip="10.0.0.10",
                dst_ip="10.0.0.20",
                dst_port=22,
                protocol=Protocol.TCP,
                priority=1,
            )
        ]
    )

    blocked = PolicyContext(
        src_ip="10.0.0.10",
        dst_ip="10.0.0.20",
        src_port=55555,
        dst_port=22,
        protocol="tcp",
    )
    allowed = PolicyContext(
        src_ip="10.0.0.11",
        dst_ip="10.0.0.20",
        src_port=55555,
        dst_port=22,
        protocol="tcp",
    )

    _assert(acl.evaluate(blocked) == Action.BLOCK, "ACL should block SSH rule")
    _assert(acl.evaluate(allowed) == Action.ALLOW, "ACL should allow non-matching rule")


def test_schedule_and_zone():
    sched = Schedule(
        name="work-hours",
        days=["Mon", "Tue", "Wed", "Thu", "Fri"],
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    monday_10 = datetime(2024, 1, 1, 10, 0, 0)
    sunday_10 = datetime(2024, 1, 7, 10, 0, 0)
    _assert(sched.is_active(monday_10) is True, "Schedule should be active on Monday")
    _assert(sched.is_active(sunday_10) is False, "Schedule should be inactive on Sunday")

    zones = ZoneManager({"eth0": "wan", "eth1": "lan"})
    _assert(zones.get_zone("eth0") == "wan", "Zone lookup should map eth0 to wan")
    _assert(zones.get_zone("eth9") == "unknown", "Unknown interface should be 'unknown'")


def test_app_control():
    pm = PolicyManager()
    pm.app_engine.load_rules(
        [
            AppRule(
                name="block-tiktok",
                action=Action.BLOCK,
                application="tiktok",
                priority=1,
            )
        ]
    )
    ctx = PolicyContext(
        src_ip="10.0.0.2",
        dst_ip="8.8.8.8",
        src_port=1234,
        dst_port=443,
        protocol="tcp",
        app_id="tiktok",
        user_id="user1",
    )
    _assert(pm.app_engine.evaluate(ctx) == Action.BLOCK, "App rule should block tiktok")

    identified = EncryptedAppSignatures.identify_by_sni("media.tiktok.com")
    _assert(identified == "tiktok", "SNI identification should match tiktok")


def test_web_filter():
    wf = PolicyManager().web_engine
    wf.load_rules([WebFilterRule(name="block-adult", action=Action.BLOCK)])

    wf.category_engine.block_category(ContentCategory.SOCIAL_NETWORKING)
    ctx_block = PolicyContext(
        src_ip="10.0.0.2",
        dst_ip="1.1.1.1",
        src_port=1234,
        dst_port=443,
        protocol="tcp",
        domain="facebook.com",
        url="https://facebook.com",
    )
    _assert(wf.evaluate(ctx_block) == Action.BLOCK, "Web filter should block social domain")

    dns = DNSFilter()
    dns.add_domain("bad.example")
    _assert(dns.check_query("bad.example") is True, "DNS filter should block domain")
    _assert(dns.get_response() == "0.0.0.0", "DNS sinkhole IP should be 0.0.0.0")

    _assert(
        SafeSearch.get_safe_cname("google.com") == "forcesafesearch.google.com",
        "SafeSearch cname should be enforced for google.com",
    )
    _assert(
        SafeSearch.append_safe_param("https://google.com/search?q=test")
        .endswith("safe=active"),
        "SafeSearch should add safe=active",
    )

    cat_engine = CategoryEngine()
    match = cat_engine.categorize("example-facebook.com")
    _assert(
        ContentCategory.SOCIAL_NETWORKING in match.categories,
        "Category engine should tag social networking",
    )


def test_ips():
    ips = IPSEngine()
    ips.threat_intel.add_indicator(
        indicator="5.5.5.5",
        type="ip",
        level=ThreatLevel.HIGH,
        types=[ThreatType.MALWARE],
        source="unit-test",
    )
    ctx_threat = PolicyContext(
        src_ip="5.5.5.5",
        dst_ip="8.8.8.8",
        src_port=1234,
        dst_port=80,
        protocol="tcp",
    )
    _assert(ips.evaluate(ctx_threat) == Action.BLOCK, "IPS should block threat intel IP")

    ctx_rep = PolicyContext(
        src_ip="6.6.6.6",
        dst_ip="8.8.8.8",
        src_port=1234,
        dst_port=80,
        protocol="tcp",
    )
    ips.reputation.update_score("6.6.6.6", -100.0)
    _assert(
        ips.evaluate(ctx_rep) == Action.BLOCK,
        "IPS should block malicious reputation IP",
    )

    sig = SignatureEngine()
    sig.load_defaults()
    alerts = sig.scan(b"GET /?q=1 UNION SELECT * FROM users")
    _assert(any("SQL Injection" in a for a in alerts), "Signature engine should alert on payload")


def test_policy_manager_end_to_end():
    pm = PolicyManager()
    pm.acl_engine.load_rules(
        [
            FirewallRule(
                name="block-telnet",
                action=Action.BLOCK,
                dst_port=23,
                protocol=Protocol.TCP,
                priority=1,
            )
        ]
    )
    pm.app_engine.load_rules(
        [
            AppRule(
                name="block-netflix",
                action=Action.BLOCK,
                application="netflix",
                priority=1,
            )
        ]
    )
    pm.web_engine.category_engine.block_category(ContentCategory.VIDEO_STREAMING)

    ctx_acl = PolicyContext(
        src_ip="10.0.0.10",
        dst_ip="10.0.0.20",
        src_port=5555,
        dst_port=23,
        protocol="tcp",
        app_id="netflix",
        domain="netflix.com",
    )
    _assert(pm.evaluate(ctx_acl) == Action.BLOCK, "PolicyManager should block at ACL stage")

    ctx_app = PolicyContext(
        src_ip="10.0.0.10",
        dst_ip="10.0.0.20",
        src_port=5555,
        dst_port=443,
        protocol="tcp",
        app_id="netflix",
        domain="netflix.com",
    )
    _assert(pm.evaluate(ctx_app) == Action.BLOCK, "PolicyManager should block at App stage")

    ctx_web = PolicyContext(
        src_ip="10.0.0.10",
        dst_ip="10.0.0.20",
        src_port=5555,
        dst_port=443,
        protocol="tcp",
        app_id="ok-app",
        domain="netflix.com",
    )
    _assert(pm.evaluate(ctx_web) == Action.BLOCK, "PolicyManager should block at Web stage")

    ctx_allow = PolicyContext(
        src_ip="10.0.0.10",
        dst_ip="10.0.0.20",
        src_port=5555,
        dst_port=443,
        protocol="tcp",
        app_id="ok-app",
        domain="example.com",
    )
    _assert(pm.evaluate(ctx_allow) == Action.ALLOW, "PolicyManager should allow clean flow")


def run_all():
    test_acl_engine()
    test_schedule_and_zone()
    test_app_control()
    test_web_filter()
    test_ips()
    test_policy_manager_end_to_end()
    print("All dummy policy tests passed.")


if __name__ == "__main__":
    run_all()

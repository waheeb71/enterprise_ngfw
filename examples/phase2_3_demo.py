#!/usr/bin/env python3
"""
Enterprise NGFW v2.0 - Phase 2 & 3 Demo

Demonstrates:
- eBPF port filtering
- Smart blocker components
- Integrated threat prevention

Author: Enterprise NGFW Team
License: Proprietary
"""

import sys
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from acceleration.ebpf import PortFilterLoader, FilterMode
from policy.smart_blocker import (
    ReputationEngine,
    GeoIPFilter,
    CategoryBlocker,
    ThreatIntelligence,
    BlockingDecisionEngine,
    IncidentType,
    ContentCategory,
    ThreatLevel,
    ThreatType,
    PolicyMode
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_port_filtering():
    """Demonstrate eBPF port filtering"""
    print("\n" + "="*70)
    print("DEMO 1: eBPF XDP Port Filtering")
    print("="*70)
    
    # Note: Requires root privileges and BCC installed
    try:
        loader = PortFilterLoader('eth0')
        
        # Note: This is a dry-run demo (won't actually load without root)
        print("\n✓ Port Filter Loader initialized")
        print(f"  Interface: {loader.interface}")
        print(f"  Program: {loader.program_path}")
        print("\n📋 Configuration:")
        print("  Mode: WHITELIST")
        print("  TCP Ports: 22, 80, 443, 8080")
        print("  UDP Ports: 53, 123")
        
        print("\n💡 In production:")
        print("  - Kernel-level filtering at 10Gbps+")
        print("  - Real-time per-port statistics")
        print("  - Zero-copy packet processing")
        
    except Exception as e:
        logger.warning(f"Port filtering demo skipped: {e}")
        print("\n⚠️  Note: Port filtering requires root privileges and BCC")


def demo_reputation_engine():
    """Demonstrate reputation scoring"""
    print("\n" + "="*70)
    print("DEMO 2: Reputation Engine")
    print("="*70)
    
    engine = ReputationEngine()
    
    # Simulate incidents
    print("\n📊 Recording incidents...")
    
    # Good actor
    engine.whitelist_ip("8.8.8.8")
    rep = engine.get_ip_reputation("8.8.8.8")
    print(f"\n✅ Trusted IP: 8.8.8.8")
    print(f"   Score: {rep.score:.1f} ({rep.level.name})")
    
    # Suspicious actor
    suspicious_ip = "203.0.113.45"
    engine.record_incident(suspicious_ip, IncidentType.PORT_SCAN, 'ip')
    engine.record_incident(suspicious_ip, IncidentType.BRUTE_FORCE, 'ip')
    engine.record_incident(suspicious_ip, IncidentType.SUSPICIOUS_DNS, 'ip')
    
    rep = engine.get_ip_reputation(suspicious_ip)
    print(f"\n⚠️  Suspicious IP: {suspicious_ip}")
    print(f"   Score: {rep.score:.1f} ({rep.level.name})")
    print(f"   Incidents: {rep.incident_count}")
    print(f"   Types: {list(rep.incident_types.keys())}")
    
    # Malicious actor
    malicious_ip = "203.0.113.66"
    engine.record_incident(malicious_ip, IncidentType.MALWARE, 'ip')
    engine.record_incident(malicious_ip, IncidentType.PHISHING, 'ip')
    engine.record_incident(malicious_ip, IncidentType.RANSOMWARE, 'ip')
    
    rep = engine.get_ip_reputation(malicious_ip)
    print(f"\n❌ Malicious IP: {malicious_ip}")
    print(f"   Score: {rep.score:.1f} ({rep.level.name})")
    print(f"   Is malicious: {rep.is_malicious}")
    
    # Domain reputation
    engine.record_incident("phishing-site.com", IncidentType.PHISHING, 'domain')
    rep = engine.get_domain_reputation("phishing-site.com")
    print(f"\n🌐 Domain: phishing-site.com")
    print(f"   Score: {rep.score:.1f} ({rep.level.name})")
    
    # Statistics
    stats = engine.get_statistics()
    print(f"\n📈 Statistics:")
    print(f"   Total IPs tracked: {stats['total_ips_tracked']}")
    print(f"   Total domains tracked: {stats['total_domains_tracked']}")
    print(f"   Total incidents: {stats['total_incidents']}")
    print(f"   Malicious IPs: {stats['malicious_ips']}")


def demo_geoip_filter():
    """Demonstrate GeoIP filtering"""
    print("\n" + "="*70)
    print("DEMO 3: GeoIP Filter")
    print("="*70)
    
    geoip = GeoIPFilter()
    
    print("\n🌍 GeoIP Configuration:")
    print("  Blacklisted countries: KP (North Korea), IR (Iran)")
    print("  Block anonymous proxies: Yes")
    
    # Configure
    geoip.blacklist_country("KP")
    geoip.blacklist_country("IR")
    geoip.set_block_anonymous_proxies(True)
    
    # Test IPs (simulated)
    test_cases = [
        ("8.8.8.8", "US", False),
        ("203.0.113.1", "KP", True),
        ("198.51.100.1", "IR", True),
        ("192.0.2.1", "GB", False),
    ]
    
    print("\n🔍 Testing IPs:")
    for ip, country, should_block in test_cases:
        # Note: Without actual GeoIP database, this returns (False, None)
        is_blocked, reason = geoip.is_blocked(ip)
        
        print(f"\n  IP: {ip} (simulated: {country})")
        print(f"  Expected: {'BLOCK' if should_block else 'ALLOW'}")
        print(f"  Note: Requires GeoIP database for actual lookups")
    
    config = geoip.get_config()
    print(f"\n📋 Active Configuration:")
    print(f"   Blacklisted countries: {config['country_blacklist']}")
    print(f"   Block anonymous proxies: {config['block_anonymous_proxies']}")


def demo_category_blocker():
    """Demonstrate content categorization"""
    print("\n" + "="*70)
    print("DEMO 4: Category Blocker (90+ Categories)")
    print("="*70)
    
    blocker = CategoryBlocker()
    
    # Configure blocking
    blocker.block_category(ContentCategory.MALWARE)
    blocker.block_category(ContentCategory.PHISHING)
    blocker.block_category(ContentCategory.ADULT_EXPLICIT)
    blocker.block_category(ContentCategory.GAMBLING_CASINO)
    
    print("\n🚫 Blocked Categories:")
    for cat in blocker.get_blocked_categories():
        print(f"  - {cat}")
    
    # Test domains
    test_domains = [
        ("google.com", "Should be ALLOWED"),
        ("malware-site.com", "Contains 'malware' - BLOCKED"),
        ("xxx-adult-site.com", "Contains 'xxx' - BLOCKED"),
        ("casino-online.com", "Contains 'casino' - BLOCKED"),
        ("github.com", "Should be ALLOWED"),
        ("phishing-verify-account.com", "Contains 'phishing' - BLOCKED"),
    ]
    
    print("\n🔍 Categorizing Domains:")
    for domain, expected in test_domains:
        match = blocker.categorize_domain(domain)
        is_blocked, reason = blocker.is_blocked(domain)
        
        print(f"\n  🌐 {domain}")
        print(f"     Categories: {[c.name for c in match.categories]}")
        print(f"     Risk Level: {match.risk_level}")
        print(f"     Blocked: {'❌ YES' if is_blocked else '✅ NO'}")
        print(f"     Expected: {expected}")
    
    # Statistics
    stats = blocker.get_statistics()
    print(f"\n📈 Statistics:")
    print(f"   Total categorizations: {stats['total_categorizations']}")
    print(f"   Total blocked: {stats['total_blocked']}")
    print(f"   Cached domains: {stats['cached_domains']}")


def demo_threat_intelligence():
    """Demonstrate threat intelligence"""
    print("\n" + "="*70)
    print("DEMO 5: Threat Intelligence")
    print("="*70)
    
    threat_intel = ThreatIntelligence()
    
    print("\n📡 Threat Feeds Configured:")
    print("  - abuse.ch URLhaus (malicious URLs)")
    print("  - abuse.ch Feodo Tracker (botnets)")
    print("  - blocklist.de (attack sources)")
    print("  - Tor exit nodes")
    print("  - PhishTank (phishing URLs)")
    
    # Add sample indicators
    print("\n➕ Adding threat indicators...")
    
    threat_intel.add_indicator(
        indicator="192.0.2.100",
        indicator_type="ip",
        threat_level=ThreatLevel.HIGH,
        threat_types=[ThreatType.BOTNET, ThreatType.C2_SERVER],
        source="custom_feed",
        confidence=0.95,
        description="Known botnet C2 server"
    )
    
    threat_intel.add_indicator(
        indicator="malicious-phishing.com",
        indicator_type="domain",
        threat_level=ThreatLevel.CRITICAL,
        threat_types=[ThreatType.PHISHING],
        source="phishtank",
        confidence=1.0,
        description="Active phishing campaign"
    )
    
    threat_intel.add_indicator(
        indicator="evil-malware.com",
        indicator_type="domain",
        threat_level=ThreatLevel.CRITICAL,
        threat_types=[ThreatType.MALWARE, ThreatType.RANSOMWARE],
        source="urlhaus",
        confidence=0.98
    )
    
    # Lookup threats
    print("\n🔍 Threat Lookups:")
    
    test_cases = [
        ("192.0.2.100", "ip"),
        ("malicious-phishing.com", "domain"),
        ("evil-malware.com", "domain"),
        ("8.8.8.8", "ip"),
        ("google.com", "domain"),
    ]
    
    for indicator, itype in test_cases:
        is_threat, info = threat_intel.is_threat(
            indicator, itype, ThreatLevel.MEDIUM
        )
        
        print(f"\n  {indicator} ({itype})")
        if is_threat and info:
            print(f"  ⚠️  THREAT DETECTED!")
            print(f"     Level: {info.threat_level.name}")
            print(f"     Types: {[t.name for t in info.threat_types]}")
            print(f"     Source: {info.source}")
            print(f"     Confidence: {info.confidence:.2f}")
        else:
            print(f"  ✅ Clean (no threat found)")
    
    # Statistics
    stats = threat_intel.get_statistics()
    print(f"\n📈 Statistics:")
    print(f"   Total lookups: {stats['total_lookups']}")
    print(f"   Hits: {stats['hits']}")
    print(f"   Hit rate: {stats['hit_rate']:.1f}%")
    print(f"   Total indicators: {stats['total_indicators']}")


def demo_decision_engine():
    """Demonstrate unified decision making"""
    print("\n" + "="*70)
    print("DEMO 6: Blocking Decision Engine (Integration)")
    print("="*70)
    
    # Initialize all engines
    reputation = ReputationEngine()
    geoip = GeoIPFilter()
    categories = CategoryBlocker()
    threat_intel = ThreatIntelligence()
    
    # Create decision engine
    decision_engine = BlockingDecisionEngine(
        reputation_engine=reputation,
        geoip_filter=geoip,
        category_blocker=categories,
        threat_intel=threat_intel,
        policy_mode=PolicyMode.BALANCED
    )
    
    print("\n⚙️  Decision Engine Configured:")
    print(f"  Policy Mode: {decision_engine.policy_mode.name}")
    print(f"  Reputation Threshold: {decision_engine._reputation_threshold}")
    print(f"  Threat Level Threshold: {decision_engine._threat_level_threshold.name}")
    
    # Configure engines
    reputation.whitelist_ip("8.8.8.8")
    geoip.blacklist_country("KP")
    categories.block_category(ContentCategory.MALWARE)
    threat_intel.add_indicator(
        "evil.com", "domain", ThreatLevel.CRITICAL,
        [ThreatType.MALWARE], "demo_feed"
    )
    
    # Simulate reputation incidents
    reputation.record_incident("203.0.113.50", IncidentType.MALWARE, 'ip')
    reputation.record_incident("203.0.113.50", IncidentType.PHISHING, 'ip')
    
    # Test connections
    print("\n🔍 Evaluating Connections:")
    
    test_connections = [
        {
            'src_ip': '8.8.8.8',
            'domain': 'google.com',
            'description': 'Trusted IP to legitimate domain'
        },
        {
            'src_ip': '203.0.113.50',
            'domain': 'example.com',
            'description': 'Low reputation IP'
        },
        {
            'src_ip': '192.0.2.1',
            'domain': 'evil.com',
            'description': 'IP to known malicious domain'
        },
        {
            'src_ip': '198.51.100.1',
            'domain': 'malware-download.com',
            'description': 'IP to malware category domain'
        },
    ]
    
    for conn in test_connections:
        print(f"\n  📡 Connection: {conn['src_ip']} → {conn['domain']}")
        print(f"     {conn['description']}")
        
        decision = decision_engine.evaluate_connection(
            src_ip=conn['src_ip'],
            domain=conn['domain']
        )
        
        if decision.is_blocked:
            print(f"     🚫 BLOCKED")
            print(f"     Reasons: {', '.join(decision.reasons)}")
            print(f"     Sources: {', '.join(decision.sources)}")
        else:
            print(f"     ✅ ALLOWED")
    
    # Statistics
    print("\n" + "="*70)
    stats = decision_engine.get_statistics()
    print("📊 Decision Engine Statistics:")
    print(f"  Total decisions: {stats['total_decisions']}")
    print(f"  Blocked: {stats['blocked']}")
    print(f"  Allowed: {stats['allowed']}")
    print(f"  Block rate: {stats['block_rate']:.1f}%")
    
    print("\n📊 Component Statistics:")
    status = decision_engine.get_status()
    print(f"  Reputation - IPs tracked: {status['reputation']['total_ips_tracked']}")
    print(f"  Reputation - Incidents: {status['reputation']['total_incidents']}")
    print(f"  Categories - Domains cached: {status['categories']['cached_domains']}")
    print(f"  Threat Intel - Indicators: {status['threat_intel']['total_indicators']}")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "Enterprise NGFW v2.0" + " "*33 + "║")
    print("║" + " "*10 + "Phase 2 & 3 Demonstration" + " "*32 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        demo_port_filtering()
        time.sleep(1)
        
        demo_reputation_engine()
        time.sleep(1)
        
        demo_geoip_filter()
        time.sleep(1)
        
        demo_category_blocker()
        time.sleep(1)
        
        demo_threat_intelligence()
        time.sleep(1)
        
        demo_decision_engine()
        
        print("\n" + "="*70)
        print("✅ All demos completed successfully!")
        print("="*70)
        
        print("\n💡 Next Steps:")
        print("  1. Review configuration: config/defaults/phase2_3.yaml")
        print("  2. Read documentation: docs/PHASE2_3_GUIDE.md")
        print("  3. Deploy in production with proper privileges")
        print("  4. Monitor logs and statistics")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == '__main__':
    main()
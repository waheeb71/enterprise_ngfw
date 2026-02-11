#!/usr/bin/env python3
"""
Enterprise NGFW - ML Components Test Examples
Demonstrates usage of Phase 5 ML components
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.inference import (
    AnomalyDetector, TrafficFeatures,
    TrafficProfiler, TrafficPattern,
    AdaptivePolicyEngine, PolicyAction
)
from ml.training import ModelTrainer, TrainingConfig, generate_training_data


def test_anomaly_detector():
    """Test anomaly detection"""
    print("\n" + "="*60)
    print("Testing Anomaly Detector")
    print("="*60)
    
    detector = AnomalyDetector(contamination=0.1, n_estimators=100)
    
    # Generate normal traffic features
    print("\n1. Testing normal traffic...")
    normal_features = TrafficFeatures(
        packets_per_second=100,
        bytes_per_second=50000,
        avg_packet_size=500,
        packet_size_variance=100,
        tcp_ratio=0.7,
        udp_ratio=0.3,
        syn_ratio=0.1,
        unique_dst_ports=5,
        unique_src_ports=10,
        inter_arrival_time_mean=0.01,
        inter_arrival_time_variance=0.001,
        failed_connections=0,
        connection_attempts=10,
        reputation_score=80.0
    )
    
    # First detection (before training)
    result = detector.detect(normal_features)
    print(f"   Before training: Anomaly={result.is_anomaly}, Score={result.anomaly_score:.3f}")
    
    # Add more samples to trigger auto-training
    print("\n2. Adding samples for auto-training...")
    for i in range(100):
        features = TrafficFeatures(
            packets_per_second=100 + (i % 50),
            bytes_per_second=50000 + (i % 10000),
            avg_packet_size=500,
            packet_size_variance=100,
            tcp_ratio=0.7,
            udp_ratio=0.3,
            syn_ratio=0.1,
            unique_dst_ports=5,
            unique_src_ports=10,
            inter_arrival_time_mean=0.01,
            inter_arrival_time_variance=0.001,
            failed_connections=0,
            connection_attempts=10,
            reputation_score=80.0
        )
        detector.detect(features)
    
    print(f"   Model trained: {detector.model_trained}")
    
    # Test anomalous traffic (DDoS-like)
    print("\n3. Testing anomalous traffic (DDoS pattern)...")
    anomalous_features = TrafficFeatures(
        packets_per_second=10000,  # Very high
        bytes_per_second=5000000,  # Very high
        avg_packet_size=50,        # Very small (SYN flood)
        packet_size_variance=10,
        tcp_ratio=0.95,
        udp_ratio=0.05,
        syn_ratio=0.9,             # Almost all SYN
        unique_dst_ports=1,        # Single target
        unique_src_ports=5000,     # Many sources
        inter_arrival_time_mean=0.0001,  # Very fast
        inter_arrival_time_variance=0.00001,
        failed_connections=4900,   # Many failed
        connection_attempts=5000,
        reputation_score=20.0      # Low reputation
    )
    
    result = detector.detect(anomalous_features)
    print(f"   After training: Anomaly={result.is_anomaly}, Score={result.anomaly_score:.3f}")
    print(f"   Reason: {result.reason}")
    print(f"   Confidence: {result.confidence:.3f}")
    
    # Get statistics
    stats = detector.get_statistics()
    print(f"\n4. Statistics:")
    print(f"   Total detections: {stats.total_detections}")
    print(f"   Anomalies found: {stats.anomalies_detected}")
    print(f"   Detection rate: {stats.anomaly_rate:.2%}")


def test_traffic_profiler():
    """Test traffic profiling and pattern detection"""
    print("\n" + "="*60)
    print("Testing Traffic Profiler")
    print("="*60)
    
    profiler = TrafficProfiler(time_window=300, max_profiles=10000)
    
    # Test 1: Normal traffic
    print("\n1. Normal traffic profile...")
    pattern, confidence = profiler.profile_connection(
        src_ip="192.168.1.100",
        dst_ip="8.8.8.8",
        dst_port=443,
        protocol="TCP",
        bytes_sent=5000,
        bytes_recv=3000,
        packets_sent=10,
        packets_recv=8,
        duration=1.0
    )
    print(f"   Pattern: {pattern.value}, Confidence: {confidence:.3f}")
    
    # Test 2: Port scanning
    print("\n2. Port scanning pattern...")
    src_ip = "192.168.1.200"
    for port in range(1, 100):  # Scan 100 ports
        profiler.profile_connection(
            src_ip=src_ip,
            dst_ip="10.0.0.50",
            dst_port=port,
            protocol="TCP",
            bytes_sent=64,
            packets_sent=1,
            duration=0.01,
            flags={'SYN'}
        )
    
    pattern, confidence = profiler.profile_connection(
        src_ip=src_ip,
        dst_ip="10.0.0.50",
        dst_port=101,
        protocol="TCP",
        bytes_sent=64,
        packets_sent=1
    )
    print(f"   Pattern: {pattern.value}, Confidence: {confidence:.3f}")
    
    # Get IP profile
    profile = profiler.get_ip_profile(src_ip)
    print(f"   Reputation: {profile.reputation_score:.1f}")
    print(f"   Connections: {profile.total_connections}")
    print(f"   Unique ports: {len(profile.unique_dst_ports)}")
    
    # Test 3: DDoS attack
    print("\n3. DDoS attack pattern...")
    attacker_ip = "203.0.113.45"
    for i in range(2000):  # High rate connections
        profiler.profile_connection(
            src_ip=attacker_ip,
            dst_ip="10.0.0.100",
            dst_port=80,
            protocol="TCP",
            bytes_sent=0,
            packets_sent=1,
            duration=0.001,
            flags={'SYN'}
        )
    
    pattern, confidence = profiler.profile_connection(
        src_ip=attacker_ip,
        dst_ip="10.0.0.100",
        dst_port=80,
        protocol="TCP"
    )
    print(f"   Pattern: {pattern.value}, Confidence: {confidence:.3f}")
    
    # Get low reputation IPs
    print("\n4. Low reputation IPs:")
    low_rep_ips = profiler.get_low_reputation_ips(threshold=60.0)
    for ip, score in low_rep_ips[:5]:
        print(f"   {ip}: {score:.1f}")
    
    # Get statistics
    stats = profiler.get_statistics()
    print(f"\n5. Statistics:")
    print(f"   Total profiles: {stats.total_profiles}")
    print(f"   Scanning detected: {stats.scanning_detected}")
    print(f"   DDoS detected: {stats.ddos_detected}")


def test_adaptive_policy():
    """Test adaptive policy engine"""
    print("\n" + "="*60)
    print("Testing Adaptive Policy Engine")
    print("="*60)
    
    engine = AdaptivePolicyEngine(learning_rate=0.1, adaptation_interval=10)
    
    # Test 1: Normal traffic evaluation
    print("\n1. Evaluating normal traffic...")
    action, confidence, reason = engine.evaluate(
        src_ip="192.168.1.100",
        dst_ip="8.8.8.8",
        dst_port=443,
        protocol="TCP",
        anomaly_score=0.3,
        reputation_score=85.0,
        pattern="normal"
    )
    print(f"   Action: {action.value}, Confidence: {confidence:.3f}")
    print(f"   Reason: {reason}")
    
    # Test 2: High anomaly score
    print("\n2. Evaluating high anomaly traffic...")
    action, confidence, reason = engine.evaluate(
        src_ip="192.168.1.200",
        dst_ip="10.0.0.50",
        dst_port=22,
        protocol="TCP",
        anomaly_score=0.95,
        reputation_score=70.0,
        pattern="suspicious"
    )
    print(f"   Action: {action.value}, Confidence: {confidence:.3f}")
    print(f"   Reason: {reason}")
    
    # Test 3: Attack pattern
    print("\n3. Evaluating attack pattern...")
    action, confidence, reason = engine.evaluate(
        src_ip="203.0.113.45",
        dst_ip="10.0.0.100",
        dst_port=80,
        protocol="TCP",
        anomaly_score=0.85,
        reputation_score=25.0,
        pattern="ddos"
    )
    print(f"   Action: {action.value}, Confidence: {confidence:.3f}")
    print(f"   Reason: {reason}")
    
    # Test 4: Add feedback (simulate multiple threats from same IP)
    print("\n4. Adding feedback for adaptive learning...")
    threat_ip = "198.51.100.23"
    for i in range(10):
        engine.add_feedback(
            src_ip=threat_ip,
            action_taken=PolicyAction.BLOCK,
            was_threat=True,
            threat_type="scanning"
        )
    
    # Wait for adaptation (in real scenario, this happens periodically)
    time.sleep(1)
    engine._perform_adaptation()
    
    # Test 5: Check if dynamic rule was created
    print("\n5. Dynamic rules created:")
    for rule_id, rule in engine.dynamic_rules.items():
        print(f"   {rule_id}: {rule.condition} -> {rule.action.value}")
        print(f"   Priority: {rule.priority}, Confidence: {rule.confidence:.3f}")
    
    # Test 6: Create custom rule
    print("\n6. Creating custom rule...")
    rule_id = engine.create_dynamic_rule(
        condition="dst_port == 23",  # Telnet
        action=PolicyAction.BLOCK,
        priority=150,
        confidence=0.95,
        reason="Insecure protocol"
    )
    print(f"   Created rule: {rule_id}")
    
    # Test 7: Get metrics
    print("\n7. Policy metrics:")
    metrics = engine.get_metrics()
    print(f"   Total adaptations: {metrics.total_adaptations}")
    print(f"   Successful blocks: {metrics.successful_blocks}")
    print(f"   False positives: {metrics.false_positives}")
    print(f"   False negatives: {metrics.false_negatives}")
    print(f"   Accuracy: {metrics.calculate_accuracy():.2%}")


def test_model_trainer():
    """Test offline model training"""
    print("\n" + "="*60)
    print("Testing Model Trainer")
    print("="*60)
    
    trainer = ModelTrainer(model_dir="./models_test")
    
    # Generate training data
    print("\n1. Generating training data...")
    X, y, feature_names = generate_training_data(n_samples=1000)
    print(f"   Generated {X.shape[0]} samples with {X.shape[1]} features")
    print(f"   Classes: Normal={sum(y==0)}, Attack={sum(y==1)}")
    
    # Train anomaly detector
    print("\n2. Training anomaly detector...")
    config = TrainingConfig(
        model_type="isolation_forest",
        n_estimators=100,
        contamination=0.3
    )
    result = trainer.train_anomaly_detector(X, feature_names, config)
    print(f"   Training time: {result.training_time:.2f}s")
    print(f"   Accuracy: {result.accuracy:.4f}")
    
    # Train classifier
    print("\n3. Training classifier...")
    config = TrainingConfig(
        model_type="random_forest",
        n_estimators=100,
        test_size=0.2
    )
    result = trainer.train_classifier(X, y, feature_names, config)
    print(f"   Training time: {result.training_time:.2f}s")
    print(f"   Accuracy: {result.accuracy:.4f}")
    print(f"   Precision: {result.precision:.4f}")
    print(f"   Recall: {result.recall:.4f}")
    print(f"   F1 Score: {result.f1_score:.4f}")
    print(f"   CV Scores: {result.cv_scores}")
    
    # Feature importance
    print("\n4. Top 5 important features:")
    sorted_features = sorted(
        result.feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )
    for feature, importance in sorted_features[:5]:
        print(f"   {feature}: {importance:.4f}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Enterprise NGFW - ML Components Testing")
    print("="*60)
    
    try:
        test_anomaly_detector()
        test_traffic_profiler()
        test_adaptive_policy()
        test_model_trainer()
        
        print("\n" + "="*60)
        print("✓ All tests completed successfully!")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
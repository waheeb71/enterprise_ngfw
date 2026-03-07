"""
Anomaly Detector Module
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
import os
import importlib

logger = logging.getLogger(__name__)

@dataclass
class TrafficFeatures:
    """Features extracted from traffic for analysis"""
    packets_per_second: float
    bytes_per_second: float
    avg_packet_size: float
    packet_size_variance: float
    tcp_ratio: float
    udp_ratio: float
    syn_ratio: float
    unique_dst_ports: int
    unique_src_ports: int
    inter_arrival_time_mean: float
    inter_arrival_time_variance: float
    failed_connections: int
    connection_attempts: int
    reputation_score: float

@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    details: Dict[str, float]

class AnomalyDetector:
    """
    ML-based Anomaly Detector
    """
    
    def __init__(self, contamination: float = 0.1, model_path: Optional[str] = None):
        self.contamination = contamination
        self.model = None
        self.model_type = None
        self.scaler = None # Stub for feature scaling
        logger.info(f"AnomalyDetector initialized with contamination={contamination}")
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def load_model(self, model_path: str):
        """Dynamically load an ONNX, Pickle, or Joblib model"""
        try:
            ext = os.path.splitext(model_path)[1].lower()
            if ext == ".onnx":
                import onnxruntime as ort
                self.model = ort.InferenceSession(model_path)
                self.model_type = "onnx"
                logger.info(f"Loaded ONNX anomaly model from {model_path}")
            elif ext in [".pkl", ".pickle"]:
                import pickle
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.model_type = "sklearn"
                logger.info(f"Loaded Pickle anomaly model from {model_path}")
            elif ext == ".joblib":
                import joblib
                self.model = joblib.load(model_path)
                self.model_type = "sklearn"
                logger.info(f"Loaded Joblib anomaly model from {model_path}")
            else:
                logger.warning(f"Unsupported model extension {ext} for {model_path}")
                
        except ImportError as ie:
            logger.error(f"Missing dependency to load module: {ie}. Install onnxruntime/joblib.")
        except Exception as e:
            logger.error(f"Failed to load anomaly model {model_path}: {e}")

    def _extract_features_array(self, features: TrafficFeatures) -> list:
        """Convert dataclass features to a numerical array suitable for ML"""
        return [
            features.packets_per_second,
            features.bytes_per_second,
            features.avg_packet_size,
            features.packet_size_variance,
            features.tcp_ratio,
            features.udp_ratio,
            features.syn_ratio,
            features.unique_dst_ports,
            features.unique_src_ports,
            features.inter_arrival_time_mean,
            features.inter_arrival_time_variance,
            features.failed_connections,
            features.connection_attempts,
            features.reputation_score
        ]

    def detect(self, features: TrafficFeatures) -> AnomalyResult:
        """
        Detect anomalies in traffic features
        
        Args:
            features: Extracted traffic features
            
        Returns:
            AnomalyResult object
        """
        # If a real model is loaded, use it bridging traffic logic to ML inference
        if self.model:
            try:
                feature_array = self._extract_features_array(features)
                
                # Convert feature list to the correct format and scale if needed
                # Typically requires numpy: import numpy as np; X = np.array([feature_array], dtype=np.float32)
                # Since we want zero dependencies dynamically if possible, we'll try to import numpy
                import numpy as np
                X = np.array([feature_array], dtype=np.float32)
                
                if self.scaler:
                    X = self.scaler.transform(X)

                if self.model_type == "onnx":
                    input_name = self.model.get_inputs()[0].name
                    ort_outs = self.model.run(None, {input_name: X})
                    # ONNX IsolationForest typically outputs: [labels, scores]
                    # labels: 1 for normal, -1 for anomaly (or 0/1 depending on the trained framework)
                    label = ort_outs[0][0]
                    anomaly_score = float(ort_outs[1][0] if len(ort_outs) > 1 else 0.5) 
                    is_anomaly = bool(label == -1 or label == 1) # Specific mapping depends on training config
                    
                elif self.model_type == "sklearn":
                    # scikit-learn IsolationForest/OneClassSVM: 1 for inliers, -1 for outliers
                    label = self.model.predict(X)[0]
                    is_anomaly = bool(label == -1)
                    
                    if hasattr(self.model, "score_samples"):
                        anomaly_score = float(-self.model.score_samples(X)[0]) # Negative implies higher anomaly
                    else:
                        anomaly_score = 0.8 if is_anomaly else 0.1
                
                return AnomalyResult(
                    is_anomaly=is_anomaly,
                    anomaly_score=anomaly_score,
                    confidence=0.9 if is_anomaly else 0.95,
                    details={"ml_confidence": anomaly_score, "model_type": self.model_type}
                )

            except Exception as e:
                logger.error(f"ML Inference failed, falling back to heuristics: {e}")

        # Fallback Heuristics if no model is loaded or if inference fails
        score = 0.0
        # High failure rate or very high packet rate might be anomalous
        score = 0.0
        details = {}
        
        if features.failed_connections > 100:
            score += 0.4
            details['high_failed_connections'] = features.failed_connections
            
        if features.packets_per_second > 10000:
            score += 0.3
            details['high_pps'] = features.packets_per_second
            
        if features.reputation_score < 50:
            score += 0.3
            details['low_reputation'] = features.reputation_score
            
        is_anomaly = score > 0.5
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=score,
            confidence=0.8 if is_anomaly else 0.9,
            details=details
        )


#!/usr/bin/env python3
"""
Enterprise NGFW - ML Model Trainer
Offline training and model optimization
"""

import logging
import pickle
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from pathlib import Path

# ML imports
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Training configuration"""
    model_type: str = "isolation_forest"  # isolation_forest, random_forest
    test_size: float = 0.2
    random_state: int = 42
    n_estimators: int = 100
    contamination: float = 0.1  # For Isolation Forest
    max_depth: Optional[int] = None
    n_jobs: int = -1
    cv_folds: int = 5


@dataclass
class TrainingResult:
    """Training results"""
    model_type: str
    training_time: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cv_scores: List[float]
    confusion_matrix: np.ndarray
    feature_importance: Optional[Dict[str, float]] = None


class ModelTrainer:
    """
    Offline ML model training and optimization
    
    Features:
    - Anomaly detection model training
    - Classification model training
    - Cross-validation
    - Feature importance analysis
    - Model persistence
    """
    
    def __init__(self, model_dir: str = "./models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.scaler = StandardScaler()
        self.current_model = None
        self.feature_names: List[str] = []
        
        logger.info(f"ModelTrainer initialized (model_dir={model_dir})")
    
    def train_anomaly_detector(
        self,
        X: np.ndarray,
        feature_names: List[str],
        config: Optional[TrainingConfig] = None
    ) -> TrainingResult:
        """
        Train an anomaly detection model (Isolation Forest)
        
        Args:
            X: Feature matrix (n_samples, n_features)
            feature_names: Names of features
            config: Training configuration
        
        Returns:
            TrainingResult with metrics
        """
        config = config or TrainingConfig()
        self.feature_names = feature_names
        
        logger.info(f"Training anomaly detector on {X.shape[0]} samples, {X.shape[1]} features")        
        start_time = datetime.now()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        model = IsolationForest(
            n_estimators=config.n_estimators,
            contamination=config.contamination,
            max_samples='auto',
            random_state=config.random_state,
            n_jobs=config.n_jobs
        )
        
        model.fit(X_scaled)
        
        # Predict anomalies
        predictions = model.predict(X_scaled)
        anomaly_scores = model.score_samples(X_scaled)
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Calculate metrics (for anomaly detection, we estimate based on contamination)
        n_anomalies = np.sum(predictions == -1)
        anomaly_ratio = n_anomalies / len(predictions)
        
        logger.info(f"Training complete in {training_time:.2f}s")
        logger.info(f"Detected {n_anomalies} anomalies ({anomaly_ratio:.2%})")
        
        # Save model
        self.current_model = model
        self._save_model(model, "anomaly_detector")
        
        result = TrainingResult(
            model_type="isolation_forest",
            training_time=training_time,
            accuracy=1.0 - abs(anomaly_ratio - config.contamination),
            precision=0.0,  # N/A for unsupervised
            recall=0.0,     # N/A for unsupervised
            f1_score=0.0,   # N/A for unsupervised
            cv_scores=[],   # N/A for unsupervised
            confusion_matrix=np.array([])
        )
        
        return result
    
    def train_classifier(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        config: Optional[TrainingConfig] = None
    ) -> TrainingResult:
        """
        Train a supervised classification model (Random Forest)
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (n_samples,)
            feature_names: Names of features
            config: Training configuration
        
        Returns:
            TrainingResult with comprehensive metrics
        """
        config = config or TrainingConfig()
        self.feature_names = feature_names
        
        logger.info(f"Training classifier on {X.shape[0]} samples, {X.shape[1]} features")
        
        start_time = datetime.now()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y,
            test_size=config.test_size,
            random_state=config.random_state,
            stratify=y
        )
        
        # Train Random Forest
        model = RandomForestClassifier(
            n_estimators=config.n_estimators,
            max_depth=config.max_depth,
            random_state=config.random_state,
            n_jobs=config.n_jobs
        )
        
        model.fit(X_train, y_train)
        
        # Cross-validation
        cv_scores = cross_val_score(
            model, X_train, y_train,
            cv=config.cv_folds,
            n_jobs=config.n_jobs
        )
        
        # Predictions
        y_pred = model.predict(X_test)
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        # Feature importance
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        logger.info(f"Training complete in {training_time:.2f}s")
        logger.info(f"Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
        logger.info(f"CV Scores: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Classification report
        logger.info(f"\n{classification_report(y_test, y_pred)}")
        
        # Save model
        self.current_model = model
        self._save_model(model, "classifier")
        
        result = TrainingResult(
            model_type="random_forest",
            training_time=training_time,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            cv_scores=cv_scores.tolist(),
            confusion_matrix=cm,
            feature_importance=feature_importance
        )
        
        return result
    
    def optimize_hyperparameters(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: Optional[Dict] = None
    ) -> Dict:
        """
        Perform hyperparameter optimization using GridSearchCV
        
        Args:
            X: Feature matrix
            y: Labels
            param_grid: Parameter grid for search
        
        Returns:
            Best parameters
        """
        from sklearn.model_selection import GridSearchCV
        
        if param_grid is None:
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        
        logger.info(f"Starting hyperparameter optimization with {len(param_grid)} parameters")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Create base model
        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
        
        # Grid search
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=5,
            n_jobs=-1,
            verbose=1,
            scoring='f1_weighted'
        )
        
        grid_search.fit(X_scaled, y)
        
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_params_
    
    def load_model(self, model_name: str):
        """Load a saved model"""
        model_path = self.model_dir / f"{model_name}.pkl"
        scaler_path = self.model_dir / f"{model_name}_scaler.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        with open(model_path, 'rb') as f:
            self.current_model = pickle.load(f)
        
        if scaler_path.exists():
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
        
        logger.info(f"Loaded model from {model_path}")
    
    def _save_model(self, model, model_name: str):
        """Save model to disk"""
        model_path = self.model_dir / f"{model_name}.pkl"
        scaler_path = self.model_dir / f"{model_name}_scaler.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        logger.info(f"Model saved to {model_path}")
    
    def evaluate_model(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Evaluate current model on test data
        
        Args:
            X: Test features
            y: Test labels
        
        Returns:
            Evaluation metrics
        """
        if self.current_model is None:
            raise ValueError("No model loaded")
        
        X_scaled = self.scaler.transform(X)
        y_pred = self.current_model.predict(X_scaled)
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y, y_pred, average='weighted', zero_division=0)
        }
        
        logger.info(f"Evaluation metrics: {metrics}")
        
        return metrics


# Example training data generator
def generate_training_data(n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Generate synthetic training data for demonstration
    
    Returns:
        (X, y, feature_names)
    """
    np.random.seed(42)
    
    feature_names = [
        'packets_per_second',
        'bytes_per_second',
        'avg_packet_size',
        'packet_size_variance',
        'tcp_ratio',
        'udp_ratio',
        'syn_ratio',
        'unique_dst_ports',
        'unique_src_ports',
        'inter_arrival_time_mean',
        'inter_arrival_time_variance',
        'failed_connections',
        'connection_attempts',
        'reputation_score'
    ]
    
    # Normal traffic (70%)
    n_normal = int(n_samples * 0.7)
    X_normal = np.random.normal(
        loc=[100, 50000, 500, 100, 0.7, 0.3, 0.1, 5, 10, 0.01, 0.001, 0, 10, 80],
        scale=[20, 10000, 100, 20, 0.1, 0.1, 0.05, 2, 3, 0.005, 0.0005, 0, 3, 10],
        size=(n_normal, len(feature_names))
    )
    y_normal = np.zeros(n_normal)
    
    # Attack traffic (30%)
    n_attack = n_samples - n_normal
    X_attack = np.random.normal(
        loc=[1000, 500000, 100, 500, 0.9, 0.1, 0.8, 50, 50, 0.001, 0.01, 20, 100, 20],
        scale=[200, 100000, 50, 100, 0.05, 0.05, 0.1, 10, 10, 0.0005, 0.005, 5, 20, 10],
        size=(n_attack, len(feature_names))
    )
    y_attack = np.ones(n_attack)
    
    # Combine
    X = np.vstack([X_normal, X_attack])
    y = np.hstack([y_normal, y_attack])
    
    # Shuffle
    indices = np.random.permutation(n_samples)
    X = X[indices]
    y = y[indices]
    
    return X, y, feature_names
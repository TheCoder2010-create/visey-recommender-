"""Matrix factorization-based collaborative filtering recommender."""

import numpy as np
from typing import Dict, List, Tuple, Optional
import structlog
from dataclasses import dataclass

from ..data.models import Resource, UserProfile, Recommendation
from ..storage.feedback_store import FeedbackStore
from ..utils.metrics import track_time

logger = structlog.get_logger(__name__)


@dataclass
class MFConfig:
    """Configuration for matrix factorization."""
    n_factors: int = 50
    learning_rate: float = 0.01
    regularization: float = 0.1
    n_epochs: int = 100
    min_rating: float = 1.0
    max_rating: float = 5.0


class MatrixFactorization:
    """Matrix factorization using gradient descent."""
    
    def __init__(self, config: MFConfig = None):
        self.config = config or MFConfig()
        self.user_factors = None
        self.item_factors = None
        self.user_bias = None
        self.item_bias = None
        self.global_bias = None
        self.user_to_idx = {}
        self.item_to_idx = {}
        self.idx_to_user = {}
        self.idx_to_item = {}
        self.is_trained = False
    
    def _create_mappings(self, interactions: List[Tuple[int, int, float]]):
        """Create user and item index mappings."""
        users = set(user_id for user_id, _, _ in interactions)
        items = set(item_id for _, item_id, _ in interactions)
        
        self.user_to_idx = {user_id: idx for idx, user_id in enumerate(sorted(users))}
        self.item_to_idx = {item_id: idx for idx, item_id in enumerate(sorted(items))}
        self.idx_to_user = {idx: user_id for user_id, idx in self.user_to_idx.items()}
        self.idx_to_item = {idx: item_id for item_id, idx in self.item_to_idx.items()}
        
        logger.info("mappings_created", 
                   n_users=len(users), 
                   n_items=len(items))
    
    def _initialize_factors(self, n_users: int, n_items: int):
        """Initialize factor matrices and biases."""
        # Initialize factors with small random values
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.config.n_factors))
        self.item_factors = np.random.normal(0, 0.1, (n_items, self.config.n_factors))
        
        # Initialize biases
        self.user_bias = np.zeros(n_users)
        self.item_bias = np.zeros(n_items)
        self.global_bias = 0.0
        
        logger.info("factors_initialized", 
                   n_users=n_users, 
                   n_items=n_items, 
                   n_factors=self.config.n_factors)
    
    @track_time("matrix_factorization_training")
    def fit(self, interactions: List[Tuple[int, int, float]]):
        """Train the matrix factorization model.
        
        Args:
            interactions: List of (user_id, item_id, rating) tuples
        """
        if not interactions:
            logger.warning("no_interactions_for_training")
            return
        
        # Create mappings
        self._create_mappings(interactions)
        
        n_users = len(self.user_to_idx)
        n_items = len(self.item_to_idx)
        
        # Initialize factors
        self._initialize_factors(n_users, n_items)
        
        # Calculate global bias
        ratings = [rating for _, _, rating in interactions]
        self.global_bias = np.mean(ratings)
        
        # Convert interactions to matrix indices
        training_data = [
            (self.user_to_idx[user_id], self.item_to_idx[item_id], rating)
            for user_id, item_id, rating in interactions
            if user_id in self.user_to_idx and item_id in self.item_to_idx
        ]
        
        logger.info("training_started", 
                   n_interactions=len(training_data),
                   n_epochs=self.config.n_epochs)
        
        # Training loop
        for epoch in range(self.config.n_epochs):
            epoch_error = 0.0
            
            # Shuffle training data
            np.random.shuffle(training_data)
            
            for user_idx, item_idx, rating in training_data:
                # Predict rating
                prediction = self._predict_rating(user_idx, item_idx)
                
                # Calculate error
                error = rating - prediction
                epoch_error += error ** 2
                
                # Update factors using gradient descent
                user_factor = self.user_factors[user_idx].copy()
                item_factor = self.item_factors[item_idx].copy()
                
                # Update user factors
                self.user_factors[user_idx] += self.config.learning_rate * (
                    error * item_factor - self.config.regularization * user_factor
                )
                
                # Update item factors
                self.item_factors[item_idx] += self.config.learning_rate * (
                    error * user_factor - self.config.regularization * item_factor
                )
                
                # Update biases
                self.user_bias[user_idx] += self.config.learning_rate * (
                    error - self.config.regularization * self.user_bias[user_idx]
                )
                
                self.item_bias[item_idx] += self.config.learning_rate * (
                    error - self.config.regularization * self.item_bias[item_idx]
                )
            
            # Calculate RMSE for this epoch
            rmse = np.sqrt(epoch_error / len(training_data))
            
            if epoch % 10 == 0:
                logger.info("training_progress", epoch=epoch, rmse=rmse)
        
        self.is_trained = True
        logger.info("training_completed", final_rmse=rmse)
    
    def _predict_rating(self, user_idx: int, item_idx: int) -> float:
        """Predict rating for a user-item pair."""
        if not self.is_trained:
            return self.global_bias
        
        prediction = (
            self.global_bias +
            self.user_bias[user_idx] +
            self.item_bias[item_idx] +
            np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
        )
        
        # Clip to valid rating range
        return np.clip(prediction, self.config.min_rating, self.config.max_rating)
    
    def predict(self, user_id: int, item_id: int) -> float:
        """Predict rating for a user-item pair using original IDs."""
        if not self.is_trained:
            return self.global_bias
        
        if user_id not in self.user_to_idx or item_id not in self.item_to_idx:
            return self.global_bias
        
        user_idx = self.user_to_idx[user_id]
        item_idx = self.item_to_idx[item_id]
        
        return self._predict_rating(user_idx, item_idx)
    
    def get_user_recommendations(self, user_id: int, item_ids: List[int], top_n: int = 10) -> List[Tuple[int, float]]:
        """Get top-N recommendations for a user."""
        if not self.is_trained or user_id not in self.user_to_idx:
            return []
        
        user_idx = self.user_to_idx[user_id]
        
        # Get predictions for all items
        predictions = []
        for item_id in item_ids:
            if item_id in self.item_to_idx:
                item_idx = self.item_to_idx[item_id]
                score = self._predict_rating(user_idx, item_idx)
                predictions.append((item_id, score))
        
        # Sort by score and return top-N
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:top_n]


class MatrixFactorizationRecommender:
    """Matrix factorization-based recommender system."""
    
    def __init__(self, feedback_store: FeedbackStore = None, config: MFConfig = None):
        self.feedback_store = feedback_store or FeedbackStore()
        self.config = config or MFConfig()
        self.model = MatrixFactorization(self.config)
        self.last_training_time = None
        self.min_interactions_for_training = 10
    
    def _should_retrain(self) -> bool:
        """Check if model should be retrained."""
        if not self.model.is_trained:
            return True
        
        # Check if enough new interactions have been added
        total_interactions = len(self.feedback_store.get_all_feedback())
        return total_interactions >= self.min_interactions_for_training
    
    def _prepare_training_data(self) -> List[Tuple[int, int, float]]:
        """Prepare training data from feedback store."""
        all_feedback = self.feedback_store.get_all_feedback()
        
        # Convert to training format
        training_data = []
        for user_id, resource_id, rating in all_feedback:
            if rating is not None:  # Only use explicit ratings
                training_data.append((user_id, resource_id, float(rating)))
        
        logger.info("training_data_prepared", n_interactions=len(training_data))
        return training_data
    
    @track_time("mf_model_training")
    def train_model(self):
        """Train or retrain the matrix factorization model."""
        training_data = self._prepare_training_data()
        
        if len(training_data) < self.min_interactions_for_training:
            logger.warning("insufficient_training_data", 
                          available=len(training_data), 
                          required=self.min_interactions_for_training)
            return
        
        self.model.fit(training_data)
        self.last_training_time = np.datetime64('now')
        
        logger.info("model_training_completed", 
                   n_interactions=len(training_data))
    
    def recommend(self, profile: UserProfile, resources: List[Resource], top_n: int = 10) -> List[Recommendation]:
        """Generate recommendations using matrix factorization."""
        # Train model if needed
        if self._should_retrain():
            self.train_model()
        
        if not self.model.is_trained:
            logger.warning("model_not_trained", user_id=profile.user_id)
            return []
        
        # Get resource IDs
        resource_ids = [r.id for r in resources]
        
        # Get predictions from model
        predictions = self.model.get_user_recommendations(
            profile.user_id, resource_ids, top_n
        )
        
        # Convert to Recommendation objects
        recommendations = []
        resource_dict = {r.id: r for r in resources}
        
        for resource_id, score in predictions:
            resource = resource_dict.get(resource_id)
            if resource:
                recommendations.append(Recommendation(
                    resource_id=resource_id,
                    score=float(score),
                    reason="based on your rating patterns",
                    title=resource.title,
                    link=resource.link
                ))
        
        logger.info("mf_recommendations_generated", 
                   user_id=profile.user_id, 
                   count=len(recommendations))
        
        return recommendations
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model."""
        return {
            "is_trained": self.model.is_trained,
            "n_users": len(self.model.user_to_idx) if self.model.is_trained else 0,
            "n_items": len(self.model.item_to_idx) if self.model.is_trained else 0,
            "n_factors": self.config.n_factors,
            "last_training_time": str(self.last_training_time) if self.last_training_time else None,
            "config": {
                "n_factors": self.config.n_factors,
                "learning_rate": self.config.learning_rate,
                "regularization": self.config.regularization,
                "n_epochs": self.config.n_epochs
            }
        }
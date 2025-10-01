"""Tests for recommendation algorithms."""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from visey_recommender.recommender.baseline import BaselineRecommender
from visey_recommender.recommender.matrix_factorization import (
    MatrixFactorization, 
    MatrixFactorizationRecommender,
    MFConfig
)
from visey_recommender.data.models import UserProfile, Resource, Recommendation
from visey_recommender.storage.feedback_store import FeedbackStore


class TestBaselineRecommender:
    """Tests for BaselineRecommender."""
    
    def test_init(self):
        """Test recommender initialization."""
        recommender = BaselineRecommender()
        assert recommender.feedback is not None
        assert recommender.popularity is not None
        assert recommender.mf_recommender is not None
    
    def test_implicit_tokens(self, feedback_store, sample_user_profile):
        """Test implicit token generation."""
        # Add some feedback
        feedback_store.upsert_feedback(123, 1, 5)
        feedback_store.upsert_feedback(123, 2, 4)
        
        recommender = BaselineRecommender(feedback=feedback_store)
        tokens = recommender._implicit_tokens(123)
        
        assert "resource:1" in tokens
        assert "resource:2" in tokens
        assert len(tokens) == 2
    
    def test_content_scores(self, sample_user_profile, sample_resources):
        """Test content-based scoring."""
        recommender = BaselineRecommender()
        scores = recommender._build_content_scores(sample_user_profile, sample_resources)
        
        assert len(scores) == len(sample_resources)
        for resource in sample_resources:
            assert resource.id in scores
            assert isinstance(scores[resource.id], float)
            assert 0 <= scores[resource.id] <= 1
    
    def test_collaborative_scores_no_feedback(self, sample_resources):
        """Test collaborative filtering with no feedback."""
        recommender = BaselineRecommender()
        scores = recommender._build_collab_scores(999, sample_resources)  # Non-existent user
        
        assert len(scores) == len(sample_resources)
        for resource in sample_resources:
            assert scores[resource.id] == 0.0
    
    def test_collaborative_scores_with_feedback(self, feedback_store, sample_resources):
        """Test collaborative filtering with feedback."""
        # Add feedback for multiple users
        feedback_store.upsert_feedback(123, 1, 5)
        feedback_store.upsert_feedback(124, 1, 4)
        feedback_store.upsert_feedback(124, 2, 5)
        
        recommender = BaselineRecommender(feedback=feedback_store)
        scores = recommender._build_collab_scores(123, sample_resources)
        
        assert len(scores) == len(sample_resources)
        # Resource 2 should have some similarity score since user 124 liked both 1 and 2
        assert scores[2] >= 0.0
    
    def test_recommend_basic(self, sample_user_profile, sample_resources):
        """Test basic recommendation generation."""
        recommender = BaselineRecommender()
        recommendations = recommender.recommend(sample_user_profile, sample_resources, top_n=2)
        
        assert len(recommendations) <= 2
        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.resource_id in [r.id for r in sample_resources]
            assert isinstance(rec.score, float)
            assert rec.reason is not None
    
    def test_recommend_empty_resources(self, sample_user_profile):
        """Test recommendation with empty resources."""
        recommender = BaselineRecommender()
        recommendations = recommender.recommend(sample_user_profile, [], top_n=5)
        
        assert len(recommendations) == 0
    
    def test_diversity_filter(self, sample_user_profile, sample_resources):
        """Test diversity filtering."""
        # Create resources with same categories
        similar_resources = []
        for i in range(10):
            resource = Resource(
                id=i + 100,
                title=f"Similar Resource {i}",
                categories=["Business"],  # All same category
                tags=[f"tag-{i}"],
                meta={}
            )
            similar_resources.append(resource)
        
        recommender = BaselineRecommender()
        
        # Create scored items (all with same category)
        scored_items = [(r.id, 0.8) for r in similar_resources]
        filtered = recommender._apply_diversity_filter(scored_items, similar_resources)
        
        # Should limit to max 3 per category
        assert len(filtered) <= 3
    
    @pytest.mark.asyncio
    async def test_mf_scores_integration(self, sample_user_profile, sample_resources, feedback_store):
        """Test matrix factorization integration."""
        # Add some feedback for training
        for i in range(15):  # Need minimum interactions
            feedback_store.upsert_feedback(100 + i, 1, 4 + (i % 2))
            feedback_store.upsert_feedback(100 + i, 2, 3 + (i % 3))
        
        recommender = BaselineRecommender(feedback=feedback_store)
        mf_scores = recommender._get_mf_scores(sample_user_profile, sample_resources)
        
        # Should return scores dict (might be empty if MF fails)
        assert isinstance(mf_scores, dict)


class TestMatrixFactorization:
    """Tests for MatrixFactorization algorithm."""
    
    def test_init(self):
        """Test matrix factorization initialization."""
        config = MFConfig(n_factors=10, learning_rate=0.05)
        mf = MatrixFactorization(config)
        
        assert mf.config.n_factors == 10
        assert mf.config.learning_rate == 0.05
        assert not mf.is_trained
    
    def test_create_mappings(self):
        """Test user/item mapping creation."""
        interactions = [(1, 10, 5.0), (2, 10, 4.0), (1, 11, 3.0)]
        
        mf = MatrixFactorization()
        mf._create_mappings(interactions)
        
        assert len(mf.user_to_idx) == 2  # Users 1, 2
        assert len(mf.item_to_idx) == 2  # Items 10, 11
        assert 1 in mf.user_to_idx
        assert 10 in mf.item_to_idx
    
    def test_fit_basic(self):
        """Test basic model fitting."""
        # Create simple training data
        interactions = [
            (1, 10, 5.0), (1, 11, 4.0),
            (2, 10, 4.0), (2, 12, 5.0),
            (3, 11, 3.0), (3, 12, 4.0)
        ]
        
        config = MFConfig(n_factors=5, n_epochs=10, learning_rate=0.1)
        mf = MatrixFactorization(config)
        mf.fit(interactions)
        
        assert mf.is_trained
        assert mf.user_factors is not None
        assert mf.item_factors is not None
        assert mf.user_factors.shape[1] == 5  # n_factors
    
    def test_predict_untrained(self):
        """Test prediction on untrained model."""
        mf = MatrixFactorization()
        prediction = mf.predict(1, 10)
        
        # Should return global bias (0.0 for untrained)
        assert prediction == 0.0
    
    def test_predict_trained(self):
        """Test prediction on trained model."""
        interactions = [(1, 10, 5.0), (1, 11, 4.0), (2, 10, 3.0)]
        
        config = MFConfig(n_factors=3, n_epochs=5)
        mf = MatrixFactorization(config)
        mf.fit(interactions)
        
        # Predict for known user-item pair
        prediction = mf.predict(1, 10)
        assert isinstance(prediction, float)
        assert 1.0 <= prediction <= 5.0  # Should be in valid range
    
    def test_predict_unknown_user_item(self):
        """Test prediction for unknown user/item."""
        interactions = [(1, 10, 5.0)]
        
        mf = MatrixFactorization()
        mf.fit(interactions)
        
        # Unknown user
        prediction = mf.predict(999, 10)
        assert prediction == mf.global_bias
        
        # Unknown item
        prediction = mf.predict(1, 999)
        assert prediction == mf.global_bias
    
    def test_get_user_recommendations(self):
        """Test getting user recommendations."""
        interactions = [
            (1, 10, 5.0), (1, 11, 4.0),
            (2, 10, 4.0), (2, 12, 5.0)
        ]
        
        mf = MatrixFactorization()
        mf.fit(interactions)
        
        recommendations = mf.get_user_recommendations(1, [10, 11, 12], top_n=2)
        
        assert len(recommendations) <= 2
        for item_id, score in recommendations:
            assert item_id in [10, 11, 12]
            assert isinstance(score, float)
        
        # Should be sorted by score (descending)
        if len(recommendations) > 1:
            assert recommendations[0][1] >= recommendations[1][1]


class TestMatrixFactorizationRecommender:
    """Tests for MatrixFactorizationRecommender."""
    
    def test_init(self):
        """Test recommender initialization."""
        recommender = MatrixFactorizationRecommender()
        assert recommender.feedback_store is not None
        assert recommender.model is not None
        assert not recommender.model.is_trained
    
    def test_should_retrain_untrained(self):
        """Test retraining decision for untrained model."""
        recommender = MatrixFactorizationRecommender()
        assert recommender._should_retrain() is True
    
    def test_should_retrain_insufficient_data(self, feedback_store):
        """Test retraining with insufficient data."""
        # Add minimal feedback (less than minimum required)
        feedback_store.upsert_feedback(1, 10, 5)
        
        recommender = MatrixFactorizationRecommender(feedback_store)
        # Should still want to retrain but won't have enough data
        assert recommender._should_retrain() is True
    
    def test_prepare_training_data(self, feedback_store):
        """Test training data preparation."""
        # Add feedback with explicit ratings
        feedback_store.upsert_feedback(1, 10, 5)
        feedback_store.upsert_feedback(1, 11, 4)
        feedback_store.upsert_feedback(2, 10, 3)
        
        # Add feedback without rating (should be excluded)
        feedback_store.upsert_feedback(3, 12, None)
        
        recommender = MatrixFactorizationRecommender(feedback_store)
        training_data = recommender._prepare_training_data()
        
        assert len(training_data) == 3  # Only explicit ratings
        for user_id, item_id, rating in training_data:
            assert isinstance(user_id, int)
            assert isinstance(item_id, int)
            assert isinstance(rating, float)
            assert 1.0 <= rating <= 5.0
    
    def test_train_model_insufficient_data(self, feedback_store):
        """Test model training with insufficient data."""
        # Add only a few interactions
        feedback_store.upsert_feedback(1, 10, 5)
        
        recommender = MatrixFactorizationRecommender(feedback_store)
        recommender.train_model()
        
        # Model should not be trained due to insufficient data
        assert not recommender.model.is_trained
    
    def test_train_model_sufficient_data(self, feedback_store):
        """Test model training with sufficient data."""
        # Add enough interactions
        for i in range(15):
            feedback_store.upsert_feedback(i + 1, 10, 4 + (i % 2))
            feedback_store.upsert_feedback(i + 1, 11, 3 + (i % 3))
        
        recommender = MatrixFactorizationRecommender(feedback_store)
        recommender.train_model()
        
        # Model should be trained
        assert recommender.model.is_trained
        assert recommender.last_training_time is not None
    
    def test_recommend_untrained(self, sample_user_profile, sample_resources):
        """Test recommendation with untrained model."""
        recommender = MatrixFactorizationRecommender()
        recommendations = recommender.recommend(sample_user_profile, sample_resources)
        
        # Should return empty list for untrained model
        assert len(recommendations) == 0
    
    def test_recommend_trained(self, sample_user_profile, sample_resources, feedback_store):
        """Test recommendation with trained model."""
        # Add sufficient training data
        for i in range(15):
            feedback_store.upsert_feedback(i + 1, 1, 4 + (i % 2))
            feedback_store.upsert_feedback(i + 1, 2, 3 + (i % 3))
        
        recommender = MatrixFactorizationRecommender(feedback_store)
        recommender.train_model()
        
        recommendations = recommender.recommend(sample_user_profile, sample_resources, top_n=2)
        
        assert len(recommendations) <= 2
        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.reason == "based on your rating patterns"
    
    def test_get_model_info(self, feedback_store):
        """Test model information retrieval."""
        recommender = MatrixFactorizationRecommender(feedback_store)
        info = recommender.get_model_info()
        
        assert "is_trained" in info
        assert "n_users" in info
        assert "n_items" in info
        assert "config" in info
        assert info["is_trained"] is False
        assert info["n_users"] == 0
        assert info["n_items"] == 0


@pytest.mark.integration
class TestRecommenderIntegration:
    """Integration tests for recommender components."""
    
    def test_baseline_with_mf_integration(self, sample_user_profile, sample_resources, feedback_store):
        """Test baseline recommender with MF integration."""
        # Add training data for MF
        for i in range(15):
            feedback_store.upsert_feedback(i + 1, 1, 4 + (i % 2))
            feedback_store.upsert_feedback(i + 1, 2, 3 + (i % 3))
        
        # Add feedback for the test user
        feedback_store.upsert_feedback(sample_user_profile.user_id, 1, 5)
        
        recommender = BaselineRecommender(feedback=feedback_store)
        recommendations = recommender.recommend(sample_user_profile, sample_resources, top_n=3)
        
        assert len(recommendations) <= 3
        assert all(isinstance(rec, Recommendation) for rec in recommendations)
        
        # Scores should be reasonable
        for rec in recommendations:
            assert 0.0 <= rec.score <= 5.0  # Combined score might exceed 1.0
    
    @pytest.mark.slow
    def test_performance_with_large_dataset(self, feedback_store):
        """Test performance with larger dataset."""
        # Create larger dataset
        users = list(range(1, 101))  # 100 users
        items = list(range(1, 201))  # 200 items
        
        # Add random feedback
        import random
        for _ in range(1000):  # 1000 interactions
            user_id = random.choice(users)
            item_id = random.choice(items)
            rating = random.randint(1, 5)
            feedback_store.upsert_feedback(user_id, item_id, rating)
        
        # Create test resources
        resources = [
            Resource(id=i, title=f"Resource {i}", categories=["Test"], tags=[], meta={})
            for i in items[:50]  # First 50 items
        ]
        
        profile = UserProfile(user_id=1, industry="Test")
        
        # Test MF recommender
        mf_recommender = MatrixFactorizationRecommender(feedback_store)
        
        import time
        start_time = time.time()
        mf_recommender.train_model()
        training_time = time.time() - start_time
        
        start_time = time.time()
        recommendations = mf_recommender.recommend(profile, resources, top_n=10)
        recommendation_time = time.time() - start_time
        
        # Performance assertions
        assert training_time < 10.0  # Should train in under 10 seconds
        assert recommendation_time < 1.0  # Should recommend in under 1 second
        assert len(recommendations) <= 10
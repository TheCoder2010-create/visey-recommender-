"""Tests for API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from visey_recommender.api.main import app


class TestRecommendEndpoint:
    """Tests for the /recommend endpoint."""
    
    def test_recommend_success(self, client: TestClient, mock_wp_client):
        """Test successful recommendation request."""
        with patch('visey_recommender.api.main.wp', mock_wp_client):
            response = client.get("/recommend?user_id=123")
            
            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            assert "items" in data
            assert data["user_id"] == 123
            assert isinstance(data["items"], list)
    
    def test_recommend_missing_wp_url(self, client: TestClient):
        """Test recommendation request with missing WordPress URL."""
        with patch('visey_recommender.config.settings.WP_BASE_URL', ''):
            response = client.get("/recommend?user_id=123")
            
            assert response.status_code == 500
            assert "WP_BASE_URL not configured" in response.json()["detail"]
    
    def test_recommend_invalid_user_id(self, client: TestClient):
        """Test recommendation request with invalid user ID."""
        response = client.get("/recommend?user_id=0")
        assert response.status_code == 422
        
        response = client.get("/recommend?user_id=-1")
        assert response.status_code == 422
        
        response = client.get("/recommend?user_id=abc")
        assert response.status_code == 422
    
    def test_recommend_with_top_n(self, client: TestClient, mock_wp_client):
        """Test recommendation request with top_n parameter."""
        with patch('visey_recommender.api.main.wp', mock_wp_client):
            response = client.get("/recommend?user_id=123&top_n=5")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) <= 5
    
    def test_recommend_invalid_top_n(self, client: TestClient):
        """Test recommendation request with invalid top_n parameter."""
        response = client.get("/recommend?user_id=123&top_n=0")
        assert response.status_code == 422
        
        response = client.get("/recommend?user_id=123&top_n=101")
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_recommend_wp_client_error(self, client: TestClient):
        """Test recommendation request when WordPress client fails."""
        mock_wp = AsyncMock()
        mock_wp.fetch_user_profile.side_effect = Exception("WordPress API error")
        
        with patch('visey_recommender.api.main.wp', mock_wp):
            response = client.get("/recommend?user_id=123")
            assert response.status_code == 500


class TestFeedbackEndpoint:
    """Tests for the /feedback endpoint."""
    
    def test_feedback_success(self, client: TestClient):
        """Test successful feedback submission."""
        response = client.post("/feedback?user_id=123&resource_id=456&rating=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
    
    def test_feedback_without_rating(self, client: TestClient):
        """Test feedback submission without rating."""
        response = client.post("/feedback?user_id=123&resource_id=456")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
    
    def test_feedback_invalid_rating(self, client: TestClient):
        """Test feedback submission with invalid rating."""
        response = client.post("/feedback?user_id=123&resource_id=456&rating=0")
        assert response.status_code == 400
        assert "rating must be 1-5" in response.json()["detail"]
        
        response = client.post("/feedback?user_id=123&resource_id=456&rating=6")
        assert response.status_code == 400
        assert "rating must be 1-5" in response.json()["detail"]
    
    def test_feedback_invalid_user_id(self, client: TestClient):
        """Test feedback submission with invalid user ID."""
        response = client.post("/feedback?user_id=0&resource_id=456&rating=5")
        assert response.status_code == 422
        
        response = client.post("/feedback?user_id=-1&resource_id=456&rating=5")
        assert response.status_code == 422
    
    def test_feedback_invalid_resource_id(self, client: TestClient):
        """Test feedback submission with invalid resource ID."""
        response = client.post("/feedback?user_id=123&resource_id=0&rating=5")
        assert response.status_code == 422
        
        response = client.post("/feedback?user_id=123&resource_id=-1&rating=5")
        assert response.status_code == 422
    
    def test_feedback_missing_parameters(self, client: TestClient):
        """Test feedback submission with missing required parameters."""
        response = client.post("/feedback?resource_id=456&rating=5")
        assert response.status_code == 422
        
        response = client.post("/feedback?user_id=123&rating=5")
        assert response.status_code == 422


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_endpoint_exists(self, client: TestClient):
        """Test that health endpoint is accessible."""
        # This test will pass once we add the health endpoint to the API
        pass
    
    def test_metrics_endpoint_exists(self, client: TestClient):
        """Test that metrics endpoint is accessible."""
        # This test will pass once we add the metrics endpoint to the API
        pass


class TestRateLimiting:
    """Tests for rate limiting functionality."""
    
    def test_rate_limit_not_exceeded(self, client: TestClient, mock_wp_client):
        """Test that normal usage doesn't trigger rate limits."""
        with patch('visey_recommender.api.main.wp', mock_wp_client):
            # Make a few requests that should be within limits
            for _ in range(5):
                response = client.get("/recommend?user_id=123")
                assert response.status_code == 200
    
    def test_rate_limit_headers(self, client: TestClient, mock_wp_client):
        """Test that rate limit headers are present."""
        with patch('visey_recommender.api.main.wp', mock_wp_client):
            response = client.get("/recommend?user_id=123")
            # Once we implement rate limiting middleware, check for headers
            # assert "X-RateLimit-Remaining" in response.headers
            pass


class TestErrorHandling:
    """Tests for error handling and responses."""
    
    def test_404_for_unknown_endpoint(self, client: TestClient):
        """Test 404 response for unknown endpoints."""
        response = client.get("/unknown-endpoint")
        assert response.status_code == 404
    
    def test_405_for_wrong_method(self, client: TestClient):
        """Test 405 response for wrong HTTP method."""
        response = client.post("/recommend?user_id=123")
        assert response.status_code == 405
        
        response = client.get("/feedback?user_id=123&resource_id=456")
        assert response.status_code == 405
    
    def test_422_for_validation_errors(self, client: TestClient):
        """Test 422 response for validation errors."""
        response = client.get("/recommend")  # Missing user_id
        assert response.status_code == 422
        
        response = client.post("/feedback")  # Missing parameters
        assert response.status_code == 422
"""Tests for input validation utilities."""

import pytest
from fastapi import HTTPException

from visey_recommender.utils.validation import (
    UserProfileValidator,
    ResourceValidator,
    RecommendationRequestValidator,
    FeedbackRequestValidator,
    validate_request_data,
    sanitize_string,
    comprehensive_security_check
)


class TestUserProfileValidator:
    """Tests for UserProfileValidator."""
    
    def test_valid_profile(self):
        """Test validation of valid user profile."""
        data = {
            "user_id": 123,
            "industry": "Technology",
            "stage": "Growth",
            "team_size": "10-50",
            "funding": "Series A",
            "location": "San Francisco"
        }
        
        validator = UserProfileValidator(**data)
        assert validator.user_id == 123
        assert validator.industry == "Technology"
    
    def test_invalid_user_id(self):
        """Test validation with invalid user ID."""
        with pytest.raises(ValueError):
            UserProfileValidator(user_id=0)
        
        with pytest.raises(ValueError):
            UserProfileValidator(user_id=-1)
    
    def test_malicious_content_detection(self):
        """Test detection of potentially malicious content."""
        with pytest.raises(ValueError):
            UserProfileValidator(
                user_id=123,
                industry="<script>alert('xss')</script>"
            )
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        validator = UserProfileValidator(
            user_id=123,
            industry="  Technology   "
        )
        assert validator.industry == "Technology"


class TestResourceValidator:
    """Tests for ResourceValidator."""
    
    def test_valid_resource(self):
        """Test validation of valid resource."""
        data = {
            "id": 1,
            "title": "Test Resource",
            "link": "https://example.com/resource",
            "excerpt": "This is a test resource",
            "categories": ["Business", "Technology"],
            "tags": ["test", "resource"],
            "meta": {"difficulty": "beginner"}
        }
        
        validator = ResourceValidator(**data)
        assert validator.id == 1
        assert validator.title == "Test Resource"
    
    def test_invalid_url(self):
        """Test validation with invalid URL."""
        with pytest.raises(ValueError):
            ResourceValidator(
                id=1,
                link="not-a-valid-url"
            )
    
    def test_malicious_script_detection(self):
        """Test detection of malicious scripts."""
        with pytest.raises(ValueError):
            ResourceValidator(
                id=1,
                title="<script>alert('xss')</script>"
            )
    
    def test_categories_validation(self):
        """Test categories list validation."""
        validator = ResourceValidator(
            id=1,
            categories=["Valid Category", "", "Another Valid"]
        )
        # Empty strings should be filtered out
        assert len(validator.categories) == 2


class TestRequestValidators:
    """Tests for request validators."""
    
    def test_recommendation_request_valid(self):
        """Test valid recommendation request."""
        data = {"user_id": 123, "top_n": 10}
        validator = RecommendationRequestValidator(**data)
        assert validator.user_id == 123
        assert validator.top_n == 10
    
    def test_recommendation_request_invalid_top_n(self):
        """Test invalid top_n values."""
        with pytest.raises(ValueError):
            RecommendationRequestValidator(user_id=123, top_n=0)
        
        with pytest.raises(ValueError):
            RecommendationRequestValidator(user_id=123, top_n=101)
    
    def test_feedback_request_valid(self):
        """Test valid feedback request."""
        data = {"user_id": 123, "resource_id": 456, "rating": 5}
        validator = FeedbackRequestValidator(**data)
        assert validator.user_id == 123
        assert validator.resource_id == 456
        assert validator.rating == 5
    
    def test_feedback_request_invalid_rating(self):
        """Test invalid rating values."""
        with pytest.raises(ValueError):
            FeedbackRequestValidator(user_id=123, resource_id=456, rating=0)
        
        with pytest.raises(ValueError):
            FeedbackRequestValidator(user_id=123, resource_id=456, rating=6)


class TestValidationHelpers:
    """Tests for validation helper functions."""
    
    def test_validate_request_data_success(self):
        """Test successful request data validation."""
        data = {"user_id": 123, "top_n": 10}
        result = validate_request_data(data, RecommendationRequestValidator)
        assert result["user_id"] == 123
        assert result["top_n"] == 10
    
    def test_validate_request_data_failure(self):
        """Test failed request data validation."""
        data = {"user_id": 0, "top_n": 10}  # Invalid user_id
        with pytest.raises(HTTPException) as exc_info:
            validate_request_data(data, RecommendationRequestValidator)
        assert exc_info.value.status_code == 422
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        # Test whitespace normalization
        result = sanitize_string("  hello   world  ")
        assert result == "hello world"
        
        # Test script removal
        result = sanitize_string("<script>alert('xss')</script>hello")
        assert "script" not in result.lower()
        assert "hello" in result
        
        # Test length truncation
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) <= 100
    
    def test_comprehensive_security_check(self):
        """Test comprehensive security validation."""
        # Safe string
        assert comprehensive_security_check("hello world") is True
        
        # SQL injection attempt
        assert comprehensive_security_check("'; DROP TABLE users; --") is False
        
        # XSS attempt
        assert comprehensive_security_check("<script>alert('xss')</script>") is False
        
        # Path traversal attempt
        assert comprehensive_security_check("../../../etc/passwd") is False
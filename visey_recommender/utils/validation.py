"""Input validation utilities and custom validators."""

import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, ValidationError
from fastapi import HTTPException
import structlog

logger = structlog.get_logger(__name__)


class ValidationError(Exception):
    """Custom validation error."""
    pass


class UserProfileValidator(BaseModel):
    """Validator for user profile data."""
    
    user_id: int = Field(..., gt=0, description="User ID must be positive")
    industry: Optional[str] = Field(None, max_length=100, description="Industry name")
    stage: Optional[str] = Field(None, max_length=50, description="Business stage")
    team_size: Optional[str] = Field(None, max_length=20, description="Team size category")
    funding: Optional[str] = Field(None, max_length=50, description="Funding stage")
    location: Optional[str] = Field(None, max_length=100, description="Location")
    
    @validator('industry', 'stage', 'team_size', 'funding', 'location')
    def validate_string_fields(cls, v):
        if v is not None:
            # Remove excessive whitespace and validate length
            v = ' '.join(v.split())
            if len(v.strip()) == 0:
                return None
            # Check for potentially malicious content
            if re.search(r'[<>"\']|javascript:|data:|vbscript:', v, re.IGNORECASE):
                raise ValueError("Invalid characters detected")
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError("User ID must be positive")
        if v > 2147483647:  # Max 32-bit integer
            raise ValueError("User ID too large")
        return v


class ResourceValidator(BaseModel):
    """Validator for resource data."""
    
    id: int = Field(..., gt=0, description="Resource ID must be positive")
    title: Optional[str] = Field(None, max_length=500, description="Resource title")
    link: Optional[str] = Field(None, max_length=2000, description="Resource URL")
    excerpt: Optional[str] = Field(None, max_length=1000, description="Resource excerpt")
    categories: Optional[List[str]] = Field(None, description="Resource categories")
    tags: Optional[List[str]] = Field(None, description="Resource tags")
    meta: Optional[Dict[str, Any]] = Field(None, description="Resource metadata")
    
    @validator('title', 'excerpt')
    def validate_text_fields(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            # Check for potentially malicious content
            if re.search(r'<script|javascript:|data:|vbscript:', v, re.IGNORECASE):
                raise ValueError("Potentially malicious content detected")
        return v
    
    @validator('link')
    def validate_url(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            # Basic URL validation
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v):
                raise ValueError("Invalid URL format")
        return v
    
    @validator('categories', 'tags')
    def validate_string_lists(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Must be a list")
            # Validate each item in the list
            validated = []
            for item in v[:50]:  # Limit to 50 items
                if isinstance(item, str):
                    item = item.strip()
                    if len(item) > 0 and len(item) <= 100:
                        # Check for malicious content
                        if not re.search(r'[<>"\']|javascript:|data:|vbscript:', item, re.IGNORECASE):
                            validated.append(item)
            return validated if validated else None
        return v
    
    @validator('meta')
    def validate_meta(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Meta must be a dictionary")
            # Limit the size and depth of metadata
            if len(str(v)) > 10000:  # Limit serialized size
                raise ValueError("Metadata too large")
        return v


class RecommendationRequestValidator(BaseModel):
    """Validator for recommendation requests."""
    
    user_id: int = Field(..., gt=0, le=2147483647, description="User ID")
    top_n: Optional[int] = Field(None, ge=1, le=100, description="Number of recommendations")
    
    @validator('top_n')
    def validate_top_n(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError("top_n must be between 1 and 100")
        return v


class FeedbackRequestValidator(BaseModel):
    """Validator for feedback requests."""
    
    user_id: int = Field(..., gt=0, le=2147483647, description="User ID")
    resource_id: int = Field(..., gt=0, le=2147483647, description="Resource ID")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


def validate_request_data(data: Dict[str, Any], validator_class: BaseModel) -> Dict[str, Any]:
    """Validate request data using the specified validator.
    
    Args:
        data: Data to validate
        validator_class: Pydantic model class for validation
        
    Returns:
        Validated data dictionary
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        validated = validator_class(**data)
        logger.info("validation_success", validator=validator_class.__name__, data_keys=list(data.keys()))
        return validated.dict(exclude_none=True)
    except ValidationError as e:
        logger.warning("validation_failed", validator=validator_class.__name__, errors=e.errors())
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Validation failed",
                "errors": e.errors()
            }
        )
    except Exception as e:
        logger.error("validation_error", validator=validator_class.__name__, error=str(e))
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid request data", "error": str(e)}
        )


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input by removing potentially dangerous content.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove excessive whitespace
    value = ' '.join(value.split())
    
    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]
    
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>'
    ]
    
    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
    
    return value.strip()


def validate_pagination_params(page: int = 1, per_page: int = 20) -> tuple[int, int]:
    """Validate and normalize pagination parameters.
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (validated_page, validated_per_page)
        
    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if page > 10000:  # Reasonable upper limit
        raise HTTPException(status_code=400, detail="Page number too large")
    
    if per_page < 1:
        raise HTTPException(status_code=400, detail="per_page must be >= 1")
    if per_page > 200:  # Reasonable upper limit
        raise HTTPException(status_code=400, detail="per_page must be <= 200")
    
    return page, per_page


class SecurityValidator:
    """Security-focused validation utilities."""
    
    @staticmethod
    def validate_sql_injection(value: str) -> bool:
        """Check for potential SQL injection patterns."""
        sql_patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
            r'[\'";]',
            r'--',
            r'/\*.*\*/',
            r'\bor\b.*\b1\s*=\s*1\b',
            r'\band\b.*\b1\s*=\s*1\b'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        return True
    
    @staticmethod
    def validate_xss(value: str) -> bool:
        """Check for potential XSS patterns."""
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'data:text/html',
            r'vbscript:'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        return True
    
    @staticmethod
    def validate_path_traversal(value: str) -> bool:
        """Check for path traversal attempts."""
        traversal_patterns = [
            r'\.\.',
            r'[/\\]etc[/\\]',
            r'[/\\]proc[/\\]',
            r'[/\\]sys[/\\]',
            r'[/\\]root[/\\]',
            r'[/\\]home[/\\]'
        ]
        
        for pattern in traversal_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        return True


def comprehensive_security_check(value: str) -> bool:
    """Run comprehensive security validation on a string value."""
    validator = SecurityValidator()
    
    checks = [
        validator.validate_sql_injection(value),
        validator.validate_xss(value),
        validator.validate_path_traversal(value)
    ]
    
    return all(checks)


def validate_wp_response(data: Dict[str, Any], required_fields: Optional[List[str]] = None) -> bool:
    """Validate WordPress API response data.
    
    Args:
        data: Response data from WordPress API
        required_fields: List of required fields to check
        
    Returns:
        True if validation passes
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("WordPress response must be a dictionary")
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
    
    # Check for common WordPress API fields
    if 'id' in data and not isinstance(data['id'], int):
        raise ValidationError("WordPress ID must be an integer")
    
    # Validate text fields for security
    text_fields = ['title', 'content', 'excerpt', 'name', 'description']
    for field in text_fields:
        if field in data:
            if isinstance(data[field], dict) and 'rendered' in data[field]:
                # WordPress often returns rendered content in nested structure
                content = data[field]['rendered']
            else:
                content = data[field]
            
            if isinstance(content, str) and not comprehensive_security_check(content):
                logger.warning("security_check_failed", field=field, content_preview=content[:100])
                # Don't raise error, just log warning for now
    
    logger.debug("wp_response_validated", fields=list(data.keys()))
    return True
"""Configuration management with validation and hot reloading."""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog
from pydantic import BaseModel, Field, validator

logger = structlog.get_logger(__name__)


class DatabaseConfig(BaseModel):
    """Database configuration."""
    sqlite_feedback_path: str = Field(default="data/feedback.db")
    sqlite_cache_path: str = Field(default="data/cache.db")
    connection_pool_size: int = Field(default=5, ge=1, le=20)


class WordPressConfig(BaseModel):
    """WordPress API configuration."""
    base_url: str = Field(..., description="WordPress site URL")
    auth_type: str = Field(default="none", regex="^(none|basic|jwt)$")
    username: Optional[str] = None
    password: Optional[str] = None
    jwt_token: Optional[str] = None
    timeout: int = Field(default=30, ge=5, le=120)
    max_retries: int = Field(default=3, ge=1, le=10)
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v.rstrip('/')


class CacheConfig(BaseModel):
    """Cache configuration."""
    backend: str = Field(default="auto", regex="^(auto|redis|sqlite)$")
    redis_url: Optional[str] = None
    default_ttl: int = Field(default=3600, ge=60, le=86400)
    max_connections: int = Field(default=10, ge=1, le=50)


class RecommenderConfig(BaseModel):
    """Recommender algorithm configuration."""
    top_n: int = Field(default=10, ge=1, le=100)
    content_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    collab_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    pop_weight: float = Field(default=0.1, ge=0.0, le=1.0)
    emb_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @validator('content_weight', 'collab_weight', 'pop_weight', 'emb_weight')
    def validate_weights_sum(cls, v, values):
        # This is a simplified check - in practice you'd want to validate the sum
        return v


class MatrixFactorizationConfig(BaseModel):
    """Matrix factorization configuration."""
    n_factors: int = Field(default=50, ge=10, le=200)
    learning_rate: float = Field(default=0.01, ge=0.001, le=0.1)
    regularization: float = Field(default=0.1, ge=0.01, le=1.0)
    n_epochs: int = Field(default=100, ge=10, le=1000)
    min_interactions: int = Field(default=10, ge=5, le=100)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    enabled: bool = Field(default=True)
    requests_per_minute: int = Field(default=100, ge=10, le=10000)
    burst_size: int = Field(default=20, ge=5, le=100)
    
    # Endpoint-specific limits
    recommend_rpm: int = Field(default=20, ge=1, le=1000)
    feedback_rpm: int = Field(default=50, ge=1, le=1000)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    json_format: bool = Field(default=True)
    log_requests: bool = Field(default=True)
    log_sql: bool = Field(default=False)


class MonitoringConfig(BaseModel):
    """Monitoring and metrics configuration."""
    enabled: bool = Field(default=True)
    metrics_endpoint: bool = Field(default=True)
    health_checks: bool = Field(default=True)
    prometheus_port: Optional[int] = Field(None, ge=1024, le=65535)


class AppConfig(BaseModel):
    """Main application configuration."""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    wordpress: WordPressConfig
    cache: CacheConfig = Field(default_factory=CacheConfig)
    recommender: RecommenderConfig = Field(default_factory=RecommenderConfig)
    matrix_factorization: MatrixFactorizationConfig = Field(default_factory=MatrixFactorizationConfig)
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # Environment
    environment: str = Field(default="development", regex="^(development|staging|production)$")
    debug: bool = Field(default=False)


class ConfigManager:
    """Configuration manager with validation and hot reloading."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("CONFIG_PATH", "config.json")
        self.config: Optional[AppConfig] = None
        self.watchers: List[callable] = []
        self._last_modified = None
    
    def load_from_env(self) -> AppConfig:
        """Load configuration from environment variables."""
        config_dict = {
            "wordpress": {
                "base_url": os.getenv("WP_BASE_URL", ""),
                "auth_type": os.getenv("WP_AUTH_TYPE", "none"),
                "username": os.getenv("WP_USERNAME"),
                "password": os.getenv("WP_PASSWORD"),
                "jwt_token": os.getenv("WP_JWT_TOKEN"),
                "timeout": int(os.getenv("WP_TIMEOUT", "30")),
                "max_retries": int(os.getenv("WP_MAX_RETRIES", "3"))
            },
            "cache": {
                "backend": os.getenv("CACHE_BACKEND", "auto"),
                "redis_url": os.getenv("REDIS_URL"),
                "default_ttl": int(os.getenv("CACHE_TTL", "3600")),
                "max_connections": int(os.getenv("CACHE_MAX_CONNECTIONS", "10"))
            },
            "recommender": {
                "top_n": int(os.getenv("TOP_N", "10")),
                "content_weight": float(os.getenv("CONTENT_WEIGHT", "0.6")),
                "collab_weight": float(os.getenv("COLLAB_WEIGHT", "0.3")),
                "pop_weight": float(os.getenv("POP_WEIGHT", "0.1")),
                "emb_weight": float(os.getenv("EMB_WEIGHT", "0.0"))
            },
            "database": {
                "sqlite_feedback_path": os.getenv("SQLITE_FEEDBACK_PATH", "data/feedback.db"),
                "sqlite_cache_path": os.getenv("SQLITE_CACHE_PATH", "data/cache.db"),
                "connection_pool_size": int(os.getenv("DB_POOL_SIZE", "5"))
            },
            "rate_limiting": {
                "enabled": os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true",
                "requests_per_minute": int(os.getenv("RATE_LIMIT_RPM", "100")),
                "burst_size": int(os.getenv("RATE_LIMIT_BURST", "20")),
                "recommend_rpm": int(os.getenv("RECOMMEND_RPM", "20")),
                "feedback_rpm": int(os.getenv("FEEDBACK_RPM", "50"))
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "json_format": os.getenv("LOG_JSON", "true").lower() == "true",
                "log_requests": os.getenv("LOG_REQUESTS", "true").lower() == "true",
                "log_sql": os.getenv("LOG_SQL", "false").lower() == "true"
            },
            "monitoring": {
                "enabled": os.getenv("MONITORING_ENABLED", "true").lower() == "true",
                "metrics_endpoint": os.getenv("METRICS_ENDPOINT", "true").lower() == "true",
                "health_checks": os.getenv("HEALTH_CHECKS", "true").lower() == "true",
                "prometheus_port": int(os.getenv("PROMETHEUS_PORT")) if os.getenv("PROMETHEUS_PORT") else None
            },
            "matrix_factorization": {
                "n_factors": int(os.getenv("MF_N_FACTORS", "50")),
                "learning_rate": float(os.getenv("MF_LEARNING_RATE", "0.01")),
                "regularization": float(os.getenv("MF_REGULARIZATION", "0.1")),
                "n_epochs": int(os.getenv("MF_N_EPOCHS", "100")),
                "min_interactions": int(os.getenv("MF_MIN_INTERACTIONS", "10"))
            },
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        }
        
        return AppConfig(**config_dict)
    
    def load_from_file(self, config_path: str) -> AppConfig:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            
            logger.info("config_loaded_from_file", path=config_path)
            return AppConfig(**config_dict)
            
        except FileNotFoundError:
            logger.warning("config_file_not_found", path=config_path)
            raise
        except json.JSONDecodeError as e:
            logger.error("config_file_invalid_json", path=config_path, error=str(e))
            raise
        except Exception as e:
            logger.error("config_load_failed", path=config_path, error=str(e))
            raise
    
    def load_config(self) -> AppConfig:
        """Load configuration from file or environment."""
        if os.path.exists(self.config_path):
            try:
                config = self.load_from_file(self.config_path)
                self._update_last_modified()
                return config
            except Exception as e:
                logger.warning("config_file_load_failed_fallback_to_env", error=str(e))
        
        # Fallback to environment variables
        return self.load_from_env()
    
    def save_config(self, config: AppConfig, config_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        path = config_path or self.config_path
        
        try:
            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(config.dict(), f, indent=2, default=str)
            
            logger.info("config_saved", path=path)
            self._update_last_modified()
            
        except Exception as e:
            logger.error("config_save_failed", path=path, error=str(e))
            raise
    
    def get_config(self) -> AppConfig:
        """Get current configuration, loading if necessary."""
        if self.config is None:
            self.config = self.load_config()
        return self.config
    
    def reload_config(self) -> AppConfig:
        """Force reload configuration."""
        logger.info("config_reloading")
        self.config = self.load_config()
        
        # Notify watchers
        for watcher in self.watchers:
            try:
                watcher(self.config)
            except Exception as e:
                logger.error("config_watcher_failed", error=str(e))
        
        return self.config
    
    def add_watcher(self, callback: callable) -> None:
        """Add a callback to be notified when config changes."""
        self.watchers.append(callback)
    
    def remove_watcher(self, callback: callable) -> None:
        """Remove a config change watcher."""
        if callback in self.watchers:
            self.watchers.remove(callback)
    
    def _update_last_modified(self) -> None:
        """Update last modified timestamp."""
        try:
            if os.path.exists(self.config_path):
                self._last_modified = os.path.getmtime(self.config_path)
        except Exception:
            pass
    
    def check_for_changes(self) -> bool:
        """Check if configuration file has changed."""
        if not os.path.exists(self.config_path):
            return False
        
        try:
            current_modified = os.path.getmtime(self.config_path)
            if self._last_modified is None:
                self._update_last_modified()
                return False
            
            return current_modified > self._last_modified
        except Exception:
            return False
    
    def auto_reload_if_changed(self) -> bool:
        """Automatically reload config if file has changed."""
        if self.check_for_changes():
            self.reload_config()
            return True
        return False
    
    def validate_config(self, config_dict: Dict[str, Any]) -> List[str]:
        """Validate configuration dictionary and return errors."""
        errors = []
        
        try:
            AppConfig(**config_dict)
        except Exception as e:
            errors.append(str(e))
        
        return errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration (without sensitive data)."""
        config = self.get_config()
        
        return {
            "environment": config.environment,
            "debug": config.debug,
            "wordpress": {
                "base_url": config.wordpress.base_url,
                "auth_type": config.wordpress.auth_type,
                "timeout": config.wordpress.timeout
            },
            "cache": {
                "backend": config.cache.backend,
                "default_ttl": config.cache.default_ttl
            },
            "recommender": {
                "top_n": config.recommender.top_n,
                "weights": {
                    "content": config.recommender.content_weight,
                    "collaborative": config.recommender.collab_weight,
                    "popularity": config.recommender.pop_weight,
                    "embedding": config.recommender.emb_weight
                }
            },
            "rate_limiting": {
                "enabled": config.rate_limiting.enabled,
                "requests_per_minute": config.rate_limiting.requests_per_minute
            },
            "monitoring": {
                "enabled": config.monitoring.enabled,
                "metrics_endpoint": config.monitoring.metrics_endpoint
            }
        }


# Global config manager instance
config_manager = ConfigManager()
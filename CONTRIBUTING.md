# Contributing to Visey Recommender

Thank you for your interest in contributing to the Visey Recommender System! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
- Use the [GitHub Issues](https://github.com/yourusername/visey-recommender/issues) page
- Search existing issues before creating a new one
- Provide detailed information including:
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Python version, etc.)
  - Error messages and logs

### Suggesting Features
- Open a [GitHub Discussion](https://github.com/yourusername/visey-recommender/discussions) first
- Describe the use case and benefits
- Consider implementation complexity
- Be open to feedback and alternative approaches

### Code Contributions

#### 1. Fork and Clone
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/yourusername/visey-recommender.git
cd visey-recommender
```

#### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

#### 3. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

#### 4. Make Changes
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

#### 5. Commit Changes
```bash
# Use conventional commit format
git commit -m "feat: add new recommendation algorithm"
git commit -m "fix: resolve WordPress API timeout issue"
git commit -m "docs: update installation instructions"
```

#### 6. Push and Create PR
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

## 📝 Coding Standards

### Python Code Style
- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [flake8](https://flake8.pycqa.org/) for linting

```bash
# Format code
black visey_recommender/ tests/
isort visey_recommender/ tests/

# Check linting
flake8 visey_recommender/ tests/
```

### Type Hints
- Use type hints for all function parameters and return values
- Import types from `typing` module when needed
- Use `Optional[Type]` for nullable parameters

```python
from typing import List, Optional, Dict, Any

def get_recommendations(user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get recommendations for a user."""
    pass
```

### Documentation
- Use docstrings for all classes and functions
- Follow [Google docstring format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Include examples in docstrings when helpful

```python
def recommend(self, profile: UserProfile, resources: List[Resource], top_n: int = 10) -> List[Recommendation]:
    """Generate personalized recommendations for a user.
    
    Args:
        profile: User profile containing preferences and metadata
        resources: List of available resources to recommend from
        top_n: Maximum number of recommendations to return
        
    Returns:
        List of recommendations sorted by relevance score
        
    Example:
        >>> recommender = BaselineRecommender()
        >>> profile = UserProfile(user_id=1, industry="tech")
        >>> resources = [Resource(id=1, title="AI Guide")]
        >>> recs = recommender.recommend(profile, resources, top_n=5)
    """
```

### Testing
- Write tests for all new functionality
- Use pytest for testing framework
- Aim for >90% code coverage
- Include both unit tests and integration tests

```python
import pytest
from visey_recommender.recommender.baseline import BaselineRecommender

class TestBaselineRecommender:
    def test_recommend_returns_correct_format(self):
        """Test that recommend returns properly formatted results."""
        recommender = BaselineRecommender()
        # ... test implementation
```

### Error Handling
- Use specific exception types
- Provide helpful error messages
- Log errors appropriately
- Handle edge cases gracefully

```python
from visey_recommender.utils.exceptions import WordPressAPIError

try:
    response = await wp_client.fetch_posts()
except httpx.HTTPStatusError as e:
    logger.error(f"WordPress API error: {e.response.status_code}")
    raise WordPressAPIError(f"Failed to fetch posts: {e}")
```

## 🧪 Testing Guidelines

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=visey_recommender --cov-report=html

# Run specific test file
pytest tests/test_recommender.py

# Run tests matching pattern
pytest -k "test_wordpress"
```

### Test Categories
1. **Unit Tests**: Test individual functions/classes in isolation
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test HTTP endpoints
4. **Performance Tests**: Test system performance under load

### Test Data
- Use fixtures for reusable test data
- Mock external dependencies (WordPress API, Redis, etc.)
- Use factories for generating test objects

```python
@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        user_id=1,
        industry="technology",
        stage="growth",
        team_size="10-50"
    )
```

## 📚 Documentation

### Code Documentation
- Document all public APIs
- Include usage examples
- Explain complex algorithms
- Document configuration options

### User Documentation
- Update README.md for user-facing changes
- Add guides to `docs/` directory
- Include screenshots for UI changes
- Update API documentation

### Changelog
- Add entries to CHANGELOG.md
- Follow [Keep a Changelog](https://keepachangelog.com/) format
- Include breaking changes prominently

## 🔄 Development Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/) format:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build/tooling changes

### Pull Request Process
1. Ensure all tests pass
2. Update documentation
3. Add changelog entry
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested

### Code Review Guidelines
- Be constructive and respectful
- Focus on code quality and maintainability
- Suggest improvements with examples
- Approve when ready, request changes when needed

## 🚀 Release Process

### Version Numbers
Follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Tag created
- [ ] GitHub release created
- [ ] Docker images built
- [ ] PyPI package published (if applicable)

## 🏗️ Architecture Guidelines

### Project Structure
```
visey_recommender/
├── api/           # FastAPI application
├── clients/       # External API clients
├── recommender/   # Recommendation algorithms
├── services/      # Business logic
├── storage/       # Data persistence
├── utils/         # Utility functions
└── models/        # Data models
```

### Design Principles
- **Separation of Concerns**: Each module has a single responsibility
- **Dependency Injection**: Use dependency injection for testability
- **Configuration**: Use environment variables for configuration
- **Async/Await**: Use async patterns for I/O operations
- **Error Handling**: Comprehensive error handling and logging

### Adding New Features

#### New Recommendation Algorithm
1. Create class in `visey_recommender/recommender/`
2. Inherit from `BaseRecommender`
3. Implement required methods
4. Add tests in `tests/test_recommender.py`
5. Update configuration options
6. Add documentation

#### New API Endpoint
1. Add endpoint to appropriate router in `visey_recommender/api/`
2. Add request/response models
3. Add validation and error handling
4. Add tests in `tests/test_api.py`
5. Update API documentation

#### New WordPress Integration
1. Add methods to `WPClient` class
2. Add service layer methods if needed
3. Add comprehensive tests
4. Update documentation
5. Consider rate limiting and caching

## 🛡️ Security Guidelines

### Security Best Practices
- Never commit secrets or credentials
- Use environment variables for sensitive data
- Validate all user inputs
- Use HTTPS in production
- Implement proper authentication
- Follow OWASP guidelines

### Reporting Security Issues
- Email security issues to: security@visey.com
- Do not create public issues for security vulnerabilities
- Allow time for fixes before public disclosure

## 📞 Getting Help

### Communication Channels
- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time chat (link in README)
- **Email**: maintainers@visey.com

### Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [Python Testing Guide](https://docs.python.org/3/library/unittest.html)
- [Docker Documentation](https://docs.docker.com/)

## 🎉 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Annual contributor highlights
- Special badges for significant contributions

Thank you for contributing to Visey Recommender! 🚀
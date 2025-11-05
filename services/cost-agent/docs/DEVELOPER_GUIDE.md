# Cost Agent Developer Guide

**Version**: 1.0.0  
**Last Updated**: 2025-01-23

---

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Code Structure](#code-structure)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Contribution Workflow](#contribution-workflow)
- [Release Process](#release-process)

---

## Development Environment Setup

### Prerequisites

- Python 3.11+
- Git
- PostgreSQL 14+
- Redis 6+
- Docker (optional)

### Setup Steps

1. **Clone Repository**:
```bash
git clone https://github.com/optiinfra/cost-agent.git
cd cost-agent
```

2. **Create Virtual Environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize Database**:
```bash
python scripts/init_db.py
```

6. **Run Tests**:
```bash
pytest
```

7. **Start Development Server**:
```bash
uvicorn src.main:app --reload --port 8001
```

---

## Code Structure

```
cost-agent/
├── src/
│   ├── api/                    # API endpoints
│   │   ├── health.py
│   │   ├── analyze.py
│   │   ├── aws_costs.py
│   │   └── ...
│   ├── collectors/             # Cloud provider collectors
│   │   ├── aws/
│   │   ├── gcp/
│   │   ├── azure/
│   │   └── vultr/
│   ├── analyzers/              # Analysis engines
│   │   ├── anomaly_detector.py
│   │   ├── trend_analyzer.py
│   │   └── forecaster.py
│   ├── recommendations/        # Recommendation engine
│   │   ├── generator.py
│   │   ├── scorer.py
│   │   └── validator.py
│   ├── execution/              # Execution engine
│   │   ├── engine.py
│   │   ├── executors/
│   │   └── rollback.py
│   ├── learning/               # Learning loop
│   │   ├── outcome_tracker.py
│   │   ├── feedback_analyzer.py
│   │   └── improvement_engine.py
│   ├── llm/                    # LLM integration
│   │   ├── llm_client.py
│   │   └── prompt_templates.py
│   ├── workflows/              # LangGraph workflows
│   │   ├── cost_optimization.py
│   │   └── spot_migration.py
│   ├── models/                 # Data models
│   ├── auth/                   # Authentication
│   ├── middleware/             # Middleware
│   ├── database/               # Database utilities
│   ├── config.py               # Configuration
│   └── main.py                 # Application entry point
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── e2e/                    # End-to-end tests
│   ├── performance/            # Performance tests
│   └── conftest.py             # Test fixtures
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── requirements.txt            # Dependencies
└── pytest.ini                  # Test configuration
```

---

## Coding Standards

### Python Style Guide

Follow **PEP 8** with these additions:

- **Line Length**: 100 characters (not 79)
- **Imports**: Organized in groups (standard library, third-party, local)
- **Type Hints**: Required for all function signatures
- **Docstrings**: Required for all public functions and classes

### Example

```python
"""
Module for cost analysis.

This module provides functions for analyzing cloud costs,
detecting anomalies, and identifying optimization opportunities.
"""

from typing import List, Dict, Optional
from datetime import datetime

from src.models.analysis import CostData, Anomaly


async def detect_anomalies(
    cost_data: List[CostData],
    sensitivity: str = "medium",
    threshold: float = 2.0
) -> List[Anomaly]:
    """
    Detect anomalies in cost data.
    
    Args:
        cost_data: List of cost data points
        sensitivity: Detection sensitivity (low, medium, high)
        threshold: Standard deviation threshold
        
    Returns:
        List of detected anomalies
        
    Raises:
        ValueError: If cost_data is empty
    """
    if not cost_data:
        raise ValueError("cost_data cannot be empty")
    
    # Implementation
    anomalies = []
    # ...
    return anomalies
```

### Code Formatting

Use **Black** for code formatting:

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

Use **flake8** for linting:

```bash
# Run linter
flake8 src/ tests/

# Configuration in .flake8
[flake8]
max-line-length = 100
exclude = venv,__pycache__
ignore = E203,W503
```

### Type Checking

Use **mypy** for type checking:

```bash
# Run type checker
mypy src/

# Configuration in mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

---

## Testing Guidelines

### Test Structure

```python
import pytest
from src.analyzers.anomaly_detector import detect_anomalies


class TestAnomalyDetector:
    """Tests for anomaly detection."""
    
    def test_detect_anomalies_with_spike(self, cost_data_with_spike):
        """Test detection of cost spike."""
        anomalies = await detect_anomalies(cost_data_with_spike)
        
        assert len(anomalies) == 1
        assert anomalies[0].severity == "high"
        assert anomalies[0].deviation_percent > 50
    
    def test_detect_anomalies_empty_data(self):
        """Test with empty data raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await detect_anomalies([])
```

### Test Categories

Use pytest markers:

```python
@pytest.mark.unit
def test_unit_function():
    """Unit test."""
    pass

@pytest.mark.integration
async def test_integration():
    """Integration test."""
    pass

@pytest.mark.e2e
async def test_end_to_end():
    """E2E test."""
    pass

@pytest.mark.performance
def test_performance():
    """Performance test."""
    pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific category
pytest -m unit
pytest -m integration

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_analyzer.py::test_detect_anomalies
```

### Test Coverage

- **Target**: 85%+ code coverage
- **Required**: All new code must have tests
- **CI/CD**: Tests run automatically on PR

---

## Contribution Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following coding standards
- Add tests for new functionality
- Update documentation

### 3. Run Tests

```bash
# Run tests
pytest

# Check formatting
black --check src/ tests/

# Run linter
flake8 src/ tests/

# Type check
mypy src/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add anomaly detection for GCP costs"
```

**Commit Message Format**:
```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create pull request on GitHub with:
- Clear description
- Link to related issues
- Screenshots (if UI changes)
- Test results

### 6. Code Review

- Address reviewer feedback
- Update PR as needed
- Ensure CI/CD passes

### 7. Merge

- Squash and merge to main
- Delete feature branch

---

## Release Process

### Version Numbering

Follow **Semantic Versioning** (SemVer):
- **Major**: Breaking changes (1.0.0 → 2.0.0)
- **Minor**: New features (1.0.0 → 1.1.0)
- **Patch**: Bug fixes (1.0.0 → 1.0.1)

### Release Steps

1. **Update Version**:
```python
# In src/__init__.py
__version__ = "1.1.0"
```

2. **Update CHANGELOG.md**:
```markdown
## [1.1.0] - 2025-01-23

### Added
- GCP cost collection support
- Anomaly detection for multi-cloud

### Fixed
- Database connection pool leak
```

3. **Create Release Branch**:
```bash
git checkout -b release/1.1.0
```

4. **Run Full Test Suite**:
```bash
pytest
pytest -m integration
pytest -m e2e
```

5. **Build and Tag**:
```bash
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

6. **Deploy**:
```bash
# Build Docker image
docker build -t optiinfra/cost-agent:1.1.0 .

# Push to registry
docker push optiinfra/cost-agent:1.1.0

# Deploy to production
kubectl set image deployment/cost-agent cost-agent=optiinfra/cost-agent:1.1.0
```

---

## Support

- **Slack**: #cost-agent-dev
- **Email**: dev@optiinfra.com
- **Wiki**: https://wiki.optiinfra.com/cost-agent

---

**Last Updated**: 2025-01-23  
**Version**: 1.0.0

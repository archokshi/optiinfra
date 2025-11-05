# Performance Agent Development Guide

## Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd optiinfra/services/performance-agent
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

**Development Dependencies**:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `pytest-benchmark` - Performance benchmarking
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking
- `locust` - Load testing

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with development settings
```

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### 5. Run Development Server

```bash
# With hot reload
uvicorn src.main:app --reload --port 8002

# With debug logging
LOG_LEVEL=DEBUG uvicorn src.main:app --reload --port 8002
```

---

## Project Structure

```
performance-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py           # Health endpoints
│   │   ├── config.py           # Config endpoints
│   │   ├── metrics.py          # Metrics endpoints
│   │   ├── analysis.py         # Analysis endpoints
│   │   ├── optimization.py     # Optimization endpoints
│   │   ├── workflows.py        # Workflow endpoints
│   │   └── error_handlers.py  # Error handling
│   ├── collectors/             # Metrics collectors
│   │   ├── __init__.py
│   │   ├── vllm_collector.py   # vLLM collector
│   │   ├── tgi_collector.py    # TGI collector
│   │   ├── sglang_collector.py # SGLang collector
│   │   └── prometheus_parser.py # Prometheus parser
│   ├── analysis/               # Analysis engine
│   │   ├── __init__.py
│   │   ├── bottleneck_detector.py
│   │   ├── slo_monitor.py
│   │   └── engine.py
│   ├── optimization/           # Optimization engine
│   │   ├── __init__.py
│   │   ├── kv_cache_optimizer.py
│   │   ├── quantization_optimizer.py
│   │   ├── batching_optimizer.py
│   │   └── engine.py
│   ├── workflows/              # Workflow management
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── optimization_workflow.py
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── analysis.py
│   │   ├── optimization.py
│   │   ├── workflow.py
│   │   ├── health.py
│   │   └── errors.py
│   └── core/                   # Core utilities
│       ├── __init__.py
│       ├── logger.py
│       └── registration.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_*.py               # Unit tests
│   ├── integration/            # Integration tests
│   └── performance/            # Performance tests
│       ├── test_load.py
│       ├── test_benchmarks.py
│       └── test_stress.py
├── docs/                       # Documentation
├── k8s/                        # Kubernetes manifests
├── .env.example                # Example environment file
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── README.md
```

---

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/ -m unit -v

# Run specific test file
pytest tests/test_vllm_collector.py -v

# Run specific test
pytest tests/test_vllm_collector.py::test_collect_metrics -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/ -m integration -v
```

### Performance Tests

```bash
# Run load tests
pytest tests/performance/test_load.py -v -m performance

# Run benchmarks
pytest tests/performance/test_benchmarks.py --benchmark-only

# Run stress tests
pytest tests/performance/test_stress.py -v -m stress
```

### Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View coverage
open htmlcov/index.html

# Check coverage percentage
pytest tests/ --cov=src --cov-report=term-missing
```

**Current Coverage**: 77% (149 tests)

---

## Code Style

### Formatting with Black

```bash
# Format all code
black src/ tests/

# Check formatting
black src/ tests/ --check

# Format specific file
black src/collectors/vllm_collector.py
```

**Black Configuration** (pyproject.toml):
```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

### Linting with Ruff

```bash
# Lint all code
ruff check src/ tests/

# Auto-fix issues
ruff check src/ tests/ --fix

# Lint specific file
ruff check src/collectors/vllm_collector.py
```

**Ruff Configuration** (pyproject.toml):
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W"]
```

### Type Checking with MyPy

```bash
# Type check all code
mypy src/

# Type check specific file
mypy src/collectors/vllm_collector.py

# Strict mode
mypy src/ --strict
```

**MyPy Configuration** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## Adding New Features

### Adding a New Collector

1. **Create collector class**:

```python
# src/collectors/new_collector.py
from typing import Dict, Any
import httpx
from src.models.metrics import InstanceMetrics

class NewCollector:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def collect(
        self,
        instance_id: str,
        metrics_url: str
    ) -> InstanceMetrics:
        """Collect metrics from new instance type."""
        response = await self.client.get(metrics_url)
        response.raise_for_status()
        
        # Parse metrics
        metrics_data = self._parse_metrics(response.text)
        
        return InstanceMetrics(
            instance_id=instance_id,
            timestamp=datetime.utcnow(),
            **metrics_data
        )
    
    def _parse_metrics(self, text: str) -> Dict[str, Any]:
        """Parse metrics from response."""
        # Implement parsing logic
        pass
```

2. **Add tests**:

```python
# tests/test_new_collector.py
import pytest
from src.collectors.new_collector import NewCollector

@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_metrics():
    async with NewCollector() as collector:
        metrics = await collector.collect(
            "test-1",
            "http://localhost:8000/metrics"
        )
        assert metrics.instance_id == "test-1"
```

3. **Register collector**:

```python
# src/collectors/__init__.py
from .new_collector import NewCollector

COLLECTORS = {
    "vllm": VLLMCollector,
    "tgi": TGICollector,
    "sglang": SGLangCollector,
    "new": NewCollector  # Add new collector
}
```

### Adding a New Optimizer

1. **Create optimizer class**:

```python
# src/optimization/new_optimizer.py
from typing import List, Tuple, Optional
from src.models.analysis import Bottleneck
from src.models.optimization import Optimization, ConfigChange

class NewOptimizer:
    def generate_optimizations(
        self,
        bottlenecks: List[Bottleneck],
        instance_type: str,
        current_config: dict
    ) -> Tuple[List[Optimization], Optional[ConfigChange]]:
        """Generate optimizations for bottlenecks."""
        optimizations = []
        
        for bottleneck in bottlenecks:
            if bottleneck.type == "SPECIFIC_TYPE":
                opt = Optimization(
                    type="NEW_OPTIMIZATION",
                    priority="HIGH",
                    description="Apply new optimization",
                    estimated_improvement={"metric": 0.2}
                )
                optimizations.append(opt)
        
        config_change = ConfigChange(
            parameter="new_param",
            old_value=current_config.get("new_param"),
            new_value="optimized_value"
        )
        
        return optimizations, config_change
```

2. **Add tests**:

```python
# tests/test_new_optimizer.py
import pytest
from src.optimization.new_optimizer import NewOptimizer
from src.models.analysis import Bottleneck, BottleneckType, Severity

@pytest.mark.unit
def test_generate_optimizations():
    optimizer = NewOptimizer()
    
    bottlenecks = [
        Bottleneck(
            type=BottleneckType.SPECIFIC_TYPE,
            severity=Severity.HIGH,
            description="Test bottleneck"
        )
    ]
    
    optimizations, config = optimizer.generate_optimizations(
        bottlenecks, "vllm", {}
    )
    
    assert len(optimizations) > 0
```

3. **Register optimizer**:

```python
# src/optimization/engine.py
from .new_optimizer import NewOptimizer

class OptimizationEngine:
    def __init__(self):
        self.optimizers = [
            KVCacheOptimizer(),
            QuantizationOptimizer(),
            BatchingOptimizer(),
            NewOptimizer()  # Add new optimizer
        ]
```

### Adding a New API Endpoint

1. **Create endpoint**:

```python
# src/api/new_endpoint.py
from fastapi import APIRouter, HTTPException
from src.models.new_model import NewRequest, NewResponse

router = APIRouter()

@router.post("/new-endpoint", response_model=NewResponse)
async def new_endpoint(request: NewRequest):
    """New endpoint description."""
    try:
        # Implement logic
        result = process_request(request)
        return NewResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Add tests**:

```python
# tests/test_new_endpoint.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.unit
def test_new_endpoint(client: TestClient):
    response = client.post(
        "/api/v1/new-endpoint",
        json={"param": "value"}
    )
    assert response.status_code == 200
```

3. **Register router**:

```python
# src/main.py
from src.api.new_endpoint import router as new_router

app.include_router(new_router, prefix="/api/v1", tags=["new"])
```

---

## Debugging

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### Debug with VS Code

**launch.json**:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.main:app",
                "--reload",
                "--port",
                "8002"
            ],
            "jinja": true
        }
    ]
}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Add debug logs
logger.debug(f"Processing request: {request}")
logger.info(f"Metrics collected: {metrics}")
logger.warning(f"High memory usage: {usage}")
logger.error(f"Failed to collect metrics: {error}")
```

---

## Contributing

### Workflow

1. **Fork repository**
2. **Create feature branch**:
   ```bash
   git checkout -b feature/new-feature
   ```

3. **Make changes**
4. **Run tests**:
   ```bash
   pytest tests/ -v
   black src/ tests/
   ruff check src/ tests/
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **Push to fork**:
   ```bash
   git push origin feature/new-feature
   ```

7. **Create pull request**

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

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

**Examples**:
```
feat(collectors): add support for new instance type
fix(analysis): correct bottleneck detection threshold
docs(api): update API documentation
test(collectors): add tests for vLLM collector
```

### Pull Request Guidelines

- **Title**: Clear and descriptive
- **Description**: Explain what and why
- **Tests**: Include tests for new features
- **Documentation**: Update docs if needed
- **Code Style**: Follow project style
- **Coverage**: Maintain or improve coverage

---

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Creating a Release

1. **Update version**:
   ```python
   # src/config.py
   VERSION = "1.1.0"
   ```

2. **Update CHANGELOG.md**:
   ```markdown
   ## [1.1.0] - 2024-01-01
   ### Added
   - New collector for XYZ
   ### Fixed
   - Bug in bottleneck detection
   ```

3. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

4. **Create tag**:
   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```

5. **Build and push Docker image**:
   ```bash
   docker build -t performance-agent:1.1.0 .
   docker push performance-agent:1.1.0
   ```

---

## Performance Optimization

### Profiling

```bash
# Profile with cProfile
python -m cProfile -o profile.stats src/main.py

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Profile memory
python -m memory_profiler src/main.py
```

### Load Testing

```bash
# Run locust
locust -f locustfile.py --host=http://localhost:8002

# Open web UI
open http://localhost:8089
```

---

## Troubleshooting Development Issues

### Tests Failing

```bash
# Run with verbose output
pytest tests/ -vv

# Run with debug logging
pytest tests/ -vv --log-cli-level=DEBUG

# Run specific test
pytest tests/test_file.py::test_function -vv
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print(sys.path)"
```

### Type Errors

```bash
# Run mypy with verbose output
mypy src/ --show-error-codes --show-traceback
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

**Last Updated**: 2024-01-01  
**Version**: 1.0.0

"""
API documentation tests for Application Agent.

Tests OpenAPI schema and documentation completeness.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_openapi_schema():
    """Test OpenAPI schema is valid."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema


def test_all_endpoints_documented():
    """Test all endpoints have documentation."""
    response = client.get("/openapi.json")
    schema = response.json()
    
    paths = schema["paths"]
    
    # Check that key endpoints are documented
    expected_endpoints = [
        "/quality/analyze",
        "/regression/baseline",
        "/validation/create",
        "/workflow/validate",
        "/llm/analyze",
        "/config/current",
        "/bulk/quality",
        "/analytics/summary",
        "/admin/stats"
    ]
    
    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Endpoint {endpoint} not documented"


def test_response_models_documented():
    """Test response models are documented."""
    response = client.get("/openapi.json")
    schema = response.json()
    
    # Check that schemas are defined
    assert "components" in schema
    assert "schemas" in schema["components"]
    
    schemas = schema["components"]["schemas"]
    assert len(schemas) > 0


def test_api_docs_accessible():
    """Test API documentation UI is accessible."""
    # Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200
    
    # ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200

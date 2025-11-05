from setuptools import setup, find_packages

setup(
    name="optiinfra-common",
    version="0.1.0",
    description="Shared utilities for OptiInfra agents",
    author="OptiInfra Team",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.23",
        "psycopg2-binary>=2.9.10",
        "redis>=5.0.1",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "httpx>=0.25.2",
        "tenacity>=8.2.3",
        "prometheus-client>=0.19.0",
    ],
    python_requires=">=3.10",
)

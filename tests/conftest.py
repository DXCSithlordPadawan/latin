"""
pytest configuration — registers custom markers.
"""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (excluded from default run; included in Phase 7 compliance run)"
    )

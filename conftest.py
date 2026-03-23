"""
Root conftest — shared fixtures and pytest configuration hooks.
"""

import logging


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests against external services",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests that hit external services"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

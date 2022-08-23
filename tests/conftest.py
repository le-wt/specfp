"""Configure pytest marks and global fixtures."""

import pytest


def pytest_configure(config):
    """Configure markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark as using live resources.")


@pytest.fixture
def wdf_stream():
    """A sample WDF file in the tests directory."""
    with open("tests/WDF/single.wdf", "rb") as file:
        yield file

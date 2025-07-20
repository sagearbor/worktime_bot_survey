import pytest

def test_project_initialization():
    """
    A simple test to ensure the test suite is running.
    """
    assert True

def test_import():
    """
    Ensures the main package is importable.
    """
    import time_profiler
    assert time_profiler is not None
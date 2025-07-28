"""Verify basic setup is working."""
import pytest


def test_import_pytest():
    """Verify pytest is importable."""
    assert pytest is not None


def test_basic_assertion():
    """Test basic assertion."""
    assert 1 + 1 == 2


class TestSetup:
    """Test class for setup verification."""
    
    def test_class_method(self):
        """Test method in class."""
        result = "hello".upper()
        assert result == "HELLO"

"""
Integration tests for file size limit errors.

These tests verify that the API correctly rejects files exceeding the size limit.
"""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    from src.main import app

    return TestClient(app)


def test_file_too_large(client: TestClient) -> None:
    """Test that files larger than 10MB are rejected."""
    from src.models import MAX_FILE_SIZE

    # Given: A file larger than the limit (10MB + 1 byte)
    large_content = b"x" * (MAX_FILE_SIZE + 1)
    files = {
        "file": (
            "large.xlsx",
            BytesIO(large_content),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Request is rejected with 413 status
    assert response.status_code == 413
    assert response.headers["content-type"] == "application/json"

    # And: Error response indicates size limit exceeded
    error_data = response.json()
    assert error_data["error_type"] == "FILE_TOO_LARGE"
    assert "size" in error_data["message"].lower()
    assert "10" in error_data["message"]  # Should mention 10MB limit


def test_file_at_limit_boundary(client: TestClient) -> None:
    """Test file at exact size limit (should be accepted if valid)."""
    from src.models import MAX_FILE_SIZE

    # Given: A file exactly at the limit
    # Note: This will fail validation due to invalid content,
    # but should not fail on size check
    boundary_content = b"x" * MAX_FILE_SIZE
    files = {
        "file": (
            "boundary.xlsx",
            BytesIO(boundary_content),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Should not fail on size (will fail on format/signature instead)
    # Status code should be 400 (invalid format), not 413 (too large)
    assert response.status_code != 413


def test_small_valid_file_accepted(client: TestClient) -> None:
    """Test that small valid files are not rejected for size reasons."""
    # This is more of a sanity check - small files should pass size validation
    # (though they may fail other validations if not actual Excel files)

    small_content = b"small content"
    files = {
        "file": (
            "small.xlsx",
            BytesIO(small_content),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Should not fail on size (will fail on format/signature instead)
    if response.status_code != 200:
        error_data = response.json()
        # Should not be a size error
        assert error_data["error_type"] != "FILE_TOO_LARGE"

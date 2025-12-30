"""
Integration tests for corrupted file errors.

These tests verify that the API correctly handles corrupted Excel files.
"""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    from src.main import app

    return TestClient(app)


def test_corrupted_xlsx_file(client: TestClient) -> None:
    """Test that corrupted .xlsx files are rejected."""
    # Given: A file with .xlsx extension and ZIP signature but corrupted content
    # ZIP signature (PK\x03\x04) followed by garbage
    corrupted_content = b"PK\x03\x04" + b"\xff" * 100
    files = {
        "file": (
            "corrupted.xlsx",
            BytesIO(corrupted_content),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Request is rejected
    assert response.status_code in [400, 422]  # Either corrupted or conversion failed
    assert response.headers["content-type"] == "application/json"

    # And: Error response indicates file issue
    error_data = response.json()
    assert error_data["error_type"] in ["CORRUPTED_FILE", "CONVERSION_FAILED"]
    assert (
        "corrupted" in error_data["message"].lower()
        or "failed" in error_data["message"].lower()
    )


def test_truncated_xlsx_file(client: TestClient) -> None:
    """Test that truncated .xlsx files are rejected."""
    # Given: A file with valid ZIP signature but truncated content
    # This simulates a file that was partially uploaded
    truncated_content = b"PK\x03\x04" + b"\x00" * 50  # Too short to be valid
    files = {
        "file": (
            "truncated.xlsx",
            BytesIO(truncated_content),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Request is rejected
    assert response.status_code in [400, 422]

    # And: Error indicates file problem
    error_data = response.json()
    assert error_data["error_type"] in ["CORRUPTED_FILE", "CONVERSION_FAILED"]


def test_empty_file(client: TestClient) -> None:
    """Test that empty files are rejected."""
    # Given: An empty file
    files = {
        "file": (
            "empty.xlsx",
            BytesIO(b""),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Request is rejected
    assert response.status_code == 400

    # And: Error indicates corrupted file
    error_data = response.json()
    assert error_data["error_type"] == "CORRUPTED_FILE"


def test_partial_zip_file(client: TestClient) -> None:
    """Test file with valid start but invalid structure."""
    # Given: A file that starts like a ZIP but isn't a valid Excel file
    # Valid ZIP header but no valid Excel structure
    partial_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00" + b"\x00" * 100
    files = {
        "file": (
            "partial.xlsx",
            BytesIO(partial_content),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Request is rejected
    assert response.status_code in [400, 422]

    # And: Error type is appropriate
    error_data = response.json()
    assert error_data["error_type"] in ["CORRUPTED_FILE", "CONVERSION_FAILED"]

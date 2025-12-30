"""
Integration tests for invalid file format errors.

These tests verify that the API correctly rejects unsupported file formats.
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


def test_invalid_extension_txt(client: TestClient) -> None:
    """Test that .txt files are rejected."""
    # Given: A text file
    file_content = b"This is a text file, not an Excel file"
    files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Request is rejected
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"

    # And: Error response includes appropriate message
    error_data = response.json()
    assert error_data["error_type"] == "INVALID_FILE_FORMAT"
    assert (
        "unsupported" in error_data["message"].lower()
        or "invalid" in error_data["message"].lower()
    )


def test_invalid_extension_png(client: TestClient) -> None:
    """Test that .png files are rejected."""
    # Given: A PNG image file
    # PNG signature
    file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    files = {"file": ("image.png", BytesIO(file_content), "image/png")}

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Request is rejected
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"

    # And: Error response includes appropriate message
    error_data = response.json()
    assert error_data["error_type"] == "INVALID_FILE_FORMAT"


def test_invalid_mime_type(client: TestClient) -> None:
    """Test that files with invalid MIME types are rejected."""
    # Given: A file with wrong MIME type
    file_content = b"Random content"
    files = {"file": ("test.xlsx", BytesIO(file_content), "application/json")}

    # When: Uploading to /convert
    response = client.post("/convert", files=files)

    # Then: Request is rejected
    assert response.status_code == 400

    # And: Error type indicates format issue
    error_data = response.json()
    assert error_data["error_type"] in ["INVALID_FILE_FORMAT", "CORRUPTED_FILE"]


def test_wrong_file_signature(client: TestClient) -> None:
    """Test that files with wrong magic numbers are rejected."""
    # Given: A file with .xlsx extension but wrong signature
    file_content = b"Not a valid Excel file"
    files = {
        "file": (
            "fake.xlsx",
            BytesIO(file_content),
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

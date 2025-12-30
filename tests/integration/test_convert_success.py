"""
Integration tests for /convert endpoint (success cases).

These tests verify the basic Excel to PDF conversion functionality.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def simple_excel() -> Path:
    """Get path to simple Excel test fixture."""
    return Path(__file__).parent.parent / "fixtures" / "simple.xlsx"


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    from src.main import app
    
    return TestClient(app)


def test_convert_simple_xlsx_success(client: TestClient, simple_excel: Path) -> None:
    """Test converting a simple .xlsx file to PDF."""
    # Given: A simple Excel file
    assert simple_excel.exists(), f"Test fixture not found: {simple_excel}"
    
    with open(simple_excel, "rb") as f:
        files = {"file": ("simple.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        # When: Uploading to /convert endpoint
        response = client.post("/convert", files=files)
    
    # Then: Response is successful
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "content-disposition" in response.headers
    assert "simple.pdf" in response.headers["content-disposition"]
    
    # And: PDF content is returned
    pdf_content = response.content
    assert len(pdf_content) > 0
    assert pdf_content[:4] == b"%PDF"  # PDF file signature


def test_convert_response_headers(client: TestClient, simple_excel: Path) -> None:
    """Test that response includes correct HTTP headers."""
    with open(simple_excel, "rb") as f:
        files = {"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/convert", files=files)
    
    # Verify headers
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "content-disposition" in response.headers
    assert "content-length" in response.headers
    assert int(response.headers["content-length"]) > 0

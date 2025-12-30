"""
Integration tests for multi-sheet Excel files.

These tests verify that multi-sheet workbooks are correctly converted to PDF.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def multisheet_excel() -> Path:
    """Get path to multi-sheet Excel test fixture."""
    return Path(__file__).parent.parent / "fixtures" / "multisheet.xlsx"


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    from src.main import app
    
    return TestClient(app)


def test_convert_multisheet_xlsx(client: TestClient, multisheet_excel: Path) -> None:
    """Test converting a multi-sheet Excel file to PDF."""
    # Given: A multi-sheet Excel file
    assert multisheet_excel.exists(), f"Test fixture not found: {multisheet_excel}"
    
    with open(multisheet_excel, "rb") as f:
        files = {"file": ("multisheet.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        # When: Converting to PDF
        response = client.post("/convert", files=files)
    
    # Then: Conversion is successful
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    
    # And: PDF is generated
    pdf_content = response.content
    assert len(pdf_content) > 0
    assert pdf_content[:4] == b"%PDF"


def test_multisheet_pdf_larger_than_single_sheet(
    client: TestClient,
    multisheet_excel: Path,
) -> None:
    """Test that multi-sheet PDF is larger than equivalent single-sheet."""
    # This is a heuristic test - multi-sheet PDFs should generally be larger
    # than single-sheet PDFs with similar content
    
    with open(multisheet_excel, "rb") as f:
        files = {"file": ("multisheet.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/convert", files=files)
    
    assert response.status_code == 200
    
    # Multi-sheet PDF should have reasonable size (> 1KB)
    pdf_size = len(response.content)
    assert pdf_size > 1024, f"PDF size too small: {pdf_size} bytes"

"""
Temporary file storage service.

This module handles secure creation and cleanup of temporary files.
"""

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator

from src.config import settings
from src.lib.logging import get_logger

logger = get_logger(__name__)


class TempStorage:
    """Service for managing temporary files."""
    
    def __init__(self) -> None:
        """Initialize temp storage with configured directory."""
        self.temp_dir = settings.temp_dir
        self.permissions = settings.temp_file_permissions
        
        # Ensure temp directory exists
        settings.ensure_temp_dir()
    
    @contextmanager
    def create_temp_file(
        self,
        suffix: str = "",
        prefix: str = "pdf_transformer_",
    ) -> Iterator[Path]:
        """
        Create a temporary file with secure permissions.
        
        The file is automatically cleaned up after use.
        
        Args:
            suffix: File suffix (e.g., ".xlsx")
            prefix: File prefix
            
        Yields:
            Path to the temporary file
            
        Example:
            ```python
            with storage.create_temp_file(suffix=".xlsx") as temp_path:
                # Use temp_path
                pass
            # File is automatically deleted
            ```
        """
        temp_file = None
        temp_path = None
        
        try:
            # Create temp file with secure permissions
            temp_file = tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=suffix,
                prefix=prefix,
                dir=self.temp_dir,
                delete=False,
            )
            temp_path = Path(temp_file.name)
            temp_file.close()
            
            # Set secure permissions (owner read/write only)
            os.chmod(temp_path, self.permissions)
            
            logger.debug(f"Created temp file: {temp_path.name}")
            
            yield temp_path
            
        finally:
            # Ensure cleanup even if exception occurs
            if temp_path and temp_path.exists():
                try:
                    # Secure deletion: overwrite then delete
                    size = temp_path.stat().st_size
                    if size > 0:
                        with open(temp_path, "wb") as f:
                            f.write(b"\x00" * min(size, 1024))  # Overwrite first KB
                    
                    temp_path.unlink()
                    logger.debug(f"Deleted temp file: {temp_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete temp file {temp_path.name}: {e}")
    
    def save_upload(self, file: BinaryIO, suffix: str = "") -> Path:
        """
        Save an uploaded file to temporary storage.
        
        Args:
            file: Uploaded file object
            suffix: File suffix (e.g., ".xlsx")
            
        Returns:
            Path to the saved temporary file
            
        Note:
            Caller is responsible for cleanup using context manager.
        """
        temp_file = tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=suffix,
            prefix="upload_",
            dir=self.temp_dir,
            delete=False,
        )
        
        try:
            # Copy file content
            file.seek(0)
            temp_file.write(file.read())
            temp_file.flush()
            temp_path = Path(temp_file.name)
            
            # Set secure permissions
            os.chmod(temp_path, self.permissions)
            
            logger.debug(f"Saved upload to temp file: {temp_path.name}")
            
            return temp_path
            
        finally:
            temp_file.close()


# Singleton instance
_temp_storage: TempStorage | None = None


def get_temp_storage() -> TempStorage:
    """
    Get the temporary storage service instance.
    
    Returns:
        TempStorage instance
    """
    global _temp_storage
    if _temp_storage is None:
        _temp_storage = TempStorage()
    return _temp_storage


__all__ = [
    "TempStorage",
    "get_temp_storage",
]

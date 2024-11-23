"""
Unit tests for file processing.
"""
import pytest
import io
from fastapi import UploadFile
from app.parsers.processor import process_file
from app.core.security import SecurityValidator
from app.core.errors import ValidationError, ProcessingError
from app.config import config

@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        'max_file_size': 1024 * 1024,  # 1MB
        'allowed_types': [
            'text/plain',
            'image/jpeg',
            'image/png',
            'application/pdf'
        ]
    }

@pytest.fixture
def security_validator():
    """Security validator instance."""
    return SecurityValidator()

@pytest.fixture
def text_file():
    """Text file fixture."""
    content = b"Hello, World!"
    return UploadFile(
        filename="test.txt",
        file=io.BytesIO(content),
        size=len(content),
        headers={"content-type": "text/plain"}
    )

@pytest.fixture
def large_file():
    """Large file fixture."""
    content = b"x" * (2 * 1024 * 1024)  # 2MB
    return UploadFile(
        filename="large.txt",
        file=io.BytesIO(content),
        size=len(content),
        headers={"content-type": "text/plain"}
    )

@pytest.fixture
def image_file():
    """Image file fixture."""
    with open("tests/data/test.jpg", "rb") as f:
        content = f.read()
    return UploadFile(
        filename="test.jpg",
        file=io.BytesIO(content),
        size=len(content),
        headers={"content-type": "image/jpeg"}
    )

async def test_process_valid_text_file(text_file, test_config):
    """Test processing valid text file."""
    result = await process_file(text_file, test_config)
    assert result is not None
    assert result['filename'] == "test.txt"
    assert result['content_type'] == "text/plain"
    assert result['size'] == len(b"Hello, World!")

async def test_process_large_file(large_file, test_config):
    """Test processing file exceeding size limit."""
    with pytest.raises(ValidationError) as exc:
        await process_file(large_file, test_config)
    assert "exceeds maximum" in str(exc.value)

async def test_process_invalid_file_type(text_file, test_config):
    """Test processing file with invalid type."""
    test_config['allowed_types'] = ['image/jpeg']
    with pytest.raises(ValidationError) as exc:
        await process_file(text_file, test_config)
    assert "not allowed" in str(exc.value)

async def test_security_validation(security_validator, text_file, test_config):
    """Test security validation."""
    assert await security_validator.validate_file_upload(text_file, test_config)

async def test_security_validation_invalid_filename(security_validator, test_config):
    """Test security validation with invalid filename."""
    file = UploadFile(
        filename="../../../etc/passwd",
        file=io.BytesIO(b"content"),
        size=7,
        headers={"content-type": "text/plain"}
    )
    with pytest.raises(ValidationError) as exc:
        await security_validator.validate_file_upload(file, test_config)
    assert "Invalid filename" in str(exc.value)

async def test_process_image_file(image_file, test_config):
    """Test processing image file."""
    result = await process_file(image_file, test_config)
    assert result is not None
    assert result['filename'] == "test.jpg"
    assert result['content_type'] == "image/jpeg"
    assert 'width' in result
    assert 'height' in result

async def test_process_empty_file(test_config):
    """Test processing empty file."""
    file = UploadFile(
        filename="empty.txt",
        file=io.BytesIO(b""),
        size=0,
        headers={"content-type": "text/plain"}
    )
    with pytest.raises(ProcessingError) as exc:
        await process_file(file, test_config)
    assert "Empty file" in str(exc.value)

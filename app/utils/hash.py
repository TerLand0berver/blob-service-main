"""
Hash utility functions.
"""
from hashlib import sha256, md5
from typing import List


def sha2_file(filename) -> str:
    """Returns hash of file."""
    with open(filename, "rb") as buffer:
        return sha256(buffer.read()).hexdigest()


def md5_file(filename) -> str:
    """Returns hash of file."""
    with open(filename, "rb") as buffer:
        return md5(buffer.read()).hexdigest()


def sha2_encode(string) -> str:
    """Returns hash of string."""
    return sha256(string.encode("utf-8")).hexdigest()


def contains(value: str, items: List[str]) -> bool:
    """Returns True if value is in items or contains it."""
    if not items:
        return False
    return any(item.lower() in value.lower() for item in items)

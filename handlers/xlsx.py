from io import BytesIO
from fastapi import UploadFile
from app.parsers.extractors import SpreadsheetExtractor

async def process(file: UploadFile) -> str:
    """
    Process xlsx/xls/csv file and return its contents along with hyperlinks.
    Format:
      - URL: [content](url)
    """
    content = await file.read()
    extractor = SpreadsheetExtractor(content, file.filename)
    return await extractor.extract()

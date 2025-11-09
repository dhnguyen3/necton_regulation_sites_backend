import requests
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import logging
from typing import Optional, Union
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

def fetch_with_retry(url: str, is_pdf: bool = False) -> Optional[Union[str, bytes]]:
    """Robust document fetcher with retry logic"""
    for attempt in range(settings.MAX_RETRIES):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": settings.USER_AGENT},
                timeout=settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.content if is_pdf else response.text
        except Exception as e:
            if attempt == settings.MAX_RETRIES - 1:
                logger.error(f"Failed to fetch {url} after {settings.MAX_RETRIES} attempts")
                raise
            logger.warning(f"Attempt {attempt + 1} failed for {url}, retrying...")

def extract_pdf_text(filepath: Path) -> Optional[str]:
    """Improved PDF text extraction"""
    try:
        with open(filepath, 'rb') as f:
            reader = PdfReader(f)
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return '\n'.join(text) if text else None
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        return None

def parse_gmp_content(html: str) -> str:
    """GMP-specific content parser"""
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'footer', 'nav', 'header']):
        element.decompose()
    
    # Extract requirement-related content
    requirements = []
    for tag in soup.find_all(['p', 'li', 'article', 'section']):
        text = tag.get_text().strip()
        if text and any(kw in text.lower() for kw in ["shall", "must", "required"]):
            requirements.append(text)
    
    return '\n'.join(requirements) or ' '.join(soup.stripped_strings)

def get_document_content(url: str, is_iso: bool = False) -> Optional[str]:
    """Unified document fetcher"""
    try:
        if url.startswith("file://"):
            filepath = Path(url[7:])
            if not filepath.exists():
                logger.error(f"Local file not found: {filepath}")
                return None
            return extract_pdf_text(filepath)
        
        content = fetch_with_retry(url, is_pdf=is_iso)
        return parse_gmp_content(content) if not is_iso else content
    except Exception as e:
        logger.error(f"Failed to process {url}: {str(e)}")
        return None
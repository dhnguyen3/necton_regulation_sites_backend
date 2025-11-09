import os
import re
import requests
import hashlib
import tempfile
import logging
import time
import functools
from pathlib import Path
from typing import Union, Optional, Dict, List
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
from config.settings import settings

logger = logging.getLogger(__name__)

def retry(attempts=3, delay=2):
    """Native Python retry decorator"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, attempts+1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == attempts:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(attempts=settings.MAX_RETRIES, delay=2)
def download_file(url: str, save_path: Path) -> bool:
    """Download file with retry logic"""
    try:
        response = requests.get(url, headers={"User-Agent": settings.USER_AGENT}, timeout=settings.REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        if save_path.exists():
            save_path.unlink()
        raise

def fetch_iso_content(url: str) -> Optional[str]:
    """Fetch ISO content with auto-download fallback"""
    try:
        if url.startswith("file://"):
            filepath = Path(url[7:])
            if not filepath.exists():
                logger.warning(f"Downloading missing ISO file: {filepath.name}")
                if not download_file(f"https://www.iso.org/obp/ui/#iso:std:{filepath.stem.replace('_','-')}:en", filepath):
                    return None
            
            with open(filepath, 'rb') as f:
                content = extract_pdf_text(f.read())
                return enhance_iso_structure(content) if content else None
        
        return fetch_web_content(url, is_iso=True)
    except Exception as e:
        logger.error(f"ISO fetch failed: {str(e)}")
        return None

def fetch_gmp_content(url: str) -> Optional[str]:
    """Fetch GMP content with enhanced parsing"""
    try:
        content = fetch_web_content(url)
        if not content:
            return None
        return parse_gmp_html(content) if isinstance(content, str) else extract_pdf_text(content)
    except Exception as e:
        logger.error(f"GMP fetch failed: {str(e)}")
        return None

def fetch_web_content(url: str, is_iso: bool = False) -> Optional[Union[str, bytes]]:
    """Universal content fetcher"""
    try:
        response = requests.get(url, headers={"User-Agent": settings.USER_AGENT}, timeout=settings.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.content if is_pdf_content(url, response.content) else response.text
    except Exception as e:
        logger.error(f"Web request failed: {str(e)}")
        return None

def is_pdf_content(url: str, content: Union[bytes, str]) -> bool:
    """Check if content is PDF"""
    return (isinstance(content, bytes) and 
           (url.endswith('.pdf') or content.startswith(b'%PDF')))

def extract_pdf_text(pdf_content: bytes) -> Optional[str]:
    """Robust PDF text extraction"""
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(pdf_content)
            tmp.seek(0)
            reader = PdfReader(tmp.name)
            return '\n'.join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        return None

def parse_gmp_html(html: str) -> str:
    """Extract requirements from GMP HTML"""
    soup = BeautifulSoup(html, 'lxml')
    for element in soup(['script', 'style', 'footer', 'nav']):
        element.decompose()
    
    requirements = []
    for tag in soup.find_all(['p', 'li']):
        text = tag.get_text().strip()
        if any(kw in text.lower() for kw in ["shall", "must", "required"]):
            requirements.append(text)
    
    return '\n'.join(requirements) or soup.get_text()

def enhance_iso_structure(text: str) -> str:
    """Improve ISO document readability"""
    lines = []
    current_section = ""
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+\.\d+', line):
            current_section = line
            lines.append(f"\nSECTION: {line}\n")
        elif current_section:
            lines.append(f"{current_section}: {line}")
    return '\n'.join(lines)

def calculate_hash(content: str) -> str:
    """Generate content hash"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
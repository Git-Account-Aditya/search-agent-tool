from pydantic import BaseModel
from typing import List, Optional, Dict
import trafilatura
import httpx
from PyPDF2 import PdfReader
from io import BytesIO
import asyncio
from urllib.parse import urlparse
import re

class ContentExtractedTool(BaseModel):
    """A tool for extracting content from URLs, handling both HTML and PDF formats."""

    name: str = 'content_extractor'
    description: str = '''
        A tool for performing content extraction from URLs with robust error handling.
        Supports both HTML websites and PDF documents.
    '''

    async def _fetch_url_html(self, url: str, timeout: float = 15) -> Dict[str, str]:
        """Fetch the HTML content of a URL asynchronously with comprehensive error handling."""
        
        # Validate URL format
        try:
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                return {'error': 'Invalid URL format'}
        except Exception:
            return {'error': 'Invalid URL format'}

        # Custom headers to appear more like a regular browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        try:
            async with httpx.AsyncClient(timeout=timeout,
                                       follow_redirects=True,
                                       headers=headers) as client:
                response = await client.get(url)
                response.raise_for_status()
                content_type = response.headers.get('content-type', '').lower()

                if 'pdf' in content_type or url.lower().endswith('.pdf'):
                    return self._extract_pdf_text(response.content)
                else:
                    return self._extract_html_text(response.text, url)

        except httpx.TimeoutException:
            return {'error': 'Request timed out. The website took too long to respond.'}
        except httpx.TooManyRedirects:
            return {'error': 'Too many redirects. The website might be trying to prevent automated access.'}
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 403:
                return {'error': 'Access forbidden. The website has blocked our request.'}
            elif status_code == 404:
                return {'error': 'Page not found. The URL might be invalid or the content has been removed.'}
            elif status_code == 429:
                return {'error': 'Too many requests. The website has rate-limited our access.'}
            elif status_code == 503:
                return {'error': 'Service unavailable. The website might be temporarily down or blocking automated access.'}
            else:
                return {'error': f'HTTP error {status_code}: The website returned an error.'}
        except httpx.HTTPError as e:
            return {'error': f'Connection error: {str(e)}'}
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}

    def _trim_whitespace(self, text: str) -> str:
        """Utility to remove extra whitespace from text."""
        text = re.sub(r'\n{3,}', '\n\n', text)  # Replace 3+ newlines with 2
        text = re.sub(r'\s{2,}', ' ', text)  # Replace 2+ spaces with a single space
        return text.strip()

    def _extract_html_text(self, html: str, url: str, max_len: int = 20000) -> Dict[str, str]:
        """Extract text from HTML content using trafilatura with error handling."""
        try:
            downloaded = trafilatura.extract(html, url=url)
            if not downloaded:
                return {
                    'error': 'No content could be extracted. This might be due to:' + 
                            '\n- Website blocking content extraction' +
                            '\n- JavaScript-heavy website' +
                            '\n- Empty or non-text content'
                }
            
            trimmed_text = self._trim_whitespace(downloaded)
            return {'text': trimmed_text[:max_len], 'source': url}
        except Exception as e:
            return {'error': f'HTML extraction error: {str(e)}'}

    def _extract_pdf_text(self, content_bytes: bytes, max_len: int = 20000) -> Dict[str, str]:
        """Extract text from PDF content using PyPDF with error handling."""
        try:
            reader = PdfReader(stream=content_bytes)
            pages = []

            if len(reader.pages) == 0:
                return {'error': 'PDF appears to be empty'}

            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)
            
            joined_text = "\n".join(pages).strip()
            if not joined_text:
                return {'error': 'PDF contains no extractable text. It might be scanned images or protected.'}
            
            trimmed_text = self._trim_whitespace(joined_text)
            return {'text': trimmed_text[:max_len]}        
        except Exception as e:
            return {'error': f'PDF extraction error: {str(e)}'}

    async def run(self, url: str) -> Dict[str, str]:
        """Extract content from a given URL with retry logic."""
        # Try up to 2 times with a short delay between attempts
        for attempt in range(2):
            result = await self._fetch_url_html(url)
            if not result.get('error') or attempt == 1:
                return result
            await asyncio.sleep(1)  # Wait 1 second before retry
            
        return result
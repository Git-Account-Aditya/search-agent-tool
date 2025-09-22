from pydantic import BaseModel
from typing import List, Optional, Dict
import trafilatura
import httpx
from pypdf import PdfReader


class ContentExtractedTool(BaseModel):
    '''
    '''

    name: str = 'content_extractor'
    description: str = '''
        A tool for performing content extraction from a url.

        Attributes:

    '''

    async def _fetch_url_html(self, url: str, timeout: float = 15) -> Optional[str]:
        """Fetch the HTML content of a URL asynchronously."""
        try:
            async with httpx.AsyncClient(timeout=timeout,
                                         follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                content_type = response.headers.get('content-type', '')

                if 'pdf' in content_type or url.lower().endswith('.pdf'):
                    # save to bytes and use PyPDF to extract text
                    return self._extract_pdf_text(response.content)
                else:
                    # Assume HTML content
                    return self._extract_html_text(response.text, url)
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return None

    def _extract_html_text(self, html: str, url: str)-> Dict[str, str]:
        """Extract text from HTML content using trafilatura."""
        try:
            downloaded = trafilatura.extract(html, url=url)
            return {'text': downloaded} if downloaded else {'error': 'No extractable content found. Possibly blocked or JavaScript-heavy site.'}
        except Exception as e:
            print(f"Error extracting HTML content: {e}")
            return None

    def _extract_pdf_text(self, content_bytes: bytes)-> Dict[str, str]:
        '''Extract text from PDF content using PyPDF.'''
        try:
            reader = PdfReader(stream = content_bytes)
            pages = []

            for page in reader.pages:
                pages.append(page.extract_text() or "")
            
            joined_text = "\n".join(pages).strip()
            if not joined_text:
                return {'error': 'PDF had no extractable text.'}
            return {'text': joined_text}        
        except Exception as e:
            return {'error': str(e)}

    async def run(self, url: str) -> Optional[dict]:
        '''
        Extract content from a given url.
        '''
        html_content = await self._fetch_url_html(url)

        if html_content is None:
            return {
                'error': 'Failed to fetch or extract content for the provided URL.'
            }
        return html_content
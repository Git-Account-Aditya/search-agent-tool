from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
import os
import json
from sqlmodel import SQLModel, Field, Session, select
from typing import Optional, Dict
from datetime import datetime

from backend.agent.web_search import SearchTool
from backend.agent.content_extractor import ContentExtractedTool

from backend.database import get_session

# Load environment variables from a .env file
load_dotenv()
router = APIRouter()

class SearchHistory(SQLModel, table=True):
    __name__ = "search_history"
    id: Optional[int] = Field(default=None, primary_key=True)
    query: str
    search_results: Dict
    extracted_contents: Dict
    timestamp: datetime = Field(default_factory=datetime.get_utcnow)

# Initialize the search tool with the API key from environment variables
serp_apikey = os.getenv('SERPAPI_API_KEY')

@router.get('/search')
async def search(query: str):
    try:
        # 1. Perform search
        search_tool = SearchTool(apikey=serp_apikey)
        search_results = await search_tool.run(query)
        
        # 2. Extract content from each URL
        extractor = ContentExtractedTool()
        extracted_contents = {}
        
        for result_id, result in search_results.items():
            url = result['link']
            content = await extractor.run(url)
            extracted_contents[url] = content

        # 3. Store in database
        db_entry = SearchHistory(
            query=query,
            search_results=search_results,
            extracted_contents=extracted_contents
        )
        
        # Add database save logic here
        with get_session() as session:
            session.add(db_entry)
            session.commit()
            session.refresh(db_entry)

        return {
            "query": query,
            "search_results": search_results,
            "extracted_contents": extracted_contents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/extract_content')
def extract_content(url: str):
    content_extract_tool = ContentExtractedTool()
    try:
        print('Executing Content Extraction Tool...')
        result = content_extract_tool.run(url)
        print('Content Extraction Completed.')

        # Check if result exists or not
        if not result:
            raise HTTPException(status_code=404,
                                detail='No content extracted.')
        # Check if there was an error during extraction
        elif result['error']:
            raise HTTPException(status_code=400,
                                detail=f'error: {result['error']}')
        else:
            return result
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=str(e))

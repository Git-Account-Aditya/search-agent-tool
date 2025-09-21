from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
import os
import json

from backend.agent.web_search import SearchTool

# Load environment variables from a .env file
load_dotenv()
router = APIRouter()

# Initialize the search tool with the API key from environment variables
serp_apikey = os.getenv('SERPAPI_API_KEY')

@router.get('/search')
def search(query: str):
    search_tool = SearchTool(apikey = serp_apikey)
    try:
        print('Executing Searching Tool...')
        result = search_tool.run(query)
        print('Search Completed.')
        if not result:
            raise HTTPException(status_code=404,
                                detail="No result found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result

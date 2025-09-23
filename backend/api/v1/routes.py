from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import os
import json
from sqlmodel import SQLModel, Field, Session, select, Column, TIMESTAMP, text, JSON
from typing import Optional, Dict
from datetime import datetime

from backend.agent.web_search import SearchTool
from backend.agent.content_extractor import ContentExtractedTool

from backend.database.db import get_session, ReportHistory, SearchHistory
from backend.llm.get_report import ReportGenerator

# Load environment variables from a .env file
load_dotenv()
router = APIRouter()


# Initialize the search tool with the API key from environment variables
serp_apikey = os.getenv('SERPAPI_API_KEY')

@router.get('/search')
async def search(query: str, session: AsyncSession = Depends(get_session)):
    """
    Perform a web search and extract content from results with comprehensive error handling.
    """
    try:
        # Validate query
        if not query or len(query.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Search query must be at least 3 characters long"
            )

        # 1. Perform search with error handling
        search_tool = SearchTool(apikey=serp_apikey)
        if not serp_apikey:
            raise HTTPException(
                status_code=500,
                detail="Search API key not configured"
            )

        search_results = await search_tool.run(query)
        
        if isinstance(search_results, str):  # Error case from search tool
            raise HTTPException(status_code=400, detail=search_results)
        
        if not search_results:
            return {
                "query": query,
                "message": "No search results found",
                "search_results": {},
                "extracted_contents": {}
            }

        # 2. Extract content with error tracking
        extractor = ContentExtractedTool()
        extracted_contents = {}
        successful_results = {}
        failed_extractions = {}
        
        for result_id, result in search_results.items():
            try:
                url = result['link']
                content = await extractor.run(url)
                
                if content and not content.get('error'):
                    extracted_contents[url] = content
                    successful_results[result_id] = result
                else:
                    failed_extractions[url] = content.get('error', 'Unknown error')
            except Exception as e:
                failed_extractions[url] = str(e)

        # 3. Prepare response based on results
        if not successful_results:
            return {
                "query": query,
                "message": "Content extraction failed for all results",
                "search_results": {},
                "extracted_contents": {},
                "failed_urls": failed_extractions
            }

        # 4. Store successful results in database
        try:
            db_entry = SearchHistory(query=query)   
            db_entry.set_search_results(successful_results)
            db_entry.set_extracted_contents(extracted_contents)

            report_generator = ReportGenerator()
            results = await report_generator.generate_report(data={
                                                                "query": query,
                                                                "results": successful_results,
                                                                "extracted_contents": extracted_contents
                                                            }, temperature=0.2)
            if not isinstance(results, dict):
                raise ValueError("Report generation failed")
            
            print('Storing data in database...')
            db_report = ReportHistory(
                title=results.get('title', f"Report for: {query}"),
                detailed_summary=results.get('detailed_summary', 'Summary not available')
            ) 
            print(results)   
            links = results.get('links', {})
            db_report.set_links(links)

            print(db_report.detailed_summary, '...')
            # Use the session from dependency injection
            session.add(db_entry)
            session.add(db_report)
            await session.commit()
            await session.refresh(db_entry)
            await session.refresh(db_report)
            
            # Query the report using the same session
            report = await session.execute(
                select(ReportHistory.detailed_summary)
                .where(ReportHistory.id == db_report.id))
            
            report_result = report.scalars().first()
            print(json.dumps(report_result))
            return json.dumps(report_result)
        
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")

        return {
            "query": query,
            "message": "Search completed successfully",
            "search_results": results,
            "extracted_contents": extracted_contents,
            "stats": {
                "total_results": len(search_results),
                "successful_extractions": len(successful_results),
                "failed_extractions": len(failed_extractions)
            },
            "failed_urls": failed_extractions if failed_extractions else None
        }

    except HTTPException as http_ex:
        raise http_ex
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


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


@router.get('/history')
async def get_search_history(session: AsyncSession = Depends(get_session)):
    """Retrieve all search history entries."""
    try:
        query = select(SearchHistory).order_by(SearchHistory.created_datetime.desc())
        result = await session.execute(query)
        history = result.scalars().all()
        
        # Convert JSON strings back to dictionaries for response
        return [{
            "id": entry.id,
            "query": entry.query,
            "search_results": entry.get_search_results(),
            "extracted_contents": entry.get_extracted_contents(),
            "created_datetime": entry.created_datetime
        } for entry in history]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve search history: {str(e)}"
        )

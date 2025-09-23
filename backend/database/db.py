from sqlmodel import SQLModel, create_engine, Session, Column, TIMESTAMP, text, JSON, Field
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from typing import List, Dict, Annotated, Any, Optional, AsyncGenerator
from datetime import datetime
import json

# Change SQLite URL to async version
DATABASE_URL = 'sqlite+aiosqlite:///./test.db'

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session for database operations."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

class ReportHistory(SQLModel, table=True):
    __tablename__ = 'reports'

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(..., description='The title of the report')
    detailed_summary: str = Field(..., description="A detailed summary of the report in at least 500 words")
    links: Dict[str, str] = Field(default_factory=dict, description="A dictionary of urls used to generate report",
                                  sa_column=Column(JSON))
    created_datetime: datetime= Field(
                                    sa_column=Column(
                                        TIMESTAMP(timezone=True),
                                        nullable=False,
                                        server_default=text('CURRENT_TIMESTAMP')
                                    )
                                )
    
    def set_links(self, links_dict: Dict[str, str]):
        """Convert dictionary to JSON string before storing"""
        self.links = json.dumps(links_dict)

    def get_links(self) -> Dict[str, str]:
        """Convert stored JSON string back to dictionary"""
        return json.loads(self.links)


class SearchHistory(SQLModel, table=True):
    __tablename__ = "searches"
    id: Optional[int] = Field(default=None, primary_key=True)
    query: str = Field(..., description="User's request for report")
    search_results: str = Field(
        default="{}",
        description="JSON string of search results",
        sa_column=Column(JSON)
    )
    extracted_contents: str = Field(
        default="{}",
        description="JSON string of extracted contents",
        sa_column=Column(JSON)
    )
    created_datetime: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP")
        )
    )

    def set_search_results(self, results: dict):
        """Convert dictionary to JSON string before storing"""
        self.search_results = json.dumps(results)

    def get_search_results(self) -> dict:
        """Convert stored JSON string back to dictionary"""
        return json.loads(self.search_results)

    def set_extracted_contents(self, contents: dict):
        """Convert dictionary to JSON string before storing"""
        self.extracted_contents = json.dumps(contents)

    def get_extracted_contents(self) -> dict:
        """Convert stored JSON string back to dictionary"""
        return json.loads(self.extracted_contents)

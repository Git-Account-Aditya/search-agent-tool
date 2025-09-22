from sqlmodel import SQLModel, create_engine, Session, Column, TIMESTAMP, text, JSON
from pydantic import BaseModel, Field

from typing import List, Dict, Annotated, Any, Optional
from datetime import datetime

DATABASE_URL = 'sqlite:///./test.db'

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.mdetadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

class ReportHistory(SQLModel, BaseModel, table=True):
    __tablename__ = 'reports'

    id: Optional[int] = Field(default=None, primary_key=True)
    title = Annotated[str, Field(..., description='The title of the report')]
    detailed_summary: Annotated[str, Field(..., description="A detailed summary of the report in at least 500 words")]
    links: Annotated[Dict[str, str], Field(..., description="A dictionary of urls used to generate report")]
    created_datetime: Annotated[datetime,
                                Field(
                                    sa_column=Column(
                                        TIMESTAMP(timezone=True),
                                        nullable=False,
                                        server_default=text('now()')
                                    )
                                )]

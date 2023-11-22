from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Link(BaseModel):
    id: Optional[int] = Field(None, description="The unique ID of the link")
    link: str = Field(..., description="The link URL")
    content_file: Optional[str] = Field(None, description="Path to the content file")
    email: Optional[str] = Field(None, description="Email address")
    contact_name: Optional[str] = Field(None, description="Contact name")
    industry: Optional[str] = Field(None, description="Industry")
    city: Optional[str] = Field(None, description="City")
    area: Optional[str] = Field(None, description="Area")
    parsed: bool = Field(False, description="Parsing status")
    contacted_at: Optional[datetime] = Field(
        None, description="Timestamp of when contact was made"
    )
    created_at: Optional[datetime] = Field(
        None, description="Timestamp of record creation"
    )

    class Config:
        from_attributes = True


class EmailEvent(BaseModel):
    # id: int
    # link_id: int
    link: str
    # qc_result: int
    # qc_date: Optional[datetime]  # Use Optional if the field can be null
    # email_content: str
    contacted_at: Optional[datetime]  # Use Optional if the field can be null

    class Config:
        from_attributes = True

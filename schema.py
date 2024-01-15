from pydantic import BaseModel, Field
from typing import Optional


class Link(BaseModel):
    id: Optional[int] = Field(None, description="The unique ID of the link")
    link: str = Field(..., description="The link URL")
    content_file: Optional[str] = Field(None, description="Path to the content file")
    email: Optional[str] = Field(None, description="Email address")
    contact_name: Optional[str] = Field(None, description="Contact name")
    pronoun: Optional[str] = Field(None, description="Pronoun")
    industry: Optional[str] = Field(None, description="Industry")
    city: Optional[str] = Field(None, description="City")
    area: Optional[str] = Field(None, description="Area")
    parsed: bool = Field(False, description="Parsing status")

    class Config:
        from_attributes = True

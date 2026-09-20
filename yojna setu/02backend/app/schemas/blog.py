from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class FinancialBlogInput(BaseModel):
    title: str = Field(..., min_length=3, max_length=180)
    summary: str = Field(..., min_length=10, max_length=500)
    content: str = Field(..., min_length=20, max_length=50000)


class FinancialBlogResponse(FinancialBlogInput):
    blog_id: str
    author_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FinancialBlogListResponse(BaseModel):
    items: List[FinancialBlogResponse]

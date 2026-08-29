from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(..., description="Standardized machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    request_id: Optional[str] = Field(None, description="Correlation request ID for tracking")
    details: Optional[Any] = Field(None, description="Optional field-level validation errors or metadata")


class StandardErrorResponse(BaseModel):
    error: ErrorBody

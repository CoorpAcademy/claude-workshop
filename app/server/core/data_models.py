from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

# Relationship Models
class RelationshipType(str, Enum):
    one_to_one = "one_to_one"
    one_to_many = "one_to_many"
    many_to_many = "many_to_many"

class FieldRelationship(BaseModel):
    source_collection: str
    source_field: str
    target_collection: str
    target_field: str
    relationship_type: RelationshipType
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class CollectionRelationships(BaseModel):
    collection_name: str
    relationships: List[FieldRelationship]

# File Upload Models
class FileUploadRequest(BaseModel):
    # Handled by FastAPI UploadFile, no request model needed
    pass

class FileUploadResponse(BaseModel):
    collection_name: str
    schema: Dict[str, str]  # field_name: data_type
    document_count: int
    sample_data: List[Dict[str, Any]]
    error: Optional[str] = None

# Query Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    llm_provider: Literal["openai", "anthropic"] = "openai"
    collection_name: Optional[str] = None  # If querying specific collection

class CrossCollectionQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    llm_provider: Literal["openai", "anthropic"] = "openai"
    collections: List[str] = Field(..., description="Collections involved in the query")
    relationships: List[FieldRelationship] = Field(default_factory=list)

class QueryResponse(BaseModel):
    mongodb_query: Dict[str, Any]  # The generated MongoDB query
    results: List[Dict[str, Any]]
    fields: List[str]
    document_count: int
    execution_time_ms: float
    error: Optional[str] = None

# Database Schema Models
class FieldInfo(BaseModel):
    name: str
    type: str
    sample: Optional[Any] = None

class CollectionSchema(BaseModel):
    name: str
    fields: List[FieldInfo]
    document_count: int

class DatabaseSchemaRequest(BaseModel):
    pass  # No input needed

class DatabaseSchemaResponse(BaseModel):
    collections: List[CollectionSchema]
    total_collections: int
    relationships: List[FieldRelationship] = Field(default_factory=list)
    error: Optional[str] = None

# Insights Models
class InsightsRequest(BaseModel):
    collection_name: str
    field_names: Optional[List[str]] = None  # If None, analyze all fields

class ColumnInsight(BaseModel):
    column_name: str
    data_type: str
    unique_values: int
    null_count: int
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[float] = None
    most_common: Optional[List[Dict[str, Any]]] = None

class InsightsResponse(BaseModel):
    collection_name: str
    insights: List[ColumnInsight]
    generated_at: datetime
    error: Optional[str] = None

# Health Check Models
class HealthCheckRequest(BaseModel):
    pass

class HealthCheckResponse(BaseModel):
    status: Literal["ok", "error"]
    database_connected: bool
    collections_count: int
    version: str = "1.0.0"
    uptime_seconds: float
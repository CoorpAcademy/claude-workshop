// These must match the Pydantic models exactly

// File Upload Types
interface FileUploadResponse {
  collection_name: string;
  schema: Record<string, string>;
  document_count: number;
  sample_data: Record<string, any>[];
  error?: string;
}

// Query Types
interface QueryRequest {
  query: string;
  llm_provider: "openai" | "anthropic";
  collection_name?: string;
}

interface QueryResponse {
  mongodb_query: Record<string, any>;
  results: Record<string, any>[];
  fields: string[];
  document_count: number;
  execution_time_ms: number;
  error?: string;
}

// Relationship Types
type RelationshipType = "one_to_one" | "one_to_many" | "many_to_many";

interface FieldRelationship {
  source_collection: string;
  source_field: string;
  target_collection: string;
  target_field: string;
  relationship_type: RelationshipType;
  confidence_score: number;
}

// Database Schema Types
interface FieldInfo {
  name: string;
  type: string;
  sample?: any;
}

interface CollectionSchema {
  name: string;
  fields: FieldInfo[];
  document_count: number;
}

interface DatabaseSchemaResponse {
  collections: CollectionSchema[];
  total_collections: number;
  relationships?: FieldRelationship[];
  error?: string;
}

// Cross-Collection Query Types
interface CrossCollectionQueryRequest extends QueryRequest {
  collections: string[];
  relationships?: FieldRelationship[];
}

// Insights Types
interface InsightsRequest {
  collection_name: string;
  field_names?: string[];
}

interface ColumnInsight {
  column_name: string;
  data_type: string;
  unique_values: number;
  null_count: number;
  min_value?: any;
  max_value?: any;
  avg_value?: number;
  most_common?: Record<string, any>[];
}

interface InsightsResponse {
  collection_name: string;
  insights: ColumnInsight[];
  generated_at: string;
  error?: string;
}

// Health Check Types
interface HealthCheckResponse {
  status: "ok" | "error";
  database_connected: boolean;
  collections_count: number;
  version: string;
  uptime_seconds: number;
}
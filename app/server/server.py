from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import traceback
from typing import Optional
from dotenv import load_dotenv
import logging
import sys
import time

# Load .env file from server directory
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

from core.data_models import (
    FileUploadResponse,
    QueryRequest,
    QueryResponse,
    DatabaseSchemaResponse,
    InsightsRequest,
    InsightsResponse,
    HealthCheckResponse,
    CollectionSchema,
    FieldInfo
)

# Import core modules
from core.file_processor import convert_csv_to_mongodb, convert_json_to_mongodb
from core.llm_processor import generate_mongodb_query
from core.mongo_processor import (
    get_mongodb_connection,
    execute_mongodb_query,
    execute_aggregation_pipeline,
    get_database_schema,
    drop_collection,
    close_mongodb_connection
)
from core.insights import generate_insights
from core.mongo_security import validate_collection_name, MongoSecurityError

app = FastAPI(
    title="Natural Language MongoDB Query Interface",
    description="Convert natural language to MongoDB queries",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global app state
app_start_time = datetime.now()


@app.on_event("startup")
async def startup_event():
    """Verify MongoDB connection on startup"""
    try:
        client = get_mongodb_connection()
        db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
        db = client[db_name]
        # Test connection
        db.command('ping')
        logger.info(f"[SUCCESS] Connected to MongoDB database: {db_name}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to connect to MongoDB: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    close_mongodb_connection()
    logger.info("[INFO] MongoDB connection closed")


@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)) -> FileUploadResponse:
    """Upload and convert .json or .csv file to MongoDB collection"""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.json')):
            raise HTTPException(400, "Only .csv and .json files are supported")

        # Generate collection name from filename
        collection_name = file.filename.rsplit('.', 1)[0].lower().replace(' ', '_')

        # Read file content
        content = await file.read()

        # Convert to MongoDB based on file type
        if file.filename.endswith('.csv'):
            result = convert_csv_to_mongodb(content, collection_name)
        else:
            result = convert_json_to_mongodb(content, collection_name)

        response = FileUploadResponse(
            collection_name=result['collection_name'],
            schema=result['schema'],
            document_count=result['document_count'],
            sample_data=result['sample_data']
        )
        logger.info(f"[SUCCESS] File upload: {response.collection_name}, {response.document_count} documents")
        return response
    except Exception as e:
        logger.error(f"[ERROR] File upload failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return FileUploadResponse(
            collection_name="",
            schema={},
            document_count=0,
            sample_data=[],
            error=str(e)
        )


@app.post("/api/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest) -> QueryResponse:
    """Process natural language query and return MongoDB results"""
    try:
        # Get database schema
        schema_info = get_database_schema()

        # Generate MongoDB query using routing logic
        mongo_query = generate_mongodb_query(request, schema_info)

        # Extract query components
        query_type = mongo_query.get('query_type', 'find')
        collection_name = mongo_query.get('collection')
        query = mongo_query.get('query')
        sort = mongo_query.get('sort')
        limit = mongo_query.get('limit', 100)

        # Detect cross-collection query
        is_cross_collection = False
        collections_involved = [collection_name]

        if query_type == 'aggregate' and isinstance(query, list):
            # Check for $lookup stages
            for stage in query:
                if '$lookup' in stage:
                    is_cross_collection = True
                    lookup_collection = stage['$lookup'].get('from')
                    if lookup_collection and lookup_collection not in collections_involved:
                        collections_involved.append(lookup_collection)

        if is_cross_collection:
            logger.info(f"[INFO] Cross-collection query detected: {', '.join(collections_involved)}")

        # Execute MongoDB query
        start_time = time.time()

        if query_type == 'aggregate':
            # Execute aggregation pipeline
            if is_cross_collection:
                logger.info(f"[INFO] Executing cross-collection aggregation with {len(query)} stages")
            results = execute_aggregation_pipeline(collection_name, query)
        else:
            # Execute find query
            results = execute_mongodb_query(
                collection_name=collection_name,
                filter_query=query,
                sort=sort,
                limit=limit
            )

        execution_time = (time.time() - start_time) * 1000

        # Extract field names from results
        fields = []
        if results:
            fields = list(results[0].keys())

        response = QueryResponse(
            mongodb_query=mongo_query,
            results=results,
            fields=fields,
            document_count=len(results),
            execution_time_ms=execution_time
        )

        log_msg = f"[SUCCESS] Query processed: collection={collection_name}, documents={len(results)}, time={execution_time:.2f}ms"
        if is_cross_collection:
            log_msg += f", cross-collection=True, collections={len(collections_involved)}"
        logger.info(log_msg)

        return response
    except Exception as e:
        logger.error(f"[ERROR] Query processing failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return QueryResponse(
            mongodb_query={},
            results=[],
            fields=[],
            document_count=0,
            execution_time_ms=0,
            error=str(e)
        )


@app.get("/api/schema", response_model=DatabaseSchemaResponse)
async def get_database_schema_endpoint() -> DatabaseSchemaResponse:
    """Get current database schema and collection information"""
    try:
        schema_result = get_database_schema()
        collections = []

        # Handle new format with collections and relationships
        schema_collections = schema_result.get("collections", schema_result)
        relationships = schema_result.get("relationships", [])

        for collection_name, collection_info in schema_collections.items():
            fields = []
            for field_name, field_info in collection_info.get('fields', {}).items():
                fields.append(FieldInfo(
                    name=field_name,
                    type=field_info.get('type', 'unknown'),
                    sample=field_info.get('sample')
                ))

            collections.append(CollectionSchema(
                name=collection_name,
                fields=fields,
                document_count=collection_info.get('count', 0)
            ))

        response = DatabaseSchemaResponse(
            collections=collections,
            total_collections=len(collections),
            relationships=relationships
        )
        logger.info(f"[SUCCESS] Schema retrieved: {len(collections)} collections, {len(relationships)} relationships")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Schema retrieval failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return DatabaseSchemaResponse(
            collections=[],
            total_collections=0,
            relationships=[],
            error=str(e)
        )


@app.post("/api/insights", response_model=InsightsResponse)
async def generate_insights_endpoint(request: InsightsRequest) -> InsightsResponse:
    """Generate statistical insights for collection fields"""
    try:
        insights = generate_insights(request.collection_name, request.field_names)
        response = InsightsResponse(
            collection_name=request.collection_name,
            insights=insights,
            generated_at=datetime.now()
        )
        logger.info(f"[SUCCESS] Insights generated for collection: {request.collection_name}, insights count: {len(insights)}")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Insights generation failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return InsightsResponse(
            collection_name=request.collection_name,
            insights=[],
            generated_at=datetime.now(),
            error=str(e)
        )


@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint with database status"""
    try:
        # Check database connection
        client = get_mongodb_connection()
        db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
        db = client[db_name]

        # Test connection
        db.command('ping')

        # Get collection count
        collections = db.list_collection_names()
        collection_count = len([c for c in collections if not c.startswith('system.')])

        uptime = (datetime.now() - app_start_time).total_seconds()

        response = HealthCheckResponse(
            status="ok",
            database_connected=True,
            collections_count=collection_count,
            uptime_seconds=uptime
        )
        logger.info(f"[SUCCESS] Health check: OK, {collection_count} collections, uptime: {uptime:.2f}s")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Health check failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return HealthCheckResponse(
            status="error",
            database_connected=False,
            collections_count=0,
            uptime_seconds=0
        )


@app.delete("/api/collection/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection from the database"""
    try:
        # Validate collection name using security module
        try:
            validate_collection_name(collection_name)
        except MongoSecurityError as e:
            raise HTTPException(400, str(e))

        # Check if collection exists
        client = get_mongodb_connection()
        db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
        db = client[db_name]
        collections = db.list_collection_names()

        if collection_name not in collections:
            raise HTTPException(404, f"Collection '{collection_name}' not found")

        # Drop the collection
        drop_collection(collection_name)

        response = {"message": f"Collection '{collection_name}' deleted successfully"}
        logger.info(f"[SUCCESS] Collection deleted: {collection_name}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Collection deletion failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error deleting collection: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

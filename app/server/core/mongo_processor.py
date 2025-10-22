"""
MongoDB Processor Module

This module handles all MongoDB database operations including connection management,
query execution, schema retrieval, and collection statistics.
"""

import os
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ConnectionFailure, OperationFailure
from bson import ObjectId
from dotenv import load_dotenv

from .mongo_security import (
    validate_collection_name,
    validate_query_structure,
    validate_aggregation_pipeline,
    validate_sort_specification,
    validate_projection,
    MongoSecurityError
)
from .relationship_detector import detect_all_relationships

load_dotenv()

# Global MongoDB client (singleton pattern for connection pooling)
_mongo_client: Optional[MongoClient] = None


def convert_objectids_to_strings(data: Any) -> Any:
    """
    Recursively convert all BSON ObjectId instances to strings in a data structure.

    This function traverses dictionaries, lists, and nested structures to find and
    convert any ObjectId instances to their string representation, making the data
    JSON-serializable for FastAPI/Pydantic responses.

    Args:
        data: Any data structure (dict, list, ObjectId, or primitive type)

    Returns:
        A new data structure with all ObjectIds converted to strings.
        Primitive types are returned as-is.
    """
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {key: convert_objectids_to_strings(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectids_to_strings(item) for item in data]
    else:
        return data


def get_mongodb_connection() -> MongoClient:
    """
    Get or create MongoDB client connection.

    Returns:
        MongoClient instance with connection pooling

    Raises:
        ConnectionFailure: If unable to connect to MongoDB
    """
    global _mongo_client

    if _mongo_client is None:
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        try:
            _mongo_client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Test the connection
            _mongo_client.admin.command('ping')
        except ConnectionFailure as e:
            raise ConnectionFailure(f"Failed to connect to MongoDB: {str(e)}")

    return _mongo_client


def close_mongodb_connection():
    """Close the MongoDB connection if it exists"""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


def execute_mongodb_query(
    collection_name: str,
    filter_query: Optional[Dict[str, Any]] = None,
    projection: Optional[Dict[str, Any]] = None,
    sort: Optional[Dict[str, int]] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Execute a MongoDB find query safely.

    Args:
        collection_name: Name of the collection to query
        filter_query: MongoDB filter query dictionary (default: {})
        projection: Fields to include/exclude in results
        sort: Sort specification (field -> direction mapping)
        limit: Maximum number of documents to return

    Returns:
        List of documents matching the query

    Raises:
        MongoSecurityError: If validation fails
        OperationFailure: If the query fails
    """
    # Validate inputs
    validate_collection_name(collection_name)

    if filter_query is None:
        filter_query = {}

    if filter_query:
        validate_query_structure(filter_query)

    if projection:
        validate_projection(projection)

    if sort:
        validate_sort_specification(sort)

    # Get database
    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]
    collection = db[collection_name]

    try:
        # Build cursor
        cursor = collection.find(filter_query, projection)

        if sort:
            cursor = cursor.sort(list(sort.items()))

        cursor = cursor.limit(limit)

        # Convert cursor to list and handle ObjectId serialization
        results = []
        for doc in cursor:
            # Convert all ObjectIds to strings for JSON serialization
            doc = convert_objectids_to_strings(doc)
            results.append(doc)

        return results

    except OperationFailure as e:
        raise OperationFailure(f"MongoDB query failed: {str(e)}")


def execute_aggregation_pipeline(
    collection_name: str,
    pipeline: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Execute a MongoDB aggregation pipeline safely.

    Args:
        collection_name: Name of the collection to query
        pipeline: List of aggregation stages

    Returns:
        List of documents from the aggregation result

    Raises:
        MongoSecurityError: If validation fails
        OperationFailure: If the aggregation fails
    """
    # Validate inputs
    validate_collection_name(collection_name)
    validate_aggregation_pipeline(pipeline)

    # Get database
    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]
    collection = db[collection_name]

    try:
        # Execute aggregation
        cursor = collection.aggregate(pipeline)

        # Convert cursor to list and handle ObjectId serialization
        results = []
        for doc in cursor:
            # Convert all ObjectIds to strings for JSON serialization
            doc = convert_objectids_to_strings(doc)
            results.append(doc)

        return results

    except OperationFailure as e:
        raise OperationFailure(f"MongoDB aggregation failed: {str(e)}")


def get_database_schema() -> Dict[str, Any]:
    """
    Get schema information for all collections in the database.

    Returns:
        Dictionary containing collection names and their schemas
    """
    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]

    schema = {}

    try:
        # Get all collection names
        collection_names = db.list_collection_names()

        for collection_name in collection_names:
            # Skip system collections
            if collection_name.startswith("system."):
                continue

            collection = db[collection_name]

            # Get sample documents to infer schema
            sample_docs = list(collection.find().limit(10))

            if not sample_docs:
                schema[collection_name] = {
                    "count": 0,
                    "fields": {}
                }
                continue

            # Infer schema from sample documents
            fields = {}
            for doc in sample_docs:
                for field_name, field_value in doc.items():
                    if field_name not in fields:
                        fields[field_name] = {
                            "type": type(field_value).__name__,
                            "sample": convert_objectids_to_strings(field_value)
                        }

            schema[collection_name] = {
                "count": collection.count_documents({}),
                "fields": fields,
                "sample_data": [convert_objectids_to_strings(doc) for doc in sample_docs[:3]]
            }

        # Detect relationships between collections
        relationships = []
        try:
            # Build schema_info for relationship detection
            schema_info = {}
            for coll_name, coll_data in schema.items():
                schema_info[coll_name] = {
                    field_name: field_data["type"]
                    for field_name, field_data in coll_data.get("fields", {}).items()
                }

            # Detect relationships
            relationships = detect_all_relationships(schema_info, db, min_confidence=0.3)

        except Exception as e:
            # Log but don't fail if relationship detection fails
            import logging
            logging.error(f"Relationship detection failed: {e}")

        return {"collections": schema, "relationships": relationships}

    except PyMongoError as e:
        raise PyMongoError(f"Failed to retrieve database schema: {str(e)}")


def get_collection_stats(collection_name: str) -> Dict[str, Any]:
    """
    Get statistics for a specific collection.

    Args:
        collection_name: Name of the collection

    Returns:
        Dictionary containing collection statistics

    Raises:
        MongoSecurityError: If collection name is invalid
    """
    validate_collection_name(collection_name)

    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]
    collection = db[collection_name]

    try:
        stats = {
            "name": collection_name,
            "count": collection.count_documents({}),
            "indexes": [idx for idx in collection.list_indexes()],
        }

        # Get collection stats from MongoDB
        db_stats = db.command("collStats", collection_name)
        stats["size_bytes"] = db_stats.get("size", 0)
        stats["storage_size_bytes"] = db_stats.get("storageSize", 0)

        return stats

    except OperationFailure as e:
        raise OperationFailure(f"Failed to get collection stats: {str(e)}")


def drop_collection(collection_name: str) -> bool:
    """
    Drop a collection from the database.

    Args:
        collection_name: Name of the collection to drop

    Returns:
        True if successful

    Raises:
        MongoSecurityError: If collection name is invalid
    """
    validate_collection_name(collection_name)

    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]

    try:
        db.drop_collection(collection_name)
        return True

    except OperationFailure as e:
        raise OperationFailure(f"Failed to drop collection: {str(e)}")


def create_collection(collection_name: str) -> bool:
    """
    Create a new collection.

    Args:
        collection_name: Name of the collection to create

    Returns:
        True if successful

    Raises:
        MongoSecurityError: If collection name is invalid
    """
    validate_collection_name(collection_name)

    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]

    try:
        db.create_collection(collection_name)
        return True

    except OperationFailure as e:
        raise OperationFailure(f"Failed to create collection: {str(e)}")


def insert_documents(collection_name: str, documents: List[Dict[str, Any]]) -> int:
    """
    Insert multiple documents into a collection.

    Args:
        collection_name: Name of the collection
        documents: List of documents to insert

    Returns:
        Number of documents inserted

    Raises:
        MongoSecurityError: If collection name is invalid
        OperationFailure: If insertion fails
    """
    validate_collection_name(collection_name)

    if not documents:
        return 0

    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]
    collection = db[collection_name]

    try:
        result = collection.insert_many(documents)
        return len(result.inserted_ids)

    except OperationFailure as e:
        raise OperationFailure(f"Failed to insert documents: {str(e)}")

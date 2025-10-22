import json
import pandas as pd
import io
import re
import os
from typing import Dict, Any, List
from .mongo_security import validate_collection_name, MongoSecurityError
from .mongo_processor import insert_documents, drop_collection, get_mongodb_connection, convert_objectids_to_strings


def sanitize_collection_name(collection_name: str) -> str:
    """
    Sanitize collection name for MongoDB by removing/replacing bad characters
    and validating against NoSQL injection
    """
    # Remove file extension if present
    if '.' in collection_name:
        collection_name = collection_name.rsplit('.', 1)[0]

    # Replace bad characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', collection_name)

    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = '_' + sanitized

    # Ensure it's not empty
    if not sanitized:
        sanitized = 'collection'

    # Validate the sanitized name
    try:
        validate_collection_name(sanitized)
    except MongoSecurityError:
        # If validation fails, use a safe default
        sanitized = f"collection_{hash(collection_name) % 100000}"

    return sanitized


def collection_exists(collection_name: str) -> bool:
    """
    Check if a collection exists in the MongoDB database.

    Args:
        collection_name: Name of the collection to check

    Returns:
        True if collection exists, False otherwise
    """
    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]

    collection_names = db.list_collection_names()
    return collection_name in collection_names


def infer_field_types(documents: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Infer field types from a list of documents

    Args:
        documents: List of document dictionaries

    Returns:
        Dictionary mapping field names to type names
    """
    field_types = {}

    for doc in documents:
        for field_name, field_value in doc.items():
            if field_name not in field_types:
                # Map Python types to MongoDB type names
                python_type = type(field_value).__name__
                if python_type in ['int', 'int64']:
                    field_types[field_name] = 'number'
                elif python_type in ['float', 'float64']:
                    field_types[field_name] = 'double'
                elif python_type == 'bool':
                    field_types[field_name] = 'boolean'
                elif python_type == 'list':
                    field_types[field_name] = 'array'
                elif python_type == 'dict':
                    field_types[field_name] = 'object'
                elif python_type == 'NoneType':
                    field_types[field_name] = 'null'
                else:
                    field_types[field_name] = 'string'

    return field_types


def convert_csv_to_mongodb(csv_content: bytes, collection_name: str) -> Dict[str, Any]:
    """
    Convert CSV file content to MongoDB collection

    Args:
        csv_content: Raw CSV file bytes
        collection_name: Name for the collection

    Returns:
        Dictionary with collection info, schema, and sample data

    Raises:
        Exception: If conversion fails
    """
    try:
        # Sanitize collection name
        collection_name = sanitize_collection_name(collection_name)

        # Drop existing collection if it exists to replace data (as documented)
        if collection_exists(collection_name):
            drop_collection(collection_name)

        # Read CSV into pandas DataFrame
        df = pd.read_csv(io.BytesIO(csv_content))

        # Clean column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]

        # Convert DataFrame to list of dictionaries
        # Replace NaN with None for proper JSON serialization
        df = df.where(pd.notnull(df), None)
        documents = df.to_dict('records')

        if not documents:
            raise ValueError("CSV file is empty")

        # Insert documents into MongoDB
        inserted_count = insert_documents(collection_name, documents)

        # Infer schema from documents
        schema = infer_field_types(documents)

        # Get sample data (first 5 documents)
        sample_data = [convert_objectids_to_strings(doc) for doc in documents[:5]]

        return {
            'collection_name': collection_name,
            'schema': schema,
            'document_count': inserted_count,
            'sample_data': sample_data
        }

    except Exception as e:
        raise Exception(f"Error converting CSV to MongoDB: {str(e)}")


def convert_json_to_mongodb(json_content: bytes, collection_name: str) -> Dict[str, Any]:
    """
    Convert JSON file content to MongoDB collection

    Args:
        json_content: Raw JSON file bytes
        collection_name: Name for the collection

    Returns:
        Dictionary with collection info, schema, and sample data

    Raises:
        Exception: If conversion fails
    """
    try:
        # Sanitize collection name
        collection_name = sanitize_collection_name(collection_name)

        # Drop existing collection if it exists to replace data (as documented)
        if collection_exists(collection_name):
            drop_collection(collection_name)

        # Parse JSON
        data = json.loads(json_content.decode('utf-8'))

        # Ensure it's a list of objects
        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects")

        if not data:
            raise ValueError("JSON array is empty")

        # Convert to pandas DataFrame and back to clean the data
        df = pd.DataFrame(data)

        # Clean column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]

        # Convert DataFrame to list of dictionaries
        # Replace NaN with None for proper JSON serialization
        df = df.where(pd.notnull(df), None)
        documents = df.to_dict('records')

        # Insert documents into MongoDB
        inserted_count = insert_documents(collection_name, documents)

        # Infer schema from documents
        schema = infer_field_types(documents)

        # Get sample data (first 5 documents)
        sample_data = [convert_objectids_to_strings(doc) for doc in documents[:5]]

        return {
            'collection_name': collection_name,
            'schema': schema,
            'document_count': inserted_count,
            'sample_data': sample_data
        }

    except Exception as e:
        raise Exception(f"Error converting JSON to MongoDB: {str(e)}")

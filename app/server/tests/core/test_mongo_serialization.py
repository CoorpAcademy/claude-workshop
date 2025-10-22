"""
Tests for MongoDB ObjectId serialization in query results.

This test suite ensures that all BSON ObjectId instances are properly converted
to JSON-serializable strings in various query scenarios including simple queries,
aggregation pipelines with $lookup, nested structures, and arrays.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId

from core.mongo_processor import (
    convert_objectids_to_strings,
    execute_mongodb_query,
    execute_aggregation_pipeline,
    get_database_schema
)


class TestConvertObjectIdsToStrings:
    """Test the ObjectId conversion utility function"""

    def test_convert_simple_objectid(self):
        """Test conversion of a single ObjectId"""
        obj_id = ObjectId()
        result = convert_objectids_to_strings(obj_id)
        assert isinstance(result, str)
        assert result == str(obj_id)

    def test_convert_dict_with_objectid(self):
        """Test conversion of dictionary with ObjectId fields"""
        obj_id = ObjectId()
        data = {
            "_id": obj_id,
            "name": "test",
            "count": 42
        }
        result = convert_objectids_to_strings(data)
        assert isinstance(result["_id"], str)
        assert result["_id"] == str(obj_id)
        assert result["name"] == "test"
        assert result["count"] == 42

    def test_convert_nested_dict_with_objectids(self):
        """Test conversion of nested dictionaries with multiple ObjectId fields"""
        obj_id1 = ObjectId()
        obj_id2 = ObjectId()
        obj_id3 = ObjectId()
        data = {
            "_id": obj_id1,
            "user_id": obj_id2,
            "profile": {
                "avatar_id": obj_id3,
                "name": "John"
            }
        }
        result = convert_objectids_to_strings(data)
        assert isinstance(result["_id"], str)
        assert isinstance(result["user_id"], str)
        assert isinstance(result["profile"]["avatar_id"], str)
        assert result["_id"] == str(obj_id1)
        assert result["user_id"] == str(obj_id2)
        assert result["profile"]["avatar_id"] == str(obj_id3)
        assert result["profile"]["name"] == "John"

    def test_convert_list_with_objectids(self):
        """Test conversion of lists containing ObjectIds"""
        obj_id1 = ObjectId()
        obj_id2 = ObjectId()
        data = [obj_id1, obj_id2, "regular_string", 123]
        result = convert_objectids_to_strings(data)
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)
        assert result[0] == str(obj_id1)
        assert result[1] == str(obj_id2)
        assert result[2] == "regular_string"
        assert result[3] == 123

    def test_convert_array_of_dicts_with_objectids(self):
        """Test conversion of arrays containing dictionaries with ObjectIds (simulates $lookup results)"""
        obj_id1 = ObjectId()
        obj_id2 = ObjectId()
        data = {
            "_id": obj_id1,
            "name": "User",
            "products": [
                {"_id": obj_id2, "name": "Product A"},
                {"_id": ObjectId(), "name": "Product B"}
            ]
        }
        result = convert_objectids_to_strings(data)
        assert isinstance(result["_id"], str)
        assert isinstance(result["products"][0]["_id"], str)
        assert isinstance(result["products"][1]["_id"], str)
        assert result["_id"] == str(obj_id1)
        assert result["products"][0]["_id"] == str(obj_id2)

    def test_convert_primitive_types_unchanged(self):
        """Test that primitive types are returned unchanged"""
        assert convert_objectids_to_strings("string") == "string"
        assert convert_objectids_to_strings(123) == 123
        assert convert_objectids_to_strings(45.67) == 45.67
        assert convert_objectids_to_strings(True) is True
        assert convert_objectids_to_strings(None) is None

    def test_convert_empty_structures(self):
        """Test conversion of empty dictionaries and lists"""
        assert convert_objectids_to_strings({}) == {}
        assert convert_objectids_to_strings([]) == []

    def test_result_is_json_serializable(self):
        """Test that converted results can be serialized to JSON"""
        obj_id = ObjectId()
        data = {
            "_id": obj_id,
            "nested": {
                "user_id": ObjectId(),
                "items": [
                    {"_id": ObjectId(), "name": "Item 1"}
                ]
            }
        }
        result = convert_objectids_to_strings(data)
        # This should not raise any exception
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        # Verify we can parse it back
        parsed = json.loads(json_str)
        assert parsed["_id"] == str(obj_id)


class TestExecuteMongoDBQuery:
    """Test execute_mongodb_query with ObjectId serialization"""

    @patch('core.mongo_processor.get_mongodb_connection')
    @patch('core.mongo_processor.validate_collection_name')
    @patch('core.mongo_processor.validate_query_structure')
    def test_query_converts_objectids(self, mock_validate_query, mock_validate_name, mock_get_connection):
        """Test that simple queries properly convert ObjectIds"""
        obj_id1 = ObjectId()
        obj_id2 = ObjectId()

        # Mock cursor with documents containing ObjectIds
        mock_cursor = [
            {"_id": obj_id1, "name": "Doc 1"},
            {"_id": obj_id2, "user_id": ObjectId(), "name": "Doc 2"}
        ]

        # Setup mocks - create proper chain
        mock_limit = MagicMock()
        mock_limit.__iter__ = Mock(return_value=iter(mock_cursor))

        mock_sort = MagicMock()
        mock_sort.limit.return_value = mock_limit

        mock_find = MagicMock()
        mock_find.sort.return_value = mock_sort
        mock_find.limit.return_value = mock_limit

        mock_collection = MagicMock()
        mock_collection.find.return_value = mock_find

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_get_connection.return_value = mock_client

        # Execute query
        results = execute_mongodb_query("test_collection", filter_query={"name": "test"})

        # Verify ObjectIds are converted to strings
        assert len(results) == 2
        assert isinstance(results[0]["_id"], str)
        assert isinstance(results[1]["_id"], str)
        assert isinstance(results[1]["user_id"], str)
        assert results[0]["_id"] == str(obj_id1)
        assert results[1]["_id"] == str(obj_id2)

        # Verify result is JSON serializable
        json.dumps(results)


class TestExecuteAggregationPipeline:
    """Test execute_aggregation_pipeline with ObjectId serialization"""

    @patch('core.mongo_processor.get_mongodb_connection')
    @patch('core.mongo_processor.validate_collection_name')
    @patch('core.mongo_processor.validate_aggregation_pipeline')
    def test_aggregation_converts_nested_objectids(self, mock_validate_pipeline, mock_validate_name, mock_get_connection):
        """Test that aggregation results with $lookup properly convert nested ObjectIds"""
        user_id = ObjectId()
        product_id1 = ObjectId()
        product_id2 = ObjectId()

        # Mock aggregation cursor simulating $lookup results
        mock_cursor = [
            {
                "_id": user_id,
                "name": "User 1",
                "local_products": [
                    {"_id": product_id1, "name": "Product A", "price": 100},
                    {"_id": product_id2, "name": "Product B", "price": 200}
                ]
            }
        ]

        # Setup mocks
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value = mock_cursor
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_get_connection.return_value = mock_client

        # Execute aggregation
        pipeline = [{"$lookup": {"from": "products", "localField": "product_ids", "foreignField": "_id", "as": "local_products"}}]
        results = execute_aggregation_pipeline("users", pipeline)

        # Verify all ObjectIds are converted to strings
        assert len(results) == 1
        assert isinstance(results[0]["_id"], str)
        assert results[0]["_id"] == str(user_id)
        assert isinstance(results[0]["local_products"][0]["_id"], str)
        assert isinstance(results[0]["local_products"][1]["_id"], str)
        assert results[0]["local_products"][0]["_id"] == str(product_id1)
        assert results[0]["local_products"][1]["_id"] == str(product_id2)

        # Verify result is JSON serializable
        json.dumps(results)

    @patch('core.mongo_processor.get_mongodb_connection')
    @patch('core.mongo_processor.validate_collection_name')
    @patch('core.mongo_processor.validate_aggregation_pipeline')
    def test_aggregation_converts_various_objectid_fields(self, mock_validate_pipeline, mock_validate_name, mock_get_connection):
        """Test that aggregation handles ObjectIds with different field names"""
        mock_cursor = [
            {
                "_id": ObjectId(),
                "user_id": ObjectId(),
                "product_id": ObjectId(),
                "category_id": ObjectId(),
                "metadata": {
                    "created_by": ObjectId(),
                    "updated_by": ObjectId()
                }
            }
        ]

        # Setup mocks
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value = mock_cursor
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_get_connection.return_value = mock_client

        # Execute aggregation
        results = execute_aggregation_pipeline("test_collection", [{"$match": {}}])

        # Verify all ObjectIds are converted
        result = results[0]
        assert isinstance(result["_id"], str)
        assert isinstance(result["user_id"], str)
        assert isinstance(result["product_id"], str)
        assert isinstance(result["category_id"], str)
        assert isinstance(result["metadata"]["created_by"], str)
        assert isinstance(result["metadata"]["updated_by"], str)

        # Verify result is JSON serializable
        json.dumps(results)


class TestGetDatabaseSchema:
    """Test get_database_schema with ObjectId serialization"""

    @patch('core.mongo_processor.get_mongodb_connection')
    @patch('core.mongo_processor.detect_all_relationships')
    def test_schema_sample_data_converts_objectids(self, mock_detect_relationships, mock_get_connection):
        """Test that schema sample data properly converts ObjectIds"""
        obj_id1 = ObjectId()
        obj_id2 = ObjectId()

        sample_docs = [
            {"_id": obj_id1, "name": "Sample 1", "user_id": ObjectId()},
            {"_id": obj_id2, "name": "Sample 2", "product_id": ObjectId()}
        ]

        # Setup mocks
        mock_collection = MagicMock()
        mock_collection.find.return_value.limit.return_value = sample_docs
        mock_collection.count_documents.return_value = 2

        mock_db = MagicMock()
        mock_db.list_collection_names.return_value = ["test_collection"]
        mock_db.__getitem__.return_value = mock_collection
        mock_db.command.return_value = {"size": 0, "storageSize": 0}

        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_get_connection.return_value = mock_client

        mock_detect_relationships.return_value = []

        # Get schema
        schema = get_database_schema()

        # Verify ObjectIds in sample_data are converted
        collection_schema = schema["collections"]["test_collection"]
        sample_data = collection_schema["sample_data"]

        assert len(sample_data) == 2
        assert isinstance(sample_data[0]["_id"], str)
        assert isinstance(sample_data[0]["user_id"], str)
        assert isinstance(sample_data[1]["_id"], str)
        assert isinstance(sample_data[1]["product_id"], str)
        assert sample_data[0]["_id"] == str(obj_id1)
        assert sample_data[1]["_id"] == str(obj_id2)

        # Verify fields samples are also converted
        assert isinstance(collection_schema["fields"]["_id"]["sample"], str)

        # Verify entire schema is JSON serializable
        json.dumps(schema)

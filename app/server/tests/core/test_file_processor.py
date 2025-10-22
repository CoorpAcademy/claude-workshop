import pytest
import json
import pandas as pd
import os
import io
from pathlib import Path
from unittest.mock import patch, MagicMock
from bson import ObjectId
from core.file_processor import convert_csv_to_mongodb, convert_json_to_mongodb


@pytest.fixture
def test_assets_dir():
    """Get the path to test assets directory"""
    return Path(__file__).parent.parent / "assets"


class TestFileProcessor:

    def test_convert_csv_to_mongodb_success(self, test_assets_dir):
        # Load real CSV file
        csv_file = test_assets_dir / "test_users.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()

        table_name = "users"
        result = convert_csv_to_mongodb(csv_data, table_name)

        # Verify return structure
        assert result['collection_name'] == table_name
        assert 'schema' in result
        assert 'document_count' in result
        assert 'sample_data' in result

        # Test the returned data
        assert result['document_count'] == 4  # 4 users in test file
        assert len(result['sample_data']) <= 5  # Should return up to 5 samples
        
        # Verify schema has expected columns (cleaned names)
        assert 'name' in result['schema']
        assert 'age' in result['schema'] 
        assert 'city' in result['schema']
        assert 'email' in result['schema']
        
        # Verify sample data structure and content
        john_data = next((item for item in result['sample_data'] if item['name'] == 'John Doe'), None)
        assert john_data is not None
        assert john_data['age'] == 25
        assert john_data['city'] == 'New York'
        assert john_data['email'] == 'john@example.com'
    
    def test_convert_csv_to_mongodb_field_cleaning(self, test_assets_dir):
        # Test column name cleaning with real file
        csv_file = test_assets_dir / "column_names.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()

        table_name = "test_users"
        result = convert_csv_to_mongodb(csv_data, table_name)
        
        # Verify columns were cleaned in the schema
        assert 'full_name' in result['schema']
        assert 'birth_date' in result['schema']
        assert 'email_address' in result['schema']
        assert 'phone_number' in result['schema']
        
        # Verify sample data has cleaned column names and actual content
        sample = result['sample_data'][0]
        assert 'full_name' in sample
        assert 'birth_date' in sample
        assert 'email_address' in sample
        assert sample['full_name'] == 'John Doe'
        assert sample['birth_date'] == '1990-01-15'
    
    def test_convert_csv_to_mongodb_with_inconsistent_data(self, test_assets_dir):
        # Test with CSV that has inconsistent row lengths - should raise error
        csv_file = test_assets_dir / "invalid.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()

        table_name = "inconsistent_table"

        # Pandas will fail on inconsistent CSV data
        with pytest.raises(Exception) as exc_info:
            convert_csv_to_mongodb(csv_data, table_name)

        assert "Error converting CSV to MongoDB" in str(exc_info.value)
    
    def test_convert_json_to_mongodb_success(self, test_assets_dir):
        # Load real JSON file
        json_file = test_assets_dir / "test_products.json"
        with open(json_file, 'rb') as f:
            json_data = f.read()

        table_name = "products"
        result = convert_json_to_mongodb(json_data, table_name)

        # Verify return structure
        assert result['collection_name'] == table_name
        assert 'schema' in result
        assert 'document_count' in result
        assert 'sample_data' in result

        # Test the returned data
        assert result['document_count'] == 3  # 3 products in test file
        assert len(result['sample_data']) == 3
        
        # Verify schema has expected columns
        assert 'id' in result['schema']
        assert 'name' in result['schema']
        assert 'price' in result['schema']
        assert 'category' in result['schema']
        assert 'in_stock' in result['schema']
        
        # Verify sample data structure and content
        laptop_data = next((item for item in result['sample_data'] if item['name'] == 'Laptop'), None)
        assert laptop_data is not None
        assert laptop_data['price'] == 999.99
        assert laptop_data['category'] == 'Electronics'
        assert laptop_data['in_stock'] == True
    
    def test_convert_json_to_mongodb_invalid_json(self):
        # Test with invalid JSON
        json_data = b'invalid json'
        table_name = "test_table"

        with pytest.raises(Exception) as exc_info:
            convert_json_to_mongodb(json_data, table_name)

        assert "Error converting JSON to MongoDB" in str(exc_info.value)
    
    def test_convert_json_to_mongodb_not_array(self):
        # Test with JSON that's not an array
        json_data = b'{"name": "John", "age": 25}'
        table_name = "test_table"

        with pytest.raises(Exception) as exc_info:
            convert_json_to_mongodb(json_data, table_name)

        assert "JSON must be an array of objects" in str(exc_info.value)

    def test_convert_json_to_mongodb_empty_array(self):
        # Test with empty JSON array
        json_data = b'[]'
        table_name = "test_table"

        with pytest.raises(Exception) as exc_info:
            convert_json_to_mongodb(json_data, table_name)

        assert "JSON array is empty" in str(exc_info.value)

    @patch('core.file_processor.insert_documents')
    @patch('core.file_processor.collection_exists')
    def test_csv_upload_converts_objectids_to_strings(self, mock_collection_exists, mock_insert_documents):
        """Test that CSV upload converts ObjectId _id fields to strings for JSON serialization"""
        mock_collection_exists.return_value = False

        # Mock insert_documents to simulate MongoDB adding ObjectId _id fields
        def mock_insert_with_objectids(collection_name, documents):
            for doc in documents:
                doc['_id'] = ObjectId()
            return len(documents)

        mock_insert_documents.side_effect = mock_insert_with_objectids

        # Create test CSV data
        csv_data = b"name,age,city\nJohn,25,NYC\nJane,30,LA"

        result = convert_csv_to_mongodb(csv_data, "test_collection")

        # Verify sample_data contains string _id fields, not ObjectId instances
        assert 'sample_data' in result
        assert len(result['sample_data']) > 0

        for doc in result['sample_data']:
            if '_id' in doc:
                # _id should be a string, not an ObjectId
                assert isinstance(doc['_id'], str)
                assert not isinstance(doc['_id'], ObjectId)

        # Verify the entire result is JSON-serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @patch('core.file_processor.insert_documents')
    @patch('core.file_processor.collection_exists')
    def test_json_upload_converts_objectids_to_strings(self, mock_collection_exists, mock_insert_documents):
        """Test that JSON upload converts ObjectId _id fields to strings for JSON serialization"""
        mock_collection_exists.return_value = False

        # Mock insert_documents to simulate MongoDB adding ObjectId _id fields
        def mock_insert_with_objectids(collection_name, documents):
            for doc in documents:
                doc['_id'] = ObjectId()
            return len(documents)

        mock_insert_documents.side_effect = mock_insert_with_objectids

        # Create test JSON data
        json_data = b'[{"name": "Product1", "price": 100}, {"name": "Product2", "price": 200}]'

        result = convert_json_to_mongodb(json_data, "test_collection")

        # Verify sample_data contains string _id fields, not ObjectId instances
        assert 'sample_data' in result
        assert len(result['sample_data']) > 0

        for doc in result['sample_data']:
            if '_id' in doc:
                # _id should be a string, not an ObjectId
                assert isinstance(doc['_id'], str)
                assert not isinstance(doc['_id'], ObjectId)

        # Verify the entire result is JSON-serializable
        json_str = json.dumps(result)
        assert json_str is not None
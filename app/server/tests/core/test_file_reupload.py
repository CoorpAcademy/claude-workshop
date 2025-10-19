"""
Tests for file re-upload behavior to prevent duplicate documents.

This module tests that re-uploading files with the same name replaces
the existing collection rather than creating duplicate documents.
"""

import pytest
import io
import json
import os
from typing import Generator
from pymongo import MongoClient
from core.file_processor import convert_csv_to_mongodb, convert_json_to_mongodb
from core.mongo_processor import get_mongodb_connection, drop_collection


@pytest.fixture
def test_collection_name() -> str:
    """Provide a unique test collection name"""
    return "test_reupload_collection"


@pytest.fixture
def cleanup_test_collection(test_collection_name: str) -> Generator:
    """Clean up test collection after test"""
    yield
    try:
        drop_collection(test_collection_name)
    except Exception:
        pass


def get_collection_document_count(collection_name: str) -> int:
    """Helper to get document count from a collection"""
    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
    db = client[db_name]
    return db[collection_name].count_documents({})


class TestFileReupload:
    """Test file re-upload behavior"""

    def test_csv_reupload_replaces_collection(self, test_collection_name: str, cleanup_test_collection):
        """Test that re-uploading CSV file replaces collection instead of duplicating"""
        # Create sample CSV data with 5 users
        csv_data = """name,email,age
Alice,alice@example.com,30
Bob,bob@example.com,25
Charlie,charlie@example.com,35
Diana,diana@example.com,28
Eve,eve@example.com,32"""

        csv_bytes = csv_data.encode('utf-8')

        # First upload
        result1 = convert_csv_to_mongodb(csv_bytes, test_collection_name)
        assert result1['document_count'] == 5
        count1 = get_collection_document_count(test_collection_name)
        assert count1 == 5

        # Second upload (same file)
        result2 = convert_csv_to_mongodb(csv_bytes, test_collection_name)
        assert result2['document_count'] == 5
        count2 = get_collection_document_count(test_collection_name)
        assert count2 == 5  # Should still be 5, not 10

        # Verify no duplicates by checking for unique emails
        client = get_mongodb_connection()
        db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
        db = client[db_name]
        collection = db[test_collection_name]

        # Count documents with Alice's email (should be exactly 1)
        alice_count = collection.count_documents({"email": "alice@example.com"})
        assert alice_count == 1, f"Expected 1 Alice document, found {alice_count}"

    def test_json_reupload_replaces_collection(self, cleanup_test_collection):
        """Test that re-uploading JSON file replaces collection instead of duplicating"""
        test_collection_name = "test_json_reupload"

        # Create sample JSON data with 5 products
        json_data = [
            {"name": "Product A", "price": 10.99, "category": "Electronics"},
            {"name": "Product B", "price": 25.50, "category": "Books"},
            {"name": "Product C", "price": 15.00, "category": "Clothing"},
            {"name": "Product D", "price": 8.99, "category": "Food"},
            {"name": "Product E", "price": 100.00, "category": "Electronics"}
        ]

        json_bytes = json.dumps(json_data).encode('utf-8')

        # First upload
        result1 = convert_json_to_mongodb(json_bytes, test_collection_name)
        assert result1['document_count'] == 5
        count1 = get_collection_document_count(test_collection_name)
        assert count1 == 5

        # Second upload (same file)
        result2 = convert_json_to_mongodb(json_bytes, test_collection_name)
        assert result2['document_count'] == 5
        count2 = get_collection_document_count(test_collection_name)
        assert count2 == 5  # Should still be 5, not 10

        # Verify no duplicates by checking for unique product names
        client = get_mongodb_connection()
        db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
        db = client[db_name]
        collection = db[test_collection_name]

        # Count documents with Product A (should be exactly 1)
        product_a_count = collection.count_documents({"name": "Product A"})
        assert product_a_count == 1, f"Expected 1 Product A document, found {product_a_count}"

        # Cleanup
        try:
            drop_collection(test_collection_name)
        except Exception:
            pass

    def test_multiple_reuploads_maintain_count(self, cleanup_test_collection):
        """Test that multiple re-uploads maintain correct document count"""
        test_collection_name = "test_multiple_reupload"

        # Create sample CSV with 3 users
        csv_data = """name,email,age
User1,user1@example.com,20
User2,user2@example.com,21
User3,user3@example.com,22"""

        csv_bytes = csv_data.encode('utf-8')

        # Upload 5 times in a row
        for i in range(5):
            result = convert_csv_to_mongodb(csv_bytes, test_collection_name)
            assert result['document_count'] == 3, f"Upload {i+1}: Expected 3 documents, got {result['document_count']}"

            # Verify collection has exactly 3 documents after each upload
            count = get_collection_document_count(test_collection_name)
            assert count == 3, f"Upload {i+1}: Expected 3 total documents, found {count}"

        # Final verification: ensure no duplicates
        client = get_mongodb_connection()
        db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
        db = client[db_name]
        collection = db[test_collection_name]

        # Check each user appears exactly once
        for user_num in [1, 2, 3]:
            email = f"user{user_num}@example.com"
            user_count = collection.count_documents({"email": email})
            assert user_count == 1, f"Expected 1 {email} document, found {user_count}"

        # Cleanup
        try:
            drop_collection(test_collection_name)
        except Exception:
            pass
